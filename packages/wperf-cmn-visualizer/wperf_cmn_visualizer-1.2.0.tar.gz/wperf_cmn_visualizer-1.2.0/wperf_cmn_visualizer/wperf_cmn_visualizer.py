# BSD 3-Clause License
#
# Copyright (c) 2025, Arm Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Main application class for wperf_cmn_visualizer
"""

import argparse
from typing import Optional, List
from sys import argv
from itertools import product
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QFrame, QDialog
)
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtCore import QRect

from wperf_cmn_visualizer.config import Config
from wperf_cmn_visualizer.topology_loader import cmn_topology_loader
from wperf_cmn_visualizer.telemetry_loader import cmn_telemetry_loader
from wperf_cmn_visualizer.cmn import CMN
from wperf_cmn_visualizer.cmn_metrics import CMNMetrics
from wperf_cmn_visualizer.renderer import CMNRenderer
from wperf_cmn_visualizer.time_scrubber import TimeScrubber
from wperf_cmn_visualizer.tabbing import TabbedInterface
from wperf_cmn_visualizer.help import HelpPage
from wperf_cmn_visualizer.time_scrubber import TimelineCanvas, _global_timeline_sync
from wperf_cmn_visualizer.input_dialog import InputDialog


class wperfCmnVisualizer:
    """
    GUI application class for the WindowsPerf CMN Visualizer.
    Handles window creation, layout, and launching the Qt execution loop.
    """

    def __init__(self, args: argparse.Namespace):
        """
        Initialise the application with the provided topology file.
        Args:
            args (argparse.Namespace): Parsed command line arguments.
        """

        # pick up CLI arguments
        self.args = args
        self.topology_json_file = self.args.topology
        self.telemetry_csv_dir = self.args.telemetry

        # init GUI control flow and main settings
        self.app = QApplication(argv)

        if self.topology_json_file is None and self.telemetry_csv_dir is None:
            dialog = InputDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.topology_json_file, self.telemetry_csv_dir = dialog.get_inputs()
            else:
                quit()

        # open main window
        self.window = QMainWindow()
        self._set_up_window()

        # load topology
        self.topology = cmn_topology_loader()
        if self.topology_json_file is not None:
            self.topology.load_topology_from_file(self.topology_json_file)
        else:
            quit()

        # construct CMN object
        self.cmn: CMN = CMN(self.topology.data)

        # load telemetry if available
        self.telemetry = cmn_telemetry_loader()
        if self.telemetry_csv_dir:
            self.telemetry.load_telemetry_from_path(self.telemetry_csv_dir)
            self.cmn_metrics: Optional[CMNMetrics] = CMNMetrics(self.cmn, self.telemetry.data, self.app.palette())
        else:
            self.cmn_metrics = None

        # set up UI in main window.
        self._setup_widgets()
        self._setup_help_dialog()

    def _setup_widgets(self):
        """
        Set up the main widgets and layout.
        +--------------+
        |     CMN      |
        |              |
        |______________|
        |   Time Line  |
        +--------------+
        """
        # Create central widget and main layout
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # create tabs
        self.tabs = TabbedInterface()
        self.tabs.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.tabs, 1)

        self.renderers: List[CMNRenderer] = []
        for i, j in product(
            range(self.cmn.num_meshes),
            range(self.cmn_metrics.num_metrics if self.cmn_metrics else 1)
        ):
            self.renderers.append(
                CMNRenderer(self.tabs, self.app.palette(), self.cmn, self.cmn_metrics)
            )
            self.renderers[-1].cmn_idx = i
            self.renderers[-1].cmn_metrics_metric_id = j
            self.renderers[-1].canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            label = f"CMN {i}" + (
                f", metric: {self.cmn_metrics.metric_names[j]}"
                if self.cmn_metrics else ""
            )
            self.tabs.add_tab(self.renderers[-1].canvas, label)

        # construct TimeScrubber class only if metrics are available
        if self.cmn_metrics is not None:
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            main_layout.addWidget(separator)

            self.time_scrubber: TimeScrubber = TimeScrubber(
                central_widget, self.cmn_metrics, height=100
            )
            self.time_scrubber.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            main_layout.addWidget(self.time_scrubber, 0)  # no stretch, fixed height
            # connect scrubbing event broadcasted from TimeScrubber
            for renderer in self.renderers:
                _global_timeline_sync.time_changed.connect(renderer._on_time_changed)

        # Update Layout of UI
        central_widget.updateGeometry()

    def _set_up_window(self):
        """
        Configure the main application window's appearance and geometry.
        """
        self.window.setWindowTitle(Config.MAIN_WINDOW_TITLE)

        # centre window on screen
        screen = QGuiApplication.primaryScreen()
        screen_size = screen.size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        width = int(screen_width * Config.MAIN_WINDOW_INIT_SIZE_RATIO)
        height = int(screen_height * Config.MAIN_WINDOW_INIT_SIZE_RATIO)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        min_width, min_height = Config.MAIN_WINDOW_MIN_SIZE
        if width < min_width or height < min_height:
            width = min_width
            height = min_height

        self.window.setGeometry(QRect(x, y, width, height))
        self.window.setMinimumSize(min_width, min_height)

    def _setup_help_dialog(self):
        """Set up the global help dialog and F1 shortcut."""
        shortcut_key = QKeySequence("?")
        self.help_dialog = HelpPage(self.window, shortcut_key, self.cmn, self.cmn_metrics)
        self.help_dialog.hide()  # Start hidden

        # Center the dialog on parent
        if self.window:
            parent_rect = self.window.geometry()
            dialog_size = self.help_dialog.size()
            x = parent_rect.x() + (parent_rect.width() - dialog_size.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_size.height()) // 2
            self.help_dialog.move(x, y)

        # bind "?" key to toggle help window.
        self.help_shortcut = QShortcut(shortcut_key, self.window)
        self.help_shortcut.activated.connect(self.toggle_help_dialog)

    def toggle_help_dialog(self):
        """Toggle the help dialog visibility."""
        if self.help_dialog.isVisible():
            self.help_dialog.hide()
        else:
            self.help_dialog.show()
            self.help_dialog.raise_()
            self.help_dialog.activateWindow()

    def run(self) -> int:
        """
        Start the application's main event loop.
        Returns:
            int: to be used as exit code
        """
        try:
            self.window.show()
            return self.app.exec()
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1

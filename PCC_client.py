# -*- coding: utf-8 -*-

__version__ = "45.0.0"

"""
Physiology Command Center
(C) 2019
@author: Christopher Ward (christow@bcm.edu, ward.chris.s@gmail.com)
Created as part of the Russell Ray Molecular Neurobiology Group's
Autoresuscitation Project
contributions to this project include code, concepts, or consultation from 
several individuals including Russell Ray, Eunice Aissi, Dipak Patel, 
Mariana Garcia Costa, Savannah Lusk, Brandon Ruiz, and Kevin Jiang.
The current iteration is intended to function primarily as a headless
client for control via web app while delivering similar control of assays
such as the neonate autoresuscitation reflex assay.

Additional changes include transition away from pygame to pyside6,
and general refactoring and reoganization of modules and functions.
"""

# %% import libraries
# external libraries
import argparse
import logging
import os
import psutil
from PySide6.QtCore import QTimer, QFile
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtUiTools import QUiLoader
import pyqtgraph
import sys


# internal libraries
import DATA
import DETECTORS
import EFFECTORS
from MinervaPlugin import plugin as mp
import SETTINGS
import STREAMS


# %% define functions
def get_mac():
    interfaces = psutil.net_if_addrs()
    for i_name, i_addr in interfaces.items():
        for addr in i_addr:
            if addr.family == psutil.AF_LINK or addr.family == psutil.AF_PACKET:
                return addr.address


# %% define classes
class MainWindow(QWidget):
    def __init__(self, version, ui):
        super().__init__()

        self.ui = ui
        # migrate ui children to parent level of class
        for att, val in ui.__dict__.items():
            setattr(self, att, val)

        self.setWindowTitle(f"PCC-client {version}")

        # get mac - used for registering with Minerva Server
        self.mac = get_mac()
        print(self.mac)

        # create a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # load settings
        self.settings = SETTINGS.SETTINGS()

        # populate data class
        self.data = DATA.DATA()

        # configure i/o
        self.settings.sim_mode = 1  # dev !!!
        if self.settings.sim_mode == 1:
            self.arduino_stream = STREAMS.SimulatedArduino()
            self.labjack_stream = STREAMS.SimulatedDataReader()
        else:
            self.arduino_stream = STREAMS.StreamArduino()
            self.labjack_stream = STREAMS.StreamDataReader()

        self.minerva_stream = mp.Plugin(mp.PluginRegistration(self.mac), self.logger)

        # set up timers

        self.pulse_counter = 0

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.action_pulse_timer)

        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self.action_stream_timer)

    def action_start_timers(self):
        self.pulse_timer.start(1000)
        self.stream_timer.start(10)

    def action_pulse_timer(self):
        print(self.pulse_counter)
        self.pulse_counter += 1

        if self.pulse_counter >= 10:
            sys.exit()

    def action_stream_timer(self):
        pass
        # collect labjack stream

        # collect arduino stream

        # collect minerva stream

        # append to output

        # refresh gui (if needed)

    ## Timers (to create event loops)
    # receiver_timer

    # broadcast_timer

    # status_pulse_timer

    # experiment_loop_timer

    ## METHODS
    # read in data from streams

    # send out data

    # send out pulse

    # experiment loop


# %% define main
def main():
    # describe font location

    # parse arguments
    parser = argparse.ArgumentParser("PCC_client")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-s", "--simulation", action="store_true")
    parsed_args = parser.parse_args()

    args = sys.argv.copy()

    if not parsed_args.interactive:
        args.append(f"--platform")
        args.append("offscreen")

    print("startup")
    print(sys.argv)

    print(args)

    loader = QUiLoader()
    app = QApplication(args)

    ui_file = QFile(os.path.join(os.path.dirname(__file__), "PCC_client.ui"))

    ui = loader.load(ui_file)

    window = MainWindow(__version__, ui)

    window.version_info = {
        "main": __version__,
        "DETECTORS": DETECTORS.__version__,
        "EFFECTORS": EFFECTORS.__version__,
        "STREAMS": STREAMS.__version__,
        "SETTINGS": SETTINGS.__version__,
    }
    if parsed_args.simulation:
        window.settings.sim_mode = 1

    window.ui.show()
    window.action_start_timers()
    print("running")
    sys.exit(app.exec())


# run main
if __name__ == "__main__":
    main()

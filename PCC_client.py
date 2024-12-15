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
from PySide6.QtCore import QFile, Qt, QTimer
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
    def __init__(self, version, ui, parsed_args):
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

        # override and set sim mode if CL option provided
        if parsed_args.simulation:
            self.settings.sim_mode = 1

        # populate data class
        self.data = DATA.DATA()

        # configure i/o
        # !!! self.settings.sim_mode = 1  # dev !!!
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

        # prepare graph windows
        self.prepare_graphs()

    def prepare_graphs(self):
        self.graph1 = pyqtgraph.PlotWidget()
        self.graph2 = pyqtgraph.PlotWidget()
        self.legend1 = self.graph1.addLegend()
        self.legend1.setColumnCount(5)
        self.legend1.setOffset([1, -1])
        self.legend1.anchor(itemPos=(0.5, 1), parentPos=(0.5, 1), offset=(0, 15))
        self.legend2 = self.graph2.addLegend()
        self.legend2.setColumnCount(5)
        self.legend2.setOffset([1, -1])
        self.legend2.anchor(itemPos=(0.5, 1), parentPos=(0.5, 1), offset=(0, 15))
        self.verticalLayout_graph_1.addWidget(self.graph1)
        self.verticalLayout_graph_2.addWidget(self.graph2)
        self.graph1.setBackground("w")
        self.graph2.setBackground("w")

        self.line1_threshold_1 = self.graph1.plot(
            x=[-5, 0],
            y=[self.settings.thresh_flow, self.settings.thresh_flow],
            name="threshold 1",
            pen=pyqtgraph.mkPen("Red", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line1_threshold_2 = self.graph1.plot(
            x=[-5, 0],
            y=[self.settings.thresh2_flow, self.settings.thresh2_flow],
            name="threshold 2",
            pen=pyqtgraph.mkPen("Green", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line1_baseline = self.graph1.plot(
            x=[-5, 0],
            y=[self.settings.baseline_flow, self.settings.baseline_flow],
            name="baseline",
            pen=pyqtgraph.mkPen("Black", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line1 = self.graph1.plot(
            x=self.data.time,
            y=self.data.pneumo,
            name="line 1",
            pen=pyqtgraph.mkPen("Blue", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.markers1 = self.graph1.plot(
            x=[i for i in self.data.breath_list],
            y=[0 for i in self.data.breath_list],
            name="markers 1",
            pen=pyqtgraph.mkPen("Blue", width=1, style=Qt.PenStyle.SolidLine),
            symbol="o",
            symbolBrush=(255, 0, 0),
            symbolPen=(0, 0, 0),
            symbolSize=8,
        )

        self.line2_threshold_1 = self.graph2.plot(
            x=[-5, 0],
            y=[self.settings.thresh_ecg1, self.settings.thresh_ecg1],
            name="threshold 1",
            pen=pyqtgraph.mkPen("Red", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line2_threshold_2 = self.graph2.plot(
            x=[-5, 0],
            y=[self.settings.thresh_ecg2, self.settings.thresh_ecg2],
            name="threshold 2",
            pen=pyqtgraph.mkPen("Green", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line2_baseline = self.graph2.plot(
            x=[-5, 0],
            y=[self.settings.baseline_ecg, self.settings.baseline_ecg],
            name="baseline",
            pen=pyqtgraph.mkPen("Black", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.line2 = self.graph2.plot(
            x=self.data.time,
            y=self.data.ecg,
            name="line 2",
            pen=pyqtgraph.mkPen("Blue", width=1, style=Qt.PenStyle.SolidLine),
            symbol=None,
            symbolBrush=None,
            symbolPen=None,
            symbolSize=14,
        )
        self.markers2 = self.graph2.plot(
            x=[i for i in self.data.beat_list],
            y=[0 for i in self.data.beat_list],
            name="markers 2",
            pen=pyqtgraph.mkPen("Blue", width=1, style=Qt.PenStyle.SolidLine),
            symbol="o",
            symbolBrush=(255, 0, 0),
            symbolPen=(0, 0, 0),
            symbolSize=8,
        )

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
        # Pull results out of the Queue in a blocking manner.
        if not self.labjack_stream.data.empty():
            result = self.labjack_stream.data.get(True, 1)

            # If there were errors, print that.
            if result["errors"] != 0:
                # !!!
                self.data.errors += result["errors"]
                self.data.error_list.append(result["errors"])
                self.data.missed += result["missed"]
                print(
                    "+++++ Total Errors: %s, Total Missed: %s +++++" % (errors, missed)
                )

            # Convert the raw bytes (result['result']) to voltage data.
            if self.settings.sim_mode == 0:
                processed_result = self.labjack_stream.device.processStreamData(
                    result["result"]
                )
            elif self.settings.sim_mode == 1:
                processed_result = result["result"]
            # parse channels and migrate into short term streams
            flow_channel = self.labjack_stream.channel_list[
                self.labjack_stream.channel_dict["FLOW"]
            ]
            ecg_channel = self.labjack_stream.channel_list[
                self.labjack_stream.channel_dict["ECG"]
            ]
            self.data.new_pneumo = processed_result[f"AIN{flow_channel}"]
            self.data.new_ecg = processed_result[f"AIN{ecg_channel}"]

            self.data.pneumo = (self.data.pneumo + self.data.new_pneumo)[
                self.data.window * -2 :
            ]
            self.data.ecg = (self.data.ecg + self.data.new_ecg)[self.data.window * -2 :]

            # apply inversion/filter as appropriate
            if self.settings.flow_filt_state == 1:
                if self.settings.INVERT_FLOW == 1:
                    trimmed_pneumo = [
                        -1 * i for i in DETECTORS.butterFilt(self.data.pneumo, 50)
                    ][self.data.window * -1 :]
                else:
                    trimmed_pneumo = DETECTORS.butterFilt(self.data.pneumo, 50)[
                        self.data.window * -1 :
                    ]
            else:
                if self.settings.INVERT_FLOW == 1:
                    trimmed_pneumo = [-1 * i for i in self.data.pneumo][
                        self.data.window * -1 :
                    ]
                else:
                    trimmed_pneumo = self.data.pneumo[self.data.window * -1 :]
            if self.settings.ecg_filt_state == 1:
                if self.settings.INVERT_ECG == 1:
                    trimmed_ecg = [
                        -1 * i for i in DETECTORS.basicFilt(self.data.ecg, 1000, 60, 30)
                    ][self.data.window * -1 :]
                else:
                    trimmed_ecg = [
                        i for i in DETECTORS.basicFilt(self.data.ecg, 1000, 60, 30)
                    ][self.data.window * -1 :]
            else:
                if self.settings.INVERT_ECG == 1:
                    trimmed_ecg = [-1 * i for i in self.data.ecg][
                        self.data.window * -1 :
                    ]
                else:
                    trimmed_ecg = self.data.ecg[self.data.window * -1 :]

            # call breaths and beats with thresh as appropriate
            if self.data.flow_thresh_to_use == 2:
                flow_thresh = self.settings.thresh2_flow
            else:
                flow_thresh = self.settings.thresh_flow

            self.data.breath_list = DETECTORS.basic_breathcall(
                trimmed_pneumo, self.data.time, self.settings.baseline_flow, flow_thresh
            )
            self.data.beat_list = DETECTORS.beat_caller(
                trimmed_ecg,
                self.data.time,
                absthresh=self.settings.thresh_ecg1,
                minRR=self.settings.minRR_ecg,
            )

            # update plot
            self.line1.setData(self.data.time, trimmed_pneumo)
            self.line2.setData(self.data.time, trimmed_ecg)
            self.markers1.setData(
                [v["TS-I"] for v in self.data.breath_list.values()],
                [0 for i in self.data.breath_list],
            )
            self.markers2.setData(
                list(self.data.beat_list["ts"]),
                [0 for i in range(self.data.beat_list.shape[0])],
            )

            # call breaths

            # call heartbeats

        # collect arduino stream

        # collect minerva stream

        # append to output

        # refresh gui (if needed)

        # check for effector or auto_advance

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

    window = MainWindow(__version__, ui, parsed_args)

    window.version_info = {
        "main": __version__,
        "DETECTORS": DETECTORS.__version__,
        "EFFECTORS": EFFECTORS.__version__,
        "STREAMS": STREAMS.__version__,
        "SETTINGS": SETTINGS.__version__,
    }

    window.ui.show()
    window.action_start_timers()
    print("running")
    sys.exit(app.exec())


# run main
if __name__ == "__main__":
    main()

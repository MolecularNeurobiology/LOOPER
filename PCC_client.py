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
import numpy
import os
import psutil
from PySide6.QtCore import QFile, Qt, QTimer, QObject, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog, QInputDialog, QLineEdit
from PySide6.QtUiTools import QUiLoader
import pyqtgraph
import sys
from datetime import datetime


# internal libraries
import fm_tools
import DATA
import DETECTORS
import EFFECTORS
from MinervaPlugin import plugin as mp
import SETTINGS
import STREAMS
import STAGES


# %% define functions
def get_mac():
    interfaces = psutil.net_if_addrs()
    for i_name, i_addr in interfaces.items():
        for addr in i_addr:
            if addr.family == psutil.AF_LINK or addr.family == psutil.AF_PACKET:
                return addr.address


# %% define classes
class LogEmitter(QObject):
    """
    LogEmitter is used by QTextEditLogger to enable access to
    QObject Signal for emitting to and
    """

    log = Signal(str)


class QTextEditLogger(logging.Handler):
    """
    QTextEditLogger serves as a logging handler to display logging messages
    within the GUI if running the client in interactive mode
    """

    def __init__(self, text_edit_widget):
        super().__init__()
        self.widget = text_edit_widget
        self.widget.setReadOnly(True)
        self.widget.setStyleSheet("background-color: lightgray;")

        self.log_emitter = LogEmitter()
        self.log_emitter.log.connect(self.widget.insertHtml)

    def emit(self, record):
        msg = self.format(record)
        # color code messages
        if "| INFO |" in msg:
            msg = f'<span style="color:black">{msg}</span><br>'
        elif "| DEBUG |" in msg:
            msg = f'<span style="color:green">{msg}</span><br>'
        elif "| WARNING |" in msg:
            msg = f'<span style="color:red">{msg}</span><br>'
        elif "| ERROR |" in msg:
            msg = f'<span style="color:red"><strong>{msg}</strong></span><br>'
        else:
            msg = f'<span style="color:black"><strong>{msg}</strong></span><br>'
        self.log_emitter.log.emit(msg)


class MainWindow(QWidget):
    def __init__(self, version, ui, parsed_args, app):
        super().__init__()

        self.app = app

        self.ui = ui
        # migrate ui children to parent level of class
        for att, val in ui.__dict__.items():
            setattr(self, att, val)

        self.setWindowTitle(f"PCC-client {version}")
        self.label_Title_and_Version.setText(f"PCC-client {version}")

        # get mac - used for registering with Minerva Server
        self.mac = get_mac()
        print(self.mac)

        # create a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logging_format = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s\n"
        )
        self.logging_text_browser = QTextEditLogger(self.textBrowser_Status)
        self.logging_text_browser.setFormatter(self.logging_format)
        self.logger.addHandler(self.logging_text_browser)

        # test logging output
        self.logger.debug("DEBUG")
        self.logger.info("INFO")
        self.logger.warning("WARNING")
        self.logger.error("ERROR")

        # create some default variable values
        self.stage_dict = {}
        self.automated = False

        # populate data class
        self.data = DATA.DATA()

        # load default settings
        self.logger.debug("loading settings")
        self.settings = SETTINGS.SETTINGS()

        # override settings with CL arguments if provided
        if parsed_args.simulation:
            self.settings.sim_mode = 1

        # set kill mode if CL option provided
        self.kill_after_count = parsed_args.kill

        # configure i/o
        if self.settings.sim_mode == 1:
            self.logger.debug("Simulation Mode")
            self.arduino_stream = STREAMS.SimulatedArduino(self.logger)
            self.labjack_stream = STREAMS.SimulatedDataReader(self.logger)
            self.settings.config_path = "testing.config"
        else:
            self.logger.debug("Live Stream Mode")
            self.arduino_stream = STREAMS.StreamArduino(self.logger)
            self.labjack_stream = STREAMS.StreamDataReader(self.logger)

        self.stream_start_ts = datetime.now()

        self.minerva_stream = mp.Plugin(mp.PluginRegistration(self.mac), self.logger)
        self.minerva_stream.start()
        self.minerva_stream_reader = STREAMS.MinervaReceiver(
           self.minerva_stream, self.logger
        )

        self.output_file_writer = EFFECTORS.OutputFileWriter(output_path=self.settings.output_path, pcc = self)

        self.prepare_stages()

        ## TODO !!! load settings based on signal from Minerva

        # set up timers

        self.pulse_counter = 0

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.action_pulse_timer)

        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self.action_stream_timer)

        # prepare graph windows
        self.prepare_graphs()

        # connect buttons and widgets
        self.pushButton_Send_Arduino_Command.clicked.connect(
            self.action_send_serial_to_arduino
        )
        self.pushButton_Next_Stage.clicked.connect(self.action_next_stage)
        self.comboBox_Jump_To_Stage.currentTextChanged.connect(
            self.action_jump_to_stage
        )
        self.pushButton_Save.clicked.connect(self.action_set_output_file_path)

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

    def prepare_stages(self):
        # clear comboBox_Jump_To_Stage
        self.logger.info("preparing STAGES")
        self.comboBox_Jump_To_Stage.clear()
        # repopulate comboBox_Jump_To_Stage
        self.comboBox_Jump_To_Stage.addItems(
            [k for k in self.settings.Mode_settings.keys()]
        )
        # create a dictionary of stages
        for k in self.settings.Mode_settings.keys():
            self.logger.debug(f"adding STAGE: {k}")
            self.stage_dict[k] = getattr(STAGES, k)(k, self)
        # register stage specific data attributes
        for k, v in self.stage_dict.items():
            v.register_data()

        # load the active stage (provide settings and data class as arguments)
        self.active_stage = self.stage_dict[list(self.settings.Mode_settings.keys())[0]]
        self.active_stage.on_load()

        # stage methods
        # on_load
        # on_exit ... runs just before moving to the next stage (includes a default next stage if multiple following stages are possible, next stage can also be an argument or derived from an ordered list of stages)
        # event_loop
        # exit_condition_test ... runs at end of event loop

        pass

    def action_jump_to_stage(self):
        self.logger.info(
            f"jumping to stage: {self.comboBox_Jump_To_Stage.currentText()}"
        )
        if not self.automated:
            self.active_stage.on_exit()
        self.automated = False
        self.active_stage = self.stage_dict[self.comboBox_Jump_To_Stage.currentText()]
        self.active_stage.on_load()

    
    def action_set_output_file_path(self):
        #if manual oride checkbox checked, manually set filepath, else use automated partsing
        if self.checkBox_Oride.isChecked():
            self.settings.output_path = QFileDialog.getSaveFileName(self,caption="select output filename",filter="PCC Output (*.pcco)")
        else:
            self.logger.debug(f"generating save path... config: {self.settings.config_path}")
            self.settings.output_path,_ = fm_tools.generate_rig_save_path(
                QInputDialog.getText(self, "Scan Barcode","RUID:",QLineEdit.Normal)[0],
                config_path=self.settings.config_path
            )
        self.logger.info(f"output_path set: {self.settings.output_path}")
        self.output_file_writer.output_path = self.settings.output_path
        self.label_output_path.setText(self.settings.output_path)
        self.output_file_writer.write_header()

    def action_next_stage(self):
        self.active_stage.on_jump_exit()
        #self.logger.debug(f"stages: {len(self.stage_dict)}")
        #self.logger.debug(f"{self.comboBox_Jump_To_Stage.currentIndex()}")
        #if self.comboBox_Jump_To_Stage.currentIndex() == len(self.stage_dict) - 1:
        #    self.logger.error(
        #        'Already at last stage - use "Jump To" function to choose a stage'
        #    )
        #else:
        #    self.comboBox_Jump_To_Stage.setCurrentIndex(
        #        self.comboBox_Jump_To_Stage.currentIndex() + 1
        #    )

    def action_send_serial_to_arduino(self):
        command = self.lineEdit_Arduino_Command.text()
        self.logger.info(f"Sending: {command}")
        self.arduino_stream.sendCommand(command)
        self.lineEdit_Arduino_Command.clear()

    def action_start_timers(self):
        self.pulse_timer.start(1000)
        self.stream_timer.start(10)

    def action_pulse_timer(self):
        print(self.pulse_counter)
        self.pulse_counter += 1

        if self.kill_after_count and self.pulse_counter >= self.kill_after_count:
            self.kill_app()
            

            #app.quit()
            sys.exit()

    def kill_app(self):
        # wait on threads for clean exit?
        self.minerva_stream.stop()

    def action_stream_timer(self):
        # determine current time in stream
        self.data.current_time = datetime.now()
        self.data.stream_duration = round(
            (self.data.current_time - self.stream_start_ts).seconds + 
            ((self.data.current_time - self.stream_start_ts).microseconds)/1000000,
            6
        )
        # reset labjack stream if needed

        # collect labjack stream !!! move this over into a function call
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
                    "+++++ Total Errors: %s, Total Missed: %s +++++" % (self.data.errors, self.data.missed)
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

            new_samples = len(self.data.new_pneumo)
            time_increment = round(new_samples/self.labjack_stream.scan_frequency,3)

            self.data.data_time += time_increment
            self.data.time = [round((int(self.data.data_time * self.data.data_frequency) - self.data.window + i) / 1000, 3) for i in range(self.data.window)]

            self.data.current_lag = self.data.stream_duration - self.data.data_time

            self.data.pneumo = (self.data.pneumo + self.data.new_pneumo)[
                self.data.window * -2 :
            ]
            self.data.ecg = (self.data.ecg + self.data.new_ecg)[self.data.window * -2 :]

            # apply inversion/filter as appropriate
            if self.settings.flow_filt_state == 1:
                if self.settings.INVERT_FLOW == 1:
                    self.data.trimmed_pneumo = [
                        -1 * i for i in DETECTORS.butterFilt(self.data.pneumo, 50)
                    ][self.data.window * -1 :]
                else:
                    self.data.trimmed_pneumo = DETECTORS.butterFilt(self.data.pneumo, 50)[
                        self.data.window * -1 :
                    ]
            else:
                if self.settings.INVERT_FLOW == 1:
                    self.data.trimmed_pneumo = [-1 * i for i in self.data.pneumo][
                        self.data.window * -1 :
                    ]
                else:
                    self.data.trimmed_pneumo = self.data.pneumo[self.data.window * -1 :]
            if self.settings.ecg_filt_state == 1:
                if self.settings.INVERT_ECG == 1:
                    self.data.trimmed_ecg = [
                        -1 * i for i in DETECTORS.basicFilt(self.data.ecg, 1000, 60, 30)
                    ][self.data.window * -1 :]
                else:
                    self.data.trimmed_ecg = [
                        i for i in DETECTORS.basicFilt(self.data.ecg, 1000, 60, 30)
                    ][self.data.window * -1 :]
            else:
                if self.settings.INVERT_ECG == 1:
                    self.data.trimmed_ecg = [-1 * i for i in self.data.ecg][
                        self.data.window * -1 :
                    ]
                else:
                    self.data.trimmed_ecg = self.data.ecg[self.data.window * -1 :]

        # call breaths and beats with thresh as appropriate
        if self.data.flow_thresh_to_use == 2:
            flow_thresh = self.settings.thresh2_flow
        else:
            flow_thresh = self.settings.thresh_flow

        self.data.breath_list = DETECTORS.basic_breathcall(
            self.data.trimmed_pneumo,
            self.data.time,
            self.settings.baseline_flow,
            flow_thresh,
        )
        self.data.beat_list = DETECTORS.beat_caller(
            self.data.trimmed_ecg,
            self.data.time,
            absthresh=self.settings.thresh_ecg1,
            minRR=self.settings.minRR_ecg,
        )
        # update instantaneous summary parameters
        self.data.avg_bsd = abs(
            numpy.average(self.data.trimmed_pneumo) - self.settings.baseline_flow
        )
        if self.data.breath_list is None or len(self.data.breath_list) < 2:
            self.data.avg_bpm = "<12"
            self.data.avg_tv = "-----"
            self.data.avg_tt = 999
            self.data.cv_tt = 999
            self.data.avg_dvtv = 999

            self.label_BPM.setText(f"VF: {self.data.avg_bpm}")
        else:
            self.data.avg_tt = numpy.average(
                [
                    self.data.breath_list[i]["TT"]
                    for i in self.data.breath_list
                    if "TT" in self.data.breath_list[i].keys()
                ]
            )
            self.data.cv_tt = (
                numpy.std(
                    [
                        self.data.breath_list[i]["TT"]
                        for i in self.data.breath_list
                        if "TT" in self.data.breath_list[i].keys()
                    ]
                )
                / self.data.avg_tt
            )
            self.data.avg_tv = numpy.average(
                [
                    self.data.breath_list[i]["iTV"]
                    for i in self.data.breath_list
                    if "iTV" in self.data.breath_list[i].keys()
                ]
            )
            self.data.avg_bpm = (
                60 / self.data.avg_tt
            )  # this creates a 'less' transformed BPM (division transform) - relationship between TT and BPM modified by Irregularity
            self.data.avg_dvtv = numpy.average(
                [
                    self.data.breath_list[i]["DVTV"]
                    for i in self.data.breath_list
                    if "DVTV" in self.data.breath_list[i].keys()
                ]
            )

            self.label_BPM.setText(f"VF: {self.data.avg_bpm:.0F}")

        if self.data.beat_list is None or len(self.data.beat_list) < 5:
            self.data.avg_hr = "low"
            self.data.avg_rr = 999
            self.data.cv_rr = 999

            self.label_HR.setText(f"HR: {self.data.avg_hr}")

        else:
            self.data.avg_rr = self.data.beat_list["rr"].mean()
            self.data.avg_hr = 60 / self.data.avg_rr
            self.data.cv_rr = self.data.beat_list["rr"].std() / self.data.avg_rr

            self.label_HR.setText(f"HR: {self.data.avg_hr:.0F}")


        if self.data.breath_list:
            self.data.ts_last_breath = max(max(self.data.breath_list.keys()),self.data.ts_last_breath)
        self.data.SLB = self.data.time[-1] - self.data.ts_last_breath

        # update plot
        #self.graph1.setXRange(self.data.data_time - self.data.window/self.data.data_frequency,self.data.data_time,padding=0)
        #self.graph2.setXRange(self.data.data_time - self.data.window/self.data.data_frequency,self.data.data_time,padding=0)
        self.line1.setData(self.data.rel_time, self.data.trimmed_pneumo)
        self.line2.setData(self.data.rel_time, self.data.trimmed_ecg)
        self.markers1.setData(
            [v["TS-I"] - self.data.data_time for v in self.data.breath_list.values()],
            [0 for i in self.data.breath_list],
        )
        self.markers2.setData(
            [i - self.data.data_time for i in list(self.data.beat_list["ts"])],
            [0 for i in range(self.data.beat_list.shape[0])],
        )

        # update widgets
        self.label_Lag.setText(f"Lag: {self.data.current_lag:.2F}")
        # self.label_Lag.setText(f"t{self.data.stream_duration}-{self.data.data_time}")
        self.label_SLB.setText(f"SLB: {self.data.SLB:.3F}")
        self.label_Time_In_Stage.setText(f"time in stage (sec): {self.data.time_in_stage_seconds}")


        # collect arduino stream
        Arduino_Dump_Toggle = 0
        self.arduino_list = []

        # !!! TODO do we need to worry about arduino outputs being split across entries?
        if self.arduino_stream.data.empty() == False:
            Arduino_Dump_Toggle = 1
            arduino_out = self.arduino_stream.data.get_nowait()
            self.arduino_list = [
                i.decode() for i in arduino_out.split(b"\r\n") if i != b" " and i != b""
            ]
            self.arduino_string = "".join(self.arduino_list)
            for i in self.arduino_list:
                self.logger.info(f"ARDUINO:{i}")
                ### !!! TODO finish this to process arduino outputs for triggering stage changes
                if self.settings.Challenge_phrase in i:
                    if Challenge_Toggle == 0:
                        Challenge_Timer = datetime.now()
                    Challenge_Toggle = 1

        # collect minerva stream
        if self.minerva_stream_reader.data:
            self.logger.debug(self.minerva_stream_reader.data)
            print(f"minerva - {self.minerva_stream_reader.data}")
            self.minerva_stream_reader.data = None

        # append to output


        # refresh gui (if needed)
        self.label_Time_In_Stage.setText(f"{self.data.time_in_stage_seconds:.0f} sec")
        # check for effector or auto_advance
        self.active_stage.event_loop()

    ## Timers (to create event loops)
    # receiver_timer

    # broadcast_timer

    # status_pulse_timer

    # experiment_loop_timer

    ## METHODS

    # send out pulse

    # experiment loop


# %% define main
def main():
    # describe font location

    # parse arguments
    parser = argparse.ArgumentParser("PCC_client")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-s", "--simulation", action="store_true")
    parser.add_argument("-k", "--kill", type=int, help="kill process after __ seconds")
    parsed_args = parser.parse_args()

    args = sys.argv.copy()

    if not parsed_args.interactive:
        args.append(f"--platform")
        args.append("offscreen")

    print("startup")
    print(sys.argv)

    print(args)

    loader = QUiLoader()
    global app
    app = QApplication(args)

    ui_file = QFile(os.path.join(os.path.dirname(__file__), "PCC_client.ui"))

    ui = loader.load(ui_file)

    window = MainWindow(__version__, ui, parsed_args, app)

    app.aboutToQuit.connect(window.kill_app)

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
    #app.exec()
    sys.exit(app.exec())


# run main
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(e)
        traceback.print_exc()
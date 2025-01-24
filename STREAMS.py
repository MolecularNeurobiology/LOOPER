# -*- coding: utf-8 -*-

__version__ = "0.1.0"


import queue as Queue
from scipy import signal
import sys
import threading
from copy import deepcopy
from datetime import datetime
import math
from PySide6.QtCore import QTimer
import u6
import serial


# Arduino Related
class StreamArduino(object):
    def __init__(self, logger):

        self.logger = logger
        self.device = serial.Serial()
        self.device.baudrate = 9600
        self.data = Queue.Queue()
        self.finished = True
        self.Connected_Arduino = False

        try:
            # search for Arduino on comports
            arduino_list = []
            device_list = [d for d in serial.tools.list_ports.comports()]
            for d in device_list:
                if d.manufacturer is not None and "Arduino" in d.manufacturer:
                    arduino_list.append(d)
                elif d.description is not None and "Arduino" in d.description:
                    arduino_list.append(d)

            if len(arduino_list) > 1:
                if self.logger:
                    self.logger.warning("multiple arduinos found, using first")
                self.device.port = arduino_list[0].device
            elif len(arduino_list) == 1:
                self.device.port = arduino_list[0].device
            else:
                if self.logger:
                    self.logger.warning("unable to locate arduino")
            self.device.timeout = 1
            self.device.open()
            self.Connected_Arduino = True

            self.data = Queue.Queue()
            self.finished = False
        except:
            self.Connected_Arduino = False

    def sendCommand(self, command):
        self.device.write(command.encode())

    def readStreamData(self):
        while not self.finished:
            self.finished = False
            returnText = self.device.read(1000)
            self.data.put_nowait(deepcopy(returnText))


class SimulatedArduino:
    def __init__(self, logger):
        self.logger = logger
        self.data = Queue.Queue()
        self.listener = Queue.Queue()
        self.finished = False
        self.Connected_Arduino = True
        self.device = "Simulated_Arduino"
        # self.update_interval_ms = 10000
        # self.arduino_sim_timer = QTimer()
        # self.arduino_sim_timer.timeout.connect(self.readStreamData)
        # self.arduino_sim_timer.start(self.update_interval_ms)

        if self.logger:
            self.logger.info("using simulated arduino")

    def sendCommand(self, command):
        self.listener.put_nowait(command)
        self.readStreamData()

    def write(self, command):  # do i need this method !!! TODO
        self.listener.put_nowait(command)

    def translate_command_to_response(self, command):
        translation_dict = {
            b"[C": b"calibration-sim",
            b"[R": b"room air-sim",  # update
            b"[A": b"challenge gas-sim",  # update
            b"[U": b"startup sent-sim",
            b"[S": b"standby sent-sim",
            b"[Z": b"abort sent-sim",
            b"[D": b"shutdown-sim",
            b"[E": b"finish startup-sim",
            b"unknown": b"unknown command",
            "[C": b"calibration-sim",
            "[R": b"room air-sim",  # update
            "[A": b"challenge gas-sim",  # update
            "[U": b"startup sent-sim",
            "[S": b"standby sent-sim",
            "[Z": b"abort sent-sim",
            "[D": b"shutdown-sim",
            "[E": b"finish startup-sim",
            "unknown": b"unknown command",
        }

        translated_command = translation_dict.get(command[:2], b"unknown")
        print(translated_command)
        return translated_command

    def readStreamData(self):
        print("reading")
        self.finished = False
        while not self.finished:
            if self.listener.empty() == False:
                command = self.listener.get_nowait()
                response = self.translate_command_to_response(command)
                self.data.put_nowait(deepcopy(response))
            else:
                self.finished = True


# LabJack Related
class SimulatedDataReader:
    def __init__(self, logger):

        self.logger = logger
        self.finished = True
        if self.logger:
            self.logger.info("using simulated labjack interface")

        self.channel_list = [0, 1, 2, 3, 4, 5]
        self.channel_key = ["FLOW", "ECG", "BT", "RH", "O2", "CO2"]
        self.channel_dict = dict(zip(self.channel_key, self.channel_list))
        self.number_channels = len(self.channel_list)

        self.data = Queue.Queue()
        self.start = 0
        self.current = 0
        self.duration = 0.0
        self.captured_time = 0

        self.lag = 0
        self.missed = []
        self.errors = []
        self.data_sim_timer = QTimer()
        self.data_sim_timer.timeout.connect(self.readStreamData)

        self.sim_sig_3Hz = [math.sin(i * 6.28 * 3) for i in range(60000)]
        self.sim_sig_30Hz = [math.sin(i * 6.28 * 30) * 5 for i in range(60000)]
        self.counter = 0
        self.counter_limit = 60000
        self.scan_frequency = 1000
        self.num_channels = 6
        self.sample_frequency = self.scan_frequency * self.num_channels
        self.update_interval_ms = 100
        self.samples_per_interval = int(
            self.update_interval_ms / 1000 * self.sample_frequency
        )

        self.data_sim_timer.start(self.update_interval_ms)

    def setDIOState(self, *args):
        pass

    def close(self, *args):
        pass

    def get_labjack_temperature(self):
        return 42

    def readStreamData(self):
        self.finished = False
        self.start = datetime.now()
        self.readCount = 0

        if self.counter + self.update_interval_ms >= self.counter_limit:
            self.counter = 0

        if not self.finished:

            returnDict = {
                "errors": 0,
                "missed": [],
                "result": {
                    "AIN0": self.sim_sig_3Hz[
                        self.counter : self.counter + self.update_interval_ms
                    ],
                    "AIN1": self.sim_sig_30Hz[
                        self.counter : self.counter + self.update_interval_ms
                    ],
                    "AIN2": [0.2 for i in range(self.update_interval_ms)],
                    "AIN3": [0.3 for i in range(self.update_interval_ms)],
                    "AIN4": [0.4 for i in range(self.update_interval_ms)],
                    "AIN5": [0.5 for i in range(self.update_interval_ms)],
                },
            }
            if returnDict is None:
                print("No stream data")

            self.data.put_nowait(deepcopy(returnDict))

            self.missed += returnDict["missed"]
            self.readCount += 1
            self.counter += self.update_interval_ms
            self.current = datetime.now()

    def stopStreamData(self):
        self.finished = True


class StreamDataReader(object):
    def __init__(self):
        self.device = u6.U6()

        self.channel_list = [0, 1, 2, 3, 4, 5]
        self.channel_key = ["FLOW", "ECG", "BT", "RH", "O2", "CO2"]
        self.channel_dict = dict(zip(self.channel_key, self.channel_list))
        self.number_channels = len(self.channel_list)

        self.data = Queue.Queue()
        self.readCount = 0
        self.missed = 0
        self.finished = True
        self.start = 0
        self.current = 0
        self.duration = 0.0
        self.captured_time = 0
        self.scan_frequency = 1000
        self.sample_frequency = self.scan_frequency * self.number_channels
        self.update_interval_ms = 100
        self.samples_per_interval = int(
            self.update_interval / 1000 * self.sample_frequency
        )

        self.lag = 0

        self.device.getCalibrationData()
        try:
            self.device.streamStop()
            print("stream found running - now stopped")
        except:
            print("labjack pre-stream checked")

        self.device.streamConfig(
            NumChannels=self.number_channels,
            ChannelNumbers=self.channel_list,
            ChannelOptions=[0 for i in self.channel_list],
            SettlingFactor=1,
            ResolutionIndex=1,
            ScanFrequency=self.scan_frequency,
        )

        # set packets per datastream call - maybe this is not neccessary - just go with default rate?
        self.device.packetsPerRequest = int(self.samples_per_interval / 25)
        self.device.setDIOState(0, 0)
        self.device.setDIOState(1, 0)
        self.device.setDIOState(2, 0)
        self.device.setDIOState(3, 0)

    def get_labjack_temperature(self):
        return self.device.getTemperature() - 273.15

    def readStreamData(self):
        self.finished = False

        print("Start stream.")

        try:
            # Try to stop stream mode. Ignore exception if it fails.
            self.device.streamStop()
            print("Prior Stream Terminated")
        except:
            print("No Prior Stream")

        try:
            self.start = datetime.now()
            self.readCount = 0
            self.device.streamStart()

            while not self.finished:
                # Calling with convert = False, because we are going to convert in
                # the main thread.
                returnDict = next(self.device.streamData(convert=False))
                if returnDict is None:
                    print("No stream data")
                    continue

                self.data.put_nowait(deepcopy(returnDict))

                self.missed += returnDict["missed"]
                self.readCount += 1
                self.current = datetime.now()

            print("Stream stopped.\n")
            self.device.streamStop()

        except Exception:
            try:
                # Try to stop stream mode. Ignore exception if it fails.
                self.device.streamStop()
            except:
                pass
            self.finished = True
            e = sys.exc_info()[1]
            print("readStreamData exception: %s %s" % (type(e), e))

    def stopStreamData(self):
        try:
            # Try to stop stream mode. Ignore exception if it fails.
            self.finished = True
        except:
            pass


# Minerva related
class MinervaReceiver:
    def __init__(self, minerva_plugin_object):
        pass

    def process_data(self, data_object, settings_object, callbacks_object):
        pass

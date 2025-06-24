# -*- coding: utf-8 -*-

__version__ = "0.1.0"

"""
collection of classes and functions that are primarily for transmitting output
"""

# %% import libraries
import pickle
import gzip

# %% define functions


def processStatus(status, device, ser, ADC, logger=None):
    device.setDIOState(0, 0)
    device.setDIOState(1, 0)
    device.setDIOState(2, 0)
    device.setDIOState(3, 0)
    now = datetime.now()
    print(status)
    serialtext = ""

    if status["standby"] == 1:
        serialtext = "<S,0,0>"

    if status["startup"] == 1 and status["startup_ready"] < 1:
        serialtext = "<U,0,0>"
        try:
            ser.write(serialtext.encode())
            if logger:
                log_to_file(logger, "{} - sent".format(serialtext))
            print("{} - sent".format(serialtext))
            status["startup_ready"] = 1
        except Exception as e:
            print(f'unable to transmit "{serialtext}" via serial io\n{e}')
            status["startup_ready"] = 1
        return status

    if status["streaming"] == 1:
        device.setDIOState(0, 1)

    if status["ready to save"] == 1:
        pass
    if status["calibration"] == 1:
        device.setDIOState(1, 1)
        serialtext = "<C,{},0>".format(ADC["Duration_Cal"])
        status["pulse"]["calibration"]["state"] = 1
        status["pulse"]["calibration"]["start"] = now
    if status["challenge air"] == 1:
        device.setDIOState(3, 1)
        serialtext = "<R,{},0>".format(ADC["Position_RA"])
        status["pulse"]["challenge air"]["state"] = 1
        status["pulse"]["challenge air"]["start"] = now
    if status["challenge gas"] == 1:
        device.setDIOState(2, 1)
        serialtext = "<A,{},{}>".format(ADC["Position_Gas"], ADC["Duration_Prefill"])
        status["pulse"]["challenge gas"]["state"] = 1
        status["pulse"]["challenge gas"]["start"] = now
    else:
        pass

    if serialtext != "":

        try:
            ser.write(serialtext.encode())
            log_to_file(logger, "{} - sent".format(serialtext))
            if logger:
                logger.info("{} - sent".format(serialtext))
        except Exception as e:
            if logger:
                logger.warning(f'unable to transmit "{serialtext}" via serial io\n{e}')

    return status


class MinervaBroadcaster:
    def __init__(self, minerva_plugin_object):
        pass

    def broadcast_data(self, data_object):
        pass

    def broadcast_settings(self, settings_object):
        pass


class OutputFileWriter:
    def __init__(self, output_path=None, pcc=None):
        self.output_path = output_path
        self.pcc = pcc

    def write_header_p(self):
        if self.output_path:
            with open(self.output_path, "ab") as open_file:
                pickle.dump(
                    self.pcc.version_info | {
                        "stage": self.pcc.active_stage.name,
                        "lj_columns":self.pcc.labjack_stream.channel_key,
                        "arduino_columns":"stream",
                        "minerva_columns":"stream"
                        },
                    open_file,
                )
            self.pcc.logger.debug("header written")
        else:
            self.pcc.logger.warning("no output path set")

    def write_data_p(self):
        if self.output_path:
            with open(self.output_path, "ab") as open_file:
                pickle.dump(
                    {
                        "lj": self.pcc.processed_result, 
                        "arduino": self.pcc.arduino_list, 
                        "minerva": self.pcc.minerva_stream_reader.data
                    },
                    open_file
                )
            pass
        pass

    def write_header(self):
        if self.output_path:
            with gzip.open(self.output_path, "a", 9) as open_file:
                open_file.write(pickle.dumps(
                    self.pcc.version_info | {
                        "stage": self.pcc.active_stage.name,
                        "lj_columns":self.pcc.labjack_stream.channel_key,
                        "arduino_columns":"stream",
                        "minerva_columns":"stream"
                        },
                ))
            self.pcc.logger.debug("header written")
        else:
            self.pcc.logger.warning("no output path set")

    def write_data(self):
        if self.output_path:
            with gzip.open(self.output_path, "a", 9) as open_file:
                open_file.write(pickle.dumps(
                    {
                        "lj": self.pcc.processed_result, 
                        "arduino": self.pcc.arduino_list, 
                        "minerva": self.pcc.minerva_stream_reader.data
                    }
                ))
            pass
        pass

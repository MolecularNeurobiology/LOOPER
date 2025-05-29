# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from datetime import datetime

#!!! TODO, clean this up - a lot of these are not needed and can be moved to STAGE specific data


class DATA:
    def __init__(self):
        # short term
        self.window = 5000  # !!! this should probably be a setting ...
        self.data_frequency = 1000 # this should probably be a setting ...
        self.time = [round(-5 + i / 1000, 3) for i in range(self.window)]
        self.rel_time = [round(-5 + i / 1000, 3) for i in range(self.window)]
        self.pneumo = [0 for i in range(self.window)]
        self.trimmed_pneumo = [0 for i in range(self.window)]
        self.ecg = [0 for i in range(self.window)]
        self.trimmed_ecg = [0 for i in range(self.window)]

        self.data_time = 0

        self.breath_list = []
        self.beat_list = []

        self.flow_thresh_to_use = 1


        

        # instantaneous_arrays
        # self.new_time = []
        # self.new_pneumo = []
        # self.new_ecg = []
        self.errors = []
        

        # instantaneous_values
        self.avg_bpm = None
        self.avg_tt = None
        self.cv_tt = None
        self.avg_rr = None
        self.avg_hr = None
        self.cv_rr = None
        self.avg_tv = None
        self.avg_bsd = None
        self.avg_dvtv = None
        self.SLB = None

        self.ts_last_breath = 0
        self.stream_duration = 0

        self.current_lag = None

        # stage values
        
        self.start_time = datetime.now()
        self.current_time = datetime.now()
        self.time_in_stage = 0
        self.time_in_stage_seconds = 0
        # self.current_mode = None
        # self.flow_thresh_to_use = 1

        # self.cur_status_dict = {
        #     "standby": 0,
        #     "startup": 0,
        #     "streaming": 0,
        #     "ready to save": 0,
        #     "calibration": 0,
        #     "challenge air": 0,
        #     "challenge gas": 0,
        #     "pulse": {
        #         "calibration": {"state": 0, "start": 0, "pin": 1},
        #         "challenge air": {"state": 0, "start": 0, "pin": 3},
        #         "challenge gas": {"state": 0, "start": 0, "pin": 2},
        #     },
        #     "startup_ready": 0,
        # }

        # persistent / semi-persistant
        self.challenge_history = {}
        self.recovery_bpm = None
        self.recovery_hr = None
        # self.stage_start_time = None
        self.prev_mode = -1
        self.error_list = []
        self.missed = 0

        self.recent_log_entries = ""

        # self.old_status_dict = {
        #     "standby": 0,
        #     "startup": 0,
        #     "streaming": 0,
        #     "ready to save": 0,
        #     "calibration": 0,
        #     "challenge air": 0,
        #     "challenge gas": 0,
        #     "pulse": {
        #         "calibration": {"state": 0, "start": 0, "pin": 1},
        #         "challenge air": {"state": 0, "start": 0, "pin": 3},
        #         "challenge gas": {"state": 0, "start": 0, "pin": 2},
        #     },
        #     "startup_ready": 0,
        # }

    def prepare_data_payload(self,attr_dict = None):
        """
        prepare a json string populated from the attributes specified by attr_list
        """

        """
        TIME_SERIES = "time_series"
        TIMESTAMP = "timestamp"
        SINGLE_VALUE = "single_value"
        STATUS = "status"
        DEBUG = "debug"
        """

        if attr_dict is None:
            attr_dict = {
                "trimmed_pneumo":"TIME_SERIES",
                "trimmed_ecg":"TIME_SERIES",
                "breath_list":"TIMESTMP",
                "beat_list":"TIMESTAMP",
                "avg_bpm":"SINGLE_VALUE",
                "avg_hr":"SINGLE_VALUE",
                "arduino_startup_motion_tested":"STATUS",
                "recent_log_entries":"DEBUG"
            }

        self.payload = {"signals":[]}
        for k,v in attr_dict:
            if v == "DEBUG":
                self.payload["signals"].append({"name":k,"type":"debug","data":getattr(self.data,k)})
                
            if v == "STATUS":
                self.payload["signals"].append({"name":k,"type":"status","data":getattr(self.data,k)})
                
            if v == "SINGLE_VALUE":
                self.payload["signals"].append({"name":k,"type":"single_value","data":getattr(self.data,k)})
                
            if v == "TIMESTAMP":
                self.payload["signals"].append(
                    {
                    "name":k,
                    "type":"timestamp",
                    "data":[
                        {"x":"""x value""","y":1} for i in getattr(self.data,k)
                    ]
                    }
                    )
                
            if v == "TIME_SERIES":
                self.payload["signals"].append({
                    "name":k,
                    "type":"time_series",
                    "xUnit":seconds,

                    "data":[
                        {"x":self.time[i],"y":getattr(self.data,k)[i]} for i in range(len(self.time))
                    ]
                }
                )
                pass
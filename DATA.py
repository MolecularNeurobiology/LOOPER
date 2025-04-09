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

    def prepare_data_json(attr_list):
        """
        prepare a json string populated from the attributes specified by attr_list
        """
        pass

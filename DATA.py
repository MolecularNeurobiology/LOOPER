# -*- coding: utf-8 -*-

__version__ = "0.1.0"


class DATA:
    def __init__(self):
        # short term
        self.window = 5000  # !!! this should probably be a setting ...
        self.time = [i for i in range(self.window)]
        self.pneumo = [0 for i in range(self.window)]
        self.ecg = [0 for i in range(self.window)]

        self.breath_list = []
        self.beat_list = []

        # instantaneous_arrays
        self.new_time = []
        self.new_pneumo = []
        self.new_ecg = []
        self.errors = []

        # instantaneous_values
        self.avg_bpm = None
        self.avg_hr = None
        self.avd_tv = None
        self.current_time = None
        self.curreng_lag = None
        self.current_mode = None

        self.cur_status_dict = {
            "standby": 0,
            "startup": 0,
            "streaming": 0,
            "ready to save": 0,
            "calibration": 0,
            "challenge air": 0,
            "challenge gas": 0,
            "pulse": {
                "calibration": {"state": 0, "start": 0, "pin": 1},
                "challenge air": {"state": 0, "start": 0, "pin": 3},
                "challenge gas": {"state": 0, "start": 0, "pin": 2},
            },
            "startup_ready": 0,
        }

        # persistent / semi-persistant
        self.challenge_history = {}
        self.recovery_bpm = None
        self.recovery_hr = None
        self.stage_start_time = None
        self.prev_mode = -1
        self.error_list = []
        self.missed = 0

        self.old_status_dict = {
            "standby": 0,
            "startup": 0,
            "streaming": 0,
            "ready to save": 0,
            "calibration": 0,
            "challenge air": 0,
            "challenge gas": 0,
            "pulse": {
                "calibration": {"state": 0, "start": 0, "pin": 1},
                "challenge air": {"state": 0, "start": 0, "pin": 3},
                "challenge gas": {"state": 0, "start": 0, "pin": 2},
            },
            "startup_ready": 0,
        }

    def prepare_data_json(attr_list):
        """
        prepare a json string populated from the attributes specified by attr_list
        """
        pass

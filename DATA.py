# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from datetime import datetime

#!!! TODO, clean this up - a lot of these are not needed and can be moved to STAGE specific data


class DATA:
    def __init__(self):
        # short term
        self.window = 5000  # !!! this should probably be a setting ...
        self.data_frequency = 1000  # this should probably be a setting ...
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

        self.error_dict = {}

        self.advanceable = True

        # instantaneous_arrays
        self.errors = [] # !!! is this actually used

        # instantaneous_values
        # self.avg_bpm = None
        self.avg_vf = None
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

        self.PCC_client_status = "N/A"

        # stage values (#!!! are these actually used?)
        self.start_time = datetime.now()
        self.current_time = datetime.now()
        self.time_in_stage = 0
        self.time_in_stage_seconds = 0

        # persistent / semi-persistant
        

        self.prev_mode = -1
        self.error_list = [] # !!! is this actually used
        self.missed = 0

        self.recent_log_entries = ""

        # register entries for minerva payloads
        self.minerva_attr_dict = {
            "trimmed_pneumo": {"sig_type": "TIME_SERIES"},
            "trimmed_ecg": {"sig_type": "TIME_SERIES"},
            "breath_list": {
                "sig_type": "TIMESTAMP",
                "displayWith": "trimmed_pneumo",
            },
            "beat_list": {"sig_type": "TIMESTAMP", "displayWith": "trimmed_ecg"},
            "avg_vf": {"sig_type": "SINGLE_VALUE"},
            "avg_hr": {"sig_type": "SINGLE_VALUE"},
            "arduino_startup_motion_tested": {"sig_type": "STATUS"},
            "recent_log_entries": {"sig_type": "DEBUG"},
            "error_state": {"sig_type": "STATUS"},
            "error_state_text": {"sig_type": "DEBUG"},
            "time_in_stage_seconds": {"sig_type": "DURATION"}
        }

        

    def prepare_data_payload(self, attr_dict=None):
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
                "trimmed_pneumo": {"sig_type": "TIME_SERIES"},
                "trimmed_ecg": {"sig_type": "TIME_SERIES"},
                "breath_list": {
                    "sig_type": "TIMESTAMP",
                    "displayWith": "trimmed_pneumo",
                },
                "beat_list": {"sig_type": "TIMESTAMP", "displayWith": "trimmed_ecg"},
                "avg_vf": {"sig_type": "SINGLE_VALUE"},
                "avg_hr": {"sig_type": "SINGLE_VALUE"},
                "arduino_startup_motion_tested": {"sig_type": "STATUS"},
                "recent_log_entries": {"sig_type": "DEBUG"},
                "error_state": {"sig_type": "STATUS"},
                "error_state_text": {"sig_type": "DEBUG"},
                "quality_status":{"sig_type": "DEBUG"},
                "qb_time_running_sec":{"sig_type":"SINGLE_VALUE"},
                "baseline_vf":{"sig_type": "SINGLE_VALUE"},
                "baseline_hr":{"sig_type":"SINGLE_VALUE"}
            }
            # updated datas

        signal_payload = {"signals": []}
        for k, v in attr_dict.items():
            if v["sig_type"] == "DEBUG":
                signal_payload["signals"].append(
                    {"name": v.get("name",k), "type": "debug", "data": getattr(self, k)}
                )

            if v["sig_type"] == "STATUS":
                signal_payload["signals"].append(
                    {"name": v.get("name",k), "type": "status", "data": getattr(self, k)}
                )

            if v["sig_type"] == "SINGLE_VALUE":
                signal_payload["signals"].append(
                    {"name": v.get("name",k), "type": "single_value", "data": getattr(self, k)}
                )

            if v["sig_type"] == "TIMESTAMP":
                timestamp_data = getattr(self, k, [])

                # Handle different data types for timestamp signals
                if hasattr(timestamp_data, 'columns') and 'ts' in timestamp_data.columns:
                    # DataFrame case (like beat_list from beat_caller)
                    numeric_timestamps = list(timestamp_data['ts'])
                elif isinstance(timestamp_data, dict):
                    # Dictionary case (like breath_list from basic_breathcall)
                    numeric_timestamps = list(timestamp_data.keys())
                elif isinstance(timestamp_data, list):
                    # List case - filter to only include numeric time values
                    numeric_timestamps = [
                        time_value for time_value in timestamp_data
                        if time_value is not None and isinstance(time_value, (int, float))
                    ]
                else:
                    # Fallback for other types
                    numeric_timestamps = []

                signal_payload["signals"].append(
                    {
                        "name": v.get("name",k),
                        "type": "timestamp",
                        "displayWith": v["displayWith"],
                        "data": [
                            {"x": time_value, "y": 1} for time_value in numeric_timestamps
                        ],
                    }
                )

            if v["sig_type"] == "TIME_SERIES":
                signal_payload["signals"].append(
                    {
                        "name": v.get("name",k),
                        "type": "time_series",
                        "xUnit": "seconds",
                        "data": [
                            {"x": self.time[i], "y": getattr(self, k)[i]}
                            for i in range(len(self.time))
                        ],
                    }
                )

        return signal_payload

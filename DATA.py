# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from datetime import datetime

#!!! TODO, clean this up - a lot of these are not needed and can be moved to STAGE specific data


class DATA:
    def __init__(self):
        # short term
        self.window = 5000  # !!! this should probably be a setting ...
        self.data_frequency = 1000  # this should probably be a setting ...
        # Downsampling configuration for stream payloads
        self.stream_downsample_factor = 25  # Reduce from 5000 to ~200 points
        self.stream_target_points = self.window // self.stream_downsample_factor  # ~200 points

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
        DURATION = "duration"
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
                # Get the full signal data
                signal_data = getattr(self, k)
                time_data = self.time

                # Downsample the data to reduce payload size while maintaining signal fidelity
                downsampled_time, downsampled_signal = self.downsample_signal_data(time_data, signal_data)

                # Create data points from downsampled data
                data_points = [
                    {"x": downsampled_time[i], "y": downsampled_signal[i]}
                    for i in range(len(downsampled_time))
                ]

                if data_points:
                    min_x = min(point["x"] for point in data_points)
                    max_x = max(point["x"] for point in data_points)

                    # Add some padding to the window
                    x_range = max_x - min_x
                    padding = x_range * 0.05  # 5% padding

                    signal_payload["signals"].append(
                        {
                            "name": v.get("name",k),
                            "type": "time_series",
                            "xUnit": "seconds",
                            "yUnit": "V",  # Default unit for signals
                            "xWindowMinInSeconds": min_x - padding,
                            "xWindowMaxInSeconds": max_x + padding,
                            "yWindowMinInSeconds": -2.0,  # Default Y range
                            "yWindowMaxInSeconds": 2.0,
                            "data": data_points,
                        }
                    )
                else:
                    # Fallback for empty data
                    signal_payload["signals"].append(
                        {
                            "name": v.get("name",k),
                            "type": "time_series",
                            "xUnit": "seconds",
                            "yUnit": "V",
                            "xWindowMinInSeconds": -5.0,
                            "xWindowMaxInSeconds": 0.0,
                            "yWindowMinInSeconds": -2.0,
                            "yWindowMaxInSeconds": 2.0,
                            "data": [],
                        }
                    )


            if v["sig_type"] == "DURATION":
                # Get duration data - should be a dict with 'duration' and 'severity' keys
                duration_data = getattr(self, k, {"duration": 0.0, "severity": "normal"})
                if isinstance(duration_data, dict):
                    signal_payload["signals"].append(
                        {
                            "name": k,
                            "type": "duration",
                            "duration": duration_data.get("duration", 0.0),
                            "severity": duration_data.get("severity", "normal"),
                        }
                    )
                else:
                    # Fallback if duration_data is not a dict
                    signal_payload["signals"].append(
                        {
                            "name": k,
                            "type": "duration",
                            "duration": float(duration_data) if duration_data else 0.0,
                            "severity": "normal",
                        }
                    )

        return signal_payload

    def downsample_signal_data(self, time_data, signal_data):
        """
        Downsample signal data using averaging to reduce aliasing artifacts.

        Args:
            time_data: List of time values
            signal_data: List of signal values

        Returns:
            Tuple of (downsampled_time, downsampled_signal)
        """
        if len(time_data) != len(signal_data):
            raise ValueError("Time and signal data must have the same length")

        if len(time_data) <= self.stream_target_points:
            # No downsampling needed if data is already small enough
            return time_data, signal_data

        # Calculate the actual downsampling factor based on data length
        actual_factor = len(time_data) / self.stream_target_points

        downsampled_time = []
        downsampled_signal = []

        for i in range(self.stream_target_points):
            # Calculate the range of indices to average
            start_idx = int(i * actual_factor)
            end_idx = int((i + 1) * actual_factor)
            end_idx = min(end_idx, len(time_data))  # Ensure we don't exceed bounds

            if start_idx < end_idx:
                # Average the time values in this window
                avg_time = sum(time_data[start_idx:end_idx]) / (end_idx - start_idx)
                # Average the signal values in this window (anti-aliasing)
                avg_signal = sum(signal_data[start_idx:end_idx]) / (end_idx - start_idx)

                downsampled_time.append(round(avg_time, 3))
                downsampled_signal.append(avg_signal)

        return downsampled_time, downsampled_signal

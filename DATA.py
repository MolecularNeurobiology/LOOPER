# -*- coding: utf-8 -*-

__version__ = "0.1.0"


class DATA:
    def __init__(self):
        # short term
        self.time = []
        self.pneumo = []
        self.ecg = []

        # instantaneous_arrays
        self.new_time = []
        self.new_pneumo = []
        self.new_ecg = []

        # instantaneous_values
        self.avg_bpm = None
        self.avg_hr = None
        self.avd_tv = None
        self.current_time = None

        # persistent
        self.challenge_history = {}
        self.recovery_bpm = None
        self.recovery_hr = None

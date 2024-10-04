# -*- coding: utf-8 -*-

__version__ = "0.0.1"

import pandas
import json
import ast


class SETTINGS:
    def __init__(self):

        ## settings:
        self.filt_crit_Dict = {
            "avgBPM": 250,
            "cvTT": 0.50,
            "avgHR": 850,
            "avgRR": 999,
            "cvRR": 1.00,
            "BSD": 0.25,
            "DVTV": 0.75,
        }
        self.HR_recovery_thresh = 63.0
        self.BPM_recovery_thresh = 50.0
        self.QB_minimum_duration = 5.0

        self.baseline_flow = 0.0
        self.thresh_flow = 0.050
        self.thresh2_flow = 0.100

        self.pleth_filt_state = 1  # either 1 or 0
        self.ecg_filt_state = 0  # either 1 or 0

        self.baseline_vol = 0.0
        self.thresh_vol = 0.25

        self.baseline_ecg = 0.0
        self.absthresh_ecg = 0.14
        self.minRR_ecg = 0.100
        self.thresh_ecg1 = 4.0
        self.thresh_ecg2 = 2.0
        self.noise_ecg = 75.0

        self.INVERT_FLOW = 0
        self.INVERT_ECG = 0

        self.current_recovery = 300.0  # is this a setting?
        self.recovery_increment = 5 * 60.0
        self.sustained_recovery = 60.0
        self.minimum_sustained_recovery = 60.0
        self.sustained_recovery_flag = 1

        self.recovery_mode = "consecutive"  # or 'accumulated'
        self.minimum_resus_time = 5 * 60.0

        self.minimum_cummulative_QB_duration = 60.0
        self.baseline_increment = 60.0

        self.baseHR = 1.0
        self.avgRR = 999.0
        self.OUTPUTFILE = ''
        self.SLB_Trigger = 5.0
        self.CALL_DEATH_trigger = 10 * 60.0
        self.Abort_Toggle = 0

        self.Arduino_Function_Constants = {
            "Position_RA": 0,
            "Position_Gas": 3,
            "Duration_Cal": 100,
            "Duration_Prefill": 10,
        }

        self.Challenge_phrase = "Finished: On Anoxic"
        self.Challenge_Delay = 5.0

        self.Mode_dict = {
            0: "startup",
            1: "standby",
            2: "Signal Preview 1",
            3: "calibration",
            4: "Signal Preview 2",
            5: "Habituation-1",
            6: "Signal Preview 3",
            7: "Pre-Inject",
            8: "Inject",
            9: "Habituation-2",
            10: "Baseline",
            11: "Challenge",
            12: "Finished",
        }
        self.Mode_timing = {
            0: -0.02,
            1: -0.02,
            2: -0.02,
            3: 60 * 2,
            4: -0.02,
            5: 30 * 60,
            6: 0,
            7: 0,
            8: 0,
            9: 0,
            10: 2 * 60,
            11: -0.02,
            12: -0.02,
        }

        self.savable_modes = [
            "calibration",
            "Habituation-1",
            "Pre-Inject",
            "Habituation-2",
            "Baseline",
            "Challenge",
        ]

        self.made_for_PCC_version = "43.0.0"

        self.expected_fields = {
            "filt_crit_Dict": {},
            "HR_recovery_thresh": 1.1,
            "BPM_recovery_thresh": 1.1,
            "QB_minimum_duration": 1.1,
            "baseline_flow": 1.1,
            "thresh_flow": 1.1,
            "thresh2_flow": 1.1,
            "pleth_filt_state": 1,
            "ecg_filt_state": 1,
            "baseline_vol": 1.1,
            "thresh_vol": 1.1,
            "baseline_ecg": 1.1,
            "absthresh_ecg": 1.1,
            "minRR_ecg": 1.1,
            "thresh_ecg1": 1.1,
            "thresh_ecg2": 1.1,
            "noise_ecg": 1.1,
            "INVERT_FLOW": 1,
            "INVERT_ECG": 1,
            "current_recovery": 1.1,
            "recovery_increment": 1.1,
            "sustained_recovery": 1.1,
            "minimum_sustained_recovery": 1.1,
            "sustained_recovery_flag": 1,
            "recovery_mode": "",
            "minimum_resus_time": 1.1,
            "minimum_cummulative_QB_duration": 1.1,
            "baseline_increment": 1.1,
            "baseHR": 1.1,
            "avgRR": 1.1,
            "OUTPUTFILE": "",
            "SLB_Trigger": 1.1,
            "CALL_DEATH_trigger": 1.1,
            "Abort_Toggle": 1,
            "Arduino_Function_Constants": {},
            "Challenge_phrase": "",
            "Challenge_Delay": 1.1,
            "Mode_dict": {},
            "Mode_timing": {},
            "savable_modes": [],
            "made_for_PCC_version": "",
            "expected_fields": {},
        }

    def load_from_file(self, filepath, logger=None):

        settings = pandas.read_csv(
            filepath, sep=",", encoding="UTF-8", index_col="Parameter"
        )["Setting"].to_dict()
        for k, v in settings.items():
            try:
                attr_val = int(v)
            except:
                try:
                    attr_val = float(v)
                except ValueError:
                    attr_val = v
                except TypeError:
                    attr_val = v
            try:
                if "[" in v or "{" in v:
                    attr_val = ast.literal_eval(v)
            except:
                pass
            setattr(self, k, attr_val)

            if logger:
                logger.info(f'"{k}" set to "{attr_val}" from file')

    def save_to_file(self, filepath, logger=None):

        settings = {}
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            settings[k] = self.__dict__[k]
        settings_df = pandas.DataFrame(
            {
                "Parameter": settings.keys(),
                "Setting": settings.values(),
            }
        )
        settings_df.to_csv(filepath, index=False)
        if logger:
            logger.info(f"settings saved to file: {filepath}")

    def load_from_json_string(self, json_string, logger=None):
        settings = json.loads(json_string)
        
        for k, v in settings.items():
            try:
                attr_val = float(v)
            except ValueError:
                attr_val = v
            except TypeError:
                attr_val = v

            if "[" in v or "{" in v:
                attr_val = ast.literal_eval(v)

            setattr(self, k, attr_val)

            if logger:
                logger.info(f'"{k}" set to "{attr_val}" from json')
            else: print(f'"{k}" set to "{attr_val}" from json')



    def convert_to_json_string(self, logger=None):

        settings = {}
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            settings[k] = self.__dict__[k]
        
        if logger:
            logger.info(f"settings being translated to json")

        return json.dumps(settings)


    def type_check_settings(self, return_summary=False, logger=None):
        summary = []
        for k,v in self.expected_fields.items():
            summary.append(f'{k} as {type(v)}: {type(getattr(self,k)) == type(v)}')
            
        if logger: logger.info(summary)
        if return_summary: return summary

    def check_for_expected(self, return_summary=False, logger=None):
        settings = {}
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            settings[k] = self.__dict__[k]

        set_settings = set(list(settings.keys()))
        set_expected = set(list(settings['expected_fields'].keys()))
        summary = [f'settings parameters received as expected: {set_settings==set_expected}']

        summary.append(f'received but not expected: {set_settings.difference(set_expected)}')
        summary.append(f'not received byt expected: {set_expected.difference(set_settings)}')

        if logger: logger.info(summary)
        if return_summary: return summary
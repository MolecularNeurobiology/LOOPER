# -*- coding: utf-8 -*-

__version__ = "0.1.0"

import pandas
import json
import ast
from fmrest import server

testing_credentials = {
    "ip": "https://3.141.29.47",
    "user": "Fix_Database",
    "password": "Fix_Database",
}


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

        self.flow_filt_state = 1  # either 1 or 0
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
        self.OUTPUTFILE = ""
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

        self.Mode_settings = {
            'startup1':{'duration':-1,'savable':False, 'special_exit':'na'},
            'startup2':{'duration':-1,'savable':False, 'special_exit':'na'},
            'standby':{'duration':-1,'savable':False, 'special_exit':'na'},
            'signal_preview_1':{'duration':-1,'savable':False, 'special_exit':'na'},
            'calibration':{'duration':120,'savable':True, 'special_exit':'na'},
            'signal_preview_2':{'duration':-1,'savable':False, 'special_exit':'na'},
            'habituation_1':{'duration':30*60,'savable':True, 'special_exit':'na'},
            'signal_preview_3':{'duration':0,'savable':False, 'special_exit':'na'},
            'pre_inject':{'duration':0,'savable':True, 'special_exit':'na'},
            'inject':{'duration':0,'savable':True, 'special_exit':'na'},
            'habituation_2':{'duration':0,'savable':True, 'special_exit':'na'},
            'baseline':{'duration':2*60,'savable':True, 'special_exit':'na'},
            'challenge':{'duration':-1,'savable':True, 'special_exit':'na'},
            'finished':{'duration':-1,'savable':False, 'special_exit':'na'}
        }

        self.sim_mode = 0

        self.made_for_PCC_version = "43.0.0"

        self.expected_fields = {
            "filt_crit_Dict": {},
            "sim_mode": 1,
            "HR_recovery_thresh": 1.1,
            "BPM_recovery_thresh": 1.1,
            "QB_minimum_duration": 1.1,
            "baseline_flow": 1.1,
            "thresh_flow": 1.1,
            "thresh2_flow": 1.1,
            "flow_filt_state": 1,
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
            ##
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
            ##

            setattr(self, k, attr_val)

            if logger:
                logger.info(f'"{k}" set to "{attr_val}" from json')
            else:
                print(f'"{k}" set to "{attr_val}" from json')

    def load_from_fm(self, credentials, database, layout, assay_id, logger=None):
        return_dict = self.fm_collect_records(credentials, database, layout, assay_id)
        for k, v in return_dict.items():
            setting = v["Setting"]
            parameter = v["Parameter"]

            try:
                attr_val = int(setting)
            except:
                try:
                    attr_val = float(setting)
                except ValueError:
                    attr_val = setting
                except TypeError:
                    attr_val = setting
            try:
                if "[" in setting or "{" in setting:
                    attr_val = ast.literal_eval(setting)
            except:
                pass

            setattr(self, parameter, attr_val)

            if logger:
                logger.info(f'"{parameter}" set to "{attr_val}" from fm')
            else:
                print(f'"{parameter}" set to "{attr_val}" from fm')

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
        for k, v in self.expected_fields.items():
            summary.append(f"{k} as {type(v)}: {type(getattr(self,k)) == type(v)}")

        if logger:
            logger.info(summary)
        if return_summary:
            return summary

    def check_for_expected(self, return_summary=False, logger=None):
        settings = {}
        duplicate_entries = []
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            if k in settings:
                duplicate_entries.append(k)
            settings[k] = self.__dict__[k]

        set_settings = set(list(settings.keys()))
        set_expected = set(list(settings["expected_fields"].keys()))
        summary = [
            f"settings parameters received as expected: {set_settings==set_expected}"
        ]
        summary.append(
            f"received but not expected: {set_settings.difference(set_expected)}"
        )
        summary.append(
            f"not received but expected: {set_expected.difference(set_settings)}"
        )
        summary.append(f"received multiple of the same parameter: {duplicate_entries}")

        if logger:
            logger.info(summary)
        if return_summary:
            return summary

    def fm_collect_records(self, credentials, database, layout, assay_id):
        SERVER_IP = credentials["ip"]
        USER = credentials["user"]
        PASSWORD = credentials["password"]
        DATABASE = database
        LAYOUT = layout

        fms = server.Server(
            SERVER_IP,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            layout=LAYOUT,
            api_version="v2",
            verify_ssl=False,
        )

        table_keys = ["Assay_Id", "Parameter", "Setting"]
        search_args = [{"Assay_Id": assay_id}]

        fms.login()

        records = []
        offset = 1
        limit = 100

        while True:
            try:
                print(f"{offset}-{len(records)}")
                current_records = fms.find(search_args, limit=limit, offset=offset)
                records += [i for i in current_records]
                offset += limit
                if current_records.is_complete:
                    break

            except Exception as e:
                print(e)
                break

        fms.logout()
        print(f"{len(records)} records found")
        if "recordId" not in table_keys:
            table_keys.append("recordId")

        record_dict = {i["recordId"]: {k: i[k] for k in table_keys} for i in records}
        return record_dict

    def fm_create_update_records(
        self, credentials, database, layout, assay_id, logger=None
    ):
        SERVER_IP = credentials["ip"]
        USER = credentials["user"]
        PASSWORD = credentials["password"]
        DATABASE = database
        LAYOUT = layout

        fms = server.Server(
            SERVER_IP,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            layout=LAYOUT,
            api_version="v2",
            verify_ssl=False,
        )

        settings = {}
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            settings[k] = self.__dict__[k]

        if logger:
            logger.info(f"settings being translated to for FM API")

        fms.login()

        # check if record exists
        table_keys = ["Assay_Id", "Parameter", "Setting", "recordId"]
        for k, v in settings.items():
            print("\n", assay_id, k)
            search_args = [{"Assay_Id": assay_id, "Parameter": f"=={k}"}]
            # if record exists, update it
            try:
                current_records = fms.find(search_args)
                records = [i for i in current_records]
            # except Exception('FileMakerError: FileMaker Server returned error 401, No records match the request'):
            #    records = []
            #    print('no records returned')
            except Exception as e:
                print(f"!!!{e}!!!")
                if "No records match the request" in str(e):
                    print("No records found - making new records")
                    records = []
            print(f"\n{len(records)} records found")
            record_dict = {
                i["recordId"]: {k: i[k] for k in table_keys} for i in records
            }
            print(record_dict)
            if len(records) > 1:
                raise Exception(
                    f"Duplicate Parameter Entries Present in DB: {assay_id}-{k}"
                )
            elif len(records) == 1:

                fms.edit_record(
                    list(record_dict.keys())[0],
                    {"Assay_Id": assay_id, "Parameter": k, "Setting": str(v)},
                )
            else:
                fms.create_record(
                    {"Assay_Id": assay_id, "Parameter": k, "Setting": str(v)}
                )

            # if record doesn't exist create it

        fms.logout()

    def fm_check_for_matching_settings(self, credentials, database, layout):
        SERVER_IP = credentials["ip"]
        USER = credentials["user"]
        PASSWORD = credentials["password"]
        DATABASE = database
        LAYOUT = layout

        fms = server.Server(
            SERVER_IP,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            layout=LAYOUT,
            api_version="v2",
            verify_ssl=False,
        )

        table_keys = ["Assay_Id", "Parameter", "Setting"]

        fms.login()

        records = []
        offset = 1
        limit = 100

        search_args = [{"Assay_Id": "*"}]

        while True:
            try:
                print(f"{offset}-{len(records)}")
                current_records = fms.find(search_args, limit=limit, offset=offset)
                records += [i for i in current_records]
                offset += limit
                if current_records.is_complete:
                    break

            except Exception as e:
                print(e)
                break

        fms.logout()
        print(f"{len(records)} records found")
        if "recordId" not in table_keys:
            table_keys.append("recordId")

        assay_dict = {}
        for i in records:
            if i["Assay_Id"] not in assay_dict:
                assay_dict[i["Assay_Id"]] = {}
            try:
                assay_dict[i["Assay_Id"]][i["Parameter"]] = int(i["Setting"])
            except:
                try:
                    assay_dict[i["Assay_Id"]][i["Parameter"]] = float(i["Setting"])
                except ValueError:
                    assay_dict[i["Assay_Id"]][i["Parameter"]] = i["Setting"]
                except TypeError:
                    assay_dict[i["Assay_Id"]][i["Parameter"]] = i["Setting"]
            try:
                if (
                    "[" in i["Setting"]
                    or "{" in i["Setting"]
                    or '"' in i["Setting"]
                    or "'" in i["Setting"]
                ):
                    assay_dict[i["Assay_Id"]][i["Parameter"]] = ast.literal_eval(
                        i["Setting"]
                    )
            except:
                pass

        current_settings = {}
        for k in self.__dict__:
            if k.startswith("__"):
                continue
            current_settings[k] = self.__dict__[k]

        settings_match_list = [
            (k, d == current_settings) for k, d in assay_dict.items()
        ]

        return settings_match_list

# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from abc import ABC, abstractmethod
from datetime import datetime
import numpy
import EFFECTORS


class STAGE(ABC):
    def __init__(self, setting_dict, pcc):
        self.name = setting_dict["name"]
        self.pcc = pcc
        self.next_stage = setting_dict["next_stage"]
        self.setting_dict = setting_dict

        self.pcc.data.stage_start_time = datetime.now()
        self.pcc.data.current_time = datetime.now()
        self.pcc.data.time_in_stage = 0
        self.pcc.data.time_in_stage_seconds = 0
        self.pcc.data.minerva_attr_dict["time_in_stage_seconds"] = {"sig_type":"DURATION"}

        self.stage_time_limit = setting_dict["duration"]
        self.save_flag = setting_dict["savable"]

    def test_time_in_stage(self):
        """
        returns true if time in stage is greater or equal to the limit for the stage
        """
        self.pcc.data.time_in_stage = (
            self.pcc.data.current_time - self.pcc.data.stage_start_time
        )
        self.pcc.data.time_in_stage_seconds = self.pcc.data.time_in_stage.seconds
        if self.setting_dict["stage_type"] == "timed":
            if self.stage_time_limit > self.pcc.data.time_in_stage_seconds:
                return False
            elif self.stage_time_limit < self.pcc.data.time_in_stage_seconds:
                self.pcc.logger.info(
                    f"time in stage ({self.pcc.data.time_in_stage_seconds}) greater than time limit ({self.stage_time_limit})"
                )
                self.pcc.automated = True
                return True
        return False

    def register_data(self):
        pass

    def on_load(self):
        self.pcc.data.stage_start_time = datetime.now()
        self.pcc.data.current_time = datetime.now()
        self.pcc.data.time_in_stage_seconds = 0
        self.pcc.logger.info(f"STAGE: {self.name}")
        self.pcc.automated = False
        if self.save_flag:
            self.pcc.output_file_writer.write_header()
        self.additional_on_load()

    def additional_on_load(self):
        pass

    def additional_on_exit(self):
        pass

    def on_exit(self):
        self.additional_on_exit()
        if not self.pcc.data.advanceable:
            if "unable_to_advance" in self.pcc.data.error_dict:
                pass
            else:
                self.pcc.data.error_dict["unable_to_advance"] = {
                    "message": "unable to advance to next stage, criteria not yet met"
                }
                self.pcc.logger.warning(
                    "unable to advance to next stage, criteria not yet met"
                )
        elif self.pcc.automated:
            self.pcc.comboBox_Jump_To_Stage.setCurrentText(self.next_stage)
        else:
            # ready to exit but step isn't automated
            pass

    def event_loop(self):
        self.pcc.data.current_time = datetime.now()
        if self.save_flag:
            self.pcc.output_file_writer.write_data()

        if self.exit_condition_test():
            self.pcc.automated = True
            self.on_exit()

        self.additional_event_loop()



    def additional_event_loop(self):
        pass

    def exit_condition_test(self):
        # test for time
        if self.test_time_in_stage():
            self.on_exit()
        # test for more complicated condition
        if self.additional_exit_test():
            self.on_exit()

    def additional_exit_test(self):
        pass


class startup1(STAGE):
    def additional_on_load(self):
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand("<U,0,0>")
        self.pcc.data.PCC_client_status = "Waiting"

    def additional_exit_test(self):
        # test for startup tests passed
        if any(["startup sent" in i for i in self.pcc.arduino_list]):
            print("!!!!!!!!startup!!!!!!!!")
            self.pcc.automated = True
            return True


class startup2(STAGE):
    def register_data(self):
        self.pcc.data.arduino_startup_motion_tested = False
        
        self.pcc.data.minerva_attr_dict["arduino_startup_motion_tested"] = {"sig_type":"STATUS"}

    def additional_on_load(self):
        self.pcc.data.arduino_startup_motion_tested = False
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand("<E,0,0>")
        self.pcc.data.PCC_client_status = "Waiting"

    def additional_exit_test(self):
        # test for startup tests passed
        if any(["finish startup" in i for i in self.pcc.arduino_list]):
            print("!!!!!!FINISHED STARTUP!!!!!!")
            self.pcc.automated = True
            self.pcc.data.arduino_startup_motion_tested = True
            return True


class standby(STAGE):
    def additional_on_load(self):
        self.pcc.logger.debug("moving to standby position")
        self.pcc.arduino_stream.sendCommand("<S,0,0>")
        self.pcc.data.PCC_client_status = "Waiting"

    def additional_event_loop(self):
        if "standby sent" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True

    def additional_exit_test(self):
        if (
            self.pcc.settings.output_path
            and self.pcc.data.arduino_startup_motion_tested
        ):
            return True


class signal_preview_1(STAGE):
    # this stage will create a holding point that will prevent
    # "automated advance" if an output filename is not set
    def additional_on_load(self):
        super().additional_on_load()
        self.pcc.data.advanceable = False
        self.pcc.data.PCC_client_status = "Waiting"

    def additional_event_loop(self):
        if not self.pcc.data.advanceable and self.pcc.settings.output_path:
            self.pcc.data.advanceable = True
            if "unable_to_advance" in self.pcc.data.error_dict:
                self.pcc.data.error_dict.pop("unable_to_advance")


class calibration(STAGE):
    def register_data(self):
        self.pcc.data.calibration_tv_voltage = None
        self.pcc.data.calibration_breath_duration = None
        self.pcc.data.calibration_breath_dict = {}
        self.pcc.data.recent_calibration_breath = 0

        self.pcc.data.minerva_attr_dict["calibration_tv_voltage"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["calibration_breath_duration"] = {"sig_type":"SINGLE_VALUE"}

    def additional_on_load(self):
        self.pcc.arduino_stream.sendCommand(
            f"<C,{self.setting_dict['auto_pipette_duration']},0>"
        )
        self.pcc.logger.debug(f"stage time limit: {self.stage_time_limit}")
        self.pcc.data.PCC_client_status = "Running"

    def additional_on_exit(self):
        # print(self.pcc.data.calibration_breath_dict)
        self.pcc.data.calibration_tv_voltage = numpy.mean(
            [v["iTV"] for v in self.pcc.data.calibration_breath_dict.values()]
        )
        self.pcc.logger.info(
            f"calibration VT voltage: {self.pcc.data.calibration_tv_voltage}"
        )
        self.pcc.data.calibration_breath_duration = numpy.mean(
            [
                v["TT"]
                for v in self.pcc.data.calibration_breath_dict.values()
                if "TT" in v
            ]
        )
        self.pcc.logger.info(
            f"calibration breath duration: {self.pcc.data.calibration_breath_duration}"
        )

    def additional_event_loop(self):
        for k, v in self.pcc.data.breath_list.items():
            if k < self.pcc.data.recent_calibration_breath:
                continue
            else:
                self.pcc.data.calibration_breath_dict[k] = v


class signal_preview_2(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Waiting"


class habituation_1(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Running"


class signal_preview_3(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Waiting"


class pre_inject(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Running"


class inject(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Waiting"


class habituation_2(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Running"


class baseline(STAGE):
    def register_data(self):
        self.pcc.data.running_breaths = []
        self.pcc.data.running_beats = {"ts": [], "rr": []}
        self.pcc.data.quality_seg_list = []  # list of start and stop times
        self.pcc.data.quality_test = 0
        self.pcc.data.prev_quality_test = 0
        self.pcc.data.qb_timer = 0
        self.pcc.data.qb_time_running_sec = 0
        self.pcc.data.quality_status = ""
        self.pcc.data.baseline_tt = 0
        self.pcc.data.baseline_vf = 0
        self.pcc.data.baseline_itv = 0
        self.pcc.data.baseline_rr = 0
        self.pcc.data.baseline_hr = 0

        self.pcc.data.minerva_attr_dict["quality_test"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["quality_status"] = {"sig_type":"DEBUG"}
        self.pcc.data.minerva_attr_dict["qb_time_running_sec"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["baseline_tt"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["baseline_vf"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["baseline_itv"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["baseline_rr"] = {"sig_type":"SINGLE_VALUE"}
        self.pcc.data.minerva_attr_dict["baseline_hr"] = {"sig_type":"SINGLE_VALUE"}

    def additional_on_load(self):
        self.filt_crit_Dict = {
            k: self.setting_dict.get(k)
            for k in ["avgVF", "cvTT", "avgHR", "cvRR", "BSD", "DVTV"]
        }
        print("base add load")
        self.pcc.data.PCC_client_status = "Running"

    def additional_on_exit(self):
        self.pcc.data.baseline_tt = numpy.average(
            [
                i["TI"] + i["TE"]
                for i in self.pcc.data.running_breaths
                if "TE" in i.keys()
            ]
        )
        self.pcc.data.baseline_tv = numpy.average(
            [i["iTV"] for i in self.pcc.data.running_breaths]
        )
        self.pcc.data.baseline_vf = 60 / self.pcc.data.baseline_tt
        self.pcc.data.baseline_rr = numpy.average(self.pcc.data.running_beats["rr"])
        self.pcc.data.baseline_hr = 60 / self.pcc.data.baseline_rr

    def quality_test(self):
        self.pcc.data.prev_quality_test = int(self.pcc.data.quality_test)
        # check if in 'good recording section'
        self.filt_test_Dict = {
            "avgVF": 60 / self.pcc.data.avg_tt,
            "cvTT": self.pcc.data.cv_tt,
            "avgHR": 60 / self.pcc.data.avg_rr,
            "avgRR": self.pcc.data.avg_rr,
            "cvRR": self.pcc.data.cv_rr,
            "BSD": self.pcc.data.avg_bsd,
            "DVTV": self.pcc.data.avg_dvtv,
        }

        exclude = []
        for i in self.filt_crit_Dict.keys():
            if self.filt_crit_Dict[i] < self.filt_test_Dict[i]:
                exclude.append(i)
        if len(exclude) >= 1:
            self.pcc.data.quality_test = 0
            self.pcc.data.quality_status = ",".join(exclude)

        else:
            self.pcc.data.quality_test = 1
            self.pcc.data.quality_status = "PASS"

    def additional_exit_test(self):
        if len(self.pcc.data.quality_seg_list)>0:
            self.pcc.label_debug.setText(
                f"{self.pcc.data.quality_test};{self.pcc.data.time_in_stage_seconds:.0F};{self.pcc.data.qb_time_running_sec:.1F};[{self.pcc.data.quality_seg_list[-1][0]:.1F},{self.pcc.data.quality_seg_list[-1][1]:.1F}]"
            )
        else:
            self.pcc.label_debug.setText(
                f"{self.pcc.data.quality_test};{self.pcc.data.time_in_stage_seconds:.0F};{self.pcc.data.qb_time_running_sec:.1F};"
            )
        
        # if quality time > minimum quality time return True
        if self.pcc.data.quality_test == 0:
            self.pcc.data.qb_time_running_sec = self.pcc.data.qb_timer
            if (
                self.pcc.data.qb_timer
                > self.setting_dict["minimum_cummulative_QB_duration"]
            ) and self.stage_time_limit < self.pcc.data.time_in_stage_seconds:
                self.pcc.logger.info(
                    f"time in stage ({self.pcc.data.time_in_stage_seconds}) greater than time limit ({self.stage_time_limit}), QB duration met {self.pcc.data.qb_timer}"
                )
                self.pcc.automated = True
                return True
            else:
                return False
        else:
            self.pcc.data.qb_time_running_sec = (
                self.pcc.data.qb_timer
                + self.pcc.data.quality_seg_list[-1][1]
                - self.pcc.data.quality_seg_list[-1][0]
            )
            if (
                self.pcc.data.qb_time_running_sec
                > self.setting_dict["minimum_cummulative_QB_duration"]
                and self.stage_time_limit < self.pcc.data.time_in_stage_seconds
            ):
                self.pcc.logger.info(
                    f"time in stage ({self.pcc.data.time_in_stage_seconds}) greater than time limit ({self.stage_time_limit}), QB duration met {self.pcc.data.qb_timer}"
                )
                self.pcc.automated = True
                return True
            else:
                return False

    def additional_event_loop(self):
        self.quality_test()

        if self.pcc.data.quality_test == 1:
            for k, v in self.pcc.data.breath_list.items():
                if "TE" in v:
                    if len(self.pcc.data.running_breaths) == 0:
                        self.pcc.data.running_breaths.append(v)
                    elif k > self.pcc.data.running_breaths[-1]["TS-I"]:
                        self.pcc.data.running_breaths.append(v)
            if len(self.pcc.data.running_beats["ts"]) == 0:
                self.pcc.data.running_beats["ts"] += list(self.pcc.data.beat_list["ts"])
                self.pcc.data.running_beats["rr"] += list(self.pcc.data.beat_list["rr"])
            else:
                ts_last_update = self.pcc.data.running_beats["ts"][-1]
                self.pcc.data.running_beats["ts"] += list(
                    self.pcc.data.beat_list[
                        self.pcc.data.beat_list["ts"] > ts_last_update
                    ]["ts"]
                )
                self.pcc.data.running_beats["rr"] += list(
                    self.pcc.data.beat_list[
                        self.pcc.data.beat_list["ts"] > ts_last_update
                    ]["rr"]
                )

        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_quality_test == 0:
            self.pcc.data.quality_seg_list.append(
                [
                    self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000),
                    self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000),
                ]
            )
        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_quality_test == 1:
            if len(self.pcc.data.quality_seg_list) == 0:
                self.pcc.data.quality_seg_list.append(
                    [
                        self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000),
                        self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000),
                    ]
                )
            self.pcc.data.quality_seg_list[-1][1] = self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000) - self.pcc.data.SLB
        if self.pcc.data.quality_test == 0 and self.pcc.data.prev_quality_test == 1:
            self.pcc.data.quality_seg_list[-1][1] = self.pcc.data.time_in_stage.seconds + (self.pcc.data.time_in_stage.microseconds/1000000) - self.pcc.data.SLB
            self.pcc.data.qb_timer += max(
                0,
                self.pcc.data.quality_seg_list[-1][1]
                - self.pcc.data.quality_seg_list[-1][0]
            )


class challenge(STAGE):
    def register_data(self):
        if "baseline" not in self.pcc.stage_dict.keys():
            self.pcc.logger.error(
                "stages includes a challenge without an earlier baseline"
            )
            raise KeyError
        self.pcc.data.challenge_state = "n/a"
        self.pcc.data.prev_challenge_state = "n/a"
        self.pcc.data.challenge_history = {}
        self.pcc.data.challenge_history_text = ""
        self.pcc.data.recovery_bout_start = None
        self.pcc.data.recovery_bout_duration = 0
        self.pcc.data.accumulated_recovery_bout_duration = 0
        self.pcc.data.recovery_status = ""
        self.pcc.data.current_challenge_round = 0
        self.pcc.data.current_challenge_start = None
        self.pcc.data.current_prefill_start = None
        self.pcc.data.current_prefill_duration = 0
        self.pcc.data.current_gas_exposure_start = None
        self.pcc.data.current_gas_exposure_duration = 0
        self.pcc.data.current_recovery_start = None
        self.pcc.data.current_recovery_duration = 0
        self.pcc.data.current_recovery_waiting_interval = 0
        self.pcc.data.current_latency_to_gasp = None
        self.pcc.data.acc_rec_flag = False
        self.pcc.data.con_rec_flag = False
        self.pcc.data.recovered_flag = False
        self.pcc.data.recovery_bout_flag = False
        self.pcc.data.gasp_detected_flag = False
        self.pcc.data.new_state = False
        self.pcc.data.pulse_sender = None

        self.pcc.data.minerva_attr_dict["challenge_state"] = {"sig_type":"DEBUG"}
        self.pcc.data.minerva_attr_dict["challenge_history_text"] = {"sig_type":"DEBUG"}
        self.pcc.data.minerva_attr_dict["recovery_status"] = {"sig_type":"DEBUG"}

        self.pcc.data.minerva_attr_dict["acc_rec_flag"] = {"sig_type":"STATUS"}
        self.pcc.data.minerva_attr_dict["con_rec_flag"] = {"sig_type":"STATUS"}
        self.pcc.data.minerva_attr_dict["recovered_flag"] = {"sig_type":"STATUS"}
        self.pcc.data.minerva_attr_dict["gasp_detected_flag"] = {"sig_type":"STATUS"}

        self.pcc.data.minerva_attr_dict["current_prefill_duration"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["current_gas_exposure_duration"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["current_recovery_waiting_interval"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["current_recovery_duration"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["current_latency_to_gasp"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["recovery_bout_duration"] = {"sig_type":"DURATION"}
        self.pcc.data.minerva_attr_dict["accumulated_recovery_bout_duration"] = {"sig_type":"DURATION"}
        

    def recovery_test(self):
        # test for not recovered conditions
        recovery_tests = {
            "SLB": self.pcc.data.SLB > self.setting_dict["slb_trigger"],
            "VF": 60 / self.pcc.data.avg_tt
            < self.pcc.data.baseline_vf
            * (self.setting_dict["vf_recovery_thresh"] / 100),
            "HR": 60 / self.pcc.data.avg_rr
            < self.pcc.data.baseline_hr
            * (self.setting_dict["hr_recovery_thresh"] / 100),
        }
        recovery_dict = {
            k: v for k, v in recovery_tests.items() if v == True
        }  # use == instead of "is" for this comparison due to VF and HR comparisons populating as np.True_ or np.False_
        # report back conditions that are blocking a instantaneous recovered status
        self.pcc.data.recovery_status = ", ".join([i for i in recovery_dict.keys()])
        recovery_text = "good" if self.pcc.data.recovery_status == "" else self.pcc.data.recovery_status
        self.pcc.label_debug.setText(
            f"{recovery_text}, {self.pcc.data.recovery_bout_duration:.1F}, {self.pcc.data.accumulated_recovery_bout_duration:.1F}"
        )
        # update for accumulated vs consecutive recovery bouts
        if self.pcc.data.recovery_bout_flag is False:
            if len(recovery_dict) == 0:
                self.pcc.data.recovery_bout_flag = True
                self.pcc.data.recovery_bout_start = datetime.now()
                recovery_time_diff = datetime.now() - self.pcc.data.recovery_bout_start
                self.pcc.data.recovery_bout_duration = (
                    recovery_time_diff.seconds
                    + (recovery_time_diff.microseconds / 1000000)
                    - self.pcc.data.SLB
                )
            else:
                self.pcc.data.recovery_bout_flag = False
                self.pcc.data.recovery_bout_start = None
        else:
            if len(recovery_dict) == 0:
                self.pcc.data.recovery_bout_flag = True
                recovery_time_diff = datetime.now() - self.pcc.data.recovery_bout_start
                self.pcc.data.recovery_bout_duration = (
                    recovery_time_diff.seconds
                    + (recovery_time_diff.microseconds / 1000000)
                    - self.pcc.data.SLB
                )
            else:
                self.pcc.data.recovery_bout_flag = False
                self.pcc.data.recovery_bout_start = None
                self.pcc.data.accumulated_recovery_bout_duration += (
                    self.pcc.data.recovery_bout_duration
                )
                self.pcc.data.recovery_bout_duration = 0

        # test if animal meets recovery criteria

        if (
            not self.pcc.data.con_rec_flag
            and self.pcc.data.recovery_bout_duration
            >= self.setting_dict["minimum_sustained_recovery"]
        ):
            self.pcc.data.con_rec_flag = True
            self.pcc.logger.info("Consecutive Recovery Detected")
            self.pcc.data.challenge_history[self.pcc.data.current_challenge_round][
                "con_rec"
            ] = self.pcc.data.current_recovery_duration
        if (
            not self.pcc.data.acc_rec_flag
            and self.pcc.data.accumulated_recovery_bout_duration
            + self.pcc.data.recovery_bout_duration
            >= self.setting_dict["minimum_sustained_recovery"]
        ):
            self.pcc.data.acc_rec_flag = True
            self.pcc.logger.info("Accumulated Recovery Detected")
            self.pcc.data.challenge_history[self.pcc.data.current_challenge_round][
                "acc_rec"
            ] = self.pcc.data.current_recovery_duration

        # first level is if enough time has passed and current state is within a recovery bout
        if (
            self.pcc.data.recovery_bout_flag is True
            and self.pcc.data.current_recovery_duration
            >= self.pcc.data.current_recovery_waiting_interval
        ):
            # use accumulated or consecutive recovery per settings
            if self.setting_dict["recovery_mode"] == "consecutive":
                if self.pcc.data.con_rec_flag is True:
                    self.pcc.data.challenge_state = "prefill"
                else:
                    self.pcc.data.current_recovery_waiting_interval += (
                        self.setting_dict["recovery_increment"]
                    )
                    self.pcc.logger.info(
                        f"animal not yet recovered: rec bout ({self.pcc.data.recovery_bout_flag}), rec status ({self.pcc.data.recovery_status})"
                    )

            elif self.setting_dict["recovery_mode"] == "accumulated":
                if self.pcc.data.acc_rec_flag is True:
                    self.pcc.data.challenge_state = "prefill"
                else:
                    self.pcc.data.current_recovery_waiting_interval += (
                        self.setting_dict["recovery_increment"]
                    )
                    self.pcc.logger.info(
                        f"animal not yet recovered: rec bout ({self.pcc.data.recovery_bout_flag}), rec status ({self.pcc.data.recovery_status})"
                    )

            else:
                self.pcc.data.error_dict["BAD_RECOVERY_SETTINGS"] = {
                    "message": f"setting for recovery mode not among implemented options - {self.setting_dict['recovery_mode']}"
                }
                self.pcc.logger.error(self.pcc.data.error_dict["BAD_RECOVERY_SETTINGS"])
                self.pcc.abort_experiment

    def apnea_test(self):
        if self.pcc.data.SLB >= self.setting_dict["slb_trigger"]:
            self.pcc.logger.info("apnea detected")
            self.pcc.data.challenge_state = "recovery"
            self.pcc.data.challenge_history[self.pcc.data.current_challenge_round][
                "expose"
            ] = self.pcc.data.current_gas_exposure_duration
            self.pcc.arduino_stream.sendCommand(
                f"<R,{self.setting_dict['position_ra']},0>"
            )

        elif (
            self.pcc.data.current_gas_exposure_duration
            > self.setting_dict["max_gas_exposure"]
        ):
            self.pcc.data.error_dict["RUN_ERROR"] = {
                "message": "animal not going into apnea, this may be a sign of a leaky mask, an empty tank, or another anomoly that needs to be addressed"
            }
            self.pcc.logger.error(self.pcc.data.error_dict["RUN_ERROR"])
            self.pcc.abort_experiment()

    def gasp_test(self):
        """
        tests for occurance of a gasping breath (called during recovery phase if gasp not yet detected)

        on detection of a gasp, will transition to threshold1 for breath detection and check if the
        latency to gasp was shorter than anticipated for autoresuscitation
        """
        if len(self.pcc.data.breath_list) > 0:
            self.pcc.logger.info("Gasp Detected")
            self.pcc.data.gasp_detected_flag = True
            self.pcc.data.flow_thresh_to_use = 1
            self.pcc.data.current_latency_to_gasp = (
                datetime.now() - self.pcc.data.current_recovery_start
            ).seconds
            if (
                self.pcc.data.current_latency_to_gasp
                < self.setting_dict["short_recovery_warning"]
            ):
                self.pcc.data.error_dict["SHORT_RECOVERY_WARNING"] = {
                    "message": "recovery gasping detected immediately after initiation of recovery period. this may indicate that the animal did not enter a sustained apnea requiring autoresuscitation."
                }
                self.pcc.logger.warning(
                    self.pcc.data.error_dict["SHORT_RECOVERY_WARNING"]
                )
            self.pcc.data.challenge_history[self.pcc.data.current_challenge_round][
                "lat_to_gasp"
            ] = self.pcc.data.current_latency_to_gasp

    def exposure_test(self, timeout=None):
        """
        listens for adruino_stream signal indicating transition from prefill to gas exposure, on timeout, will trigger experiment abort
        """
        if any(
            [self.setting_dict["challenge_phrase"] in i for i in self.pcc.arduino_list]
        ):
            self.pcc.data.challenge_state = "exposure"
            self.pcc.data.challenge_history[self.pcc.data.current_challenge_round][
                "prefill"
            ] = self.pcc.data.current_prefill_duration

        elif timeout is not None:
            if (
                self.pcc.data.current_prefill_duration
                > self.setting_dict["prefill_limit"]
                + self.setting_dict["prefill_duration"]
            ):
                self.pcc.data.error_dict["PREFILL ERROR"] = {
                    "message": f"prefill duration exceeded typical timing by {self.setting_dict['prefill_limit']}, communication with the arduino may have been lost"
                }
                self.pcc.logger.error(self.pcc.data.error_dict["PREFILL ERROR"])
                self.pcc.abort_experiment()

    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Running"
        self.pcc.data.challenge_state = "n/a"
        self.pcc.data.prev_challenge_state = "n/a"

    def additional_on_exit(self):
        self.pcc.data.challenge_state = "n/a"
        self.pcc.data.prev_challenge_state = "n/a"

    def prepare_challenge_history_text(self):
        self.pcc.logger.info("updating challenge history")
        self.pcc.data.challenge_history_text = "\n".join([f"{chall_num}:" + ", ".join([f"{k}-{v}" for k,v in chall_outcomes.items()]) for chall_num,chall_outcomes in self.pcc.data.challenge_history.items()])


    def additional_event_loop(self):
        self.pcc.label_debug.setText(self.pcc.data.challenge_state)

        self.pcc.data.prev_challenge_state = self.pcc.data.challenge_state

        if self.pcc.data.challenge_state == "recovery":
            if self.pcc.data.new_state is True:
                self.pcc.logger.info("starting recovery")
                self.pcc.data.current_recovery_start = datetime.now()
                # reset "gas exposure timer" for next round
                self.pcc.data.current_gas_exposure_duration = 0

                # prepare challenge_history_text
                self.prepare_challenge_history_text()
                self.pcc.logger.info(self.pcc.data.challenge_history_text)


            # maintain thresh2 until gasp detected then transition to thresh1 (if possible revise marker color)
            self.pcc.data.current_recovery_duration = (
                datetime.now() - self.pcc.data.current_recovery_start
            ).seconds
            if not self.pcc.data.gasp_detected_flag:
                self.gasp_test()

            self.recovery_test()

        elif self.pcc.data.challenge_state == "prefill":
            if self.pcc.data.new_state is True:
                self.pcc.logger.info("starting prefill")
                self.pcc.data.current_prefill_start = datetime.now()
                self.pcc.data.current_challenge_round += 1
                self.pcc.data.challenge_history[
                    self.pcc.data.current_challenge_round
                ] = {}
                # reset "recovery timer", etc. for next round
                self.pcc.data.current_recovery_duration = 0
                self.pcc.data.gasp_detected_flag = False
                self.pcc.data.recovered_flag = False
                self.pcc.data.acc_rec_flag = False
                self.pcc.data.con_rec_flag = False
                self.pcc.data.recovery_bout_flag = False
                self.pcc.data.recovery_bout_start = None
                self.pcc.data.recovery_bout_duration = 0
                self.pcc.data.accumulated_recovery_bout_duration = 0
                self.pcc.data.current_recovery_waiting_interval = self.setting_dict[
                    "minimum_recovery"
                ]
                # prepare challenge_history_text
                self.prepare_challenge_history_text()
                # send command to arduino to initiate gas challenge
                self.pcc.arduino_stream.sendCommand(
                    f"<A,{self.setting_dict['position_gas']},{self.setting_dict['prefill_duration']}>"
                )
                self.pcc.data.pulse_sender = EFFECTORS.LJ_DIO_pulse(self.pcc.labjack_stream.device, 2, 1000)

            self.pcc.data.current_prefill_duration = (
                datetime.now() - self.pcc.data.current_prefill_start
            ).seconds
            self.exposure_test(timeout=self.setting_dict["prefill_limit"])

        elif self.pcc.data.challenge_state == "exposure":
            if self.pcc.data.new_state is True:
                self.pcc.logger.info("starting exposure")
                # reset "prefill timer" for next round
                self.pcc.data.current_prefill_duration = 0
                self.pcc.data.current_gas_exposure_start = datetime.now()
                # prepare challenge_history_text
                self.prepare_challenge_history_text()

            self.pcc.data.current_gas_exposure_duration = (
                datetime.now() - self.pcc.data.current_gas_exposure_start
            ).seconds

            # after challenge delay, transition to thresh2 (if possible change marker color)
            if not (
                self.pcc.data.flow_thresh_to_use == 2
                and self.pcc.data.current_gas_exposure_duration
                > self.setting_dict["threshold_transition_delay"]
            ):
                self.pcc.data.flow_thresh_to_use = 2

            self.apnea_test()

        else:
            self.pcc.logger.info("starting challenges")
            self.pcc.data.challenge_state = "prefill"

        self.pcc.data.new_state = (
            self.pcc.data.prev_challenge_state != self.pcc.data.challenge_state
        )

    def additional_exit_test(self):
        if self.pcc.data.SLB > self.setting_dict["call_death_trigger"]:
            self.pcc.automated = True
            self.prepare_challenge_history_text()
            self.pcc.logger.info(self.pcc.data.challenge_history_text)


            return True
        elif (
            self.pcc.data.current_challenge_round
            >= self.setting_dict["challenge_round_limit"]
            and self.setting_dict["challenge_round_limit"] > 0
            and self.pcc.data.recovered_flag
        ):
            self.pcc.automated = True
            self.pcc.logger.info("animal reached challenge round limit")
            self.prepare_challenge_history_text()
            self.pcc.logger.info(self.pcc.data.challenge_history_text)


            return True


class finished(STAGE):
    def additional_on_load(self):
        self.pcc.data.PCC_client_status = "Finished"
        self.pcc.logger.info("Experiment Ended")
        self.pcc.arduino_stream.sendCommand("<D,0,0>")
        self.pcc.label_debug.setText = self.pcc.data.challenge_history_text

# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from abc import ABC, abstractmethod
from datetime import datetime
import numpy


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
        self.stage_time_limit = setting_dict["duration"]
        self.save_flag = setting_dict["savable"]
        # self.register_data()

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
        if self.pcc.automated:
            
            self.pcc.comboBox_Jump_To_Stage.setCurrentText(self.next_stage)

    def event_loop(self):
        self.pcc.data.current_time = datetime.now()
        self.additional_event_loop()

        if self.exit_condition_test():
            self.pcc.automated = True
            self.on_exit()

    def additional_event_loop(self):
        pass

    def exit_condition_test(self):
        # test for time
        if self.test_time_in_stage():
            self.on_exit()
        if self.additional_exit_test():
            self.on_exit()

    def additional_exit_test(self):
        pass


class startup1(STAGE):
    def additional_on_load(self):
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand(b"[U")

    def additional_exit_test(self):
        # test for startup tests passed
        if "startup sent" in self.pcc.arduino_string:
            self.on_exit()


class startup2(STAGE):
    def register_data(self):
        self.pcc.data.arduino_startup_motion_tested = False

    def additional_on_load(self):
        self.pcc.data.arduino_startup_motion_tested = False
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand(b"[E")

    def additional_exit_test(self):
        # test for startup tests passed
        if "finish startup" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True
            self.on_exit()


class standby(STAGE):
    def additional_on_load(self):
        self.pcc.logger.debug("moving to standby position")
        self.pcc.arduino_stream.sendCommand(b"[S")

    def additional_event_loop(self):
        if "standby sent" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True

    def additional_exit_test(self):
        if (
            self.pcc.settings.output_path
            and self.pcc.data.arduino_startup_motion_tested
        ):
            self.on_exit()


class signal_preview_1(STAGE):
    pass


class calibration(STAGE):
    def register_data(self):
        self.pcc.data.calibration_tv_voltage = None
        self.pcc.data.calibration_breath_duration = None
        self.pcc.data.calibration_breath_dict = {}
        self.pcc.data.recent_calibration_breath = 0

    def additional_on_load(self):
        self.pcc.arduino_stream.sendCommand(b"[C")
        self.pcc.logger.debug(f"stage time limit: {self.stage_time_limit}")

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
    pass


class habituation_1(STAGE):
    pass


class signal_preview_3(STAGE):
    pass


class pre_inject(STAGE):
    pass

class inject(STAGE):
    pass

class habituation_2(STAGE):
    pass

class baseline(STAGE):
    def register_data(self):
        self.pcc.data.running_breaths = []
        self.pcc.data.running_beats = {"ts": [], "rr": []}
        self.pcc.data.quality_seg_list = []  # list of start and stop times
        self.pcc.data.quality_test = 0
        self.pcc.data.prev_quality_test = 0
        self.pcc.data.qb_timer = 0
        self.pcc.data.quality_status = ""
        # self.pcc.data.avgTT = 0  # how to handle common summura measures that are common between stages but not used in all stages TODO !!!
        # self.pcc.data.cvTT = 0
        # self.pcc.data.avgHR = 0
        # self.pcc.data.avgRR = 0
        # self.pcc.data.cvRR = 0
        # self.pcc.data.BSD = 0
        # self.pcc.data.DVTV = 0

    def additional_on_load(self):
        self.filt_crit_Dict = {
            k: self.setting_dict.get(k)
            for k in ["avgBPM", "cvTT", "avgHR", "cvRR", "BSD", "DVTV"]
        }
        print("base add load")

    def quality_test(self):
        self.pcc.data.prev_quality_test = int(self.pcc.data.quality_test)
        # check if in 'good recording section'
        self.filt_test_Dict = {
            "avgBPM": 60 / self.pcc.data.avg_tt,
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
        # if quality time > minimum quality time return True
        if self.pcc.data.quality_test == 0:
            if (
                self.pcc.data.qb_timer
                > self.setting_dict["minimum_cummulative_QB_duration"]
            ):
                return True
            else:
                return False
        else:
            if (
                self.pcc.data.qb_timer
                + self.pcc.data.quality_seg_list[-1][1]
                - self.pcc.data.quality_seg_list[-1][0]
            ) > self.setting_dict["minimum_cummulative_QB_duration"]:
                return True
            else:
                return False

    def additional_event_loop(self):
        self.quality_test()

        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_quality_test == 0:
            self.pcc.data.quality_seg_list.append(
                [self.data.time_in_stage_seconds, self.data.time_in_stage_seconds]
            )
        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_quality_test == 1:
            if len(self.pcc.data.quality_seg_list) == 0:
                self.pcc.data.quality_seg_list.append(
                    [self.data.time_in_stage_seconds, self.data.time_in_stage_seconds]
                )
            self.pcc.data.quality_seg_list[-1][1] = self.data.time_in_stage_seconds
        if self.pcc.data.quality_test == 0 and self.pcc.data.prev_quality_test == 1:
            self.pcc.data.quality_seg_list[-1][1] = self.data.time_in_stage_seconds
            self.pcc.data.qb_timer += (
                self.pcc.data.quality_seg_list[-1][1]
                - self.pcc.data.quality_seg_list[-1][0]
            )

    # !!!
    """
                
                for i in BL:
                    if 'TE' in BreathCalls[i].keys():
                        
                        if len(RunningBreaths)==0:
                            RunningBreaths.append(BreathCalls[i])
                            
                        elif  i>RunningBreaths[-1]['TS-I']:
                            RunningBreaths.append(BreathCalls[i])
                
                if len(RunningBeats['ts'])==0:
                    RunningBeats['ts']+=list(BeatCalls['ts'])
                    RunningBeats['rr']+=list(BeatCalls['rr'])
                    
                else:
                    ts_last_update = RunningBeats['ts'][-1]
                    RunningBeats['ts']+=list(BeatCalls[BeatCalls['ts']>ts_last_update]['ts'])
                    RunningBeats['rr']+=list(BeatCalls[BeatCalls['ts']>ts_last_update]['rr'])

                # for i in HL:
                #     if len(RunningBeats)==0:
                #         RunningBeats.append({'ts':i,'BC':BeatCalls[i]})
                        
                #     elif i>RunningBeats[-1]['ts']:
                #         RunningBeats.append({'ts':i,'BC':BeatCalls[i]})
                        
            prev_qual_test=int(quality_test)
            #filter to the good breaths and summarize stats


        pass

    def exit_condition_test(self):
        pass
"""


class challenge(STAGE):
    def register_data(self):
        if "baseline" not in self.pcc.stage_dict.keys():
            self.pcc.logger.error(
                "stages includes a challenge without an earlier baseline"
            )
            raise KeyError
        pass

    def additional_on_load(self):
        pass


    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class finished(STAGE):
    pass
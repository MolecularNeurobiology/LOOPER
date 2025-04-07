# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from abc import ABC, abstractmethod
from datetime import datetime
import numpy


class STAGE(ABC):
    def __init__(self, name, pcc):
        self.name = name
        self.pcc = pcc

        self.pcc.data.start_time = datetime.now()
        self.pcc.data.current_time = datetime.now()
        self.pcc.data.time_in_stage = 0
        self.pcc.data.time_in_stage_seconds = 0
        self.stage_time_limit = self.pcc.settings.Mode_settings[self.name]["duration"]
        self.register_data()

    def test_time_in_stage(self):
        """
        returns true if time in stage is greater or equal to the limit for the stage
        """
        self.pcc.data.time_in_stage = self.pcc.data.current_time - self.pcc.data.start_time
        self.pcc.data.time_in_stage_seconds = self.pcc.data.time_in_stage.seconds

        if self.stage_time_limit < 0:
            return False
        elif (
            self.stage_time_limit == 0
        ):  # !!! TODO this should stop being a thing moveing forward...don't include instead of duration 0
            self.pcc.logger.info("no duration set for current stage, skipping")
            return True
        elif self.stage_time_limit > self.pcc.data.time_in_stage_seconds:
            return False
        else:
            self.pcc.logger.info(f"time in stage ({self.pcc.data.time_in_stage_seconds}) greater than time limit ({self.stage_time_limit})")
            return True

    
    def register_data(self):
        pass

    
    def on_load(self):
        self.pcc.data.start_time = datetime.now()
        self.pcc.logger.info(f"STAGE: {self.name}")
        self.pcc.data.automated = False
        self.additional_on_load()

    def additional_on_load(self):
        pass


    def on_jump_exit(self):
        self.on_exit()
        

    @abstractmethod
    def on_exit(self):
        pass

    def event_loop(self):
        self.pcc.data.current_time = datetime.now()
        self.additional_event_loop()

        if self.exit_condition_test():
            self.pcc.data.automated = True
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
    
    # def on_load(self):
    #     self.pcc.data.start_time = datetime.now()
    #     self.pcc.logger.info("STAGE: startup1")
    #     self.pcc.automated = False
    def additional_on_load(self):
        
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand(b"[U")

    def on_exit(self):

        self.pcc.comboBox_Jump_To_Stage.setCurrentText("startup2")

    # def event_loop(self):
    #     self.current_time = datetime.now()
    #     if self.exit_condition_test():
    #         self.pcc.automated = True
    #         self.on_exit()

    # def exit_condition_test(self):
    #     # test for time
    #     if self.test_time_in_stage():
    #         self.on_exit()
    
    def additional_exit_test(self):
        # test for startup tests passed
        if "startup sent" in self.pcc.arduino_string:
            self.on_exit()


class startup2(STAGE):
    def register_data(self):
        self.pcc.data.arduino_startup_motion_tested = False

    # def on_load(self):
    #     self.pcc.start_time = datetime.now()
    #     self.pcc.logger.info("STAGE: startup2")
    #     self.automated = False

    def additional_on_load(self):
        self.pcc.data.arduino_startup_motion_tested = False
        self.pcc.logger.debug("starting up arduino tests")
        self.pcc.arduino_stream.sendCommand(b"[E")

    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText("standby")

    # def exit_condition_test(self):
    #     # test for time
    #     if self.test_time_in_stage():
    #         self.on_exit()

    def additional_exit_test(self):
        # test for startup tests passed
        if "finish startup" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True
            self.on_exit()


class standby(STAGE):
    def register_data(self):
        pass

    # def on_load(self):
    #     self.pcc.start_time = datetime.now()
    #     self.pcc.logger.info("STAGE: standby")
    #     self.automated = False
    #     self.pcc.arduino_startup_motion_tested = False
    def additional_on_load(self):
        self.pcc.logger.debug("moving to standby position")
        self.pcc.arduino_stream.sendCommand(b"[S")

    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText("signal_preview_1")

    # def exit_condition_test(self):
    #     # test for time
    #     if self.test_time_in_stage():
    #         self.on_exit()

    def additional_exit_test(self):    
        # test for standby mode completed
        if "standby sent" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True
            self.on_exit()


class signal_preview_1(STAGE):
    
    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText("calibration")



class calibration(STAGE):
    def register_data(self):
        self.pcc.data.calibration_tv_voltage = None
        self.pcc.data.calibration_breath_duration = None
        self.pcc.data.calibration_breath_dict = {}
        self.pcc.data.recent_calibration_breath = 0

    def additional_on_load(self):
        self.pcc.arduino_stream.sendCommand(b"[C")
        self.pcc.logger.debug(f"stage time limit: {self.stage_time_limit}")

    def on_exit(self):
        #print(self.pcc.data.calibration_breath_dict)
        self.pcc.data.calibration_tv_voltage = numpy.mean(
            [v['iTV'] for v in self.pcc.data.calibration_breath_dict.values()]
        )
        self.pcc.logger.info(f'calibration VT voltage: {self.pcc.data.calibration_tv_voltage}')
        self.pcc.data.calibration_breath_duration = numpy.mean(
            [v['TT'] for v in self.pcc.data.calibration_breath_dict.values() if 'TT' in v]
        )

        self.pcc.logger.info(f'calibration breath duration: {self.pcc.data.calibration_breath_duration}')
        self.pcc.comboBox_Jump_To_Stage.setCurrentText("signal_preview_2")

    def additional_event_loop(self):
        for k,v in self.pcc.data.breath_list.items():
            if k < self.pcc.data.recent_calibration_breath:
                continue
            else:
                self.pcc.data.calibration_breath_dict[k]=v




class signal_preview_2(STAGE):
    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText("habituation_1")

    

class habituation_1(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class signal_preview_3(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class pre_inject(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class inject(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class habituation_2(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass
        print([i for i in range(1000)])


class baseline(STAGE):
    def register_data(self):
        self.pcc.data.running_breaths = []
        self.pcc.data.running_beats = {"ts": [], "rr": []}
        self.pcc.data.quality_seg_list = []  # list of start and stop times
        self.pcc.data.quality_test = 0
        self.pcc.data.prev_quality_test = 0
        self.pcc.data.qb_timer = 0
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def quality_test(self):
        self.pcc.data.prev_quality_test = int(self.pcc.data.quality_test)
        # check if in 'good recording section'
        filt_test_Dict = {
            "avgBPM": 60 / avgTT,
            "cvTT": CV_TT,
            "avgHR": 60 / avgRR,
            "avgRR": avgRR,
            "cvRR": CV_RR,
            "BSD": BSD,
            "DVTV": avgDVTV,
        }

        exclude = []
        for i in filt_crit_Dict:
            if filt_crit_Dict[i] < filt_test_Dict[i]:
                exclude.append(i)
        if len(exclude) >= 1:
            quality_test = 0
            QualColor = RED
        else:
            quality_test = 1
            QualColor = GREEN

    def event_loop(self):
        self.exit_condition_test()
        self.quality_test()

        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_qual_test == 0:
            self.pcc.data.quality_seg_list.append(
                [self.data.time_in_stage_seconds, self.data.time_in_stage_seconds]
            )
        if self.pcc.data.quality_test == 1 and self.pcc.data.prev_qual_test == 1:
            if len(self.pcc.data.quality_seg_list) == 0:
                self.pcc.data.quality_seg_list.append(
                    [self.data.time_in_stage_seconds, self.data.time_in_stage_seconds]
                )
            self.pcc.data.quality_seg_list[-1][1] = self.data.time_in_stage_seconds
        if self.pcc.data.quality_test == 0 and self.pcc.data.prev_qual_test == 1:
            pass

    # !!!
    """
        if Mode_dict[Current_Mode]=='Baseline' and prev_Mode!=Current_Mode:
                RunningBreaths=[]
                RunningBeats={'ts':[],'rr':[]}
                quality_seg_list=[]
            if Mode_dict[Current_Mode]=='Baseline':
                # populate quality segment list 
                if quality_test==1 and prev_qual_test==0:
                    QB_TIMER=REL_TIMER
                    quality_seg_list.append([QB_TIMER,REL_TIMER])
                if quality_test==1 and prev_qual_test==1:
                    if len(quality_seg_list)==0:
                        quality_seg_list.append([QB_TIMER,REL_TIMER])
                    quality_seg_list[-1][1]=REL_TIMER
                if quality_test==0 and prev_qual_test==1:
                    if REL_TIMER-QB_TIMER>=QB_minimum_duration:
                        QB_Counter+=1
                        QB_duration+=REL_TIMER-QB_TIMER
                    
                    
            
                
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

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass


class finished(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass

    def additional_on_load(self):
        pass

    def on_exit(self):
        pass

    def on_jump_exit(self):
        pass

    def event_loop(self):
        pass

    def exit_condition_test(self):
        pass

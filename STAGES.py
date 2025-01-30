# -*- coding: utf-8 -*-

__version__ = "0.1.0"

from abc import ABC, abstractmethod
from datetime import datetime


class STAGE(ABC):
    def __init__(self,name,pcc):
        self.name = name
        self.pcc = pcc

        self.start_time = datetime.now()
        self.current_time = datetime.now()
        self.time_in_stage_seconds = 0
        self.time_limit = self.pcc.settings.Mode_settings[self.name]['duration']

    def test_time_in_stage(self):
        """
        returns true if time in stage is greater or equal to the limit for the stage
        """
        self.time_in_stage_seconds = (self.current_time-self.start_time).seconds
        
        if self.time_limit < 0:
            False
        elif self.time_limit == 0: # !!! TODO this should stop being a thing moveing forward...don't include instead of duration 0
            True
        elif self.time_limit > self.time_in_stage_seconds:
            False
        else:
            True

    @abstractmethod
    def register_data(self):
        pass

    @abstractmethod
    def on_load(self):
        pass

    @abstractmethod
    def on_jump_exit(self):
        pass

    @abstractmethod
    def on_exit(self):
        pass
    
    @abstractmethod
    def event_loop(self):
        pass

    @abstractmethod
    def exit_condition_test(self):
        pass  

class startup1(STAGE):
    def register_data(self):
        self.pcc.data.arduino_startup_motion_tested = False

    def on_load(self):
        self.pcc.start_time = datetime.now()
        self.pcc.logger.info('STAGE: startup1')
        self.pcc.automated = False
        self.pcc.arduino_startup_motion_tested = False
        
        self.pcc.logger.debug('starting up arduino tests')
        self.pcc.arduino_stream.sendCommand(b'[U')
        pass
    def on_exit(self):
        
        self.pcc.comboBox_Jump_To_Stage.setCurrentText('startup2')


    def on_jump_exit(self):
        pass

    def event_loop(self):
        self.current_time = datetime.now()
        


        if self.exit_condition_test():
            self.pcc.automated = True
            self.on_exit()

    def exit_condition_test(self):
        # test for time
            if self.test_time_in_stage():
                self.on_exit()

            # test for startup tests passed
            if "startup sent" in self.pcc.arduino_string:
                self.on_exit()

class startup2(STAGE):
    def register_data(self):
        self.pcc.data.arduino_startup_motion_tested = False
        
    def on_load(self):
        self.pcc.start_time = datetime.now()
        self.pcc.logger.info('STAGE: startup2')
        self.automated = False
        self.pcc.arduino_startup_motion_tested = False
        self.pcc.logger.debug('starting up arduino tests')
        self.pcc.arduino_stream.sendCommand(b'[E')
        pass
    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText('standby')


    def on_jump_exit(self):
        pass

    def event_loop(self):
        self.current_time = datetime.now()
        
        if self.exit_condition_test():
            self.pcc.automated = True
            self.on_exit()

    def exit_condition_test(self):
        # test for time
        if self.test_time_in_stage():
            self.on_exit()

        # test for startup tests passed
        if "finish startup" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True
            self.on_exit()
            

class standby(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        self.pcc.start_time = datetime.now()
        self.pcc.logger.info('STAGE: standby')
        self.automated = False
        self.pcc.arduino_startup_motion_tested = False
        self.pcc.logger.debug('moving to standby position')
        self.pcc.arduino_stream.sendCommand(b'[S')
        
    def on_exit(self):
        self.pcc.comboBox_Jump_To_Stage.setCurrentText('standby')

    def on_jump_exit(self):
        pass
    def event_loop(self):
        self.current_time = datetime.now()
        
        if self.exit_condition_test():
            self.pcc.automated = True
            self.on_exit()

    def exit_condition_test(self):
        # test for time
        if self.test_time_in_stage():
            self.on_exit()

        # test for standby mode completed
        if "standby sent" in self.pcc.arduino_string:
            self.pcc.data.arduino_startup_motion_tested = True
            self.on_exit()
        pass

class signal_preview_1(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

class calibration(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

class signal_preview_2(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

class habituation_1(STAGE):
    def register_data(self):
        pass

    def on_load(self):
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
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

class baseline(STAGE):
    def register_data(self):
        pass

    def on_load(self):
        pass
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

class challenge(STAGE):
    def register_data(self):
        if 'baseline' not in self.pcc.stage_dict.keys():
            self.pcc.logger.error('stages includes a challenge without an earlier baseline')
            raise KeyError
        pass

    def on_load(self):
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
    def on_exit(self):
        pass
    def on_jump_exit(self):
        pass
    def event_loop(self):
        pass
    def exit_condition_test(self):
        pass

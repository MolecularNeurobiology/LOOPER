from abc import ABC, abstractmethod

from step import Step

class Run(ABC): 
    def __init__(self):
        self.steps = [Step(name="NOT_STARTED"), Step(name="FINISHED")]
        self.current_step_index = 0

    def start(self):
        if self.current_step_index != 0:
            return
        
        self.go_to_next_step()

    def define_step(self, step):
        self.steps.insert(-1, step)

    def go_to_next_step(self):
        if self.current_step_index == len(self.steps) - 1:
            return
        
        self.current_step_index += 1

    def go_to_prev_step(self):
        if self.current_step_index == 0:
            return
        
        self.current_step_index -= 1

    def get_current_step_name(self):
        return self.steps[self.current_step_index].name

    @abstractmethod
    def define_steps(self):
        pass

class BasicRun(Run):
    def __init__(self):
        super().__init__()
        self.define_steps()

    def define_steps(self):
       self.define_step(Step(name="STARTUP"))
       self.define_step(Step(name="STANDBY"))
       self.define_step(Step(name="SIG_PREVIEW_1"))
       self.define_step(Step(name="CALIBRATION"))
       self.define_step(Step(name="SIG_PREVIEW_2"))
       self.define_step(Step(name="HABITUATION"))
       self.define_step(Step(name="BASELINE"))
       self.define_step(Step(name="CHALLENGE"))
# -*- coding: utf-8 -*-
"""
GEMouse

A basic physiological signal simulator for raspberry pi that
provides a Graphical Interface for adjusting settings.

For use with the Ray Lab automated autoresuscitation system and PCC software.

created by Christopher S Ward (C) 2022

Features include
*customizable settings for duration and rate of simulated signals
*control of RPi pin-out for signal simulations
*listening to RPi pin-in for trigger signal (indicating gas challenge)
*GUI for customizing settings, buttons for hold mode or 'emouse' challenge runs

"""

__version__ = '1.0.0'

#%% import libraries

from PyQt5.QtCore import pyqtSlot, Qt,  QThreadPool, QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton 
from PyQt5.QtWidgets import QTextEdit
import sys


try:
    import RPi.GPIO as GPIO
    
except:
    print('RPi.GPIO library unavailable - Are you using a Pi?')
    class GPIO:
        BOARD = 1
        OUT = 1
        IN = 1
        HIGH = 5
        LOW = 0
        simulated = True
        
        def setmode(a):
           print(a)
        def setup(a, b):
           print(a)
        def input(a):
            return 0
        def output(a, b):
           print(a)
        def cleanup():
           print('a')
        def setwarnings(flag):
           print('False')



#%% setup Raspberry Pi pins

GPIO.setmode(GPIO.BOARD)
GPIO.setup(3, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(7, GPIO.IN)



#%% functions

def cycler_prep(instance,label):
    print(f'cycler_prep : {label}')
    VF = float(getattr(instance,f'{label}_VF'))
    VF_IS = float(getattr(instance,f'{label}_VF_IS'))
    HR = float(getattr(instance,f'{label}_HR'))
    HR_IS = float(getattr(instance,f'{label}_HR_IS'))
    
    VF = min(VF,1000)
    HR = min(HR,1000)
    
    VF_IS = min(max(0.33,VF_IS),3)
    HR_IS = min(max(0.33,HR_IS),3)
    
    # convert VF and HR to TT and RR (msec)    
    if float(VF) == 0:
        TT = 999999
    else:
        TT = int(60/float(VF)*1000)
    
    if float(HR) == 0:
        RR = 999999
    else:
        RR = int(60/float(HR)*1000)
        
    if float(VF) == 0:
        TT_on = 10
        TT_2 = 0
        TT_2_on = 10
    else:
        TT_on = int(TT/2)
        TT_2 = int(TT+TT*float(VF_IS))
        TT_2_on = int(TT_2/2)
        
    if float(HR) == 0:
        RR_on = 10
        RR_2 = 0
        RR_2_on = 10
    else:    
        RR_on = 10
        RR_2 = int(RR+RR*float(HR_IS))
        RR_2_on = 10
            
    return {
        'TT':{
            1:{
                'on_limit':TT_on,
                'beat_limit':TT
                },
            0:{
                'on_limit':TT_2_on,
                'beat_limit':TT_2
                }
            },
        'RR':{
            1:{
                'on_limit':RR_on,
                'beat_limit':RR
                },
            0:{
                'on_limit':RR_2_on,
                'beat_limit':RR_2
                }
            }
        }



def pulse(pulse_timer,timings_dict,pulse_toggle,pin = None):
    pulse_timer += 1
    on_limit = timings_dict[pulse_toggle]['on_limit']
    beat_limit = timings_dict[pulse_toggle]['beat_limit']
    
    
    
    if pulse_timer == 1:
        if hasattr(GPIO,'simulated'):
            print(f'{pin} - ON')
        else:
            GPIO.output(pin,GPIO.HIGH)
            
    elif pulse_timer == on_limit:
        if hasattr(GPIO,'simulated'):
            print(f'{pin} - OFF')
        else:
            GPIO.output(pin,GPIO.LOW)
    elif pulse_timer == beat_limit:
        pulse_timer = 0
        pulse_toggle = int(not(bool(pulse_toggle)))
    return pulse_timer,pulse_toggle


def trigger_check(pin = None):
    if GPIO.input(pin) == GPIO.HIGH:
        return 1
    else:
        return 0
        
    
        
def pin_reset(pin_list):
    for i in pin_list:
        GPIO.output(i,GPIO.LOW)
    


def widget_builder(
        instance,
        label,
        size = [(100,25),(75,25)],
        position = (0,0)
        ):
    
    setattr(instance, f'{label}_label', QLabel(label, parent = instance))
    setattr(instance, f'{label}_edit', QTextEdit(
        str(getattr(instance,label)), 
        instance)
        )
    
    getattr(instance, f'{label}_label').setFixedSize(*size[0])
    getattr(instance, f'{label}_edit').setFixedSize(*size[1])
    getattr(instance, f'{label}_label').move(*position)
    getattr(instance, f'{label}_edit').move(
        position[0]+size[0][0],
        position[1]
        )
    setattr(instance, f'{label}_set', QPushButton('Set', parent = instance))
    getattr(instance, f'{label}_set').setFixedSize(50,25)
    getattr(instance, f'{label}_set').move(
        position[0]+size[0][0]+size[1][0],
        position[1]
        )
    def widget_action(instance):
        print(instance,label)
        print(getattr(instance,label))
        setattr(instance,label,getattr(instance,f'{label}_edit').toPlainText())
        print(getattr(instance,label))
    
    # add an {label}_action method to handle the button click - 
    # lambda is used to facillitate loading an agument needed for the function 
    # to associate the correct value for instance
    setattr(instance, f'{label}_action',lambda: widget_action(instance)) 
    getattr(instance, f'{label}_set').clicked.connect(
        getattr(instance,f'{label}_action')
        )
    

        

#%% class for gui
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()

        self.setWindowTitle('GUI Electronic Mouse - v{}'.format(__version__))
        self.setGeometry(10,10,1250,750)
        self.move(100,100)
        self.Label_1=QLabel(
            '<h1>**GUI Electronic Mouse - v{}**</h1>'.format(__version__),
            parent=self
            )
        self.Label_1.setFixedSize(1250,25)
        self.Label_1.move(0,10)
        self.Label_1.setAlignment(Qt.AlignCenter)

        
        # settings/attributes
        self.running = 0
        self.repeat_challenges = 0
        
        self.cycle_duration = 0.001
        self.qthreadpool = QThreadPool()
        self.qthreadpool.setMaxThreadCount(1)

        self.looptimer = QTimer(self, interval = 1)
        self.looptimer.timeout.connect(self.run)
        self.duration = 0
        
        self.calibration_VF = 30
        self.calibration_VF_IS = 0
        self.calibration_HR = 60
        self.calibration_HR_IS = 0
        self.calibration_duration = 5
        widget_builder(self,'calibration_VF',position = (100,100))
        widget_builder(self,'calibration_VF_IS',position = (100,125))
        widget_builder(self,'calibration_HR',position = (100,150))
        widget_builder(self,'calibration_HR_IS',position = (100,175))
        widget_builder(self,'calibration_duration',position = (100,200))
        
        
        self.habituation_VF = 180
        self.habituation_VF_IS = 2
        self.habituation_HR = 500
        self.habituation_HR_IS = 2
        self.habituation_duration = 5
        widget_builder(self,'habituation_VF',position = (100,300))
        widget_builder(self,'habituation_VF_IS',position = (100,325))
        widget_builder(self,'habituation_HR',position = (100,350))
        widget_builder(self,'habituation_HR_IS',position = (100,375))
        widget_builder(self,'habituation_duration',position = (100,400))
        
        
        self.baseline_VF = 180
        self.baseline_VF_IS = 0
        self.baseline_HR = 500
        self.baseline_HR_IS = 0
        self.baseline_duration = 5
        widget_builder(self,'baseline_VF',position = (100,500))
        widget_builder(self,'baseline_VF_IS',position = (100,525))
        widget_builder(self,'baseline_HR',position = (100,550))
        widget_builder(self,'baseline_HR_IS',position = (100,575))
        widget_builder(self,'baseline_duration',position = (100,600))
        
        
        self.hypervent_VF = 300
        self.hypervent_VF_IS = 0
        self.hypervent_HR = 400
        self.hypervent_HR_IS = 0
        self.hypervent_delay = 10
        self.hypervent_duration = 5
        widget_builder(self,'hypervent_VF',position = (400,100))
        widget_builder(self,'hypervent_VF_IS',position = (400,125))
        widget_builder(self,'hypervent_HR',position = (400,150))
        widget_builder(self,'hypervent_HR_IS',position = (400,175))
        widget_builder(self,'hypervent_delay',position = (400,200))
        widget_builder(self,'hypervent_duration',position = (400,225))
        
        
        self.apnea_VF = 0
        self.apnea_VF_IS = 0
        self.apnea_HR = 0
        self.apnea_HR_IS = 0
        self.apnea_duration = 5
        widget_builder(self,'apnea_VF',position = (400,300))
        widget_builder(self,'apnea_VF_IS',position = (400,325))
        widget_builder(self,'apnea_HR',position = (400,350))
        widget_builder(self,'apnea_HR_IS',position = (400,375))
        widget_builder(self,'apnea_duration',position = (400,400))
        
        
        self.recovery_VF = 120
        self.recovery_VF_IS = 0
        self.recovery_HR = 300
        self.recovery_HR_IS = 0
        self.recovery_duration = 5
        self.recovery_rounds = 10
        widget_builder(self,'recovery_VF',position = (700,100))
        widget_builder(self,'recovery_VF_IS',position = (700,125))
        widget_builder(self,'recovery_HR',position = (700,150))
        widget_builder(self,'recovery_HR_IS',position = (700,175))
        widget_builder(self,'recovery_duration',position = (700,200))
        widget_builder(self,'recovery_rounds',position = (700,225))
        
        
        self.ready_VF = 180
        self.ready_VF_IS = 0
        self.ready_HR = 500
        self.ready_HR_IS = 0
        self.ready_duration = 5
        widget_builder(self,'ready_VF',position = (700,300))
        widget_builder(self,'ready_VF_IS',position = (700,325))
        widget_builder(self,'ready_HR',position = (700,350))
        widget_builder(self,'ready_HR_IS',position = (700,375))
        widget_builder(self,'ready_duration',position = (700,400))
        
        
        self.delay_VF = self.ready_VF
        self.delay_VF_IS = self.ready_VF_IS
        self.delay_HR = self.ready_HR
        self.delay_HR_IS = self.ready_HR_IS
        self.delay_duration = self.hypervent_delay
        
        
        self.Calibration_Hold = QPushButton('Calibration', parent = self)
        self.Habituation_Hold = QPushButton('Habituation', parent = self)
        self.Baseline_Hold = QPushButton('Baseline', parent = self)
        self.Hypervent_Hold = QPushButton('Hypervent', parent = self)
        self.Apnea_Hold = QPushButton('Apnea', parent = self)
        self.Recovery_Hold = QPushButton('Recovery', parent = self)
        self.Ready_Hold = QPushButton('Ready', parent = self)
        self.OFF = QPushButton('OFF', parent = self)
        self.CHB_RHAR_cycle = QPushButton('Cycle [CHB_RHAR]', parent = self)
        self.RHAR_cycle = QPushButton('Cycle [RHAR]', parent = self)
        
        
        self.Calibration_Hold.setFixedSize(100,25)
        self.Habituation_Hold.setFixedSize(100,25)
        self.Baseline_Hold.setFixedSize(100,25)
        self.Hypervent_Hold.setFixedSize(100,25)
        self.Apnea_Hold.setFixedSize(100,25)
        self.Recovery_Hold.setFixedSize(100,25)
        self.Ready_Hold.setFixedSize(100,25)
        self.OFF.setFixedSize(100,25)
        self.CHB_RHAR_cycle.setFixedSize(100,25)
        self.RHAR_cycle.setFixedSize(100,25)
        
        self.Calibration_Hold.move(100,650)
        self.Habituation_Hold.move(200,650)
        self.Baseline_Hold.move(300,650)
        self.Hypervent_Hold.move(100,675)
        self.Apnea_Hold.move(200,675)
        self.Recovery_Hold.move(300,675)
        self.Ready_Hold.move(400,675)
        self.OFF.move(100,700)
        self.CHB_RHAR_cycle.move(300,700)
        self.RHAR_cycle.move(400,700)
        
        self.Calibration_Hold.clicked.connect(self.Calibration_Hold_action)
        self.Habituation_Hold.clicked.connect(self.Habituation_Hold_action)
        self.Baseline_Hold.clicked.connect(self.Baseline_Hold_action)
        self.Hypervent_Hold.clicked.connect(self.Hypervent_Hold_action)
        self.Apnea_Hold.clicked.connect(self.Apnea_Hold_action)
        self.Recovery_Hold.clicked.connect(self.Recovery_Hold_action)
        self.Ready_Hold.clicked.connect(self.Ready_Hold_action)
        self.CHB_RHAR_cycle.clicked.connect(self.CHB_RHAR_cycle_action)
        self.RHAR_cycle.clicked.connect(self.RHAR_cycle_action)
        self.OFF.clicked.connect(self.OFF_action)
        
    
    
    def reset_timers(self, label, hold = False):
        self.running = 1
        
        if hold == True:
            self.duration = -1
        else:
            self.duration = float(getattr(self,f'{label}_duration'))
            
        self.TT_RR_timings = cycler_prep(self, label)
        self.timer = 0
        self.TT_timer = 0
        self.TT_1v2_toggle = 1
        self.RR_timer = 0
        self.RR_1v2_toggle = 1
        self.looptimer.stop()
        
    def get_delay_timers(self):
        self.running = 1
    
    @pyqtSlot()
    def increment_duration(self):
        self.duration += 1
    
    
    @pyqtSlot()
    def Calibration_Hold_action(self):
        print('Calibration_Hold')
        self.reset_timers('calibration', hold = True)
        self.looptimer.start()
        
    
    @pyqtSlot()
    def Habituation_Hold_action(self):
        print('Habituation_Hold')
        self.reset_timers('habituation', hold = True)
        self.looptimer.start()
        
        
    @pyqtSlot()
    def Baseline_Hold_action(self):
        print('Baseline Hold')
        self.reset_timers('baseline', hold = True)
        self.looptimer.start()
        
        
    @pyqtSlot()
    def Hypervent_Hold_action(self):
        print('Hypervent_Hold')
        self.reset_timers('hypervent', hold = True)
        self.looptimer.start()
        
        
    @pyqtSlot()
    def Apnea_Hold_action(self):
        print('Apnea_Hold')
        self.reset_timers('apnea', hold = True)
        self.looptimer.start()
    
    
    @pyqtSlot()
    def Recovery_Hold_action(self):
        print('Recovery_Hold')
        self.reset_timers('recovery', hold = True)
        self.looptimer.start()
        
        
    @pyqtSlot()
    def Ready_Hold_action(self):
        print('Ready_Hold')
        self.reset_timers('ready', hold = True)
        self.looptimer.start()
        
        
    @pyqtSlot()
    def CHB_RHAR_cycle_action(self):
        print('CHB->(RHAR)')
        self.repeat_challenges = 1
        self.delay_duration = self.hypervent_delay
        self.delay_for_trigger = 0
        self.state = 'calibration'
        self.timed_run()
        
        
        
        
    @pyqtSlot()
    def RHAR_cycle_action(self):
        print('(RHAR)')
        self.repeat_challenges = 1
        self.delay_duration = self.hypervent_delay
        self.delay_for_trigger = 0
        self.state = 'ready'
        self.timed_run()
        
        
    @pyqtSlot()
    def timed_run(self):
        if int(self.repeat_challenges) < int(self.recovery_rounds):
            print(self.state)
            print(self.repeat_challenges,self.recovery_rounds)
            self.reset_timers(self.state)
            self.looptimer.start()
            if self.state == 'delay':
                if float(self.hypervent_delay) <0:
                    self.delay_for_trigger = 1
                else: 
                    self.delay_for_trigger = 0
                    
            
            if self.state == 'recovery':
                self.repeat_challenges = int(self.repeat_challenges) + 1
            QTimer.singleShot(int(self.duration*1000),self.advance_state)
        
        else:
            print('Finished')
        
        
    
    @pyqtSlot()
    def advance_state(self):
        self.running = 0
        
        if self.state == 'calibration':
            self.state = 'habituation'
        elif self.state == 'habituation':
            self.state = 'baseline'
        elif self.state == 'baseline':
            self.state = 'delay'
        elif self.state == 'delay':
            self.state = 'hypervent'
        elif self.state == 'hypervent':
            self.state = 'apnea'
        elif self.state == 'apnea':
            self.state = 'recovery'
        elif self.state == 'recovery':
            self.state = 'ready'
        elif self.state == 'ready':
            self.state = 'delay'
        
        self.timed_run()
    
    
    @pyqtSlot()
    def run(self):
        if self.running == 0:
            self.looptimer.stop()
        
        # VF pulse
        self.TT_timer,self.TT_1v2_toggle = pulse(
            self.TT_timer,
            self.TT_RR_timings['TT'],
            self.TT_1v2_toggle,
            pin = 3)
        
        # HR pulse
        self.RR_timer,self.RR_1v2_toggle = pulse(
            self.RR_timer,
            self.TT_RR_timings['RR'],
            self.RR_1v2_toggle,
            pin = 5)  
        
        # check for trigger
        self.trigger = trigger_check(pin = 7)
        if self.trigger == 1 and \
                self.state == 'delay' and \
                self.delay_for_trigger == 1:
            self.advance_state()
        
  

        
    
    @pyqtSlot()
    def OFF_action(self):
        self.reset_timers('ready', hold = True)
        self.running = 0
        self.repeat_challenges = int(self.recovery_rounds)
        pin_reset([3,5])
        print('off')
        
        
    
        
#%% main

def main():
    app=QApplication(sys.argv)
    MW = MainWindow()
    MW.show()
    sys.exit(app.exec_())



#%% run main()

if __name__ == '__main__':
    main()

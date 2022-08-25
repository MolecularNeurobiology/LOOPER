# -*- coding: utf-8 -*-
"""
GEMouse

A basic physiological signal simulator for raspberry pi that
provides a Graphical Interface for adjusting settings.

For use with the Ray Lab automated autoresuscitation system and PCC software.

created by Christopher S Ward (C) 2022

"""

__version__ = '1.0.0'

#%% import libraries
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QRunnable, QThreadPool, QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QPushButton, QButtonGroup, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QFileDialog, QComboBox, QLineEdit, QDoubleSpinBox, QGroupBox, QRadioButton, QListWidget, QListWidgetItem
from PyQt5.QtWidgets import QAbstractItemView, QTextEdit
from PyQt5.QtGui import QImage, QPixmap, QTransform, QPainter, QPen, QColor
import io
from PIL import Image, ImageDraw, ImageFont
import sys
import os
#import RPi.GPIO as GPIO
import time


#%% setup Raspberry Pi pins
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(3, GPIO.OUT)
# GPIO.setup(5, GPIO.OUT)
# GPIO.setup(7, GPIO.IN)


#%% functions

# timer
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
        
    TT_on = int(TT/2)
    TT_2 = int(TT+TT*float(VF_IS))
    TT_2_on = int(TT_2/2)
    
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

# def cycler_run(instance,duration,TT_RR_timings):
#     print('cycler run')
#     timer = 0
    
#     TT_timer = 0
#     TT_1v2_toggle = 1
#     RR_timer = 0
#     RR_1v2_toggle = 1
    
    
#     while instance.running == 1:
#         timer += instance.cycle_duration
#         if duration < 0:
#             pass
#         elif timer >= duration:
#             print('duration ended')
#             instance.running = 0
        
#         # VF pulse
#         TT_timer,TT_1v2_toggle = pulse(
#             TT_timer,
#             TT_RR_timings['TT'],
#             TT_1v2_toggle,
#             pin = 'TT')
        
#         # HR pulse
#         RR_timer,RR_1v2_toggle = pulse(
#             RR_timer,
#             TT_RR_timings['RR'],
#             RR_1v2_toggle,
#             pin = 'RR')
            
#         time.sleep(instance.cycle_duration)
        



def pulse(pulse_timer,timings_dict,pulse_toggle,pin = None):
    pulse_timer += 1
    on_limit = timings_dict[pulse_toggle]['on_limit']
    beat_limit = timings_dict[pulse_toggle]['beat_limit']
    
    if pulse_timer == 1:
        print(f'{pin} - ON') # remove this once on RPi
    elif pulse_timer == on_limit:
        print(f'{pin} - OFF')
    elif pulse_timer == beat_limit:
        pulse_timer = 0
        pulse_toggle = int(not(bool(pulse_toggle)))
    return pulse_timer,pulse_toggle
        
        
def pin_reset(pin_list):
    pass    


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
   
    
#%% class for threading
class Worker(QRunnable):
    def __init__(self, thing_to_do):
        """
        Instantiate the Worker Class.

        Parameters
        ---------
        ...
        """
        super(Worker, self).__init__()
        self.thing_to_do = thing_to_do

    
    def run(self):
        """
        ...
        """
        self.thing_to_do()

        print('done')

class Cycler(QRunnable):
    def __init__(self, instance,duration,TT_RR_timings):
        """
        Instantiate the Worker Class.

        Parameters
        ---------
        ...
        """
        super(Cycler, self).__init__()
        self.instance = instance
        self.duration = duration
        self.TT_RR_timings = TT_RR_timings
        
        print('cycler run')
        self.timer = 0
        
        self.TT_timer = 0
        self.TT_1v2_toggle = 1
        self.RR_timer = 0
        self.RR_1v2_toggle = 1
        
    def run(self):
        """
        ...
        """



        while self.instance.running == 1:
            pass
        
    

        
            self.timer += self.instance.cycle_duration
            if self.duration < 0:
                pass
            elif self.timer >= self.duration:
                print('duration ended')
                self.instance.running = 0
            
            # VF pulse
            self.TT_timer,self.TT_1v2_toggle = pulse(
                self.TT_timer,
                self.TT_RR_timings['TT'],
                self.TT_1v2_toggle,
                pin = 'TT')
            
            # HR pulse
            self.RR_timer,self.RR_1v2_toggle = pulse(
                self.RR_timer,
                self.TT_RR_timings['RR'],
                self.RR_1v2_toggle,
                pin = 'RR')
                    
               
        
            QTimer.singleShot(1)
        print('Done')
        

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
        self.cycle_duration = 0.001
        self.qthreadpool = QThreadPool()
        self.qthreadpool.setMaxThreadCount(1)


        
        
        self.calibration_VF = 180
        self.calibration_VF_IS = 0
        self.calibration_HR = 120
        self.calibration_HR_IS = 0
        self.calibration_duration = 90
        widget_builder(self,'calibration_VF',position = (100,100))
        widget_builder(self,'calibration_VF_IS',position = (100,125))
        widget_builder(self,'calibration_HR',position = (100,150))
        widget_builder(self,'calibration_HR_IS',position = (100,175))
        widget_builder(self,'calibration_duration',position = (100,200))
        
        
        self.habituation_VF = 180
        self.habituation_VF_IS = 2
        self.habituation_HR = 500
        self.habituation_HR_IS = 2
        self.habituation_duration = 120
        widget_builder(self,'habituation_VF',position = (100,300))
        widget_builder(self,'habituation_VF_IS',position = (100,325))
        widget_builder(self,'habituation_HR',position = (100,350))
        widget_builder(self,'habituation_HR_IS',position = (100,375))
        widget_builder(self,'habituation_duration',position = (100,400))
        
        
        self.baseline_VF = 180
        self.baseline_VF_IS = 0
        self.baseline_HR = 500
        self.baseline_HR_IS = 0
        self.baseline_duration = 120
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
        self.hypervent_duration = 20
        widget_builder(self,'hypervent_VF',position = (300,100))
        widget_builder(self,'hypervent_VF_IS',position = (300,125))
        widget_builder(self,'hypervent_HR',position = (300,150))
        widget_builder(self,'hypervent_HR_IS',position = (300,175))
        widget_builder(self,'hypervent_delay',position = (300,200))
        widget_builder(self,'hypervent_duration',position = (300,225))
        
        
        self.apnea_VF = 0
        self.apnea_VF_IS = 0
        self.apnea_HR = 0
        self.apnea_HR_IS = 0
        self.apnea_duration = 30
        widget_builder(self,'apnea_VF',position = (300,300))
        widget_builder(self,'apnea_VF_IS',position = (300,325))
        widget_builder(self,'apnea_HR',position = (300,350))
        widget_builder(self,'apnea_HR_IS',position = (300,375))
        widget_builder(self,'apnea_duration',position = (300,400))
        
        
        self.recovery_VF = 120
        self.recovery_VF_IS = 0
        self.recovery_HR = 300
        self.recovery_HR_IS = 0
        self.recovery_duration = 60
        widget_builder(self,'recovery_VF',position = (500,100))
        widget_builder(self,'recovery_VF_IS',position = (500,125))
        widget_builder(self,'recovery_HR',position = (500,150))
        widget_builder(self,'recovery_HR_IS',position = (500,175))
        widget_builder(self,'recovery_duration',position = (500,200))
        
        
        self.ready_VF = 180
        self.ready_VF_IS = 0
        self.ready_HR = 500
        self.ready_HR_IS = 0
        self.ready_duration = -1
        widget_builder(self,'ready_VF',position = (500,300))
        widget_builder(self,'ready_VF_IS',position = (500,325))
        widget_builder(self,'ready_HR',position = (500,350))
        widget_builder(self,'ready_HR_IS',position = (500,375))
        widget_builder(self,'ready_duration',position = (500,400))
        
        
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
        self.OFF.clicked.connect(self.OFF_action)
        
        
    @pyqtSlot()
    def Calibration_Hold_action(self):
        print('Calibration_Hold')
        self.running = 1
        settings = cycler_prep(self, 'calibration')
        
        # new_worker = Cycler(self,-1,settings)

        # self.qthreadpool.start(new_worker)
    
    

        # while self.instance.running == 1:
        #     pass
        # self.looptimer.stop()

        
        self.duration = -1
        self.TT_RR_timings = settings
        
        print('cycler run')
        self.timer = 0
        
        self.TT_timer = 0
        self.TT_1v2_toggle = 1
        self.RR_timer = 0
        self.RR_1v2_toggle = 1


        self.looptimer = QTimer(self, interval = 1)
        # self.looptimer.interval(1)
        self.looptimer.timeout.connect(self.run)
        self.looptimer.start()
    
    @pyqtSlot()
    def run(self):
        if self.running == 0:
            self.looptimer.stop()
    
        self.timer += self.cycle_duration
        if self.duration < 0:
            pass
        elif self.timer >= self.duration:
            print('duration ended')
            self.running = 0
        
        # VF pulse
        self.TT_timer,self.TT_1v2_toggle = pulse(
            self.TT_timer,
            self.TT_RR_timings['TT'],
            self.TT_1v2_toggle,
            pin = 'TT')
        
        # HR pulse
        self.RR_timer,self.RR_1v2_toggle = pulse(
            self.RR_timer,
            self.TT_RR_timings['RR'],
            self.RR_1v2_toggle,
            pin = 'RR')    


        
    
    @pyqtSlot()
    def OFF_action(self):
        self.running = 0
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

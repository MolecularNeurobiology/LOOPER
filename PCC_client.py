# -*- coding: utf-8 -*-

__version__ = '45.0.0'

"""
Physiology Command Center
(C) 2019
@author: Christopher Ward (christow@bcm.edu, ward.chris.s@gmail.com)
Created as part of the Russell Ray Molecular Neurobiology Group's
Autoresuscitation Project
contributions to this project include code, concepts, or consultation from 
several individuals including Russell Ray, Eunice Aissi, Dipak Patel, 
Mariana Garcia Costa, Savannah Lusk, Brandon Ruiz, and Kevin Jiang.
The current iteration is intended to function primarily as a headless
client for control via web app while delivering similar control of assays
such as the neonate autoresuscitation reflex assay.

Additional changes include transition away from pygame to pyside6,
and general refactoring and reoganization of modules and functions.
"""

# %% import libraries
# external libraries
import argparse
import logging
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
import pyqtgraph
import sys


# internal libraries
import SETTINGS
import DETECTORS
import EFFECTORS

# %% define functions



# %% define classes
class DATA():
    def __init__(self):
        self.current_mode = 0
        self.prev_mode = -1

        self.flow_signal = []
        self.ecg_signal = []
        self.vol_signal = [] # remove ?
        
        self.breath_list = []
        self.beat_list = []


        self.now=datetime.now()
        self.cur_status_dict={'standby':0,'startup':0,'streaming':0,'ready to save':0,'calibration':0,'challenge air':0,'challenge gas':0,
                 'pulse':{
                         'calibration':{'state':0,'start':now,'pin':1},
                         'challenge air':{'state':0,'start':now,'pin':3},
                         'challenge gas':{'state':0,'start':now,'pin':2}
                         },
                 'startup_ready':0
                 }
        self.old_status_dict={'standby':0,'startup':0,'streaming':0,'ready to save':0,'calibration':0,'challenge air':0,'challenge gas':0,
                 'pulse':{
                         'calibration':{'state':0,'start':now,'pin':1},
                         'challenge air':{'state':0,'start':now,'pin':3},
                         'challenge gas':{'state':0,'start':now,'pin':2}
                         },
                 'startup_ready':0
                 }
        
    def prepare_data_json(attr_list):
        """
        prepare a json string populated from the attributes specified by attr_list
        """
        pass


class MainWindow(QWidget):
    def __init__(self,version):
        super().__init__()

        self.setWindowTitle(f'PCC-client {version}')

        self.pulse_counter = 0

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.action_pulse_timer)
        self.pulse_timer.start(1000)

    def action_pulse_timer(self):
        print(self.pulse_counter)
        self.pulse_counter += 1

        if self.pulse_counter >= 10:
            sys.exit()


        # QApplication
        pass
    ## Timers (to create event loops)
    # receiver_timer

    # broadcast_timer

    # status_pulse_timer

    # experiment_loop_timer

    ## METHODS
    # read in data from streams

    # send out data

    # send out pulse

    # experiment loop



# %% define main
def main():
    # parse arguments
    parser = argparse.ArgumentParser('PCC_client')
    parser.add_argument('-platform',default = 'offscreen')
    parsed_args = parser.parse_args()
    sys.argv.append('--platform')
    sys.argv.append('minimal')
    # checkin-pulse
    print('startup')
    print(sys.argv)
    
    app = QApplication(sys.argv)
    window = MainWindow(__version__)
    window.show()
    print('running')
    sys.exit(app.exec())



    print('exit')


# run main
if __name__ == '__main__':
    main()
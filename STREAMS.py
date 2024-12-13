
import queue as Queue
from scipy import signal
import sys
import threading
from copy import deepcopy
from datetime import datetime
import pygame
import math


# Arduino Related
class StreamArduino(object):
    def __init__(self,device):
        self.device=device
        self.data=Queue.Queue()
        self.finished = False

    def readStreamData(self):
        while not self.finished:
            self.finished = False
            returnText=self.device.read(1000)
            self.data.put_nowait(deepcopy(returnText))


class SimulatedArduino():
    def __init__(self):
        self.data=Queue.Queue()
        self.listener=Queue.Queue()
        self.finished = False
    
    def sendCommand(self,command):
        self.listener.put_nowait(command)

    def write(self,command):
        self.listener.put_nowait(command)

    def translate_command_to_response(self,command):
        translation_dict = {
            b'<C':b'calibration-sim',
            b'<R':b'room air-sim',# update
            b'<A':b'challenge gas-sim',# update
            b'<U':b'startup sent-sim',
            b'<S':b'standby sent-sim',
            b'<Z':b'abort sent-sim',
            b'<D':b'shutdown-sim',
            b'<E':b'finish startup-sim',
        }
        return translation_dict.get(command[:2],'unknown')

    def readStreamData(self):
        while not self.finished:
            self.finished = False

            if self.listener.empty()==False:
                command = self.listener.get_nowait()
                response = self.translate_command_to_response(command)
                self.data.put_nowait(deepcopy(response))
        
        
# LabJack Related
class SimulatedDataReader():
    def __init__(self):
        self.finished = True
        self.data = Queue.Queue()
        self.start=0
        self.current=0
        self.duration=0.0
        self.captured_time=0
        self.SCAN_FREQUENCY=0
        self.NUM_CHANNELS=0
        self.lag=0
        self.missed = []
        self.errors = []
        self.clock = pygame.time.Clock()

    def setDIOState(self,*args):
        pass

    def close(self, *args):
        pass

    def readStreamData(self):
        self.finished = False
        self.start = datetime.now()
        self.readCount=0

        while not self.finished:
            # Calling with convert = False, because we are going to convert in
            # the main thread.

            # 16 samples per frame

            # simulate 2Hz and 10Hz signals

            #t = datetime.now().microsecond / 1000000

            #ain0 = math.sin(t*6.28*2)
            #ain1 = math.sin(t*6.28*10)

            returnDict = {
                'errors':0,
                'missed':[],
                'result':{
                    'AIN0':[math.sin(i*6.28*2) for i in range(1000)],
                    'AIN1':[math.sin(i*6.28*10) for i in range(1000)],
                    'AIN2':[0.2 for i in range(1000)],
                    'AIN3':[0.3 for i in range(1000)],
                    'AIN4':[0.4 for i in range(1000)],
                    'AIN5':[0.5 for i in range(1000)]
                }
            }
            if returnDict is None:
                print("No stream data")
                continue

            self.data.put_nowait(deepcopy(returnDict))

            self.missed += returnDict["missed"]
            self.readCount += 1
            self.current=datetime.now()

            self.clock.tick(1)


    def stopStreamData(self):
        self.finished = True
        

        
class StreamDataReader(object):
    def __init__(self, device):
        self.device = device
        self.data = Queue.Queue()
        self.readCount = 0
        self.missed = 0
        self.finished = True
        self.start=0
        self.current=0
        self.duration=0.0
        self.captured_time=0
        self.SCAN_FREQUENCY=0
        self.NUM_CHANNELS=0
        self.lag=0
        
    def readStreamData(self):
        self.finished = False
        
        print("Start stream.")
        
        try:
            # Try to stop stream mode. Ignore exception if it fails.
            self.device.streamStop()
            print('Prior Stream Terminated')
        except:
            print('No Prior Stream')
        
        try:
            self.start = datetime.now()
            self.readCount=0
            self.device.streamStart()
            
            while not self.finished:
                # Calling with convert = False, because we are going to convert in
                # the main thread.
                returnDict = next(self.device.streamData(convert=False))
                if returnDict is None:
                    print("No stream data")
                    continue

                self.data.put_nowait(deepcopy(returnDict))

                self.missed += returnDict["missed"]
                self.readCount += 1
                self.current=datetime.now()

            
            print("Stream stopped.\n")
            self.device.streamStop()
            
        except Exception:
            try:
                # Try to stop stream mode. Ignore exception if it fails.
                self.device.streamStop()
            except:
                pass
            self.finished = True
            e = sys.exc_info()[1]
            print("readStreamData exception: %s %s" % (type(e), e))

    def stopStreamData(self):
        try:
            # Try to stop stream mode. Ignore exception if it fails.
            self.finished = True
        except:
            pass

# Minerva related
class MinervaReceiver():
    def __init__(self,minerva_plugin_object):
        pass

    def process_data(
            self,
            data_object,
            settings_object,
            callbacks_object
    ):
        pass
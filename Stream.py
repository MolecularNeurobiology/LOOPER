
import queue as Queue
from scipy import signal
import sys
import threading
from copy import deepcopy
from datetime import datetime

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


        
##
        
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

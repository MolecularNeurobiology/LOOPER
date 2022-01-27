# -*- coding: utf-8 -*-

__VERSION__ = '41.0.1'

"""

Physiology Command Center
(C) 2019
@author: Christopher Ward (christow@bcm.edu, ward.chris.s@gmail.com)

Created as part of the Russell Ray Molecular Neurobiology Group's
Autoresuscitation Project

contributions to this project include code, concepts, or consultation from 
several individuals including Russell Ray, Eunice Aissi, Dipak Patel, 
Mariana Garcia Costa, Savannah Lusk, Brandon Ruiz, and Kevin Jiang


This software provides a graphical interface for I/O between an computer
and 1) Arduino Microcontroller, 2) LabJack Analog to Digital Converter.
Signals from the LabJack undergo signal processing to identify key features
used as triggers to execute programmed control sequences run by the Arduino.

The current implementation utilizes pneumotachography and electrocardiogram 
signals to monitor breathing and heart rate as part of a neonate 
autoresuscitation assay.


Default Workflow (subject to change)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
0-signal preview mode (adjust baseline and confirm tunable parameters)
**user confirmation for next step
1-calibration mode (receive calibration signals [20x30uL pulses])
**signal to DC out [trigger auto pipette and LED] upon start
**end upon timer (and confirmation from auto pipett upon complete?)
+++creates save file for calibration values
2-signal preview mode (adjust baseline and confirm tunable parameters)
**user confirmation for next step
3-habituation mode (wait 30 minutes for habituation)
**preview and capture signals for review later - consider updates to interval
4-baseline mode (capture 10 minutes of signal for baseline)
**preview and capture signals - consider criteria of 
    QUANTITY_OF_QUALITY signal...
    Q_O_Q : 10 seconds per interval of 'calm breathing', 
    sum of intervals is at least 1 minute
5-challenge mode (ANOXIA challenge until breath cessation, 
    Room Air until recovery....recovery based on >=X% HR and BPM recovery)
**preview and capture signals - include tags for ANOXIA vs ROOM AIR
**signal to DC/Serial out 
    [trigger to switch between modes (DC on for ANOXIA, DC off for ROOM AIR)]
**move to EXPERIMENT ENDED mode upon failure to recover breathing/hr
6-experiment ended mode 
**terminate preview and capture, send signal to notify user
**signal to DC out, or other Raspberry Pi notification

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs: currently none - all settings are coordinated within the GUI
Outputs: timeseries signal datafile 
    [calibration capture, animal signal capture] - this is currently one file 
    with seperate sections

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TODO regarding PCC

*create flexibility for alternate study designs/data collection
*create flexibility to terminate study after variable number of trials
*error checking to prevent inversion of y axis, baseline and threshold values
    (and any other common sources of crashes)
*better handle/close out of labjack 
    (probably try except and closing out connection)
*better handling for arduino connection


*revisit UX restrictions for tweakables for display and general UX design


related but slightly seperate
*server/client for comms with Supervisor System and Worker Systems 
    (i.e. central workstation communicates to rigs running PCC for set-up and 
     monitoring)
*tools to adapt PCC output for BASSPRO_STAGG pipeline, and Rice D2K pipelines

"""

##
#%% import libraries
import pygame
import numpy
from scipy import signal
import sys
import threading
from copy import deepcopy
from datetime import datetime

from gpiozero import CPUTemperature

import queue as Queue
import u6
import tkinter
import tkinter.filedialog
import tkinter.simpledialog
import os

import smtplib
import ssl
import serial

##
#%%
# prep serial connection to arduino
try:
    ser=serial.Serial()
    ser.baudrate=9600
    ser.port='/dev/ttyACM0' #this may need to be updated if arduino settings change
    ser.timeout=1
    ser.open()
    Connected_Arduino=True
except Exception as e:
    print('unable to connect to arduino')
    Connected_Arduino=False
    
##
#%% define functions
def guiSaveFileName(kwargs={}):
    """Returns the path to the filename and location entered in the GUI
    *Function calls on tkFileDialog and uses those arguments
    .....
    (declare as a dictionairy)
    {"defaultextension":"","filetypes":"","initialdir":"",...
    "initialfile":"","multiple":"","message":"","parent":"","title":""}
    .....
    """
    root=tkinter.Tk()
    outputtext=tkinter.filedialog.asksaveasfilename(
        **kwargs)
    root.destroy()
    return outputtext

def guiOpenFileName(kwargs={}):
    """Returns the path to the filename and location entered in the GUI
    *Function calls on tkFileDialog and uses those arguments
    .....
    (declare as a dictionairy)
    {"defaultextension":"","filetypes":"","initialdir":"",...
    "initialfile":"","multiple":"","message":"","parent":"","title":""}
    .....
    """
    root=tkinter.Tk()
    outputtext=tkinter.filedialog.askopenfilename(
        **kwargs)
    root.destroy()
    return outputtext

def guiGetFloat(title,text,default_if_canceled):
    """Returns a float based on the users entry
    *Function calls on tkinter.simpledialog and uses those arguments
    .....
    declare as a dictionairy)
    {"title":"","minvalue":"","maxvalue":""}

    .....
    """
    root=tkinter.Tk().withdraw()
    outputfloat=tkinter.simpledialog.askfloat(title,text)
    if outputfloat is None:
        try:
            root.destroy()
        except: pass
        return default_if_canceled
    else:
        try:
            root.destroy()
        except: pass
        return outputfloat

def guiGetText(title,text,default_if_canceled):
    """Returns text based on the users entry
    *Function calls on tkinter.simpledialog and uses those arguments
    .....
    declare as a dictionairy)
    {"title":"","minvalue":"","maxvalue":""}

    .....
    """
    root=tkinter.Tk().withdraw()
    outputtext=tkinter.simpledialog.askstring(title,text)
    if outputtext is None:
        try:
            root.destroy()
        except: pass
        return default_if_canceled
    else:
        try:
            root.destroy()
        except: pass
        return outputtext
#%%
def emailnotification(emailsettingslocation,dev):
    with open(emailsettingslocation,'r') as oif:
        settings=oif.read()
    settings_list=settings.split('\n')
    
    port=587 #port for starttls
    smtp_server = "smtp.gmail.com"
    sender_email = settings_list[0]
    receiver_email=settings_list[2]
    password=settings_list[1]
    now=datetime.now()
    message="""\
    Subject: NOTIFICATION FROM LABJACK - RPi station {device} - {serial}
    
    
    Message: Program has ended at {YYYY}-{MM:02d}-{DD:02d} {hh:02d}:{mm:02d}:{ss:02d}""".format(
    device=dev.deviceName,
    serial=dev.serialNumber,
    YYYY=now.year,
    MM=now.month,
    DD=now.day,
    hh=now.hour,
    mm=now.minute,
    ss=now.second)
    
    context=ssl.create_default_context()
    with smtplib.SMTP(smtp_server,port) as server:
        server.starttls(context=context)
        server.login(sender_email,password)
        server.sendmail(sender_email,receiver_email,message)
    print('message sent to {}'.format(receiver_email))
    print(message)


def saveCapturedData(filename,TEXTBLOCK):
    now=datetime.now()
    with open(filename,'a') as f:
        f.write('$$$$$ DATA SESSION -----\n')
        f.write('SESSION STARTED {year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}:{microsecond:06d}\n'.format(
                year=now.year, month=now.month, day=now.day,
                hour=now.hour, minute=now.minute, second=now.second,
                microsecond=now.microsecond))
        f.write('\n'.join(TEXTBLOCK)+'\n')
        
def appendCapturedData(filename,TEXTBLOCK):
    with open(filename,'a') as f:
        for r in TEXTBLOCK:
            f.write('\n'.join(r)+'\n')
            
def graphScaler(topleft,xy_size,x_minmax,y_minmax,x_vals,y_vals):
    x_size=xy_size[0]
    y_size=xy_size[1]
    bottomright=(topleft[0]+x_size,topleft[1]+y_size)
    x_range=x_minmax[1]-x_minmax[0]
    y_range=y_minmax[1]-y_minmax[0]
    x_pg_offset=topleft[0]
    y_pg_offset=topleft[1]
    x_scale=x_size/x_range
    y_scale=y_size/y_range
    corr_x=[(i-x_minmax[0])*x_scale+x_pg_offset for i in x_vals]
    corr_y=[(y_minmax[1]+i*-1)*y_scale+y_pg_offset for i in y_vals] #also inverts y value to match pygame coordinte system
    xy_list=[(max(min(corr_x[i],bottomright[0]),topleft[0]),max(min(corr_y[i],bottomright[1]),topleft[1])) for i in range(len(corr_x))]
    return xy_list

def toggle(state):
    if state==0:
        return 1
    else:
        return 0

def pulse_ender(device,pin,start,duration):
    pulse_status=1
    duration_timer=datetime.now()-start
    cur_dur_sec=duration_timer.seconds
    
    if cur_dur_sec>=duration:
        #print(cur_dur_sec)
        #print(start)
        #print(now)
        device.setDIOState(pin,0)
        pulse_status=0
    else:
        #print(cur_dur_sec)
        pass
    return pulse_status
        
    
def advance(state,minstate,maxstate):
    state+=1
    if state>maxstate:
        state=minstate
    return state

def trianglepoints(direction):
    if direction=='up':
        return [(10,0),(0,10),(20,10)]
    elif direction=='down':
        return [(10,10),(0,0),(20,0)]
    elif direction=='left':
        return [(0,10),(10,0),(10,20)]
    elif direction=='right':
        return [(0,0),(0,20),(10,10)]
    
def save_button():
    print('save')
    try:
        outputfile=guiSaveFileName({'title':'Save Signal Data','defaultextension':'.txt'})
        readytosave=1
        now=datetime.now()
        ##
        with open(outputfile,'w') as f:
            f.write('PLETHYSMOGRAPHY COMMAND CENTER DATA FILE\n')
            f.write('file may contain mutliple sessions, session marker : $$$$$\n')
            f.write('file created {year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}\n'.format(
                    year=now.year, month=now.month, day=now.day,
                    hour=now.hour, minute=now.minute, second=now.second))
        ##
    except:
        outputfile=None
        readytosave=0
        
    return outputfile,readytosave

def basicRR(CT,TS,noisecutoff,threshfactor,absthresh,minRR):
    """
    simple RR peak caller based on relative signal to noise thresholding
    CT = signal
    noisecutoff = perrcentile within signal to consider as noise
    threshfactor = multiple of the noisecutoff to use for beat detaction
    minRR = minimum RR in samples (1000BPM ~ 60 ms RR, minRR ~60 @1000Hz)
    **CV and Rvolt to thresh ratios may help for QC
    signal filtering is helpful (recommend butter highpass and notch filters)
    """
    
    #get above thresh
    noise_level=numpy.percentile(CT,noisecutoff)
    thresh=max(noise_level*threshfactor,absthresh)
    beats={}
    index_crosses=[]
    for i in range(len(CT)-1):
        if CT[i+1]>=thresh and CT[i]<thresh:
            index_crosses.append(i+1)
    
    if len(index_crosses)==0:
    
        return beats#pass #no beats
    
    prevJ=0
    #prevRR=0
    for i in index_crosses[:-1]:
        maxR=CT[i]
        #indexR=i
        TS_R=TS[i]
        for j in range(i,len(CT),1):
            if CT[j]<thresh:
                break
            if j>=index_crosses[-1]:
                break
            elif CT[j]>maxR:
                maxR=CT[j]
        #        indexR=j
        if j-prevJ>=minRR:
            #beats[TS_R]={'Rvolt':maxR,'indexR':indexR,'RR':TS[j]-TS[prevJ], 'CV': ((j-prevJ)-prevRR)/(((j-prevJ)+prevRR)/2),'thresh':thresh}
            beats[TS_R]={'RR':TS[j]-TS[prevJ]}
            if prevJ==0: 
                beats[TS_R]['first']=True
            else: beats[TS_R]['first']=False
            prevJ=j
            #prevRR=TS[j]-TS[prevJ]
    
    return beats
#%%
def basic_breathcall(CT,ts,base,thresh): #needs debugging for collisions between breaths
    #
    #note - the anticipated signal input duration is ~10sec with sliding repeat performed every 0.1 sec
    #performance can be improved with mdest loss of precision by downsampling input signal (minimum~50Hz)
    #find thresh crossing
    ##
    logic_AT=[1 if i>thresh else 0 for i in CT]
    logic_BB=[1 if i<base else 0 for i in CT]
    logic_Ins=[logic_AT[i+1]-logic_AT[i] for i in range(len(CT)-1)]
    index_i=[i+1 for i in range(len(logic_Ins)) if logic_Ins[i]==1] #index of inspiration threshold crosses
    BC={}
    ##
    if len(index_i)==0: return BC
    ##
    BC_list=[]
    ##
    if sum(logic_BB)==0: return BC
    ##
    index_b=[i for i in range(len(logic_BB)) if logic_BB[i]==1] #index of below baseline values
    #check for closest baseline cross preceding, skip if prior baseline belongs to prev crossing
    #
    FIRST_BREATH_FOUND=False
    for i in range(len(index_i)):
        validbreath=False
        # skip until first base crossing is available
        if index_i[i]<index_b[0]: continue #no baseline crossing found before current thresh crossing
        if FIRST_BREATH_FOUND==False:
            #scan back until baseline cross (CT[index_b[0]])
            for j in range(index_i[i],index_b[0],-1):
                if CT[j]>base:
                    continue
                else:
                    FIRST_BREATH_FOUND=True
                    validbreath=True
                    break
        else:
            for j in range(index_i[i],index_i[i-1],-1): #skip if prior baseline belongs to prev crossing
                if j<=index_i[i-1]+1: break #skip segment - belongs to prior breath exp phase
                if CT[j]>base:
                    pass
                else:
                    validbreath=True
                    break
        if validbreath==False: continue
        
        BC[ts[j]]={'TS-I':ts[j]}
        BC_list.append(ts[j])
        #
        #check for closest baseline cross following
        if index_i[i]!=index_i[-1]: # check if special case dealing with last breath
            for k in range(index_i[i],index_i[i+1],1):
                if CT[k]>=base: #consider if should be >=
                    BC[ts[j]]['TS-E']=ts[k]
                else: break
        else:
            for k in range(index_i[i],len(CT),1):
                if CT[k]>=base: #consider if should be >=
                    BC[ts[j]]['TS-E']=ts[k]
                else: break
        BC[ts[j]]['j']=j
        BC[ts[j]]['k']=k
        #fill in BC measures TI PIF iTV
        BC[ts[j]]['TI']=ts[k]-ts[j]
        #BC[ts[j]]['PIF']=max(CT[j:k])
        BC[ts[j]]['iTV']=sum(CT[j:k])-len(CT[j:k])*base #updated to reflect volume if baseline !=0
    #fill in BC measures TE PEF eTV
    for i in range(len(BC_list)-1):
        BC[BC_list[i]]['TE']=BC[BC_list[i+1]]['TS-I']-BC[BC_list[i]]['TS-E']
        #BC[ts[BC_list[i]]]['PEF']=min(CT[BC[BC_list[i]]['k']:BC[BC_list[i+1]]['j']])
        BC[BC_list[i]]['eTV']=(sum(CT[BC[BC_list[i]]['k']:BC[BC_list[i+1]]['j']])*-1)+len(CT[BC[BC_list[i]]['k']:BC[BC_list[i+1]]['j']])*base #updated to reflect volume if baseline !=0
        BC[BC_list[i]]['DVTV']=abs(BC[BC_list[i]]['iTV']-BC[BC_list[i]]['eTV'])/BC[BC_list[i]]['iTV']
    ##
    return BC
#%%

def basicFilt(CT,sampleHz,f0,Q):
    b,a=signal.iirnotch(f0/(sampleHz/2),Q)
    
    notched=signal.lfilter(b,a,CT)
    #notched=CT
    b,a=signal.butter(1,1/(sampleHz/2),btype='highpass')
    buttered=signal.lfilter(b,a,notched)
    return buttered


def notchFilt(CT,sampleHz,f0,Q):
    b,a=signal.iirnotch(f0/(sampleHz/2),Q)
    
    notched=signal.lfilter(b,a,CT)
    return notched


def butterFilt(CT,sampleHz):
    b,a=signal.butter(1,1/(sampleHz/2),btype='highpass')
    buttered=signal.lfilter(b,a,CT)
    return buttered        

def processStatus(status,device,serial_connection,ADC):
    device.setDIOState(0,0)
    device.setDIOState(1,0)
    device.setDIOState(2,0)
    device.setDIOState(3,0)
    now=datetime.now()
    print(status)
    serialtext=''
    
    if status['standby']==1:
        serialtext='<S,0,0>'
    
    if status['startup']==1 and status['startup_ready']<1:
        serialtext='<U,0,0>'
        try:
            ser.write(serialtext.encode())
            print('{} - sent'.format(serialtext))
            status['startup_ready']=1
        except:
            print('unable to transmit "{}"via serial io'.format(serialtext))
            status['startup_ready']=1
        return status
    
    if status['streaming']==1:
        device.setDIOState(0,1)
        
    if status['ready to save']==1:
        pass
    if status['calibration']==1:
        device.setDIOState(1,1)
        serialtext='<C,{},0>'.format(ADC['Duration_Cal'])
        status['pulse']['calibration']['state']=1
        status['pulse']['calibration']['start']=now
    if status['challenge air']==1:
        device.setDIOState(3,1)
        serialtext='<R,{},0>'.format(ADC['Position_RA'])
        status['pulse']['challenge air']['state']=1
        status['pulse']['challenge air']['start']=now
    if status['challenge gas']==1:
        device.setDIOState(2,1)
        serialtext='<A,{},{}>'.format(ADC['Position_Gas'],ADC['Duration_Prefill'])
        status['pulse']['challenge gas']['state']=1
        status['pulse']['challenge gas']['start']=now
    else:
        pass
    
    if serialtext!='':
        
        try:
            ser.write(serialtext.encode())
            print('{} - sent'.format(serialtext))
        except:
            print('unable to transmit "{}"via serial io'.format(serialtext))
    
    return status


#%% define classes
class adjustbutton(pygame.sprite.Sprite):
    def __init__(self,color,width,height,points,TL=(0,0)):
        super().__init__() #not sure what this does - probably gathers sprite class initialization data...
        
        self.TL=TL
        self.image=pygame.Surface([width,height])
        self.image.fill(WHITE)
        pygame.draw.polygon(self.image,color,points)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
        
class labeledbutton(pygame.sprite.Sprite):
    def __init__(self,color1,color2,width,height,label,TL=(0,0)):
        super().__init__() #not sure what this does - probably gathers sprite class initialization data...

        self.width=width
        self.height=height
        self.TL=TL
        self.label=label
        self.color1=color1
        self.color2=color2
        
        buttonlabel = font.render(label,True,color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(width/2),int(height/2))
        
        self.image=pygame.Surface([width,height])
        self.image.fill(color1)
        pygame.draw.rect(self.image,color1,(0,0,width,height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
    
    def relocate(self,x,y):
        self.TL=(x,y)

        buttonlabel = font.render(self.label,True,self.color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(self.width/2),int(self.height/2))
        
        self.image=pygame.Surface([self.width,self.height])
        self.image.fill(self.color1)
        pygame.draw.rect(self.image,self.color1,(0,0,self.width,self.height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
    
    def update(self,color1,color2,label):
        self.color1=color1
        self.color2=color2
        self.label=label
        
        buttonlabel = font.render(label,True,color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(self.width/2),int(self.height/2))
        self.image=pygame.Surface([self.width,self.height])
        self.image.fill(color1)
        pygame.draw.rect(self.image,color1,(0,0,self.width,self.height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])

    def update_left(self,color1,color2,label):
            self.color1=color1
            self.color2=color2
            self.label=label
            
            buttonlabel = font.render(label,True,color2)
            buttonlabel_rect= buttonlabel.get_rect()
            buttonlabel_rect.midleft=(10,int(self.height/2))
            self.image=pygame.Surface([self.width,self.height])
            self.image.fill(color1)
            pygame.draw.rect(self.image,color1,(0,0,self.width,self.height))
            self.image.blit(buttonlabel,buttonlabel_rect)
            self.rect = self.image.get_rect()
            self.rect.x,self.rect.y=(self.TL[0],self.TL[1])

#%% set-up class for streaming data
## try streaming arduino data
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
##
#%% define constants/buffers/status-tags/customization-parameters
Mode_dict={0:'startup',
           1:'standby',
           2:'Signal Preview 1',
           3:'calibration',
           4:'Signal Preview 2',
           5:'Habituation',
           6:'Baseline',
           7:'Challenge',
           8:'Finished'}
Mode_timing={0:-1,
             1:-1,
             2:-1,
             3:60*2,
             4:-1,
             5:30*60,
             6:10*60,
             7:-1,
             8:-1}

savable_modes=['calibration','Habituation','Baseline','Challenge']


Current_Mode=0 # start in standby mode
prev_Mode=-1


## buffers
breath_list=[]
breath_dict={}

HR_list=[]
HR_dict={}

quality_seg_list=[]
quality_seg_dict={}

serial_list=['1','2','3','4','5','6','7','8','9']

## constants
ScreenSize=(1280,960)
FPS = 60 # frames per second setting
fpsClock = pygame.time.Clock()

BACKGROUND_COLOR = (200,200,200)
GRAPH_BACKGROUND = (255,255,255)
BUTTON_NORMAL_COLOR = (100,100,100)
BUTTON_TOGGLED_COLOR = (50,150,50)
BUTTON_URGENT_COLOR = (200,0,0)
BUTTON_WARNING_COLOR = (200,200,0)

BLACK=(0,0,0)
WHITE=(255,255,255)
LGREY=(200,200,200)
DGREY=(50,50,50)
RED=(200,0,0)
ORANGE=(200,50,0)
YELLOW=(200,200,0)
GREEN=(50,150,50)
BLUE=(0,0,255)
VIOLET=(200,0,255)

g1_TL=(100,25)
g1_xySize=(250,250)
g1_x_minmax=[0,500]
g1_y_minmax=[-2,2]

g2_TL=(100,325)
g2_xySize=(250,250)
g2_x_minmax=[0,500]
g2_y_minmax=[-1,5]


g3_TL=(100,625)
g3_xySize=(250,250)
g3_x_minmax=[0,500]
g3_y_minmax=[-3,3]

#sensor value displays
BT_TL=(450,50)
CT_TL=(450,100)
RH_TL=(450,150)
O2_TL=(450,200)
CO2_TL=(450,250)
#derived param displays
BPM_TL=(450,300)

TV_TL=(450,350)
HR_TL=(450,400)

baseBPM_TL=(450,500)

baseTV_TL=(450,550)
baseHR_TL=(450,600)
qual_bouts_TL=(450,750)
qual_dur_TL=(450,800)
sincelastbreath_TL=(450,700)

SLB_Value_TL=(900,700)
qual_test_TL=(700,750)

#sizes
#sensor value displays
BT_xySize=(200,50)
CT_xySize=(200,50)
RH_xySize=(200,50)
O2_xySize=(200,50)
CO2_xySize=(200,50)
#derived param displays
BPM_xySize=(200,50)
#PIF_xySize=(200,50)
TV_xySize=(200,50)
HR_xySize=(200,50)
baseBPM_xySize=(200,50)
#basePIF_xySize=(200,50)
baseTV_xySize=(200,50)
baseHR_xySize=(200,50)
sincelastbreath_xySize=(200,50)
qual_bouts_xySize=(200,50)
qual_dur_xySize=(200,50)
qual_test_xySize=(200,50)

increment=0.1
inc_TL=(450,50)

cur_time=datetime.now()

#$$$$ Scoreboard
SLB_Trigger_Setter_xySize=(200,50)
Challenge_Counter_xySize=(200,50)
CurrentChallengeCO2_Timer_xySize=(200,50)
CurrentChallengeRecovery_Timer_xySize=(200,50)


Position_RA_xySize=(200,25)
Position_Gas_xySize=(200,25)
Duration_Cal_xySize=(200,25)
Duration_Prefill_xySize=(200,25)

Serial_Abort_xySize=(100,50)
Serial_ShutDown_xySize=(100,50)
finish_startup_xySize=(200,50)
SerialOutTester_xySize=(200,50)

SLB_Trigger_Setter_TL=(700,50)
Challenge_Counter_TL=(700,100)
CurrentChallengeCO2_Timer_TL=(700,150)
CurrentChallengeRecovery_Timer_TL=(700,200)

Arduino_Function_Constants={
    'Position_RA':0,
    'Position_Gas':3,
    'Duration_Cal':30,
    'Duration_Prefill':60
    }

Position_RA_TL=(700,250)
Position_Gas_TL=(700,275)
Duration_Cal_TL=(700,300)
Duration_Prefill_TL=(700,325)


Serial_Abort_TL=(700,350)
Serial_ShutDown_TL=(800,350)
finish_startup_TL=(700,400)

SerialOutTester_TL=(700,450)

SO1_xySize=(300,25)
SO2_xySize=(300,25)
SO3_xySize=(300,25)
SO4_xySize=(300,25)
SO5_xySize=(300,25)
SO6_xySize=(300,25)
SO7_xySize=(300,25)
SO8_xySize=(300,25)
SO9_xySize=(300,25)

SO1_TL=(650,500)
SO2_TL=(650,525)
SO3_TL=(650,550)
SO4_TL=(650,575)
SO5_TL=(650,600)
SO6_TL=(650,625)
SO7_TL=(650,650)
SO8_TL=(650,675)
SO9_TL=(650,700)


#$$$$

baseline_flow_TL=(40,170)
thresh_flow_TL=(40,100)
thresh2_flow_TL=450,200
baseline_vol_TL=(40,470)
thresh_vol_TL=(40,400)
baseline_ecg_TL=(40,770)
noise_ecg_TL=(450,630)
absthresh_ecg_TL=(40,700)
thresh_ecg1_TL=(450,700)
thresh_ecg2_TL=(450,770)

INVERT_FLOW_TL=(950,300)
PLETHFILT_TL=(950,325)

ECGFILT_TL=(950,360)
INVERT_ECG_TL=(950,385)#

HR_recovery_thresh_TL=(950,420)
BPM_recovery_thresh_TL=(950,450)
avgBPM_thresh_TL=(950,490)
cvTT_thresh_TL=(950,520)
avgHR_thresh_TL=(950,550)
avgRR_thresh_TL=(950,580)
cvRR_thresh_TL=(950,610)
BSD_thresh_TL=(950,640)
DVTV_thresh_TL=(950,670)
QB_duration_TL=(950,700)

SLB_trigger_TL=(950,750)
minimum_resus_time_TL=(950,780)
CALL_DEATH_trigger_TL=(950,810)
               

## buffers and status tags
# variables to hold error reports - need to make and move this to a log file eventually

PreFilt_data1=[0 for i in range(1000)]
#PreFilt_data2=[0 for i in range(1000)]
PreFilt_data3=[0 for i in range(20000)]
PreFilt_data3_ds=[0 for i in range(1000)]

data1=[0 for i in range(500)]
#data2=[0 for i in range(500)]
data3=[0 for i in range(10000)]
data3_ds=[0 for i in range(500)]

RunningBreaths=[]
RunningBeats=[]

errors = 0
errlist=[]
missed = 0
curdata={}

pleth_filt_state=0
ecg_filt_state=1

baseHR=1 #move this to the constants/buffer section
avgRR=999
OUTPUTFILE=None
running=True
READYTOSAVE=False
RESCUE_STATUS=False
slb_COLOR=BLACK
slb_COLOR2=WHITE
REL_TIMER=0
QB_TIMER=0
QB_Counter=0
QB_duration=0
SinceLastBreath=0
SLB_Trigger=5
CALL_DEATH_trigger=10*60
minimum_resus_time=5*60
current_recovery=300
resus_START=0-minimum_resus_time

#$$$$ scoreboard
value_Challenge_Counter=0
value_CurrentChallengeCO2_Timer=0
value_CurrentChallengeCO2_Start=datetime.now()
value_CurrentChallengeRecovery_Timer=0
value_CurrentChallengeRecovery_Start=datetime.now()


#$$$$

INVERT_FLOW=0
INVERT_ECG=0
pulse_duration=3 #duration of high voltage pulse to microcontroller

## tuning and customization parameters
baseline_flow=0
thresh_flow=0.25
thresh2_flow=0.5
filt_flow='None'

baseline_vol=0
thresh_vol=0.25
filt_vol='None'

baseline_ecg=0
absthresh_ecg=0.3
thresh_ecg1=4.0
thresh_ecg2=2.0
noise_ecg=75

HR_recovery_thresh=63
BPM_recovery_thresh=50
QB_minimum_duration=5
stream_lag=0
prev_qual_test=0
CURRENT_STATUS="Not Ready"
OLD_STATUS="Not Ready"

filt_crit_Dict={
            'avgBPM':250,
            'cvTT':0.5,
            'avgHR':700,
            'avgRR':999,
            'cvRR':0.5,
            'BSD':0.25,
            'DVTV':0.75
            }

#%%
now=datetime.now()
cur_STATUS_Dict={'standby':0,'startup':0,'streaming':0,'ready to save':0,'calibration':0,'challenge air':0,'challenge gas':0,
                 'pulse':{
                         'calibration':{'state':0,'start':now,'pin':1},
                         'challenge air':{'state':0,'start':now,'pin':3},
                         'challenge gas':{'state':0,'start':now,'pin':2}
                         },
                 'startup_ready':0
                 }
old_STATUS_Dict={'standby':0,'startup':0,'streaming':0,'ready to save':0,'calibration':0,'challenge air':0,'challenge gas':0,
                 'pulse':{
                         'calibration':{'state':0,'start':now,'pin':1},
                         'challenge air':{'state':0,'start':now,'pin':3},
                         'challenge gas':{'state':0,'start':now,'pin':2}
                         },
                 'startup_ready':0
                 }

##
#%% setup display
pygame.init()
font=pygame.font.SysFont('lucidaconsole',18)
DISPLAYSURF = pygame.display.set_mode(ScreenSize)
pygame.display.set_caption('Plethysmography Command Center')
#%%
DISPLAYSURF.fill(BACKGROUND_COLOR)
## prepare sprites
control_sizes={'vertical':{'inc':(20,10),'dec':(20,10),'reset':(20,20),'float':(95,20)}}
control_offset={'verticalA':{'inc':(-30,-10),'dec':(-30,40),'reset':(-30,0),'float':(-95,20)},
                'verticalB':{'inc':(-30,-10),'dec':(-30,40),'reset':(-30,0),'float':(-35,20)},
                'verticalC':{'inc':(-30,200),'dec':(-30,250),'reset':(-30,210),'float':(-95,230)},
                'verticalD':{'inc':(-30,200),'dec':(-30,250),'reset':(-30,210),'float':(-35,230)},
                'horizontalA':{'inc':(-10,10),'dec':(40,10),'reset':(0,10),'float':(20,10)}}

#g1 controls
g1_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g1_TL[0]+control_offset['verticalA']['inc'][0],
                          g1_TL[1]+control_offset['verticalA']['inc'][1]))
g1_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g1_TL[0]+control_offset['verticalA']['dec'][0],
                          g1_TL[1]+control_offset['verticalA']['dec'][1]))
g1_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g1_TL[0]+control_offset['verticalA']['reset'][0],
                                 g1_TL[1]+control_offset['verticalA']['reset'][1]))
g1_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g1_y_minmax[1]),(g1_TL[0]+control_offset['verticalA']['float'][0],
                                 g1_TL[1]+control_offset['verticalA']['float'][1]))
g1_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g1_TL[0]+control_offset['verticalC']['inc'][0],
                          g1_TL[1]+control_offset['verticalC']['inc'][1]))
g1_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g1_TL[0]+control_offset['verticalC']['dec'][0],
                          g1_TL[1]+control_offset['verticalC']['dec'][1]))
g1_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g1_TL[0]+control_offset['verticalC']['reset'][0],
                                 g1_TL[1]+control_offset['verticalC']['reset'][1]))
g1_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g1_y_minmax[0]),(g1_TL[0]+control_offset['verticalC']['float'][0],
                                 g1_TL[1]+control_offset['verticalC']['float'][1]))

#g2 controls
#
g2_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g2_TL[0]+control_offset['verticalA']['inc'][0],
                          g2_TL[1]+control_offset['verticalA']['inc'][1]))
g2_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g2_TL[0]+control_offset['verticalA']['dec'][0],
                          g2_TL[1]+control_offset['verticalA']['dec'][1]))
g2_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g2_TL[0]+control_offset['verticalA']['reset'][0],
                                 g2_TL[1]+control_offset['verticalA']['reset'][1]))
g2_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g2_y_minmax[1]),(g2_TL[0]+control_offset['verticalA']['float'][0],
                                 g2_TL[1]+control_offset['verticalA']['float'][1]))
g2_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g2_TL[0]+control_offset['verticalC']['inc'][0],
                          g2_TL[1]+control_offset['verticalC']['inc'][1]))

g2_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g2_TL[0]+control_offset['verticalC']['dec'][0],
                          g2_TL[1]+control_offset['verticalC']['dec'][1]))
g2_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g2_TL[0]+control_offset['verticalC']['reset'][0],
                                 g2_TL[1]+control_offset['verticalC']['reset'][1]))
g2_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g2_y_minmax[0]),(g2_TL[0]+control_offset['verticalC']['float'][0],
                                 g2_TL[1]+control_offset['verticalC']['float'][1]))

#g3 controls
g3_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g3_TL[0]+control_offset['verticalA']['inc'][0],
                          g3_TL[1]+control_offset['verticalA']['inc'][1]))
g3_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g3_TL[0]+control_offset['verticalA']['dec'][0],
                          g3_TL[1]+control_offset['verticalA']['dec'][1]))
g3_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g3_TL[0]+control_offset['verticalA']['reset'][0],
                                 g3_TL[1]+control_offset['verticalA']['reset'][1]))
g3_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g3_y_minmax[1]),(g3_TL[0]+control_offset['verticalA']['float'][0],
                                 g3_TL[1]+control_offset['verticalA']['float'][1]))
g3_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g3_TL[0]+control_offset['verticalC']['inc'][0],
                          g3_TL[1]+control_offset['verticalC']['inc'][1]))

g3_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g3_TL[0]+control_offset['verticalC']['dec'][0],
                          g3_TL[1]+control_offset['verticalC']['dec'][1]))
g3_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g3_TL[0]+control_offset['verticalC']['reset'][0],
                                 g3_TL[1]+control_offset['verticalC']['reset'][1]))
g3_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g3_y_minmax[0]),(g3_TL[0]+control_offset['verticalC']['float'][0],
                                 g3_TL[1]+control_offset['verticalC']['float'][1]))

#increment adjuster
inc_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (inc_TL[0]+control_offset['verticalA']['inc'][0],
                          inc_TL[1]+control_offset['verticalA']['inc'][1]))
inc_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (inc_TL[0]+control_offset['verticalA']['dec'][0],
                          inc_TL[1]+control_offset['verticalA']['dec'][1]))
inc_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(inc_TL[0]+control_offset['verticalA']['reset'][0],
                                 inc_TL[1]+control_offset['verticalA']['reset'][1]))
inc_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(increment),(inc_TL[0]+control_offset['verticalA']['float'][0],
                                 inc_TL[1]+control_offset['verticalA']['float'][1]))

#baseline flow adjuster
baseline_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_flow_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_flow_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_flow_reset=labeledbutton(BLUE,WHITE,
                                  control_sizes['vertical']['reset'][0],
                                  control_sizes['vertical']['reset'][1],
                                  'R',
                                  (baseline_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                   baseline_flow_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_flow),(baseline_flow_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_flow_TL[1]+control_offset['verticalB']['float'][1]))

#thresh flow adjuster
thresh_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_flow_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_flow_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_flow_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_flow_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh_flow),(thresh_flow_TL[0]+control_offset['verticalB']['float'][0],
                                 thresh_flow_TL[1]+control_offset['verticalB']['float'][1]))

#thresh2 flow adjuster
thresh2_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh2_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh2_flow_TL[1]+control_offset['verticalA']['inc'][1]))
thresh2_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh2_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh2_flow_TL[1]+control_offset['verticalA']['dec'][1]))
thresh2_flow_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh2_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh2_flow_TL[1]+control_offset['verticalA']['reset'][1]))
thresh2_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh2_flow),(thresh2_flow_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh2_flow_TL[1]+control_offset['verticalA']['float'][1]))

#baseline vol adjuster
baseline_vol_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_vol_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_vol_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_vol_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_vol_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_vol_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_vol_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',
                            (baseline_vol_TL[0]+control_offset['verticalA']['reset'][0],
                             baseline_vol_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_vol_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_vol),(baseline_vol_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_vol_TL[1]+control_offset['verticalB']['float'][1]))

#thresh flow adjuster
thresh_vol_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_vol_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_vol_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_vol_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_vol_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_vol_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_vol_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_vol_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_vol_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_vol_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh_vol),(thresh_vol_TL[0]+control_offset['verticalB']['float'][0],
                                 thresh_vol_TL[1]+control_offset['verticalB']['float'][1]))

#baseline ecg adjuster
baseline_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(baseline_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 baseline_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_ecg),(baseline_ecg_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_ecg_TL[1]+control_offset['verticalB']['float'][1]))

#noise ecg adjuster
noise_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (noise_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          noise_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
noise_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (noise_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          noise_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
noise_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(noise_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 noise_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
noise_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.1F}'.format(noise_ecg),(noise_ecg_TL[0]+control_offset['verticalA']['float'][0],
                                 noise_ecg_TL[1]+control_offset['verticalA']['float'][1]))

#absthresh ecg adjuster
absthresh_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (absthresh_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          absthresh_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
absthresh_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (absthresh_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          absthresh_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
absthresh_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(absthresh_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 absthresh_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
absthresh_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(absthresh_ecg),(absthresh_ecg_TL[0]+control_offset['verticalB']['float'][0],
                                 absthresh_ecg_TL[1]+control_offset['verticalB']['float'][1]))


#thresh ecg1 adjuster
thresh_ecg1_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_ecg1_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_ecg1_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_ecg1_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_ecg1_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_ecg1_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_ecg1_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_ecg1_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_ecg1_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_ecg1_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.2F}'.format(thresh_ecg1),(thresh_ecg1_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh_ecg1_TL[1]+control_offset['verticalA']['float'][1]))

thresh_ecg2_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_ecg2_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_ecg2_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_ecg2_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_ecg2_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_ecg2_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_ecg2_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_ecg2_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_ecg2_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_ecg2_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.2F}'.format(thresh_ecg2),(thresh_ecg2_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh_ecg2_TL[1]+control_offset['verticalA']['float'][1]))
box_stream_lag=labeledbutton(BACKGROUND_COLOR,RED,
                             150,25,
                             '{:#.3F}'.format(stream_lag),
                                 (ScreenSize[0]-150,ScreenSize[1]-25))
PLETHFILT_TOGGLE=labeledbutton(RED,BLACK,300,25,'FILTER PLETH',PLETHFILT_TL)
ECGFILT_TOGGLE=labeledbutton(RED,BLACK,300,25,'FILTER ECG',ECGFILT_TL)
INVERT_FLOW_TOGGLE=labeledbutton(WHITE,BLACK,300,25,'Invert Flow:{}'.format(INVERT_FLOW),INVERT_FLOW_TL)
INVERT_ECG_TOGGLE=labeledbutton(WHITE,BLACK,300,25,'Invert ECG:{}'.format(INVERT_ECG),INVERT_ECG_TL)

box_minimum_resus_time=labeledbutton(WHITE,BLACK,300,25,'RECOVERY:{:d}/{:d})'.format(int(current_recovery),int(minimum_resus_time)),minimum_resus_time_TL)

box_SLB_trigger=labeledbutton(YELLOW,BLACK,300,25,'SLB: {:#.2F} sec'.format(SLB_Trigger),SLB_trigger_TL)
box_CALL_DEATH_trigger=labeledbutton(YELLOW,BLACK,300,25,'CALL DEATH: {:#.2F} min'.format(CALL_DEATH_trigger/60),CALL_DEATH_trigger_TL)
box_HR_recovery_thresh=labeledbutton(YELLOW,BLACK,300,25,'HR recover: *NA* %',HR_recovery_thresh_TL)
box_BPM_recovery_thresh=labeledbutton(YELLOW,BLACK,300,25,'BPM recover: *NA* %',BPM_recovery_thresh_TL)
box_avgBPM_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg BPM: *NA* bpm',avgBPM_thresh_TL)
box_cvTT_thresh=labeledbutton(YELLOW,BLACK,300,25,'CV TT: *NA* ratio',cvTT_thresh_TL)
box_avgHR_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg HR: *NA* bpm',avgHR_thresh_TL)
box_avgRR_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg RR: *NA* sec',avgRR_thresh_TL)
box_cvRR_thresh=labeledbutton(YELLOW,BLACK,300,25,'CV RR: *NA* ratio',cvRR_thresh_TL)
box_BSD_thresh=labeledbutton(YELLOW,BLACK,300,25,'Base Drift: *NA* V',BSD_thresh_TL)
box_DVTV_thresh=labeledbutton(YELLOW,BLACK,300,25,'DVTV: *NA* ratio',DVTV_thresh_TL)
box_QB_duration=labeledbutton(YELLOW,BLACK,300,25,'min QB: *NA* sec',QB_duration_TL)

box_BT=labeledbutton(WHITE,BLUE,BT_xySize[0],BT_xySize[1],'BT:*NA* C',BT_TL)
box_CT=labeledbutton(WHITE,BLUE,CT_xySize[0],CT_xySize[1],'CT:*NA* C',CT_TL)
box_RH=labeledbutton(WHITE,BLUE,RH_xySize[0],RH_xySize[1],'RH:*NA* %',RH_TL)
box_O2=labeledbutton(WHITE,BLUE,O2_xySize[0],O2_xySize[1],'O2:*NA** %',O2_TL)
box_CO2=labeledbutton(WHITE,BLUE,CO2_xySize[0],CO2_xySize[1],'CO2: *NA* %',CO2_TL)
#derived param displays
box_BPM=labeledbutton(BLUE,WHITE,BPM_xySize[0],BPM_xySize[1],'BPM:*NA*',BPM_TL)

box_TV=labeledbutton(BLUE,WHITE,TV_xySize[0],TV_xySize[1],'TV:*NA*',TV_TL)
box_HR=labeledbutton(BLUE,WHITE,HR_xySize[0],HR_xySize[1],'HR:*NA*',HR_TL)
box_baseBPM=labeledbutton(GREEN,BLACK,baseBPM_xySize[0],baseBPM_xySize[1],'base BPM:*NA*',baseBPM_TL)

box_baseTV=labeledbutton(GREEN,BLACK,baseTV_xySize[0],baseTV_xySize[1],'base TV:*NA*',baseTV_TL)
box_baseHR=labeledbutton(GREEN,BLACK,baseHR_xySize[0],baseHR_xySize[1],'base HR:*NA*',baseHR_TL)
box_sincelastbreath=labeledbutton(WHITE,GREEN,sincelastbreath_xySize[0],sincelastbreath_xySize[1],
                                  'SLB: *NA* sec',sincelastbreath_TL)
box_qual_bouts=labeledbutton(YELLOW,BLACK,qual_bouts_xySize[0],qual_bouts_xySize[1],'bouts:*NA*',qual_bouts_TL)
box_qual_dur=labeledbutton(YELLOW,BLACK,qual_dur_xySize[0],qual_dur_xySize[1],'duration:*NA*',qual_dur_TL)
box_qual_test=labeledbutton(WHITE,BLACK,qual_test_xySize[0],qual_test_xySize[1],'',qual_test_TL)

graph1=labeledbutton(WHITE,WHITE,g1_xySize[0],g1_xySize[1],'',g1_TL)
graph2=labeledbutton(WHITE,WHITE,g2_xySize[0],g2_xySize[1],'',g2_TL)
graph3=labeledbutton(WHITE,WHITE,g3_xySize[0],g3_xySize[1],'',g3_TL)

FLOW_LABEL=labeledbutton(WHITE,BLACK,125,25,'Flow',g1_TL)
VOL_LABEL=labeledbutton(WHITE,BLACK,125,25,'Volume',g2_TL)
ECG_LABEL=labeledbutton(WHITE,BLACK,125,25,'ECG',g3_TL)

box_MODE=labeledbutton(BLACK,WHITE,250,25,Mode_dict[Current_Mode],(ScreenSize[0]-275,0))
box_NEXT=labeledbutton(GREEN,WHITE,25,25,'>>',(ScreenSize[0]-25,0))
box_duration=labeledbutton(BLACK,RED,250,25,'*NA* sec',(0,ScreenSize[1]-25))

#$$$$ scoreboard

SLB_Trigger_Setter=labeledbutton(WHITE,BLACK,SLB_Trigger_Setter_xySize[0],SLB_Trigger_Setter_xySize[1],
                                 'SLB_Trigger: {}sec'.format(SLB_Trigger),SLB_Trigger_Setter_TL)
Challenge_Counter=labeledbutton(WHITE,BLACK,Challenge_Counter_xySize[0],Challenge_Counter_xySize[1],
                                'Challenge #: __', Challenge_Counter_TL)
CurrentChallengeCO2_Timer=labeledbutton(WHITE,BLACK,CurrentChallengeCO2_Timer_xySize[0],CurrentChallengeCO2_Timer_xySize[1],
                                           'CO2 Time: ___sec',CurrentChallengeCO2_Timer_TL)
CurrentChallengeRecovery_Timer=labeledbutton(WHITE,BLACK,CurrentChallengeRecovery_Timer_xySize[0],CurrentChallengeRecovery_Timer_xySize[1],
                                                'Rec Time: ___sec',CurrentChallengeRecovery_Timer_TL)

Position_RA=labeledbutton(BLACK,WHITE,Position_RA_xySize[0],Position_RA_xySize[1],
                          'RA position: {}'.format(Arduino_Function_Constants['Position_RA']),
                          Position_RA_TL)
Position_Gas=labeledbutton(BLACK,WHITE,Position_Gas_xySize[0],Position_Gas_xySize[1],
                                        'Gas position: {}'.format(Arduino_Function_Constants['Position_Gas']),
                                        Position_Gas_TL)
Duration_Cal=labeledbutton(BLACK,WHITE,Duration_Cal_xySize[0],Duration_Cal_xySize[1],
                           'Cal dur: {}'.format(Arduino_Function_Constants['Duration_Cal']),
                           Duration_Cal_TL)
Duration_Prefill=labeledbutton(BLACK,WHITE,Duration_Cal_xySize[0],Duration_Cal_xySize[1],
                               'Prefill dur: {}'.format(Arduino_Function_Constants['Duration_Prefill']),
                               Duration_Prefill_TL)

Serial_Abort=labeledbutton(RED,BLACK,Serial_Abort_xySize[0],Serial_Abort_xySize[1],
                           'ABORT!',Serial_Abort_TL)
Serial_ShutDown=labeledbutton(BLACK,WHITE,Serial_ShutDown_xySize[0],Serial_ShutDown_xySize[1],
                              'ShutDown',Serial_ShutDown_TL)

finish_startup=labeledbutton(BLACK,WHITE,finish_startup_xySize[0],finish_startup_xySize[1],
                             '',finish_startup_TL)

SerialOutTester=labeledbutton(WHITE,BLACK,SerialOutTester_xySize[0],SerialOutTester_xySize[1],
                              'Serial Out',SerialOutTester_TL)

SO1=labeledbutton(DGREY,WHITE,SO1_xySize[0],SO1_xySize[1],
                  ':',SO1_TL)
SO2=labeledbutton(DGREY,WHITE,SO2_xySize[0],SO2_xySize[1],
                  ':',SO2_TL)
SO3=labeledbutton(DGREY,WHITE,SO3_xySize[0],SO3_xySize[1],
                  ':',SO3_TL)
SO4=labeledbutton(DGREY,WHITE,SO4_xySize[0],SO4_xySize[1],
                  ':',SO4_TL)
SO5=labeledbutton(DGREY,WHITE,SO5_xySize[0],SO5_xySize[1],
                  ':',SO5_TL)
SO6=labeledbutton(DGREY,WHITE,SO6_xySize[0],SO6_xySize[1],
                  ':',SO6_TL)
SO7=labeledbutton(DGREY,WHITE,SO7_xySize[0],SO7_xySize[1],
                  ':',SO7_TL)
SO8=labeledbutton(DGREY,WHITE,SO8_xySize[0],SO8_xySize[1],
                  ':',SO8_TL)
SO9=labeledbutton(DGREY,WHITE,SO9_xySize[0],SO9_xySize[1],
                  ':',SO9_TL)

#$$$$
                          
box_SAVE=labeledbutton(BLACK,WHITE,500,25,'SAVE',(ScreenSize[0]-650,ScreenSize[1]-25))
box_NOTIFICATION=labeledbutton(DGREY,WHITE,500,25,'NOTIFICATIONS-OFF',(ScreenSize[0]-650,ScreenSize[1]-50))

box_Synch=labeledbutton(RED,WHITE,250,25,'Synch Stream',(ScreenSize[0]-275,25))
box_mode_select={}
box_mode_times={}
for i in Mode_dict:
    box_mode_select[i]=labeledbutton(BLACK,WHITE,300,25,'{}:{:#.2F}'.format(Mode_dict[i],Mode_timing[i]/60),(ScreenSize[0]-325,25*i+50))
    box_mode_times[i]=labeledbutton(VIOLET,WHITE,25,25,'t'.format(Mode_dict[i],Mode_timing[i]),(ScreenSize[0]-25,25*i+50))

#prep sprite list
sprite_list=pygame.sprite.Group()

sprite_list.add(box_MODE)

sprite_list.add(box_Synch)
for i in Mode_dict:
    sprite_list.add(box_mode_select[i])
    sprite_list.add(box_mode_times[i])


sprite_list.add(box_NEXT)
sprite_list.add(box_duration)

sprite_list.add(graph1)
sprite_list.add(graph2)
sprite_list.add(graph3)

sprite_list.add(box_SLB_trigger)
sprite_list.add(box_CALL_DEATH_trigger)
sprite_list.add(box_HR_recovery_thresh)
sprite_list.add(box_BPM_recovery_thresh)
sprite_list.add(box_avgBPM_thresh)
sprite_list.add(box_cvTT_thresh)
sprite_list.add(box_avgHR_thresh)
sprite_list.add(box_avgRR_thresh)
sprite_list.add(box_cvRR_thresh)
sprite_list.add(box_BSD_thresh)
sprite_list.add(box_DVTV_thresh)
sprite_list.add(box_QB_duration)

sprite_list.add(FLOW_LABEL)
sprite_list.add(VOL_LABEL)
sprite_list.add(ECG_LABEL)

sprite_list.add(g1_ymax_inc)
sprite_list.add(g1_ymax_dec)
sprite_list.add(g1_ymax_reset)
sprite_list.add(g1_ymax_float)
sprite_list.add(g1_ymin_inc)
sprite_list.add(g1_ymin_dec)
sprite_list.add(g1_ymin_reset)
sprite_list.add(g1_ymin_float)

sprite_list.add(g2_ymax_inc)
sprite_list.add(g2_ymax_dec)
sprite_list.add(g2_ymax_reset)
sprite_list.add(g2_ymax_float)
sprite_list.add(g2_ymin_inc)
sprite_list.add(g2_ymin_dec)
sprite_list.add(g2_ymin_reset)
sprite_list.add(g2_ymin_float)

sprite_list.add(g3_ymax_inc)
sprite_list.add(g3_ymax_dec)
sprite_list.add(g3_ymax_reset)
sprite_list.add(g3_ymax_float)
sprite_list.add(g3_ymin_inc)
sprite_list.add(g3_ymin_dec)
sprite_list.add(g3_ymin_reset)
sprite_list.add(g3_ymin_float)

sprite_list.add(baseline_flow_inc)
sprite_list.add(baseline_flow_dec)
sprite_list.add(baseline_flow_reset)
sprite_list.add(baseline_flow_float)

sprite_list.add(baseline_vol_inc)
sprite_list.add(baseline_vol_dec)
sprite_list.add(baseline_vol_reset)
sprite_list.add(baseline_vol_float)

sprite_list.add(baseline_ecg_inc)
sprite_list.add(baseline_ecg_dec)
sprite_list.add(baseline_ecg_reset)
sprite_list.add(baseline_ecg_float)

sprite_list.add(noise_ecg_inc)
sprite_list.add(noise_ecg_dec)
sprite_list.add(noise_ecg_reset)
sprite_list.add(noise_ecg_float)

sprite_list.add(thresh_flow_inc)
sprite_list.add(thresh_flow_dec)
sprite_list.add(thresh_flow_reset)
sprite_list.add(thresh_flow_float)

sprite_list.add(thresh2_flow_inc)
sprite_list.add(thresh2_flow_dec)
sprite_list.add(thresh2_flow_reset)
sprite_list.add(thresh2_flow_float)

sprite_list.add(thresh_vol_inc)
sprite_list.add(thresh_vol_dec)
sprite_list.add(thresh_vol_reset)
sprite_list.add(thresh_vol_float)

sprite_list.add(thresh_ecg1_inc)
sprite_list.add(thresh_ecg1_dec)
sprite_list.add(thresh_ecg1_reset)
sprite_list.add(thresh_ecg1_float)

sprite_list.add(absthresh_ecg_inc)
sprite_list.add(absthresh_ecg_dec)
sprite_list.add(absthresh_ecg_reset)
sprite_list.add(absthresh_ecg_float)

sprite_list.add(thresh_ecg2_inc)
sprite_list.add(thresh_ecg2_dec)
sprite_list.add(thresh_ecg2_reset)
sprite_list.add(thresh_ecg2_float)

sprite_list.add(inc_inc)
sprite_list.add(inc_dec)
sprite_list.add(inc_reset)
sprite_list.add(inc_float)

sprite_list.add(ECGFILT_TOGGLE)
sprite_list.add(PLETHFILT_TOGGLE)
sprite_list.add(box_minimum_resus_time)
sprite_list.add(INVERT_FLOW_TOGGLE)
sprite_list.add(INVERT_ECG_TOGGLE)

sprite_list.add(box_BT)
sprite_list.add(box_CT)
sprite_list.add(box_RH)
sprite_list.add(box_O2)
sprite_list.add(box_CO2)
#derived param displays
sprite_list.add(box_BPM)
sprite_list.add(box_TV)
sprite_list.add(box_HR)
sprite_list.add(box_baseBPM)
sprite_list.add(box_baseTV)
sprite_list.add(box_baseHR)
sprite_list.add(box_sincelastbreath)
sprite_list.add(box_qual_bouts)
sprite_list.add(box_qual_dur)
sprite_list.add(box_qual_test)
sprite_list.add(box_SAVE)
sprite_list.add(box_NOTIFICATION)
sprite_list.add(box_stream_lag)

#$$$$ scoreboard
sprite_list.add(Position_RA)
sprite_list.add(Position_Gas)
sprite_list.add(Duration_Cal)
sprite_list.add(Duration_Prefill)
sprite_list.add(SLB_Trigger_Setter)
sprite_list.add(Challenge_Counter)
sprite_list.add(CurrentChallengeCO2_Timer)
sprite_list.add(CurrentChallengeRecovery_Timer)
sprite_list.add(Serial_Abort)
sprite_list.add(Serial_ShutDown)
sprite_list.add(SerialOutTester)
sprite_list.add(SO1)
sprite_list.add(SO2)
sprite_list.add(SO3)
sprite_list.add(SO4)
sprite_list.add(SO5)
sprite_list.add(SO6)
sprite_list.add(SO7)
sprite_list.add(SO8)
sprite_list.add(SO9)

#$$$$

sprite_list.draw(DISPLAYSURF)


#%% setup labjack

#%% prepare labjack interface
CHANNEL_LIST = [0,1,2,3,4,5]
CHANNEL_KEY = ['FLOW','ECG','BT','RH','O2','CO2']
CHANNEL_DICT=dict(zip(CHANNEL_KEY,CHANNEL_LIST))
#NUMBER_CHANNELS is the number of signal channels to scan
NUMBER_CHANNELS = len(CHANNEL_LIST)

# SCAN_FREQUENCY is the scan frequency of stream mode in Hz. (freq per channel * # channels)
SCAN_FREQUENCY = 1000
SAMPLE_FREQUENCY = SCAN_FREQUENCY*NUMBER_CHANNELS
UPDATE_INTERVAL_SEC=0.1
SAMPLES_PER_INTERVAL=int(UPDATE_INTERVAL_SEC*SAMPLE_FREQUENCY)


Requests=0
# At high frequencies ( >5 kHz), the number of samples will be ...#of requests made...
# times 48 (packets per request) times 25 (samples per packet)
d = u6.U6()
# For applying the proper calibration to readings.
d.getCalibrationData()
##

#"""
#2.6.4 - Internal Temperature Sensor [U6 Datasheet]
#The U6 has an internal temperature sensor.  The sensor is physically located near the AIN3 screw-terminal.  It is labeled U17 on the PCB, and can be seen through the gap between the AIN3 terminal and adjacent VS terminal.
#
#The U6 enclosure typically makes a 1 °C difference in the temperature at the internal sensor.  With the enclosure on the temperature at the sensor is typically 3 °C higher than ambient, while with the enclosure off the temperature at the sensor is typically 2 °C higher than ambient.  The calibration constants have an offset of -3 °C, so returned calibrated readings are nominally the same as ambient with the enclosure installed, and 1 °C below ambient with the PCB in free air.
#
#The sensor has a specified accuracy of ±2.1 °C across the entire device operating range of -40 to +85 °C.  Allowing for a slight difference between the sensor temperature and the temperature of the screw-terminals, expect the returned value minus 3 °C to reflect the temperature of the built-in screw-terminals with an accuracy of ±2.5 °C.
#
#With the UD driver, the internal temperature sensor is read by acquiring analog input channel 14 and returns °K.
#
#The internal temperature sensor does not work in stream mode.  It takes too long to settle, thus if you stream it you will typically get totally wrong readings.
#
#Note on thermocouples
#If thermocouples are connected to the CB37, you want to know the temperature of the screw-terminals on the CB37.  The CB37 is typically at the same temperature as ambient air, so use the direct value from a read of AIN14.  Better yet, add a sensor such as the LM34CAZ to an unused analog input on the CB37 to measure the actual temperature of the CB37.
#
#The built-in screw-terminals AIN0-AIN3 on the U6 are typically 3 °C above ambient with the enclosure installed, so when the internal temperature sensor is used for CJC for thermocouples connected to the built-in screw-terminals, it is recommended to add 3 °C to its value as you want the actual temperature of the screw-terminals, not necessarily ambient temperature.
#
#***DON'T READ U6 INTERNAL TEMP THROUGH STREAM, CALL THROUGH getTemperature() -273.15 for C, (x-273.15)*9/5+32 for F***
#***caution regarding use and accuracy***
#"""

#%%
## get initial temperature
CT_value=d.getTemperature()-273.15

print("Configuring U6 stream")
#settling and resolution index may need adjustment - these values are among those suggested by labjack
d.streamConfig(NumChannels=NUMBER_CHANNELS,
               ChannelNumbers=CHANNEL_LIST,
               ChannelOptions=[0 for i in CHANNEL_LIST],
               SettlingFactor=1,
               ResolutionIndex=1,
               ScanFrequency=SCAN_FREQUENCY)

#set packets per datastream call - maybe this is not neccessary - just go with default rate?
d.packetsPerRequest=int(SAMPLES_PER_INTERVAL/25)

d.setDIOState(0,0)
d.setDIOState(1,0)
d.setDIOState(2,0)
d.setDIOState(3,0)



#%% start the labjack datastream 
sdr = StreamDataReader(d)

sdrThread = threading.Thread(target=sdr.readStreamData)
sdrThread.start()


##%% start the arduino stream
arduino_stream=StreamArduino(ser)
ardThread= threading.Thread(target=arduino_stream.readStreamData)
ardThread.start()

##%%

#%%   
#% main loop

"""
1-signal preview mode (adjust baseline and confirm tunable parameters)
**user confirmation for next step
2-calibration mode (receive calibration signals [20x30uL pulses])
**signal to DC out [trigger auto pipette and LED] upon start
**end upon timer (and confirmation from auto pipett upon complete?)
+++creates save file for calibration values
3-habituation mode (wait 30 minutes for habituation)
**preview and capture signals for review later - consider updates to interval
4-baseline mode (capture 10 minutes of signal for baseline)
**preview and capture signals - consider criteria of QUANTITY_OF_QUALITY signal...
.........Q_O_Q : 10 seconds per interval of 'calm breathing', sum of intervals is at least 1 minute
5-challenge mode (ANOXIA challenge until breath cessation, Room Air until recovery...
.........recovery based on >=63% HR recovery)
"""

"""
consider using queue.join() -> sdr.data.join() to resynch GUI as advancing between modes
need to reset self.start when fresh segment is needed - maybe do this by stopping then restarting stream
need timing for calibration file
need timing for baseline file
need timing for challenge file
"""
Arduino_Dump_Toggle=0
Challenge_Toggle=0
Challenge_phrase='Finished: On Anoxic'


while running==True: # the main game loop
    #read serial i/o from arduino
##    if cur_time.second%5==0:
    # prep serial connection to arduino
    if Connected_Arduino==False:
        try:
            ser=serial.Serial()
            ser.baudrate=9600
            ser.port='/dev/ttyACM0' #this may need to be updated if arduino settings change
            ser.timeout=1
            ser.open()
            Connected_Arduino=True
        except Exception as e:
            print('unable to connect to arduino')
            Connected_Arduino=False

    Arduino_Dump_Toggle=0
    if arduino_stream.data.empty()==False:
        Arduino_Dump_Toggle=1
        arduino_out=arduino_stream.data.get_nowait()
        arduino_list=[i for i in arduino_out.split(b'\r\n') if i!=b' ' and i!=b'']
        if len(arduino_list)>0:
            serial_list+=[str(cur_time)]+arduino_list
            serial_list=serial_list[-9:]
            print(serial_list)
        for i in arduino_list:
            if Challenge_phrase in i:
                Challenge_Toggle=1
    #%% update state of program
    if sdr.finished==False:
        cur_STATUS_Dict['streaming']=1
    if sdr.finished==True:
        cur_STATUS_Dict['streaming']=0
        
    if Mode_dict[Current_Mode]=='calibration':
        cur_STATUS_Dict['calibration']=1
    else: cur_STATUS_Dict['calibration']=0
    
    if Mode_dict[Current_Mode]=='standby':
        cur_STATUS_Dict['standby']=1
    else: cur_STATUS_Dict['standby']=0
    
    if Mode_dict[Current_Mode]=='startup':
        cur_STATUS_Dict['startup']=1
    else:
        cur_STATUS_Dict['startup']=0
        cur_STATUS_Dict['startup_ready']=0
    ##
    #%% $$$$ scoreboard additions
    if Mode_dict[Current_Mode]=='Challenge':
        try:
            if cur_STATUS_Dict['challenge air']==0 and cur_STATUS_Dict['challenge gas']==0:
                cur_STATUS_Dict['challenge gas']=1
                slb_COLOR2=BLACK
                value_Challenge_Counter=1
                value_CurrentChallengeCO2_Start=datetime.now()
                print('first challenge')
            #elif SinceLastBreath>=SLB_Trigger and cur_STATUS_Dict['challenge gas']==1 and numpy.average(r['AIN{}'.format(CHANNEL_DICT['BT'])])>1: #not sure why BT is being compared here...bad edit?
            elif SinceLastBreath>=SLB_Trigger and cur_STATUS_Dict['challenge gas']==1:
                cur_STATUS_Dict['challenge air']=1
                cur_STATUS_Dict['challenge gas']=0
                slb_COLOR2=YELLOW
                value_CurrentChallengeRecovery_Start=datetime.now()
                
                print('{:#.2F} sec apnea detected'.format(SinceLastBreath))
                Challenge_Toggle=0
                #print('air mode')
            elif SinceLastBreath<=SLB_Trigger and 60/avgTT>=baseBPM*BPM_recovery_thresh/100 and current_recovery>=minimum_resus_time and cur_STATUS_Dict['challenge air']==1 and (60/avgRR>=baseHR*HR_recovery_thresh/100 or HR_recovery_thresh==0):
                cur_STATUS_Dict['challenge air']=0
                cur_STATUS_Dict['challenge gas']=1
                slb_COLOR2=BLACK
                value_Challenge_Counter+=1
                value_CurrentChallengeCO2_Start=datetime.now()
    
                print('gas mode')
                print('{} SLB, {} RR {} baseHR {} current recovery'.format(SinceLastBreath,avgRR,baseHR,current_recovery))
        except Exception as e:
            print('challenge mode parsing error - {}'.format(e))
        
        
        if SinceLastBreath>=CALL_DEATH_trigger:
            print('DEATH CALLED')
            Current_Mode=advance(Current_Mode,0,8)
            sdr.stopStreamData()
            
            sdrThread.join()
            while sdr.data.empty()!=True:
                try:
                    q=sdr.data.get() #this may toss the lagged data when switching modes...should be ok if lag is <1sec...may want to consider a better clean up function that puts in in the output file
                except:
                    pass
            print('resetting stream')
            CT_value=d.getTemperature()-273.15
            REL_TIMER=0
            missed=0
            sdrThread = threading.Thread(target=sdr.readStreamData)
            sdrThread.start()
            box_MODE.update(BLACK,WHITE,Mode_dict[Current_Mode])  
    ## $$$$
            
    #%%
    #process status changes
    if cur_STATUS_Dict!=old_STATUS_Dict:
        old_STATUS_Dict=dict(processStatus(cur_STATUS_Dict,d,ser,Arduino_Function_Constants))
        print('change in status - {} - {}'.format(Current_Mode,Mode_dict[Current_Mode]))
    #%%

    if old_STATUS_Dict['startup_ready']==1:
        finish_startup.update(BLUE,WHITE,'Finish Startup')
        sprite_list.add(finish_startup)
        cur_STATUS_Dict['startup_ready']==1
        
    # TODO is pulse processing not needed with transition to serial i/o    
    #process pulses
    for i in cur_STATUS_Dict['pulse']:
        if cur_STATUS_Dict['pulse'][i]['state']==1:
            cur_STATUS_Dict['pulse'][i]['state']=pulse_ender(d,cur_STATUS_Dict['pulse'][i]['pin'],cur_STATUS_Dict['pulse'][i]['start'],pulse_duration)
   
    #%%
    # check for auto advance
    
    if cur_STATUS_Dict['ready to save']==1:
        if Mode_timing[Current_Mode]<0:
            pass
        elif Mode_timing[Current_Mode]<=REL_TIMER:
            Current_Mode=advance(Current_Mode,0,8)
            sdr.stopStreamData()
            
            sdrThread.join()
            while sdr.data.empty()!=True:
                try:
                    q=sdr.data.get() #this may toss the lagged data when switching modes...should be ok if lag is <1sec...may want to consider a better clean up function that puts in in the output file
                except:
                    pass
            print('resetting stream')
            CT_value=d.getTemperature()-273.15
            REL_TIMER=0
            missed=0
            sdrThread = threading.Thread(target=sdr.readStreamData)
            sdrThread.start()
            box_MODE.update(BLACK,WHITE,Mode_dict[Current_Mode])  
    
    
            
    #update from prior button clicks
    for event in pygame.event.get():
        if event.type==pygame.MOUSEBUTTONDOWN:
            if event.button==1:
                print('left clicked')
                print(event.pos)
            for i in box_mode_select:
                if box_mode_select[i].rect.collidepoint(event.pos) and cur_STATUS_Dict['ready to save']==1:
                    Current_Mode=i
                    sdr.stopStreamData()
                    
                    sdrThread.join()
                    while sdr.data.empty()!=True:
                        try:
                            q=sdr.data.get() #this will toss the lagged data when switching modes...should be ok if lag is <1sec...may want to consider a better clean up function that puts in in the output file
                        except:
                            pass
                    print('resetting stream')
                    CT_value=d.getTemperature()-273.15
                    REL_TIMER=0
                    missed=0
                    sdrThread = threading.Thread(target=sdr.readStreamData)
                    sdrThread.start()
                    box_MODE.update(BLACK,WHITE,Mode_dict[Current_Mode]) 
                if box_mode_times[i].rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                    Mode_timing[i]=60*guiGetFloat('enter duration','enter duration in minutes for \n{}\n(enter a negative number to hold until user advances)'.format(Mode_dict[i]),Mode_timing[i])
                    box_mode_select[i].update(DGREY,WHITE,'{}:{:#.2F}'.format(Mode_dict[i],Mode_timing[i]/60))
            if box_Synch.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:

                sdr.stopStreamData()
                
                sdrThread.join()
                while sdr.data.empty()!=True:
                    try:
                        q=sdr.data.get() #this will toss the lagged data when switching modes...should be ok if lag is <1sec...may want to consider a better clean up function that puts in in the output file
                    except:
                        pass
                print('resetting stream')
                CT_value=d.getTemperature()-273.15
                REL_TIMER=0
                missed=0
                sdrThread = threading.Thread(target=sdr.readStreamData)
                sdrThread.start()
                box_MODE.update(BLACK,WHITE,Mode_dict[Current_Mode])
            elif box_NEXT.rect.collidepoint(event.pos) and cur_STATUS_Dict['ready to save']==1:
                Current_Mode=advance(Current_Mode,0,8)
                sdr.stopStreamData()
                
                sdrThread.join()
                while sdr.data.empty()!=True:
                    try:
                        q=sdr.data.get() #this will toss the lagged data when switching modes...should be ok if lag is <1sec...may want to consider a better clean up function that puts in in the output file
                    except:
                        pass
                print('resetting stream')
                CT_value=d.getTemperature()-273.15
                REL_TIMER=0
                missed=0
                sdrThread = threading.Thread(target=sdr.readStreamData)
                sdrThread.start()
                box_MODE.update(BLACK,WHITE,Mode_dict[Current_Mode])  
                
            elif box_SAVE.rect.collidepoint(event.pos) and Current_Mode==0:
                OUTPUTFILE,rts=save_button()
                cur_STATUS_Dict['ready to save']=rts
                box_SAVE.update(WHITE,BLUE,os.path.basename(OUTPUTFILE))
                
                
            elif box_NOTIFICATION.rect.collidepoint(event.pos) and Current_Mode==0:
                EMAIL_SETTINGS=guiOpenFileName({'title':'select file with email notification settings'})
                box_NOTIFICATION.update(WHITE,BLUE,'NOTIFICATIONS-ON')

            elif Position_RA.rect.collidepoint(event.pos):
                Arduino_Function_Constants['Position_RA']=guiGetFloat(
                    'Room Air Position',
                    'Room Air Position',
                    Arduino_Function_Constants['Position_RA']
                    )
                Position_RA.update(BLACK,WHITE,'RA position: {}'.format(Arduino_Function_Constants['Position_RA']))
            elif Position_Gas.rect.collidepoint(event.pos):
                Arduino_Function_Constants['Position_Gas']=guiGetFloat(
                    'Gas Position',
                    'Gas Position',
                    Arduino_Function_Constants['Position_Gas']
                    )
                Position_Gas.update(BLACK,WHITE,'Gas position: {}'.format(Arduino_Function_Constants['Position_Gas']))
            elif Duration_Cal.rect.collidepoint(event.pos):
                Arduino_Function_Constants['Duration_Cal']=guiGetFloat(
                    'Calibration Duration',
                    'Calibration Duration',
                    Arduino_Function_Constants['Duration_Cal']
                    )
                Duration_Cal.update(BLACK,WHITE,'Cal dur: {}'.format(Arduino_Function_Constants['Duration_Cal']))
            elif Duration_Prefill.rect.collidepoint(event.pos):
                Arduino_Function_Constants['Duration_Prefill']=guiGetFloat(
                    'Prefill Duration',
                    'Prefill Duration',
                    Arduino_Function_Constants['Duration_Prefill']
                    )
                Duration_Prefill.update(BLACK,WHITE,'Prefill dur {}'.format(Arduino_Function_Constants['Duration_Prefill']))

            elif Serial_Abort.rect.collidepoint(event.pos):
                serialtext='<Z,0,0>'
                try:
                    ser.write(serialtext.encode())
                    print('{} - sent'.format(serialtext))
                except:
                    print('unable to transmit "{} "via serial io'.format(serialtext))

            elif Serial_ShutDown.rect.collidepoint(event.pos):
                serialtext='<D,0,0>'
                try:
                    ser.write(serialtext.encode())
                    print('{} - sent'.format(serialtext))
                except:
                    print('unable to transmit "{} "via serial io'.format(serialtext))

            elif finish_startup.rect.collidepoint(event.pos) and cur_STATUS_Dict['startup_ready']==1:
                serialtext='<E,0,0>'
                try:
                    ser.write(serialtext.encode())
                    print('{} - sent'.format(serialtext))
                except:
                    print('unable to transmit "{} "via serial io'.format(serialtext))
                cur_STATUS_Dict['startup_ready']=2
                finish_startup.update(BLACK,BLACK,'')
                
            elif SerialOutTester.rect.collidepoint(event.pos): # and Current_Mode==0:
                serialtext=guiGetText('serial output','serial output','')
                try:
                    ser.write(serialtext.encode())
                    print('{} - sent'.format(serialtext))
                except:
                    print('unable to transmit "{} "via serial io'.format(serialtext))
                
            elif g1_ymax_inc.rect.collidepoint(event.pos):
                g1_y_minmax[1]+=increment
            elif g1_ymax_dec.rect.collidepoint(event.pos):
                g1_y_minmax[1]-=increment
            elif g1_ymax_reset.rect.collidepoint(event.pos):
                g1_y_minmax[1]=2 #need dict for default values
            elif g1_ymax_float.rect.collidepoint(event.pos):
                g1_y_minmax[1]=guiGetFloat('Maximum for Graph 1','Maximum for Graph 1',g1_y_minmax[1])
            elif g1_ymin_inc.rect.collidepoint(event.pos):
                g1_y_minmax[0]+=increment
            elif g1_ymin_dec.rect.collidepoint(event.pos):
                g1_y_minmax[0]-=increment
            elif g1_ymin_reset.rect.collidepoint(event.pos):
                g1_y_minmax[0]=-2 #need dict for default values
            elif g1_ymin_float.rect.collidepoint(event.pos):
                g1_y_minmax[0]=guiGetFloat('Minimum for Graph 1','Minimum for Graph 1',g1_y_minmax[0])
                
            elif g2_ymax_inc.rect.collidepoint(event.pos):
                g2_y_minmax[1]+=increment
            elif g2_ymax_dec.rect.collidepoint(event.pos):
                g2_y_minmax[1]-=increment
            elif g2_ymax_reset.rect.collidepoint(event.pos):
                g2_y_minmax[1]=5 #need dict for default values
            elif g2_ymax_float.rect.collidepoint(event.pos):
                g2_y_minmax[1]=guiGetFloat('Maximum for Graph 2','Maximum for Graph 2',g2_y_minmax[1])
            elif g2_ymin_inc.rect.collidepoint(event.pos):
                g2_y_minmax[0]+=increment
            elif g2_ymin_dec.rect.collidepoint(event.pos):
                g2_y_minmax[0]-=increment
            elif g2_ymin_reset.rect.collidepoint(event.pos):
                g2_y_minmax[0]=-1 #need dict for default values
            elif g2_ymin_float.rect.collidepoint(event.pos):
                g2_y_minmax[0]=guiGetFloat('Minimum for Graph 2','Minimum for Graph 2',g2_y_minmax[0])
                
                
            elif g3_ymax_inc.rect.collidepoint(event.pos):
                g3_y_minmax[1]+=increment
            elif g3_ymax_dec.rect.collidepoint(event.pos):
                g3_y_minmax[1]-=increment
            elif g3_ymax_reset.rect.collidepoint(event.pos):
                g3_y_minmax[1]=5 #need dict for default values
            elif g3_ymax_float.rect.collidepoint(event.pos):
                g3_y_minmax[1]=guiGetFloat('Maximum for Graph 3','Maximum for Graph 3',g3_y_minmax[1])
            elif g3_ymin_inc.rect.collidepoint(event.pos):
                g3_y_minmax[0]+=increment
            elif g3_ymin_dec.rect.collidepoint(event.pos):
                g3_y_minmax[0]-=increment
            elif g3_ymin_reset.rect.collidepoint(event.pos):
                g3_y_minmax[0]=-1 #need dict for default values
            elif g3_ymin_float.rect.collidepoint(event.pos):
                g3_y_minmax[0]=guiGetFloat('Minimum for Graph 3','Minimum for Graph 3',g3_y_minmax[0])
                
            elif baseline_flow_inc.rect.collidepoint(event.pos):
                baseline_flow+=increment
            elif baseline_flow_dec.rect.collidepoint(event.pos):
                baseline_flow-=increment
            elif baseline_flow_reset.rect.collidepoint(event.pos):
                baseline_flow=0
            elif baseline_flow_float.rect.collidepoint(event.pos):
                baseline_flow=guiGetFloat('Baseline for Graph 1','Baseline for Graph 1', baseline_flow)
            
            elif thresh_flow_inc.rect.collidepoint(event.pos):
                thresh_flow+=increment
            elif thresh_flow_dec.rect.collidepoint(event.pos):
                thresh_flow-=increment
            elif thresh_flow_reset.rect.collidepoint(event.pos):
                thresh_flow=0.25
            elif thresh_flow_float.rect.collidepoint(event.pos):
                thresh_flow=guiGetFloat('Threshold for Flow','Threshold for Flow', thresh_flow)

            elif thresh2_flow_inc.rect.collidepoint(event.pos):
                thresh2_flow+=increment
            elif thresh2_flow_dec.rect.collidepoint(event.pos):
                thresh2_flow-=increment
            elif thresh2_flow_reset.rect.collidepoint(event.pos):
                thresh2_flow=0.5
            elif thresh2_flow_float.rect.collidepoint(event.pos):
                thresh2_flow=guiGetFloat('Threshold 2 for Flow','Threshold 2 for Flow', thresh2_flow)
            
            elif baseline_vol_inc.rect.collidepoint(event.pos):
                baseline_vol+=increment
            elif baseline_vol_dec.rect.collidepoint(event.pos):
                baseline_vol-=increment
            elif baseline_vol_reset.rect.collidepoint(event.pos):
                baseline_vol=0
            elif baseline_vol_float.rect.collidepoint(event.pos):
                baseline_vol=guiGetFloat('Baseline for Graph 2','Baseline for Graph 2', baseline_vol)
            
            elif thresh_vol_inc.rect.collidepoint(event.pos):
                thresh_vol+=increment
            elif thresh_vol_dec.rect.collidepoint(event.pos):
                thresh_vol-=increment
            elif thresh_vol_reset.rect.collidepoint(event.pos):
                thresh_vol=0.25
            elif thresh_vol_float.rect.collidepoint(event.pos):
                thresh_vol=guiGetFloat('Threshold for Volume','Threshold for Volume', thresh_vol)

            elif baseline_ecg_inc.rect.collidepoint(event.pos):
                baseline_ecg+=increment
            elif baseline_ecg_dec.rect.collidepoint(event.pos):
                baseline_ecg-=increment
            elif baseline_ecg_reset.rect.collidepoint(event.pos):
                baseline_ecg=0
            elif baseline_ecg_float.rect.collidepoint(event.pos):
                baseline_ecg=guiGetFloat('Baseline for Graph 2','Baseline for Graph 2', baseline_ecg)
            
            elif thresh_ecg1_inc.rect.collidepoint(event.pos):
                thresh_ecg1+=increment
            elif thresh_ecg1_dec.rect.collidepoint(event.pos):
                thresh_ecg1-=increment
            elif thresh_ecg1_reset.rect.collidepoint(event.pos):
                thresh_ecg1=4
            elif thresh_ecg1_float.rect.collidepoint(event.pos):
                thresh_ecg1=guiGetFloat('Threshold 1 for ECG','Threshold 1 for ECG', thresh_ecg1)

            elif thresh_ecg2_inc.rect.collidepoint(event.pos):
                thresh_ecg2+=increment
            elif thresh_ecg2_dec.rect.collidepoint(event.pos):
                thresh_ecg2-=increment
            elif thresh_ecg2_reset.rect.collidepoint(event.pos):
                thresh_ecg2=2.5
            elif thresh_ecg2_float.rect.collidepoint(event.pos):
                thresh_ecg2=guiGetFloat('Threshold 2 for ECG','Threshold 2 for ECG', thresh_ecg2)

            elif noise_ecg_inc.rect.collidepoint(event.pos):
                noise_ecg+=increment
            elif noise_ecg_dec.rect.collidepoint(event.pos):
                noise_ecg-=increment
            elif noise_ecg_reset.rect.collidepoint(event.pos):
                noise_ecg=75
            elif noise_ecg_float.rect.collidepoint(event.pos):
                noise_ecg=guiGetFloat('noise cutoff for Graph 3','noise cutoff for Graph 3', noise_ecg)

            elif absthresh_ecg_inc.rect.collidepoint(event.pos):
                absthresh_ecg+=increment
            elif absthresh_ecg_dec.rect.collidepoint(event.pos):
                absthresh_ecg-=increment
            elif absthresh_ecg_reset.rect.collidepoint(event.pos):
                absthresh_ecg=0.3
            elif absthresh_ecg_float.rect.collidepoint(event.pos):
                absthresh_ecg=guiGetFloat('absolute thresh cutoff for Graph 3','absolute thresh cutoff for Graph 3', absthresh_ecg)
       
            elif inc_inc.rect.collidepoint(event.pos):
                increment*=10
            elif inc_dec.rect.collidepoint(event.pos):
                increment/=10
            elif inc_reset.rect.collidepoint(event.pos):
                increment=0.1
            elif inc_float.rect.collidepoint(event.pos):
                increment=guiGetFloat('Adjust Increment Value','Adjust Increment Value',increment)
              
            #restrict actions on tweakables to signal preview periods
                #remove restrictions on mode for filter toggles and signal invert
            #elif ECGFILT_TOGGLE.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
            elif ECGFILT_TOGGLE.rect.collidepoint(event.pos):
                ecg_filt_state=toggle(ecg_filt_state)
            elif PLETHFILT_TOGGLE.rect.collidepoint(event.pos):
                pleth_filt_state=toggle(pleth_filt_state)
            elif INVERT_FLOW_TOGGLE.rect.collidepoint(event.pos):
                INVERT_FLOW=toggle(INVERT_FLOW)
                if INVERT_FLOW==1:
                    INVERT_FLOW_TOGGLE.update(BLACK,WHITE,'Invert Flow:{}'.format(INVERT_FLOW))
                else:
                    INVERT_FLOW_TOGGLE.update(WHITE,BLACK,'Invert Flow:{}'.format(INVERT_FLOW))
            elif INVERT_ECG_TOGGLE.rect.collidepoint(event.pos):
                INVERT_ECG=toggle(INVERT_ECG)
                if INVERT_ECG==1:
                    INVERT_ECG_TOGGLE.update(BLACK,WHITE,'Invert ECG:{}'.format(INVERT_ECG))
                else:
                    INVERT_ECG_TOGGLE.update(WHITE,BLACK,'Invert ECG:{}'.format(INVERT_ECG))

            elif box_SLB_trigger.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                SLB_Trigger=guiGetFloat('SLB trigger time','SLB trigger time',SLB_Trigger)
                SLB_Trigger_Setter.update(WHITE,BLACK,'SLB: {:#.2F} sec'.format(SLB_Trigger))
                box_SLB_trigger.update(YELLOW,BLACK,'SLB: {:#.2F} sec'.format(SLB_Trigger))
                
            elif box_minimum_resus_time.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                minimum_resus_time=guiGetFloat('minimum resus time (sec)','minimum resus time (sec)',minimum_resus_time)
                    
            elif box_CALL_DEATH_trigger.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                CALL_DEATH_trigger=60*guiGetFloat('CALL DEATH trigger time (min)','CALL DEATH trigger time (min)',CALL_DEATH_trigger)
                box_CALL_DEATH_trigger.update(YELLOW,BLACK,'CALL DEATH: {:#.2F} min'.format(CALL_DEATH_trigger/60))
            elif box_HR_recovery_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                HR_recovery_thresh=guiGetFloat('HR recovery thresh','HR recovery thresh',HR_recovery_thresh)
            elif box_BPM_recovery_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                BPM_recovery_thresh=guiGetFloat('BPM recovery thresh','BPM recovery thresh',BPM_recovery_thresh)
            elif box_avgBPM_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['avgBPM']=guiGetFloat('avg BPM threshold','avg BPM threshold',filt_crit_Dict['avgBPM'])
            elif box_cvTT_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['cvTT']=guiGetFloat('CV TT threshold','CV TT threshold',filt_crit_Dict['cvTT'])
            elif box_avgHR_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['avgHR']=guiGetFloat('avg HR threshold','avg HR threshold',filt_crit_Dict['avgHR'])
            elif box_avgRR_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['avgRR']=guiGetFloat('avg RR threshold','avg RR threshold',filt_crit_Dict['avgRR'])
            elif box_cvRR_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['cvRR']=guiGetFloat('CV RR threshold','CV RR threshold',filt_crit_Dict['cvRR'])
            elif box_BSD_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['BSD']=guiGetFloat('BSD threshold','BSD threshold',filt_crit_Dict['BSD'])
            elif box_DVTV_thresh.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                filt_crit_Dict['DVTV']=guiGetFloat('DVTV threshold','DVTV threshold',filt_crit_Dict['DVTV'])
            elif box_QB_duration.rect.collidepoint(event.pos) and 'Signal Preview' in Mode_dict[Current_Mode]:
                QB_minimum_duration=guiGetFloat('Quality Bout minimum duration','Quality Bout minimum duration',QB_minimum_duration)
                
            else: pass
            
        if event.type==pygame.QUIT:
            running=False
            print('exit')
    if running==False:
        print('exit sent')
        sdr.stopStreamData()
        continue
    # update sprites
    g1_ymax_float.update(BLACK,WHITE,'{:#.3F}'.format(g1_y_minmax[1]))
    g1_ymin_float.update(BLACK,WHITE,'{:#.3F}'.format(g1_y_minmax[0]))
    g2_ymax_float.update(BLACK,WHITE,'{:#.3F}'.format(g2_y_minmax[1]))
    g2_ymin_float.update(BLACK,WHITE,'{:#.3F}'.format(g2_y_minmax[0]))
    g3_ymax_float.update(BLACK,WHITE,'{:#.3F}'.format(g3_y_minmax[1]))
    g3_ymin_float.update(BLACK,WHITE,'{:#.3F}'.format(g3_y_minmax[0]))
    inc_float.update(BLACK,WHITE,'{:#.3F}'.format(increment))
    baseline_flow_float.update(BLACK,WHITE,'{:#.3F}'.format(baseline_flow))
    thresh_flow_float.update(BLACK,WHITE,'{:#.3F}'.format(thresh_flow))
    thresh2_flow_float.update(BLACK,WHITE,'{:#.3F}'.format(thresh2_flow))
    baseline_vol_float.update(BLACK,WHITE,'{:#.3F}'.format(baseline_vol))
    thresh_vol_float.update(BLACK,WHITE,'{:#.3F}'.format(thresh_vol))
    baseline_ecg_float.update(BLACK,WHITE,'{:#.3F}'.format(baseline_ecg))
    noise_ecg_float.update(BLACK,WHITE,'{:#.1F}'.format(noise_ecg))
    absthresh_ecg_float.update(BLACK,WHITE,'{:#.3F}'.format(absthresh_ecg))
    thresh_ecg1_float.update(BLACK,WHITE,'{:#.1F}'.format(thresh_ecg1))
    thresh_ecg2_float.update(BLACK,WHITE,'{:#.1F}'.format(thresh_ecg2))
    #$$$$ scoreboard

    SO1.update_left(DGREY,WHITE,serial_list[0])
    SO2.update_left(DGREY,WHITE,serial_list[1])
    SO3.update_left(DGREY,WHITE,serial_list[2])
    SO4.update_left(DGREY,WHITE,serial_list[3])
    SO5.update_left(DGREY,WHITE,serial_list[4])
    SO6.update_left(DGREY,WHITE,serial_list[5])
    SO7.update_left(DGREY,WHITE,serial_list[6])
    SO8.update_left(DGREY,WHITE,serial_list[7])
    SO9.update_left(DGREY,WHITE,serial_list[8])
    
    
    if cur_STATUS_Dict['challenge gas']==1:
        Challenge_Counter.update(WHITE,BLACK,'Challenge #: {}'.format(value_Challenge_Counter))
        value_CurrentChallengeCO2_Timer=cur_time-value_CurrentChallengeCO2_Start
        CurrentChallengeCO2_Timer.update(WHITE,BLACK,'CO2: {} sec'.format(
            value_CurrentChallengeCO2_Timer.days*24*60*60+value_CurrentChallengeCO2_Timer.seconds))


    elif cur_STATUS_Dict['challenge air']==1:
        value_CurrentChallengeRecovery_Timer=cur_time-value_CurrentChallengeRecovery_Start
        CurrentChallengeRecovery_Timer.update(WHITE,BLACK,'Rec: {} sec'.format(
            value_CurrentChallengeRecovery_Timer.days*24*60*60+value_CurrentChallengeRecovery_Timer.seconds))
    
    

    
    
    box_HR_recovery_thresh.update(YELLOW,BLACK,'HR recover: {:#.2F} %'.format(HR_recovery_thresh))
    box_BPM_recovery_thresh.update(YELLOW,BLACK,'BPM recover: {:#.2F} %'.format(BPM_recovery_thresh))
    box_avgBPM_thresh.update(YELLOW,BLACK,'avg BPM: {:#.1F} bpm'.format(filt_crit_Dict['avgBPM']))
    box_cvTT_thresh.update(YELLOW,BLACK,'CV TT: {:#.2F} ratio'.format(filt_crit_Dict['cvTT']))
    box_avgHR_thresh.update(YELLOW,BLACK,'avg HR: {:#.1F} bpm'.format(filt_crit_Dict['avgHR']))
    box_avgRR_thresh.update(YELLOW,BLACK,'avg RR: {:#.1F} ms'.format(filt_crit_Dict['avgRR']))
    box_cvRR_thresh.update(YELLOW,BLACK,'CV RR: {:#.2F} ratio'.format(filt_crit_Dict['cvRR']))
    box_BSD_thresh.update(YELLOW,BLACK,'Base Drift: {:#.2F} V'.format(filt_crit_Dict['BSD']))
    box_DVTV_thresh.update(YELLOW,BLACK,'DVTV: {:#.2F} ratio'.format(filt_crit_Dict['DVTV']))
    box_QB_duration.update(YELLOW,BLACK,'min QB: {:#.1F} sec'.format(QB_minimum_duration))
        
    box_stream_lag.update(BACKGROUND_COLOR,RED,'{:#.3F}'.format(stream_lag))
    box_duration.update(BLACK,RED,'{:#.3F} sec'.format(REL_TIMER))
    
        
        
        
    sprite_list.draw(DISPLAYSURF)    
    #update from stream
    #get data
    try:
        cur_time=datetime.now()
        elapsed_time=cur_time - sdr.start
        elapsed_time_sec=elapsed_time.days*24*60*60+elapsed_time.seconds+elapsed_time.microseconds/1000000
        stream_lag=elapsed_time_sec-REL_TIMER-missed/1000
        if prev_Mode!=Current_Mode:
            elapsed_time_sec=0 #used to catch lag of sdr.start update for autoadvance of segment - should prevent accidental premature 'finish' unless lag from thread is more than 1 loop iteration
    except:
        print('no lag')
        elapsed_time_sec=0 #added to deal with startup error - sdr seems to not start on first loop?
        stream_lag=0
    
    try:
        
        # Pull results out of the Queue in a blocking manner.
        result = sdr.data.get(True, 1)
        
        # If there were errors, print that.
        if result["errors"] != 0:
            errors+=result["errors"]
            errlist.append(result["errors"])
            missed += result["missed"]
            print("+++++ Total Errors: %s, Total Missed: %s +++++" % (errors, missed))
    
        # Convert the raw bytes (result['result']) to voltage data.
        r = d.processStreamData(result['result'])
        
        
        ## save the data
        if Mode_dict[Current_Mode] in savable_modes:
            if Current_Mode!=prev_Mode:
                header=[
                'baseline flow:{}'.format(baseline_flow),
                'thresh flow:{}'.format(thresh_flow),
                'baseline_ecg:{}'.format(baseline_ecg),
                'absthresh_ecg:{}'.format(absthresh_ecg),
                'thresh_ecg1:{}'.format(thresh_ecg1),
                'thresh_ecg2:{}'.format(thresh_ecg2),
                'noise_ecg:{}'.format(noise_ecg),
                'HR_recovery_thresh:{}'.format(HR_recovery_thresh),
                'minimum_resus_time:{}'.format(minimum_resus_time),
                'SLB_Trigger:{}'.format(SLB_Trigger),
                'CALL_DEATH_Trigger:{}'.format(CALL_DEATH_trigger),
                'QB_minimum_duration:{}'.format(QB_minimum_duration),
                'filt_crit_Dict:{}'.format(filt_crit_Dict)
                ]
                colheader='\t'.join(['time']+CHANNEL_KEY+['labjack_temp','mode','statuscodes'])
                header.append(colheader)
            
                saveCapturedData(OUTPUTFILE,header)
            #%%
            #writingblock=[]
            with open(OUTPUTFILE,'a') as oof:
                for j in range(len(r['AIN{}'.format(CHANNEL_LIST[0])])):
                    
                    wb_row=[REL_TIMER]
                    REL_TIMER=round(REL_TIMER+1/SCAN_FREQUENCY,3)
                    for i in ['AIN{}'.format(i) for i in CHANNEL_LIST]:
                        wb_row.append(round(r[i][j],6))
                    wb_row.append(round(CT_value,6))
                    wb_row.append(Mode_dict[Current_Mode])
                    wb_row.append(cur_STATUS_Dict)
                    if Arduino_Dump_Toggle==1:
                        wb_row.append(','.join(arduino_list))
                        Arduino_Dump_Toggle=0
                    oof.write('\t'.join([str(i) for i in wb_row])+'\n')
            #%%
        else:
            for j in range(len(r['AIN{}'.format(CHANNEL_LIST[0])])):
                REL_TIMER=round(REL_TIMER+1/SCAN_FREQUENCY,3)

            
        # prep data for graphing
        g1_app_ctr=0
        downsample_rate1=20
        for i in r['AIN{}'.format(CHANNEL_LIST[CHANNEL_DICT['FLOW']])]:
            g1_app_ctr+=1
            if g1_app_ctr%downsample_rate1==0:
                PreFilt_data1.append(i)
            else: continue
        g3_app_ctr=0
        downsample_rate3=2
        
        for i in r['AIN{}'.format(CHANNEL_LIST[CHANNEL_DICT['ECG']])]:
            g3_app_ctr+=1
            if g3_app_ctr%downsample_rate3==0:
                PreFilt_data3.append(i)
        ##crop the data (7.5 seconds) 
        PreFilt_data1=PreFilt_data1[-375:] #50Hz * 7.5s
        PreFilt_data3=PreFilt_data3[-1500:] #500Hz * 3s#minimize buffer of prefilt data to help with lag
        
        ##filter data and sample for calling
        if pleth_filt_state==0:
            if INVERT_FLOW==0:
                data1=list(PreFilt_data1)[-250:]
            else: data1=[i*-1 for i in list(PreFilt_data1)[-250:]]
            PLETHFILT_TOGGLE.update(RED,BLACK,'PLETH FILTER OFF')
        else:
            if INVERT_FLOW==0:
                data1=list(butterFilt(PreFilt_data1,50))[-250:]
            else: data1=list(butterFilt([i*-1 for i in list(PreFilt_data1)],50))[-250:]
            
            PLETHFILT_TOGGLE.update(GREEN,BLACK,'PLETH FILTER ON')
                        
        
        if ecg_filt_state==1:
            ECGFILT_TOGGLE.update(GREEN,BLACK,'ECG FILTER ON')
            if INVERT_ECG==0:
                data3=list(basicFilt(PreFilt_data3,1000,60,30))[-1251:-1:1] #downsample to 500Hz
            else:
                data3=[i*-1 for i in list(basicFilt(PreFilt_data3,1000,60,30))[-1251:-1:1]] #downsample to 500Hz
        else:
            ECGFILT_TOGGLE.update(RED,BLACK,'ECG FILTER OFF')
            if INVERT_ECG==0:
                data3=PreFilt_data3[-1250:-1:1]
            else:
                data3=[i*-1 for i in PreFilt_data3[-1250:-1:1]]
                
            
        #5 second ts window
        ts1=[i/1000+20/1000 for i in range(int(round((REL_TIMER-5)*1000,3)),int(REL_TIMER*1000),20)] # this may need adjusting if frequency is changed
        ts3=[i/1000+1/1000 for i in range(int(round((REL_TIMER-2.5)*1000,3)),int(REL_TIMER*1000),2)]
        
        if Challenge_Toggle==1:
            if max(data1)>=thresh2_flow:
                Challenge_Toggle = 2
        
        if cur_STATUS_Dict['challenge gas']==1 and Challenge_Toggle==2: #$$$ this will need to be replaced with gas verify variable from serial io
            BreathCalls=basic_breathcall(data1,ts1,baseline_flow,thresh2_flow)
            Annot_Color=RED
        else:
            BreathCalls=basic_breathcall(data1,ts1,baseline_flow,thresh_flow)
            Annot_Color=GREEN
        if BreathCalls is None or len(BreathCalls)<2:
            avgBPM='<12'
            #avgPIF='-----'
            avgTV='-----'
            avgTT=999
            CV_TT=999
            avgDVTV=999
            
            
        else:
            avgTT=numpy.average([BreathCalls[i]['TI']+BreathCalls[i]['TE'] for i in BreathCalls if 'TE' in BreathCalls[i].keys()]) # note this needs to be scaled from index to time (1000Hz/20[downscale value])
            CV_TT=numpy.std([BreathCalls[i]['TI']+BreathCalls[i]['TE'] for i in BreathCalls if 'TE' in BreathCalls[i].keys()])/avgTT
            avgTV='{:#.3F}V/s'.format(numpy.average([BreathCalls[i]['iTV'] for i in BreathCalls if 'TE' in BreathCalls[i].keys()]))
            avgBPM='{:#.1F}'.format(60/avgTT) #this creates a 'less' transformed BPM (division transform) - relationship between TT and BPM modified by Irregularity
            #avgPIF='{:#.2F}V/s'.format(numpy.average([BreathCalls[i]['PIF'] for i in BreathCalls if 'TE' in BreathCalls[i].keys()]))
            avgDVTV=numpy.average([BreathCalls[i]['DVTV'] for i in BreathCalls if 'TE' in BreathCalls[i].keys()])
            
        
        BL=list(BreathCalls.keys())
        BL.sort()
        vol_lines={}
        for i in range(len(BL[:-1])):
            vol_lines[i]={'ts':[BreathCalls[BL[i]]['TS-I'],BreathCalls[BL[i]]['TS-E'],BreathCalls[BL[i+1]]['TS-I']],
                         'vol':[0,BreathCalls[BL[i]]['iTV'],BreathCalls[BL[i]]['iTV']-BreathCalls[BL[i]]['eTV']]}


        if len(vol_lines)!=0:
            vol_lines_graphed=[]
        for l in vol_lines:
            vol_scaled=graphScaler(g2_TL,g2_xySize,(ts1[0],ts1[-1]),g2_y_minmax,
                                   vol_lines[l]['ts'],
                                    vol_lines[l]['vol'])
            vol_lines_graphed.append(pygame.draw.lines(DISPLAYSURF,BLUE,False,vol_scaled))


                        
        BeatCalls=basicRR(data3,ts3,noise_ecg,thresh_ecg1,absthresh_ecg,3)
        if BeatCalls is None or len(BeatCalls)<5 :
            BeatCalls=basicRR(data3,ts3,noise_ecg,thresh_ecg2,absthresh_ecg,3)
        if BeatCalls is None or len(BeatCalls)<5 :            
            avgHR='<60'
            avgRR=999
            CV_RR=999
        else:
            avgRR=numpy.average([BeatCalls[i]['RR'] for i in BeatCalls]) 
            avgHR='{:#.1F}'.format(60/avgRR)
            CV_RR=numpy.std([BeatCalls[i]['RR'] for i in BeatCalls])/avgRR 
        
             
        BL=list(BreathCalls.keys())
        BL.sort()

        HL=list(BeatCalls.keys())
        HL.sort()
        
        if len(BreathCalls)>0:
            LastBreath=BL[-1]
        if prev_Mode!=Current_Mode:
            LastBreath=0

        SinceLastBreath=elapsed_time_sec-LastBreath
        if SinceLastBreath>=CALL_DEATH_trigger:
            print(SinceLastBreath)
            print(elapsed_time_sec)
            print(LastBreath)
                   
        if Mode_dict[Current_Mode]=='Challenge' and SinceLastBreath<=SLB_Trigger:
            slb_COLOR=GREEN
            
        elif Mode_dict[Current_Mode]=='Challenge' and SinceLastBreath>SLB_Trigger:
            slb_COLOR=RED
            
        else: 
            slb_COLOR=BLACK
            slb_COLOR2=WHITE
        BSD=abs(numpy.average(data1[::10])-baseline_flow)
        
        
        
        #check if in 'good recording section'
        filt_test_Dict={
            'avgBPM':60/avgTT,
            'cvTT':CV_TT,
            'avgHR':60/avgRR,
            'avgRR':avgRR,
            'cvRR':CV_RR,
            'BSD':BSD,
            'DVTV':avgDVTV
            }
        
        exclude=[]
        for i in filt_crit_Dict:
            if filt_crit_Dict[i]<filt_test_Dict[i]:
                exclude.append(i)
        if len(exclude)>=1:
            quality_test=0
            QualColor=RED
        else:
            quality_test=1
            QualColor=GREEN
        
        
                
        
        
        box_qual_test.update(QualColor,BLACK,' '.join(exclude))
        
        if Mode_dict[Current_Mode]=='Baseline' and prev_Mode!=Current_Mode:
            RunningBreaths=[]
            RunningBeats=[]
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
                        
            for i in HL:
                if len(RunningBeats)==0:
                    RunningBeats.append({'ts':i,'BC':BeatCalls[i]})
                    
                elif i>RunningBeats[-1]['ts']:
                    RunningBeats.append({'ts':i,'BC':BeatCalls[i]})
                    
        prev_qual_test=int(quality_test)
        #filter to the good breaths and summarize stats
        #%%
        if Mode_dict[Current_Mode]=='Challenge' and prev_Mode!=Current_Mode:
            Q_breaths=[]
            Q_beats=[]
            QB_Counter=0
            QB_duration=0
            for i,j in quality_seg_list:
                if j-i<QB_minimum_duration:
                    continue
                QB_Counter+=1
                QB_duration+=j-i
                for k in RunningBreaths:
                    if k['TS-I']>i and k['TS-I']<j:
                        Q_breaths.append(k)
                for k in RunningBeats:
                    if k['ts']>i and k['ts']<j:
                        Q_beats.append(k)
            
                        
            baseTT=numpy.average([i['TI']+i['TE'] for i in Q_breaths if 'TE' in i.keys()])
            baseBPM=60/baseTT
            baseTV=numpy.average([i['iTV'] for i in Q_breaths])
            baseRR=numpy.average([i['BC']['RR'] for i in Q_beats])
            baseHR=60/baseRR
            
            box_baseBPM.update(GREEN,BLACK,'base BPM:{:#.1F}'.format(baseBPM))
            box_baseTV.update(GREEN,BLACK,'base TV:{:#.2F}'.format(baseTV))
            box_baseHR.update(GREEN,BLACK,'base HR:{:#.1F}'.format(baseHR))
        #%% reset voltages if no longer in challenge mode
        if Mode_dict[Current_Mode]!='Challenge':
            cur_STATUS_Dict['challenge air']=0
            cur_STATUS_Dict['challenge gas']=0
        
        #%% add timer for minimum resus time
        if Mode_dict[Current_Mode]=='Challenge':
            
            if cur_STATUS_Dict['challenge air']==1:
                rec_duration=cur_time-cur_STATUS_Dict['pulse']['challenge air']['start']
                current_recovery=rec_duration.seconds
            elif cur_STATUS_Dict['challenge gas']==1:
                current_recovery=float(minimum_resus_time)
                    
        else:
            current_recovery=float(minimum_resus_time)
            
        
        if current_recovery>=minimum_resus_time:
            MRT_color=GREEN
        elif current_recovery>=minimum_resus_time-10:
            MRT_color=YELLOW
        else:
            MRT_color=RED
        
        box_minimum_resus_time.update(MRT_color,BLACK,'RECOVERY:{:#d}/{:#d})'.format(int(current_recovery),int(minimum_resus_time)))
        
        box_qual_bouts.update(YELLOW,BLACK,'bouts:{}'.format(QB_Counter))
        box_qual_dur.update(YELLOW,BLACK,'duration:{:#.1F}'.format(QB_duration))                   
        # updated unused boxes for demo video
        box_CT.update(WHITE,BLUE,'RT:{:#.1F}C|Pi:{:#.1F}C'.format(CT_value,CPUTemperature().temperature)) #see note abot regarding labjack internal temp
        box_BT.update(RED,BLACK,'CT: {:#.1F}C'.format(1000*numpy.average(r['AIN{}'.format(CHANNEL_DICT['BT'])])))
        box_RH.update(BLACK,BLACK,'RH: {:#.2F}V'.format(numpy.average(r['AIN{}'.format(CHANNEL_DICT['RH'])])))
        box_O2.update(BLACK,BLACK,'O2: {:#.2F}V'.format(numpy.average(r['AIN{}'.format(CHANNEL_DICT['O2'])])))
        box_CO2.update(BLACK,BLACK,'CO2: {:#.2F}V'.format(numpy.average(r['AIN{}'.format(CHANNEL_DICT['CO2'])])))
        box_BPM.update(BLUE,WHITE,'BPM: {}'.format(avgBPM))
        if Mode_dict[Current_Mode]=='Challenge':
            if 60/avgRR>=baseHR*HR_recovery_thresh/100:
                box_HR_color=GREEN
            else:
                box_HR_color=RED
                
            if 60/avgTT>=baseBPM*BPM_recovery_thresh/100:
                box_BPM_color=GREEN
            else:
                box_BPM_color=RED
        else:
            box_HR_color=BLUE
            box_BPM_color=BLUE
        
        box_HR.update(box_HR_color,WHITE,'HR: {}'.format(avgHR))
        box_BPM.update(box_BPM_color,WHITE,'BPM: {}'.format(avgBPM))
        
        box_TV.update(BLUE,WHITE,'TV: {}'.format(avgTV))
        box_sincelastbreath.update(slb_COLOR2,slb_COLOR,'SLB: {:#.2F}sec'.format(SinceLastBreath))
    
                

        
          
    #% stream errors and exiting
    except Queue.Empty:
        print('empty Q')
        pass

    data1_graphed=graphScaler(g1_TL,g1_xySize,(ts1[0],ts1[-1]),g1_y_minmax,ts1[:],data1[:]) # resolution re-upscaled formerly [::2]
    baseline1_graphed=graphScaler(g1_TL,g1_xySize,(0,1),g1_y_minmax,[0,1],[baseline_flow,baseline_flow]) #update to baseline variable
    thresh1_graphed=graphScaler(g1_TL,g1_xySize,(0,1),g1_y_minmax,[0,1],[thresh_flow,thresh_flow]) #update to thresh variable
    thresh2flow_graphed=graphScaler(g1_TL,g1_xySize,(0,1),g1_y_minmax,[0,1],[thresh2_flow,thresh2_flow])

    baseline2_graphed=graphScaler(g2_TL,g2_xySize,(0,1),g2_y_minmax,[0,1],[baseline_vol,baseline_vol]) #update to baseline variable
    thresh2_graphed=graphScaler(g2_TL,g2_xySize,(0,1),g2_y_minmax,[0,1],[thresh_vol,thresh_vol]) #update to thresh variable

    
    data3_graphed=graphScaler(g3_TL,g3_xySize,(ts3[0],ts3[-1]),g3_y_minmax,ts3[::2],data3[::2]) #update this
    
    baseline3_graphed=graphScaler(g3_TL,g3_xySize,(0,1),g3_y_minmax,[0,1],[baseline_ecg,baseline_ecg]) #update to baseline variable
    thresh3_graphed=graphScaler(g3_TL,g3_xySize,(0,1),g3_y_minmax,[0,1],[absthresh_ecg,absthresh_ecg]) #update to thresh variable
##    

    d_graph1=pygame.draw.lines(DISPLAYSURF,BLUE,False,data1_graphed)
    base1=pygame.draw.lines(DISPLAYSURF,BLACK,False,baseline1_graphed)
    thresh1=pygame.draw.lines(DISPLAYSURF,RED,False,thresh1_graphed)
    thresh2flow=pygame.draw.lines(DISPLAYSURF,GREEN,False,thresh2flow_graphed)

    base2=pygame.draw.lines(DISPLAYSURF,BLACK,False,baseline2_graphed)
    thresh2=pygame.draw.lines(DISPLAYSURF,RED,False,thresh2_graphed)

    d_graph3=pygame.draw.lines(DISPLAYSURF,BLUE,False,data3_graphed)
    base3=pygame.draw.lines(DISPLAYSURF,BLACK,False,baseline3_graphed)
    thresh3=pygame.draw.lines(DISPLAYSURF,RED,False,thresh3_graphed)
    
    
    try:
        bc_points=graphScaler(g1_TL,g1_xySize,(ts1[0],ts1[-1]),g1_y_minmax,
                              [BreathCalls[i]['TS-I'] for i in BreathCalls],
                              [0 for i in BreathCalls]) #correct this for plotting timestamps on x-axis
    except:
        bc_points=[]
    if len(bc_points)!=0:
        bc_points_graphed=[]
        for p in bc_points:
            bc_points_graphed.append(pygame.draw.circle(DISPLAYSURF,Annot_Color,(int(p[0]),int(p[1])),5))

    try:
        hr_points=graphScaler(g3_TL,g3_xySize,(ts3[0],ts3[-1]),g3_y_minmax,
                          [i for i in BeatCalls if BeatCalls[i]],
                          [0 for i in BeatCalls]) #correct this for plotting timestamps on x-axis
    except:
        hr_points=[]
    if len(hr_points)!=0:
        hr_points_graphed=[]
        for p in hr_points:
            hr_points_graphed.append(pygame.draw.circle(DISPLAYSURF,GREEN,(int(p[0]),int(p[1])),5))

    if Mode_dict[Current_Mode]=='Finished' and Current_Mode!=prev_Mode:
        try:
            print('EXPERIMENT FINISHED')
            emailnotification(EMAIL_SETTINGS,d)
        except:
            print('unable to send notification')

    prev_Mode=int(Current_Mode)
    pygame.display.update()
    fpsClock.tick(FPS) # this needs to be faster than the labjack packet timer


print('exit received')
#% Wait for the stream thread to stop
try:
    sdrThread.join()
    arduino_stream.finished=True
except:
    print('no loose thread found')
# Close the device
d.setDIOState(0,0)
d.setDIOState(1,0)
d.setDIOState(2,0)
d.setDIOState(3,0)

d.close()
    
## close pygame
pygame.quit()

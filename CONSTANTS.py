"""
CONSTANTS.py

File containing all the constants defined for PCC, GUI and other python classes in this module
Divided by where they are used

"""



import pygame
from datetime import datetime

from gpiozero import CPUTemperature






##
#%% define constants/buffers/status-tags/customization-parameters
Mode_dict={0:'startup',
           1:'standby',
           2:'Signal Preview 1',
           3:'calibration',
           4:'Signal Preview 2',
           5:'Habituation-1',
           6:'Signal Preview 3',
           7:'Pre-Inject',
           8:'Inject',
           9:'Habituation-2',
           10:'Baseline',
           11:'Challenge',
           12:'Finished'}
Mode_timing={0:-1,
             1:-1,
             2:-1,
             3:60*2,
             4:-1,
             5:30*60,
             6:-1,
             7:10*60,
             8:-1,
             9:15*60,
             10:10*60,
             11:-1,
             12:-1}

savable_modes=[
    'calibration',
    'Habituation-1',
    'Pre-Inject',
    'Habituation-2',
    'Baseline',
    'Challenge'
    ]


Current_Mode=0 # start in first mode
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
Duration_Challenge_Delay_xySize=(200,25)
Text_Challenge_Phrase_xySize=(200,25)

Serial_Abort_xySize=(100,50)
Serial_Rec_OR_xySize=(100,50)
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

Challenge_phrase='Finished: On Anoxic'
Challenge_Timer=datetime.now()
Challenge_Delay=5

Position_RA_TL=(700,200)
Position_Gas_TL=(700,225)
Duration_Cal_TL=(700,250)
Duration_Prefill_TL=(700,275)
Position_Challenge_Delay_TL=(700,300)
Position_Challenge_Phrase_TL=(700,325)

Serial_Abort_TL=(650,350)
Serial_Rec_OR_TL=(750,350)
Serial_ShutDown_TL=(850,350)
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

INVERT_FLOW_TL=(200,880)
PLETHFILT_TL=(200,905)

ECGFILT_TL=(400,905)
INVERT_ECG_TL=(400,880)

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

baseline_increment = 5*60
baseline_override = 0
minimum_cummulative_QB_duration = 60
current_maximum_sustained_recovery_bout = 0

minimum_resus_time=5*60
current_minimum_resus_time=5*60

current_recovery=300
recovery_increment = 5*60
sustained_recovery = 60
minimum_sustained_recovery = 60
sustained_recovery_flag = 1
sustained_recovery_start = datetime.now()
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
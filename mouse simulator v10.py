# import modules
import RPi.GPIO as GPIO
import time

## setup pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(3, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(7, GPIO.IN)
#GPIO.setup(8, GPIO.IN)
#GPIO.setup(10, GPIO.IN)
#GPIO.setup(11, GPIO.IN)
##
p=0
e=0
hypbout=9000 #Duration of the hypercapnic breathing, begins with CO2 prefill step
hypbout_reset=9000 #Change as above
apbout=5000 #Duration of the apnea, immediately follows hypercapnic breathing
apbout_reset=5000 #Change as above
recbout=10000 #Length of recovery, will limit the start of the next challenge
recbout_reset=10000 #Change as above
statedict={'cal':{'pleth':300,'ecg':0},
           'low':{'pleth':500,'ecg':200},
           'normal':{'pleth':260,'ecg':90},
           'high':{'pleth':200,'ecg':75},
           'off1':{'pleth':0,'ecg':0},
           'off2':{'pleth':0,'ecg':0}
          }
curstate='normal'
prevstate=curstate
##
p=0
p_pin=True
while True:
    
        
    if curstate=='normal':
        if GPIO.input(7)==GPIO.HIGH:
            curstate='high'
    if curstate=='high':
        hypbout-=1
        if hypbout<=0:
            curstate='off1'
    if curstate=='off1':
        #if GPIO.input(11)==GPIO.HIGH:
            curstate='off2'
    if curstate=='off2':
        apbout-=1
        if apbout<=0:
            curstate='low'
    if curstate=='low':
        recbout-=1
        if recbout<=0:
            curstate='normal'
            #reset hyper and apnea counters
            hypbout=hypbout_reset
            apbout=apbout_reset
            recbout=recbout_reset
    if prevstate!=curstate:
        print(curstate)
    prevstate=curstate
    if p<=statedict[curstate]['pleth']/2: #and p_pin==False:
        GPIO.output(3,GPIO.HIGH)
        p_pin=True
    elif p>=statedict[curstate]['pleth']:
        p=0
    elif p>statedict[curstate]['pleth']/2: #and p_pin==True:
        GPIO.output(3,GPIO.LOW)
        p_pin=False
    if e<=10:
        GPIO.output(5,GPIO.HIGH)
    elif e>=statedict[curstate]['ecg']:
        e=0
    elif e>10:
        GPIO.output(5,GPIO.LOW)
    time.sleep(0.001)
    p+=1
    e+=1
    

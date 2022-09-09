# -*- coding: utf-8 -*-
"""
Selection Helper for Autoresuscitation Measurements (SHAM)
or
Automated Autoresuscitation Assay Analysis Helper (AAAH!)

For use with the Ray Lab automated autoresuscitation system and PCC software,
and Breathe Easy with BASSPRO and STAGG.

created by Christopher S Ward (C) 2022


=Features=
*intake breathlists and timestampes
*provide summary of basic parameters and challenge scoreboard
    *Baseline summary values (defined by baseline settings [any non challenge period])
        *Avg. VF
        *Avg. Breath Duration
        *Avg. VT
        *Avg. VT/g
        *Avg. VE
        *Avg. VE/g
        *Avg. HR
        *Avg. RR
    *Sub-challenge summary values 
     (prefill, exposure minus delay, early recovery, late recovery)
     [definitions needed for 'prefill', 'exposure minus delay', 'early recovery', 'late recovery']
        *Avg. VF
        *Avg. Breath Duration
        *Avg. VT
        *Avg. VT/g
        *Avg. VE
        *Avg. VE/g
        *Avg. HR
        *Avg. RR
    *Timestamp Challenge Start
    *Timestamp Exposure Start
    *Timestamp Apnea (Beginning of Breath)
    *Timestamp Apnea (+Trigger Duration)
    *Timestamp Recovery Gas
    *Timestamp post apnea gasps
    *Count post apnea gasps
    *Timestamp Recovery Gasp 1
    *Timestamp Recovery Gasp 2
    *Timestamp 1st Accum Recovery Start
    *Timestamp Consecutive Recovery Met
    *Timestamp Consecutive Recovery Start
    *Exposure Time (s)
    *Latency from Apnea to Recovery Gas
    *Apnea to 1st Gasp Latency (s)
    *1st Gasp Volume
    *1st Gasp Volume/g
    *1st Gasp to 2nd Gasp Latency (s)
    *2nd Gasp Volume
    *2nd Gasp Volume/g
    *Episode (s)
    *live vs post apnea discrepancy
    *latency from apnea/gasp to HR recovery (tunable) 
        (set threshold and which condition to use as baseline)
    *latency from apnea/gasp to VF recovery (tunable) 
        (set threshold and which condition to use as baseline)
    *Accumulated Recovery Latency (s)
    *Consecutive Recovery Latency (s)
    *# challenges survived
    
    tunable settings:
    minimum apnea duration:
    minimum apnea to gasp duration:
    prefill delay for hypervent phase: (0 starts at timestamp of gas start)
    early recovery starting breath: (0 starts at 1st gasp)
    condition to use for baseline:
    VF recovery threshold:
    HR recovery threshold:
    Consecutive Recovery Threshold:
    Accumulated Recovery Threshold:
    
    
    timestamp harmonizing settings:
    regex for...
    *condition
    *challenge start
    *exposure start
    *apnea detection
    *recovery gas start
    
    definitions of:
    'prefill': challenge start before gas exposure
    'exposure': challenge gas 
        [optionally trimmed from start of gas or before apnea]
    'early recovery': Nth breath after gasp until start of Accum/Consec Recov
    'late recovery': last 30sec before next challenge
    ''

"""

#%% import libraries

import pandas
import re



#%% define functions




#%% define main

def main():
    # gather settings
    
    # gather breathlist
    
    # gather beatlist
    
    # collect predefined timestamps
    
    # harmonize timestamps
    
    # identify derrived timestamps
    
    # generate summaries for non-challenge exp conditions
    
    # generate summaries for challenge conditions
    
    # create output excel-multitab or seperate csv
    
        # aggregate info 
        # (1 row per condition, each round of challenge is a condition)

#%% run main

if __name__ == '__main__':
    main()
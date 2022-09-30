# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 17:38:18 2022

tests for SHAM

@author: wardc
"""


import unittest
import pandas
import SHAM
import numpy

#%%
class TestRecovery():
    
    def __init__(self):
        
        
        
        
        # 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz,+
        # 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, 6s@1Hz,36s@2Hz, 6s@1Hz,6s@2Hz, +
        # 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, 6s@1Hz,6s@2Hz, +
        # 6s@1Hz,6s@2Hz
        
        
        t = 0
        breath_ts = []
        for i in range(13):
            if i !=6:
                breath_ts += list(numpy.arange(t+1,t+7,1))
                t = max(breath_ts)
                breath_ts += list(numpy.arange(t+1,t+7,0.5))
                t = max(breath_ts)
            else:
                breath_ts += list(numpy.arange(t+1,t+7,1))
                t = max(breath_ts)
                breath_ts += list(numpy.arange(t+1,t+36,0.5))
                t = max(breath_ts)
                breath_ts += list(numpy.arange(t+1,t+7,1))
                t = max(breath_ts)
        
        breath_bcd = [1]+[breath_ts[i+1]-breath_ts[i] for i in range(len(breath_ts)-1)]
        breath_vf = [60/i for i in breath_bcd]
        
        t = 0
        beat_ts = []
        for i in range(13):
            if i !=6:
                beat_ts += list(numpy.arange(t+1,t+5,1))
                t = max(beat_ts)
                beat_ts += list(numpy.arange(t+1,t+9,0.2))
                t = max(beat_ts)
            else:
                beat_ts += list(numpy.arange(t+1,t+7,1))
                t = max(beat_ts)
                beat_ts += list(numpy.arange(t+1,t+36,0.2))
                t = max(beat_ts)
                beat_ts += list(numpy.arange(t+1,t+7,1))
                t = max(beat_ts)
        
        beat_RR = [1]+[beat_ts[i+1]-beat_ts[i] for i in range(len(beat_ts)-1)]
        beat_HR = [60/i for i in beat_RR]
        
        
        
        self.Breath_List = pandas.DataFrame(
            {
                'Timestamp_Inspiration':breath_ts,
                'VF':breath_vf,
                'Breath_Cycle_Duration':breath_bcd
                }
            )
            
        self.Beat_List = pandas.DataFrame(
            {
                'ts':beat_ts,
                'HR':beat_HR,
                'RR':beat_RR
                }
            )
    
    
        self.Breath_Recovery_Filter = SHAM.multi_filter(
            self.Breath_List,
            'Timestamp_Inspiration',
            {
                'start':(
                    'Timestamp_Inspiration',
                    'ge',
                    3
                    ),
                'end':(
                    'Timestamp_Inspiration',
                    'l',
                    190
                    ),
                'VF':(
                    'VF',
                    'ge',
                    100
                    )
                }
            )
        
        self.Beat_Recovery_Filter = SHAM.multi_filter(
            self.Beat_List,
            'ts',
            {
                'start':(
                    'ts',
                    'ge',
                    3
                    ),
                'end':(
                    'ts',
                    'l',
                    190
                    ),
                'HR':(
                    'HR',
                    'ge',
                    100
                    )
                }
            )
    

    def accum_recovery_test(self):
        self.accum_Filter = SHAM.resample_and_merge_filters(
            self.Breath_Recovery_Filter,
            self.Breath_Recovery_Filter,
            0.001,
            5
            )[0]
        
        self.consec_Filter = SHAM.resample_and_merge_filters(
            self.Breath_Recovery_Filter,
            self.Breath_Recovery_Filter,
            0.001,
            30
            )[0]
        
        self.accum_ts = SHAM.get_ts_for_accumulated_value(
            self.Breath_List, 
            self.accum_Filter, 
            'Breath_Cycle_Duration',
            30,
            'Timestamp_Inspiration'
            )

        self.consec_ts = SHAM.get_ts_for_accumulated_value(
            self.Breath_List, 
            self.consec_Filter, 
            'Breath_Cycle_Duration',
            30,
            'Timestamp_Inspiration'
            )    
    
        print(self.accum_ts,self.consec_ts)
        
    def consec_recovery_test():
        pass


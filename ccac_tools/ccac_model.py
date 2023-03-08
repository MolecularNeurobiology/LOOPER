# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 23:15:40 2023

@author: wardc
"""

__version__  = '1.0.0'
__license__ = 'MIT license'


#%% import modules/libraries
from dataclasses import dataclass


@dataclass
class ccac_model:
    logger: None = None
    input_file_list: list = None
    output_folder_list: list = None
    delete_flag: bool = False
    good_copy_dict: dict = None
    

    
    def refresh_good_copy_dict(self):
        for i in self.input_file_list:
            if i not in self.good_copy_dict:
                self.good_copy_dict[i] = [None]
    
    def reset_model(self):
        self.input_file_list = []
        self.output_folder_list = []
        self.delete_flag = False
        self.good_copy_dict = {}
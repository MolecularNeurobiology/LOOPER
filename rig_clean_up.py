# -*- coding: utf-8 -*-
"""
Raspberry Pi, Autores Rig Clean Up Script

Created on Tue May  7 10:32:29 2024

@author: wardc
"""


#%% import libraries
import fm_tools
import os
import sys
import logging
import datetime
import json
import re

#%% define functions
def extract_ruid(filename):
    """
    Extracts ruid information from a filename provided in
    YYMMDD_RUID.txt format.

    Parameters
    ----------
    filename : str
        Filename, expected as RUID.txt format with anything surrounding the RUID.

    Returns
    -------
    ruid : str or None
        Extracted RUID if present in the filename, None otherwise.
    """
    
    # Extracts RUID from anywhere in the filename to allow for maximum flexibility in possible naming conventions.
    ruid_re = re.compile(r'.*(?P<ruid>[rR][0-9]*).*')
    match = ruid_re.match(filename)
    if match:
        return match.group(1)  # Return the matched RUID
    else:
        # Log or handle cases where the filename does not match the expected format
        return None  # Indicates that RUID was not found or filename format is incorrect


#%% define main

def main():
    # generate log file
    logger = logging.getLogger('rig_clean_up')
    logger_output_path = os.path.join(
        '/home/pi/',f'rig_cleanup_{datetime.datetime.now().strftime("%Y-%m-%d")}'
    )

    file_handler = logging.FileHandler(logger_output_path)
    console_handler = logging.StreamHandler(sys.stdout)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info('logging started')
    
    
    # collect config settings needed for fmp access and storage path
    config_path = '/home/pi/rig.config'
    with open(config_path,'r') as openfile:
        config = json.load(openfile)
    
    credentials = {
        'ip':config.get("SERVER_IP"),
        'user':config.get("USER"),
        'password':config.get("PASSWORD")
    }
    
    
    # map local storage
    config_path = '/home/pi/rig.config'
    with open(config_path,'r') as openfile:
        config = json.load(openfile)
        
    local_storage_path = os.path.join(
        "/media/pi",
        config["RIGNAME"]
    )
    
    walker = os.walk(local_storage_path)
    filedict = {}
    for d,p,f in walker:
        for filename in f:
            filedict[os.path.join(d,filename)] = filename
       

    # build list of RUIDS
    ruid_list = [extract_ruid(v) for k,v in filedict.items()]
    logger.info(f'{len(ruid_list)} files found')
    
    
    fmp_query_by_ruid = [
        {'RUID':i} for i in ruid_list
        ]

    # query FMP for records ready to delete (consider changing to query based on RUID's in found files)
    # records_to_delete = fm_tools.pull_filtered_records(
    #     credentials,
    #     "MICE",
    #     "Autoresuscitation",
    #     [{'DeleteRecord':"Yes"}],
    #     ['RUID','DeleteRecord']
    # )
    
    records = fm_tools.pull_filtered_records(
        credentials,
        "MICE",
        "Autoresuscitation",
        fmp_query_by_ruid,
        ['RUID','DeleteRecord']
    )
    
    logger.info(f'{len(records)} fmp records found related to files')
    
    # build set of files ready to delete
    records_to_delete = [
        v['RUID'] for k,v in records if v['DeleteRecord']=='Yes'
    ]
    
    logger.info(f'{len(records_to_delete)} files ready to delete')
    
    # delete files
    for k,v in filedict:
        if extract_ruid(v) in records_to_delete:
            if os.path.exists(k):
                os.remove(k)
                logger.info(f'deleted {v} at {k}')
    
    logger.info('finished')
    


#%% run main

if __name__ == "__main__":
    main()
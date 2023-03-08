# -*- coding: utf-8 -*-
"""
CopyConfirmAndClear

Created on Fri Mar  4 11:21:31 2022
@author: wardc

recommend running on python 3.8+ if on windows, should otherwise work on linux
"""

__version__ = '1.1.0'



#%% import libraries
import argparse
import shutil
import hashlib
import os
import logging
import sys

#%% define functions

def setup_logger(gui_handler = None):
    logger = logging.getLogger('ccac')
    logger.setLevel(logging.DEBUG)
    
    # create format for log and apply to handlers
    log_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    return logger

        

def copy_to_multiple(input_file, output_paths, logger = None):
    """
    

    Parameters
    ----------
    input_file : string
        path to file needing backup
    output_paths : string
        path to folder to deposit file backup
    logger : logging object [optional]
        logging object used to pass status information

    Returns
    -------
    None.

    """
    # copy file
    for p in output_paths:
        shutil.copy2(
            input_file,
            os.path.join(
                p,
                os.path.basename(input_file)
                )
            )

        
        
    

def compare_checksums(input_file, output_paths, logger = None):
    """
    

    Parameters
    ----------
    input_file : string
        path to file needing backup
    output_paths : string
        path to folder to deposit file backup
    logger : logging object [optional]
        logging object used to pass status information

    Returns
    -------
    None.

    """
    Good_Copy_Flags=[]
    orig_md5 = hashlib.md5()
    with open(input_file,'rb') as openfile:
        while True:
            data = openfile.read(65536)
            if not data:
                break
            orig_md5.update(data)
    if logger: logger.info(f'i_md5: {orig_md5.hexdigest()}')
    
    for p in output_paths:
        p_md5 = hashlib.md5()
        with open(
                os.path.join(
                    p,
                    os.path.basename(input_file)
                    ),
                'rb'
                ) as openfile:
            while True:
                data = openfile.read(65536)
                if not data:
                    break
                p_md5.update(data)
        if logger: logger.info(f'-o {p}\no_md5: {p_md5.hexdigest()}')
        Good_Copy_Flags.append(orig_md5.hexdigest()==p_md5.hexdigest())
    return Good_Copy_Flags
    
    
    
def finalize_ccac(
        good_copy, 
        delete_flag, 
        input_file, 
        output_paths, 
        logger = None
    ):
    
    if all(good_copy):
        if logger: logger.info('all copies are good')
        if delete_flag == True:
            if logger: logger.info('deleting original file')
            os.remove(input_file)
            return 'file backed up, original deleted'
        else:
            return 'file backed up, original still in place'
        
    else:
        if logger: logger.info('at least one copy failed')
        if logger: logger.info(f'{zip(output_paths,good_copy)}')
        if delete_flag == True:
            if logger: logger.info(
                    'unable to delete original file due to failed transfer'
                    )
    

#%% define main

def main():
    parser = argparse.ArgumentParser(description='CCaC')
    parser.add_argument(
        '-i', help='Path containing file for input'
        )
    parser.add_argument(
        '-o', 
        action='append', 
        help='Path to output location' + \
            '-declare multiple times to build a list of files'
        )
    parser.add_argument(
        '-d', 
        action = 'store_true',
        help='flag indicating to delete file if copy confirmed'
        )
    
    args, others = parser.parse_known_args()
    
    # if arguments are incomplete, then request from user
    if args.i is None:
        print('"i" is empty')
        input_file = input('select input file\n')
    else:
        print(args.i)
        input_file = args.i
        
    if args.o is None:
        print('"o" is empty')
        output_paths = input(
            'select output paths (comma delimit)\n'
            ).split(',')
    else:
        output_paths = []
        for p in args.o:
            output_paths.append(p)
            
    if args.d is None:
        delete_flag = False
    else:
        delete_flag = args.d

    # setup logger
    logger = setup_logger()
    logger.info(f'i: {input_file}')
    logger.info(f'o: {output_paths}')
    logger.info(f'd: delete flag {delete_flag}')
    

    # copy file
    copy_to_multiple(input_file, output_paths, logger = logger)
    
    # compare checksums
    good_copy = compare_checksums(input_file, output_paths, logger = logger)
    
    # clear files if applicable and report status
    exit_status = finalize_ccac(
        good_copy, 
        delete_flag, 
        input_file, 
        output_paths, 
        logger = logger
    )
    
    logger.info(exit_status)
        
if __name__ == '__main__':
    main()
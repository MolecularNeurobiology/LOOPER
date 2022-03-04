# -*- coding: utf-8 -*-
"""
CopyConfirmAndClear

Created on Fri Mar  4 11:21:31 2022
@author: wardc

recommend running on python 3.8+ if on windows, should otherwise work on linux
"""

#%% import libraries
import argparse
import shutil
import hashlib
import os

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

    # get orig file checksum
    orig_md5 = hashlib.md5()
    with open(input_file,'rb') as openfile:
        while True:
            data = openfile.read(65536)
            if not data:
                break
            orig_md5.update(data)
    print(orig_md5.hexdigest())


    Good_Copy_Flags=[]
    # copy file
    for p in output_paths:
        shutil.copy2(
            input_file,
            os.path.join(
                p,
                os.path.basename(input_file)
                )
            )
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
        print(p_md5.hexdigest())
        Good_Copy_Flags.append(orig_md5.hexdigest()==p_md5.hexdigest())
        
    if all(Good_Copy_Flags):
        print('all copies are good')
        if delete_flag == True:
            os.remove(input_file)
            print('deleting original file')
        
    else:
        print('at least one copy failed')
        print(zip(output_paths,Good_Copy_Flags))
        if delete_flag == True:
            print('unable to delet original file due to failed transfer')
        
if __name__ == '__main__':
    main()
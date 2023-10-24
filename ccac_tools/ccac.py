# -*- coding: utf-8 -*-
"""
CopyConfirmAndClear

Created on Fri Mar  4 11:21:31 2022
@author: wardc

recommend running on python 3.8+ if on windows, should otherwise work on linux
"""

__version__ = "1.3.1"


# %% import libraries
import argparse
import shutil
import hashlib
import os
import logging
import sys
import traceback
import pandas

# %% define functions


def setup_logger(gui_handler=None):
    logger = logging.getLogger("ccac")
    logger.setLevel(logging.DEBUG)

    # create format for log and apply to handlers
    log_format = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    return logger


def copy_to_multiple(input_file, output_paths, logger=None):
    """


    Parameters
    ----------
    input_file : string
        path to file needing backup
    output_paths : list of strings
        list of paths to folder to deposit file backup
    logger : logging object [optional]
        logging object used to pass status information

    Returns
    -------
    None.

    """
    # copy file
    try:
        for i, p in enumerate(output_paths):
            if logger:
                logger.info(
                    f"copy {i+1} of {len(output_paths)}: "
                    + f"copying {os.path.basename(input_file)} to {p}..."
                )
            shutil.copy2(
                input_file, os.path.join(p, os.path.basename(input_file))
            )
            if logger:
                logger.info("...copy completed")
    except Exception as e:
        if logger:
            logger.exception(
                f"unable to perform copy: {e} :{traceback.format_exception}"
            )


def compare_checksums(input_file, output_paths, logger=None):
    """


    Parameters
    ----------
    input_file : string
        path to file needing backup
    output_paths : list of strings
        path to folder to deposit file backup
    logger : logging object [optional]
        logging object used to pass status information

    Returns
    -------
    None.

    """
    Good_Copy_Flags = []
    orig_md5 = hashlib.md5()
    try:
        if logger:
            logger.info(
                f"checking copies of file: {os.path.basename(input_file)}"
            )

        with open(input_file, "rb") as openfile:
            while True:
                data = openfile.read(65536)
                if not data:
                    break
                orig_md5.update(data)
        if logger:
            logger.info(f"  i_md5: {orig_md5.hexdigest()}")

        for p in output_paths:
            p_md5 = hashlib.md5()
            with open(
                os.path.join(p, os.path.basename(input_file)), "rb"
            ) as openfile:
                while True:
                    data = openfile.read(65536)
                    if not data:
                        break
                    p_md5.update(data)

            if logger:
                logger.info(f"  o_md5: {p_md5.hexdigest()}    -o {p}")
            Good_Copy_Flags.append(orig_md5.hexdigest() == p_md5.hexdigest())
    except Exception as e:
        if logger:
            logger.exception(
                f"unable to perform check: {e} :{traceback.format_exception}"
            )

        Good_Copy_Flags.append(False)

    return Good_Copy_Flags


#%%
def crawl_and_compare(*input_dir,output_dir = None,logger = None):
    # if input_dir is single path,
    # its contents should be checked against output_dir
    # if input_dir is multiple paths, each folder is expected to be a 
    # subfolder in output_dir
    
    logger.info('starting crawl and compare')
    
    if not output_dir:
        if logger: logger.exception('no target location specified')
        return
    
    input_dict = {}
    
    for i in input_dir:
        for d,p,f in os.walk(i):
            for filename in f:
                input_dict[
                    os.path.join(d,filename)[len(i):]
                ] = os.path.join(d,filename)
                
    output_dict = {}
    for d,p,f in os.walk(output_dir):
        for filename in f:
            output_dict[
                os.path.join(d,filename)[len(output_dir):]
            ] = os.path.join(d,filename)
    
    input_set = set(input_dict.keys())
    output_set = set(output_dict.keys())
    
    files_in_both = {
        k:{'i':input_dict[k],'o':output_dict[k]} for k in 
        input_set.intersection(output_set)
    }
    files_in_input_not_output = {
        k:{'i':input_dict[k]} for k in 
        input_set.difference(output_set)
    }
    files_in_output_not_intput = {
        k:{'o':output_dict[k]} for k in 
        output_set.difference(input_set)    
    }
    
    files_in_both_good_hash = {}
    files_in_both_bad_hash = {}
    files_in_both_not_testable = {}
    
    for k in files_in_both:    
        if logger:
            logger.info(
                f"checking copies of file: {k}"
            )
        input_md5 = hashlib.md5()
        output_md5 = hashlib.md5()
        
        try:
            with open(input_dict[k], "rb") as openfile:
                while True:
                    data = openfile.read(65536)
                    if not data:
                        break
                    input_md5.update(data)
        
            with open(output_dict[k], "rb") as openfile:
                while True:
                    data = openfile.read(65536)
                    if not data:
                        break
                    output_md5.update(data)
            input_hash = input_md5.hexdigest()
            output_hash = output_md5.hexdigest()
            
            if input_hash == output_hash:
                files_in_both_good_hash[k] = {
                    'i':input_dict[k], 'o':output_dict[k], 'md5':input_hash
                }
            else:
                files_in_both_bad_hash[k] = {
                    'i':input_dict[k], 'o':output_dict[k], 
                    'md5-i':input_hash, 'md5-o':output_hash
                }
        
        except Exception as e:
            if logger:
                logger.exception(
                    f"unable to perform check: {e} :{traceback.format_exception}"
                )
                files_in_both_not_testable[k] = {
                    'i':input_dict[k], 'o':output_dict[k]
                }
    if logger:
        logger.info('finished crawl and compare')
    return {
        'both-good':files_in_both_good_hash,
        'both-bad':files_in_both_bad_hash,
        'both-notest':files_in_both_not_testable,
        'input_only':files_in_input_not_output,
        'output_only':files_in_output_not_intput        
    }
    


def export_crawl_and_compare_results(cac_results,output_path,logger=None):
    with pandas.ExcelWriter(output_path) as writer:
        pandas.DataFrame(
            cac_results['both-good']).transpose().rename_axis('file').to_excel(
                writer, sheet_name = 'both-good'
            )
        pandas.DataFrame(
            cac_results['both-bad']).transpose().rename_axis('file').to_excel(
                writer, sheet_name = 'both-bad'
            )
        pandas.DataFrame(
            cac_results['both-notest']).transpose().rename_axis('file').to_excel(
                writer, sheet_name = 'both-notest'
            )
        pandas.DataFrame(
            cac_results['input_only']).transpose().rename_axis('file').to_excel(
                writer, sheet_name = 'input_only'
            )
        pandas.DataFrame(
            cac_results['output_only']).transpose().rename_axis('file').to_excel(
                writer, sheet_name = 'output_only'
            )
    if logger:
        logger.info('Crawl and Compare Results Exported')

    
#%% 
    
    


def finalize_ccac(
    good_copy, delete_flag, input_file, output_paths, logger=None
):
    if os.path.dirname(input_file) in output_paths:
        return "WARNING - COPY LOCATION THE SAME AS ORIGINAL LOCATION"

    elif all(good_copy):
        if logger:
            logger.info("all copies are good")
        if delete_flag is True:
            if logger:
                logger.info("deleting original file")
            os.remove(input_file)
            return "file backed up, original deleted"
        else:
            return "file backed up, original still in place"

    else:
        if logger:
            logger.warning("at least one copy failed")
        if logger:
            logger.warning(f"{zip(output_paths,good_copy)}")
        if delete_flag is True:
            if logger:
                logger.warning(
                    "unable to delete original file due to failed transfer"
                )
            return "error at least one copy failed to correctly transfer"


# %% define main


def main():
    parser = argparse.ArgumentParser(description="CCaC")
    parser.add_argument("-i", help="Path containing file for input")
    parser.add_argument(
        "-o",
        action="append",
        help="Path to output location"
        + "-declare multiple times to build a list of files",
    )
    parser.add_argument("-r", help="number of times to retry copying")
    parser.add_argument(
        "-d",
        action="store_true",
        help="flag indicating to delete file if copy confirmed",
    )

    args, others = parser.parse_known_args()

    # if arguments are incomplete, then request from user
    if args.i is None:
        print('"i" is empty')
        input_file = input("select input file\n")
    else:
        print(args.i)
        input_file = args.i

    if args.o is None:
        print('"o" is empty')
        output_paths = input("select output paths (comma delimit)\n").split(
            ","
        )
    else:
        output_paths = []
        for p in args.o:
            output_paths.append(p)

    if args.r is None:
        retry_limit = 0
    else:
        retry_limit = args.r

    if args.d is None:
        delete_flag = False
    else:
        delete_flag = args.d

    # setup logger
    logger = setup_logger()
    logger.info(f"i: {input_file}")
    logger.info(f"o: {output_paths}")
    logger.ingo(f"r: retry limit {retry_limit}")
    logger.info(f"d: delete flag {delete_flag}")

    # copy file
    copy_to_multiple(input_file, output_paths, logger=logger)

    # compare checksums
    good_copy = compare_checksums(input_file, output_paths, logger=logger)

    # retry if bad copy
    retry_counter = 0
    while retry_counter < retry_limit:
        if all(good_copy):
            break
        elif len(good_copy) != len(output_paths):
            logger.info(
                f"bad copy detected, retrying {retry_counter}" +
                f" of {retry_limit} possible times"
            )
            # copy file
            copy_to_multiple(input_file, output_paths, logger=logger)
            # compare checksums
            good_copy = compare_checksums(
                input_file, output_paths, logger=logger
            )

        else:
            for i, retry_path in enumerate(output_paths):
                if not good_copy[i]:
                    copy_to_multiple(input_file, [retry_path], logger=logger)
                    good_copy[i] = compare_checksums(
                        input_file, [retry_path], logger=logger
                    )

        retry_counter += 1

    # clear files if applicable and report status
    exit_status = finalize_ccac(
        good_copy, delete_flag, input_file, output_paths, logger=logger
    )

    logger.info(exit_status)


if __name__ == "__main__":
    main()

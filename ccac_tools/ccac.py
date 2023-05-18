# -*- coding: utf-8 -*-
"""
CopyConfirmAndClear

Created on Fri Mar  4 11:21:31 2022
@author: wardc

recommend running on python 3.8+ if on windows, should otherwise work on linux
"""

__version__ = "1.2.0"


# %% import libraries
import argparse
import shutil
import hashlib
import os
import logging
import sys
import traceback

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
    output_paths : string
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

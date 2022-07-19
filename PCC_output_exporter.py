# -*- coding: utf-8 -*-
"""
PCC output extracter

Created on Tue Feb  1 14:07:56 2022

@author: wardc
"""

#%% import libraries
##

import tkinter
import tkinter.filedialog
import pandas
import logging
import sys
import re


#%% define functions
##

def gui_open_filenames(kwargs={}):
    """
    Returns the path to the file selected by the GUI.
    *Function calls on tkFileDialog and uses those arguments
      ......
      (declare as a dictionairy)
      {"defaultextension":'',"filetypes":'',"initialdir":'',...
      "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
      ......
    """

    root = tkinter.Tk()
    output_text = tkinter.filedialog.askopenfilenames(
        **kwargs)
    root.destroy()
    return output_text


# def load_signal_data(filename, local_logger):
#     """
#     creates a dataframe containing plethysmography signal data
#     includes calls to several other functions that are required for proper
#     parsing of an exported lab chart signal file

#     Parameters
#     ----------
#     filename : string
#         path to file containing signal data
#     local_logger : instance of logging.logger


#     Returns
#     -------
#     signal_data_assembled : pandas.DataFrame
#         dataframe containing contents of signal file (merged into a single
#         dataframe if multiple blocks are present)
#     """
    
#     Header_Tuples = extract_header_type(filename)
#     header_locations = extract_header_locations(
#         filename,
#         local_logger=local_logger
#         )
#     signal_data_pieces = read_exported_labchart_file(
#         filename,
#         header_locations,
#         header_tuples=Header_Tuples
#         )
#     signal_data_assembled = merge_signal_data_pieces(signal_data_pieces)
#     return signal_data_assembled


# def extract_header_type(filename):
#     """
#     gathers information regarding the header format/column contents present
#     in an exported lab chart signal file (assumes set-up is in line with
#     Ray Lab specifications)

#     Parameters
#     ----------
#     filename : string
#         path for file containing signal data

#     Returns
#     -------
#     header_tuples : list of tuples
#         list of tuples specifying ([column name],[datatype])
#     """
    
#     with open(filename) as opfi:
#         # check 1st ten rows to see if header is expected to include
#         # date column with data
#         for i in range(10):
#             if "DateFormat=	M/d/yyyy" in opfi.readline():
#                 header_tuples = [
#                    ('ts', float),
#                    ('date', str),
#                    ('vol', float),
#                    ('o2', float),
#                    ('co2', float),
#                    ('temp', float),
#                    ('ch5', float),
#                    ('ch6', float),
#                    ('ch7', float),
#                    ('ch8', float),
#                    ('comment', str)
#                    ]
#                 break
#             else:
#                 header_tuples = [
#                    ('ts', float),
#                    ('vol', float),
#                    ('o2', float),
#                    ('co2', float),
#                    ('temp', float),
#                    ('ch5', float),
#                    ('ch6', float),
#                    ('ch7', float),
#                    ('ch8', float),
#                    ('comment', str)
#                    ]
#     return header_tuples


def extract_header_locations(
        filename,
        header_text_firstline_fragment = '$$$',
        header_text_lastline_fragment = 'statuscodes',
        local_logger = None):
    """
    gathers information regarding the locations of header information
    throughout a signal file - needed if files may contain multiple recording
    blocks

    Parameters
    ----------
    filename : string
        path to file containing signal data
    header_text_firstline_fragment : string, optional
        string that is present at beginning of header lines. The default is '$$$'.
    header_text_lastline_fragment : string, optional
        string that is present at end of header lines. The default is 'status_codes'.
    local_logger : instance of logging.logger, optional
        The default is None (i.e. no logging)

    Returns
    -------
    headers_firstlines : list
        list of rows in the datafile that indicate header content present (first line)
    headers_lastlines : list
        list of rows in the datafile that indicate header content present (last line)
        
    """
    
    headers_firstlines = []
    headers_lastlines = []
    i = 0
    with open(filename, 'r') as opfi:
        for line in opfi:
            if header_text_firstline_fragment in line:
                if local_logger != None:
                    local_logger.info(
                        'Signal File has FL HEADER AT LINE: {}'.format(i)
                        )
                headers_firstlines.append(i)
            if header_text_lastline_fragment in line:
                if local_logger != None:
                    local_logger.info(
                        'Signal File has LL HEADER AT LINE: {}'.format(i)
                        )
                headers_lastlines.append(i)
            i += 1
            
        headers = [(headers_firstlines[j+1],headers_lastlines[j]) for j in range(len(headers_lastlines))]
    return headers


def read_exported_labchart_file(
        lc_filepath,
        header_locations,
        header_tuples,
        delim='\t',
        rows_to_skip=16,
        local_logger=None
        ):
    """
    collects data from an exported lab chart file and returns a list of
    dataframes (in order) containing the extracted contents of the signal file

    Parameters
    ----------
    lc_filepath : string
        path to file containing signal data
    header_locations : list of integers
        list describing the locations of headers throughout a signal file
    header_tuples : list of tuples
        list of tuples specifying ([column name],[datatype])
    delim : string, optional
        delimiter used. The default is '\t'.
    rows_to_skip : integer, optional
        the number of rows present in the header that should be skipped
        to get to the location containing data. The default is 6.

    Returns
    -------
    df_list : list of pandas.DataFrames
        list of dataframes containing signal data

    """
    df_list = []

    for i in range(len(header_locations)):
        
        if local_logger != None:
            local_logger.info(
                'Extracting Data Block AT LINE: {}'.format(header_locations[i])
                )
        
        # case if only one header
        if len(header_locations) == 1:
            df_list.append(
                pandas.read_csv(
                    lc_filepath,
                    sep=delim,
                    names=[i[0] for i in header_tuples],
                    skiprows=rows_to_skip+header_locations[i],
                    dtype=dict(header_tuples)
                    )
                )
        else:
            # case if not last section
            if i+1 < len(header_locations):
                df_list.append(
                    pandas.read_csv(
                        lc_filepath,
                        sep=delim,
                        names=[i[0] for i in header_tuples],
                        skiprows=rows_to_skip+header_locations[i],
                        nrows=header_locations[i+1]-header_locations[i]-rows_to_skip,
                        dtype=dict(header_tuples)
                        )
                    )
            # case if last section of multisection file
            else:
                df_list.append(
                    pandas.read_csv(
                        lc_filepath,
                        sep=delim,
                        names=[i[0] for i in header_tuples],
                        skiprows=rows_to_skip+header_locations[i],
                        dtype=dict(header_tuples)
                        )
                    )
    return df_list


def merge_signal_data_pieces(df_list):
    """
    merges multiple blocks contained in a list of dataframes into a single
    dataframe (current behavior will override timestamp information to
    place subsequent blocks of data using the next sequential timestamp)

    Parameters
    ----------
    df_list : list of pandas.DataFrames
        list of dataframes containing signal data

    Returns
    -------
    merged_data : pandas.DataFrame
        dataframe containing signal data

    """
    # merge into single dataframe
    merged_data = pandas.DataFrame()
    for piece_number in range(len(df_list)):
        if piece_number != 0:
            # revise timestamp so that multiblock data fit into the next
            # consecutive timestamp - labchart file may reset each block to 0
            # or each block may track time relative to experiment start
            ts_minus = df_list[piece_number]['ts'].min()
            ts_add = df_list[piece_number-1]['ts'].max() + \
                df_list[0]['ts'][2]-df_list[0]['ts'][1]
        else:
            ts_minus = 0
            ts_add = 0
        df_list[piece_number].loc[:, 'ts'] = df_list[piece_number]['ts'] + \
            ts_add - ts_minus
        merged_data = merged_data.append(
            df_list[piece_number], ignore_index=True
            )
    return merged_data




#%% main
##

def main():
    
    #%%
    ##
    logger = logging.getLogger('PCC Output Extractor')
    logger.setLevel(logging.DEBUG)

    # create file and console handlers to receive logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # create format for log and apply to handlers
    log_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
    console_handler.setFormatter(log_format)
    
    # add handlers to the logger
    logger.addHandler(console_handler)
    
    #%% select file to extract
    input_files = gui_open_filenames({'title':'select file to extract'})
    
    for input_file in input_files:
        try:
            # log initial inputs
            logger.info(f'file selected {input_file}')
            
            # setup some constants (!!! move these to settings file, or set dynamcally if possible)
            # recognized_headers = [
            #     'PLETHYSMOGRAPHY COMMAND CENTER DATA FILE',
            #     'file may contain mutliple sessions, session marker : $$$$$',
            #     'file created',
            #     '$$$$$ DATA SESSION -----',
            #     'SESSION STARTED',
            #     'baseline flow:',
            #     'thresh flow:',
            #     'baseline_ecg:',
            #     'absthresh_ecg',
            #     'thresh_ecg1:',
            #     'thresh_ecg2:',
            #     'noise_ecg:',
            #     'HR_recovery_thresh:',
            #     'minimum_resus_time',
            #     'recovery_increment',
            #     'SLB_Trigger:',
            #     'CALL_DEATH_Trigger',
            #     'QB_minimum_duration',
            #     'filt_crit_Dict:'
            #     ]
            
           
            
            #%% extract the file
            signal_blocks = extract_header_locations(input_file,local_logger=logger)
            try:
                signal_data_pieces = read_exported_labchart_file(
                    input_file,
                    [i[0] for i in signal_blocks],
                    header_tuples=[
                        ('time',float),
                        ('FLOW',float),
                        ('ECG',float),
                        ('BT',float),
                        ('RH',float),
                        ('O2',float),
                        ('CO2',float),
                        ('labjack_temp',float),
                        ('mode_block',str),
                        ('parameter',str),
                        ('arduino_comments',str)
                        ],
                    rows_to_skip = signal_blocks[0][1]-signal_blocks[0][0]+1
                    )
            except Exception as e:
                logger.exception(
                    f'error processing file {input_file} - {e}...attempting repair of split comments',
                    exc_info=True
                    )
                data = []
                with open(input_file,'r') as opfi:
                    for line in opfi.readlines():
                       data.append(line)
                
                fixed_rows = 0
                for i in range(len(data)):
                    row = data[i-fixed_rows]           
                    if any([h in row for h in recognized_headers]):
                        continue
                    if len(row.split('\t'))<10 and row.split('\t')[-1]!='\n':
                        logger.info(f'bad row found at index {i} - {row}')
                        data[i-fixed_rows-1] = \
                            data[i-fixed_rows-1][:-1] + data.pop(i-fixed_rows)
                        fixed_rows += 1
                
                with open(input_file+'_fixed.txt','w') as opfi:
                    for line in data:
                        opfi.write(line)
                
                signal_data_pieces = read_exported_labchart_file(
                    input_file+'_fixed.txt',
                    [i[0] for i in signal_blocks],
                    header_tuples=[
                        ('time',float),
                        ('FLOW',float),
                        ('ECG',float),
                        ('BT',float),
                        ('RH',float),
                        ('O2',float),
                        ('CO2',float),
                        ('labjack_temp',float),
                        ('mode_block',str),
                        ('parameter',str),
                        ('arduino_comments',str)
                        ],
                    rows_to_skip = signal_blocks[0][1]-signal_blocks[0][0]+1
                    )
            
            signal_header_pieces = [
                pandas.read_csv(
                    input_file,
                    sep = '\t',
                    names=[
                        'time',
                        'FLOW',
                        'ECG',
                        'BT',
                        'RH',
                        'O2',
                        'CO2',
                        'labjack_temp',
                        'mode_block',
                        'parameters',
                        'arduino_comments'
                        ],
                    skiprows=i[0],
                    nrows=i[1]-i[0]+2,
                    dtype = dict([
                        ('time',str),
                        ('FLOW',str),
                        ('ECG',str),
                        ('BT',str),
                        ('RH',str),
                        ('O2',str),
                        ('CO2',str),
                        ('labjack_temp',str),
                        ('mode_block',str),
                        ('parameter',str),
                        ('arduino_comments',str)
                        ])
                    ) for i in signal_blocks
                ]
            signal_start_pieces = [
                i.time.iloc[1] for i in signal_header_pieces
                ]
            signal_mode_pieces = [
                i.mode_block.iloc[-1] for i in signal_header_pieces
                ]
            
            
            recognized_commands_re = [
                'Starting: Calibrating for 0s',
                'Finished: Calibrating',
                'Starting: On Anoxic Air,0,0,Ongoing: On Position ,0, Prefilled for 0s',
                'Starting: On Anoxic Air,Prefill for 0s,Ongoing: On Position 0, Prefilled for 0s',
                'Finished: On Position ,0, Prefilled for 0s,Finished: On Anoxic Air',
                'Finished: On Position 0, Prefilled for 0s,Finished: On Anoxic Air',
                'Starting: On Room Air,0,0,Ongoing: On Position ,0, Gas Off',
                'Starting: On Room Air,Prefill for 0s,Ongoing: On Position 0, Gas Off',
                'Finished: On Room Air',
                'Finished: On Room Air,ABORTED'
                '0'
                ]    
        
        
            for i in range(len(signal_data_pieces)):
                broken_comment_index_1 = 0
                arduino_comment_list = []
                logger.info(
                    f'checking for fragmented commands:\n {i} {signal_mode_pieces[i]}'
                    )
                arduino_comment_list = \
                    signal_data_pieces[i]['arduino_comments'].fillna('')
                
                for j in range(len(arduino_comment_list)):
                    
                    c = arduino_comment_list[j]
                    if c == '':
                        continue
                    # adjust arduino comment list to accomodate custom timings
                    re_c = re.sub('[0-9]+','[0-9]+',c)
                    
                    if any([re.compile('^'+re_c+'$').search(k) for k in recognized_commands_re]):
                        logger.info(f'Found: {c}')
                    else:
                        logger.info(f'unrecognized arduino com:\n{c}')
                        for k in recognized_commands_re:
                            # starts with
                            if re.compile('^'+re_c).search(k):
                                broken_comment_index_1 = j
                                logger.info(f'--likely beginning fragment of command {j}')
                            # ends with
                            elif re.compile(re_c+'$').search(k) and \
                                    re.sub(
                                            '[0-9]+','[0-9]+',
                                            arduino_comment_list[
                                                broken_comment_index_1
                                                ]+c
                                            ) == \
                                        re.sub('[0-9]+','[0-9]+',k):
                                logger.info(f'--likely ending fragment of command {j}')
                                arduino_comment_list[broken_comment_index_1] = \
                                    arduino_comment_list[broken_comment_index_1]+c
                                arduino_comment_list[j] = ''
                                logger.info(
                                    f'FIXED:{arduino_comment_list[broken_comment_index_1]}'
                                    )
                            # middle piece
                            elif re.compile(
                                    '^'+re.sub('[0-9]+','[0-9]+',arduino_comment_list[broken_comment_index_1])+re_c
                                    ).search(k):
                                logger.info(f'--likely mid fragment of command {j}')
                                arduino_comment_list[broken_comment_index_1] = \
                                    arduino_comment_list[broken_comment_index_1]+c
                                logger.info(
                                    f'attempting repair:{arduino_comment_list[broken_comment_index_1]}'
                                    )
                                arduino_comment_list[j] = ''
                            # full but with gap
                            elif re.compile(
                                    '^'+re.sub('[0-9]+','[0-9]+',arduino_comment_list[broken_comment_index_1])
                                    ).search(k) \
                                    and \
                                    re.compile(re_c+'$').search(k):
                                        logger.info(
                                            f'likely ending of fragment with middle gap {j}'
                                            )
                                        gap_finder = re.compile(
                                            '^(?P<frag1>'+ \
                                            arduino_comment_list[broken_comment_index_1]+\
                                            ')(?P<gap>.*)(?P<frag2>'+\
                                            re_c+\
                                            ')$')
                                        gap_search = gap_finder.search(k)
                                        gap_contents = gap_search.group('gap')
                                        arduino_comment_list[broken_comment_index_1] = \
                                            arduino_comment_list[broken_comment_index_1]+\
                                            gap_contents+\
                                            c
                                        arduino_comment_list[j] = ''
                                        logger.info(
                                            f'Fixed: {arduino_comment_list[broken_comment_index_1]}{c}\nAs:{arduino_comment_list[broken_comment_index_1]}'
                                            )
                            #else:
                            #   logger.info(f'unmatchable comment: {c}')
                                    
                                    
                signal_data_pieces[i].loc[:,'arduino_comments'] = arduino_comment_list
                            
                
            
            # add block timestamp column
            # set on a copy warning triggered by this. not sure why
            for i in range(len(signal_data_pieces)):
                # creates timestamp comment column
                signal_data_pieces[i].loc[:,'timestamp_comment'] = ''
                # creates timestamp starttime column
                signal_data_pieces[i].loc[:,'timestamp_starttime'] = ''
                # repopulates timestamp comment column
                signal_data_pieces[i]['timestamp_comment'].iloc[0] = \
                    signal_mode_pieces[i]
                # repopulates timestamp starttime column
                signal_data_pieces[i]['timestamp_starttime'].iloc[0] = \
                    signal_start_pieces[i]
                # create all_comment column from timestamp and arduino comments
                signal_data_pieces[i].loc[:,'all_comments'] = \
                    signal_data_pieces[i]['timestamp_comment'].fillna('') + \
                    signal_data_pieces[i]['arduino_comments'].fillna('')
            
            # fix cases where serial com was missed - add labchart prefix
            
            # iterates through entries in signal_data_pieces
            for i in range(len(signal_data_pieces)):
                # use loc to isolate all_comments entries that are not empty
                # add labchart prefix to those entries
                signal_data_pieces[i].loc[
                    signal_data_pieces[i]['all_comments'] != '',
                    'all_comments'
                    ] = '#* ' + signal_data_pieces[i].loc[
                        signal_data_pieces[i]['all_comments'] != '','all_comments'
                        ]
                
            
         
            #%% export data as csv
            
            columns_for_export = [
                'time',
                'FLOW',
                'ECG',
                'all_comments'
                ]
            
            #
            
            
            
            experiment_time = 0
            sampling_interval = \
                signal_data_pieces[0]['time'].iloc[1] - \
                    signal_data_pieces[0]['time'].iloc[0]
            
            
            #
            with open(input_file[:-4]+"all.txt",'w') as lcf:
                lcf.write('\n'.join([
                    'Interval= 0.001 s',
                    'TimeFormat= StartofBlock',
                    'ChannelTitle= \tFLOW\tECG\t',
                    'Range= \t10.000V\t10.000V\t\n'                                 
                    ]
                    )
                    )
        
        
            
            for i in range(len(signal_data_pieces)):
                logger.info(f'Exporting Block {i} : {signal_mode_pieces[i]}')
                
                with open(input_file[:-4]+f"_{i}_{signal_mode_pieces[i]}.txt",'w') as lcf:
                    lcf.write('\n'.join([
                        'Interval= 0.001 s',
                        'TimeFormat= StartofBlock',
                        'ChannelTitle= \tFLOW\tECG\t',
                        'Range= \t10.000V\t10.000V\t\n'                                 
                        ]
                        )
                        )
                
                signal_data_pieces[i][columns_for_export].to_csv(
                    input_file[:-4]+f"_{i}_{signal_mode_pieces[i]}.txt",
                    index=False,
                    header=False,
                    sep='\t',
                    mode = 'a'
                    )
                
                signal_data_pieces[i][columns_for_export].to_csv(
                    input_file[:-4]+f"_{i}_{signal_mode_pieces[i]}.csv",
                    index=False
                    )
        
                # adjust timing so it doesn't reset to 0 between blocks
                signal_data_pieces[i].loc[:,'time'] += experiment_time
                
                experiment_time = \
                    signal_data_pieces[i]['time'].iloc[-1] + sampling_interval
                
                if i == 0:
                    signal_data_pieces[i][columns_for_export].to_csv(
                        input_file[:-4]+"all.csv",
                        index=False,
                        mode='w',
                        header=True
                        )
                else:
                    signal_data_pieces[i][columns_for_export].to_csv(
                        input_file[:-4]+"all.csv",
                        index=False,
                        mode='a',
                        header=False
                        )
                    
                signal_data_pieces[i][columns_for_export].to_csv(
                    input_file[:-4]+"all.txt",
                    index=False,
                    header=False,
                    sep='\t',
                    mode = 'a'
                    )
        except Exception as e:
            logger.exception(
                f'Unable to process {input_file}\n***{e}',
                exc_info=True
                )


#%% run main
##

if __name__ == '__main__':
    main()
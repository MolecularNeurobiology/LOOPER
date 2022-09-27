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
import numpy
import re
import tkinter.filedialog
import tkinter
import logging
import argparse
import sys
import os

#%% define functions

class SETTINGS:
    def __init__(self):
        
        self.challenge_pf_threshold_multiple = 2
        self.minimum_apnea_duration = 5
        self.minimum_PIF = 0.05
        self.minimum_PEF = 0.05
        self.minimum_apnea_to_gasp_duration = 15
        self.trim_for_hypervent_phase = '5,5'
        self.early_recovery_starting_breath = 10
        self.late_recovery_start_from_end = 30
        self.condition_to_use_for_baseline = 'Baseline'
        self.Baseline_minimum_bout = 5
        self.Baseline_VF = 250
        self.Baseline_TT = 1
        self.Baseline_isTT = 1
        self.Baseline_HR = 700
        self.Baseline_RR = 999
        self.Baseline_isRR = 1
        self.Baseline_BSD = 0.5
        self.Baseline_DVTV = 0.75
        self.VF_recovery_threshold = 63
        self.HR_recovery_threshold = 63
        self.Consecutive_Recovery_Threshold = 30
        self.Accumulated_Recovery_Threshold = 30
        self.Accumulated_Recovery_Minimum_Bout = 5
        self.cal_vol_mL = 0.02
        
        
        # timestamp harmonizing settings:
        # regex for...
        # *condition
        # *challenge start
        # *exposure start
        # *apnea detection
        # *recovery gas start
        
    def load_from_file(self,filepath,logger = None):
        
        Analysis_Parameters = pandas.read_csv(
            filepath,
            sep=',',
            encoding='UTF-8',
            index_col='Parameter'
            )['Setting'].to_dict()
        for k in Analysis_Parameters:
            if k.startswith('PM_'):
                attr_name = k[3:]
                try:
                    attr_val = float(Analysis_Parameters[k])
                except:
                    attr_val = Analysis_Parameters[k]
                setattr(self,attr_name,attr_val)
        
                if logger:
                    logger.info(f'"{attr_name}" set to "{attr_val}" from file')
                    
    
    def save_to_file(self,filepath,logger = None):
        Analysis_Parameters = {}
        for k in self.__dict__:
            Analysis_Parameters[f'PM_{k}'] = self.__dict__[k]
        AP_df = pandas.DataFrame(Analysis_Parameters)
        AP_df.to_csv(filepath)
        logger.info(f'analysis parameters saved to file: {filepath}')
        



def gui_open_filename(kwargs={}):
    """
    This function creates a temporary Tkinter instance that provides a GUI 
    dialog for selecting a filename.

    Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
      ......
      (declare as a dictionary)
      {"defaultextension":'',"filetypes":'',"initialdir":'',...
      "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
      ......

    Returns
    -------
    output_text : String
        String describing the path to the file selected by the GUI.
    
    """

    root = tkinter.Tk()
    output_text = tkinter.filedialog.askopenfilename(
        **kwargs)
    root.destroy()
    return output_text


def gui_open_filenames(kwargs={}):
    """
    This function creates a temporary Tkinter instance that provides a GUI
    dialog for selecting [multiple] filenames.

    Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
      ......
      (declare as a dictionary)
      {"defaultextension":'',"filetypes":'',"initialdir":'',...
      "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
      ......

    Returns
    -------
    output_text : List of Strings
        List of Strings describing the paths to the files selected by the GUI.
    
    """

    root = tkinter.Tk()
    output_text_raw = tkinter.filedialog.askopenfilenames(
        **kwargs)
    output_text = root.tk.splitlist(output_text_raw)
    root.destroy()
    return output_text


def gui_directory(kwargs={}):
    """
    This function creates a temporary Tkinter instance that provides a GUI
    dialog for selecting a directory.
    
    Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
          ......
          (declare as a dictionary)
          {"defaultextension":'',"filetypes":'',"initialdir":'',...
          "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
          ......

    Returns
    -------
    output_text : String
        Returns the directory path selected by the GUI.

    """

    root = tkinter.Tk()
    output_text = tkinter.filedialog.askdirectory(
        **kwargs)
    root.destroy()
    return output_text


def initialize_logger(filepath):
    logger = logging.getLogger('SHAM a.k.a. AAAH!')
    logger.setLevel(logging.DEBUG)

    # create file and console handlers to receive logging
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(filepath)
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

    # create format for log and apply to handlers
    log_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # log initial inputs
    logger.info('Initializing Log')
    
    return logger


def extract_ruid(
        filename,
        extension='txt',
        ):
    """
    Extracts ruid information from a filename provided in
    YYMMDD_RUID.txt format.

    Parameters
    ----------
    filename : string
        filename, expected as MUID_PLYUID.txt format

    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata

    extension : string
        extension of the file, default is txt

    Returns
    -------
    ruid : string

    """

    yymmdd_ruid_re = re.compile(
        '^((?P<yymmdd>[^_\n\r]*?)_)?(?P<ruid>[^_\n\r(?!a|_)]+)'+\
        '(?P<exported>(all|_[^\.\n\r]*?_[^\.\n\r]*?))?(?P<ext>\.{})$'.format(
            extension
            )
        )
    parsed_filename = re.search(yymmdd_ruid_re, os.path.basename(filename))
    ruid = parsed_filename['ruid']
    
    return ruid



def load_signal_data(filename, local_logger):
    """
    Creates a dataframe containing plethysmography signal data
    includes calls to several other functions that are required for proper
    parsing of an exported lab chart signal file.
    -extract_header_type()
    -extract_header_locations()
    -read_exported_labchart_file()
    -merge_signal_data_pieces()

    Parameters
    ----------
    filename : string
        path to file containing signal data
    local_logger : instance of logging.logger


    Returns
    -------
    signal_data_assembled : pandas.DataFrame
        dataframe containing contents of signal file (merged into a single
        dataframe if multiple blocks are present)

    """
    Header_Tuples = extract_header_type(filename)
    header_locations = extract_header_locations(
        filename,
        local_logger=local_logger
        )
    signal_data_pieces = read_exported_labchart_file(
        filename,
        header_locations,
        header_tuples=Header_Tuples
        )
    signal_data_assembled = merge_signal_data_pieces(signal_data_pieces)
    return signal_data_assembled


def extract_header_type(filename,rows_to_check = 20):
    """
    Gathers information regarding the header format/column contents present
    in an exported lab chart signal file (assumes set-up is in line with
    Ray Lab specifications)

    Parameters
    ----------
    filename : string
        path for file containing signal data

    Returns
    -------
    header_tuples : list of tuples
        list of tuples specifying ([column name],[datatype])

    """
    
    with open(filename,'r') as opfi:
        # check 1st [rows_to_check] rows to see if header is expected to 
        # include date column with data as well as data containing columns
    
        ts_columns = ['ts']
        for i in range(rows_to_check):
            cur_line = opfi.readline()
            if "DateFormat=	M/d/yyyy" in cur_line:
                ts_columns = ['ts','date']
            else:
                pass
                
            if "ChannelTitle=" in cur_line:
                header_columns = \
                    cur_line.lower().replace('\n','').split('\t')[1:]
                while '' in header_columns:
                    header_columns.remove('')
            else:
                pass
            
    # special_columns describe columns that should not be 
    # processed as float
    special_columns = {'date':str,'comment':str}
    
    # rename_columns describe columns that use a different alias when
    # handled by this script in subsequent steps
    rename_columns = {
        'breathing':'vol',
        'oxygen':'o2',
        'oxygen ':'o2',
        'co2':'co2',
        'tchamber':'temp',
        'channel 5':'ch5',
        'channel 6':'ch6',
        'channel 7':'ch7',
        'channel 8':'ch8',
        'vent flow':'flow'
        }
    
    combined_columns = ts_columns+\
        [
            rename_columns[j] if j in rename_columns else j \
            for j in header_columns
        ]+\
        ['comment']
    
    header_tuples = [
                (j.lower(),str) \
                if j in special_columns \
                else (j.lower(),float) \
                for j in combined_columns
                ]

    return header_tuples


def extract_header_locations(
        filename,
        header_text_fragment='Interval=',
        local_logger=None):
    """
    Gathers information regarding the locations of header information
    throughout a signal file - needed if files may contain multiple recording
    blocks

    Parameters
    ----------
    filename : string
        path to file containing signal data
    header_text_fragment : string, optional
        string that is present in header lines. The default is 'Interval='.
    local_logger : instance of logging.logger, optional
        The default is None (i.e. no logging)

    Returns
    -------
    headers : list
        list of rows in the datafile that indicate header content present
        
    """
    
    headers = []
    i = 0
    with open(filename, 'r') as opfi:
        for line in opfi:
            if header_text_fragment in line:
                if local_logger != None:
                    local_logger.info(
                        'Signal File has HEADER AT LINE: {}'.format(i)
                        )
                headers.append(i)
            i += 1
    return headers


def read_exported_labchart_file(
        lc_filepath,
        header_locations,
        header_tuples,
        delim='\t',
        rows_to_skip=6
        ):
    """
    Collects data from an exported lab chart file and returns a list of
    dataframes (in order) containing the extracted contents of the signal file.

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
                        nrows=header_locations[i+1]-header_locations[i]-6,
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
    Merges multiple blocks contained in a list of dataframes into a single
    dataframe (current behavior will override timestamp information to
    place subsequent blocks of data using the next sequential timestamp).

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



def fix_broken_timestamps(
        timestamp_dict,
        recognized_commands_re = None, 
        capture_version = None,
        logger = None
        ):
    
    if capture_version is not None:
        pass # customize recognized_commands to reflect capture_version
    
    if recognized_commands_re is None:
        recognized_commands_re = [
            'Starting: Calibrating for 0s',
            'Finished: Calibrating',
            'Habituation-1',
            'Pre-Inject',
            'Baseline',
            'Challenge',
            'ChallengeFinished: On Position ,0, Prefilled for 0s,Finished: On Anoxic Air',
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
    
    broken_comment_index_1 = 0
    for k,v in timestamp_dict.items():
        
        re_v = re.sub('[0-9]+','[0-9]+',v)
        
        if any([re.compile('^'+re_v+'$').search(i) for i in recognized_commands_re]):
            logger.info(f'Found: {k}:{v}')
        else:
            logger.info(f'unrecognized arduino com:\n{k}:{v}')
            for i in recognized_commands_re:
                # starts with
                if re.compile('^'+re_v).search(i):
                    broken_comment_index_1 = k
                    logger.info(f'--likely beginning fragment of command {k}')
                # ends with
                elif re.compile(re_v+'$').search(i) and \
                        re.sub(
                                '[0-9]+','[0-9]+',
                                timestamp_dict[
                                    broken_comment_index_1
                                    ]+v
                                ) == \
                            re.sub('[0-9]+','[0-9]+',i):
                    logger.info(f'--likely ending fragment of command {k}')
                    timestamp_dict[broken_comment_index_1] = \
                        timestamp_dict[broken_comment_index_1]+v
                    timestamp_dict[k] = ''
                    logger.info(
                        f'FIXED:{timestamp_dict[broken_comment_index_1]}'
                        )
                # middle piece
                elif re.compile(
                        '^'+re.sub('[0-9]+','[0-9]+',timestamp_dict.get(broken_comment_index_1,''))+re_v
                        ).search(i):
                    logger.info(f'--likely mid fragment of command {broken_comment_index_1}')
                    timestamp_dict[broken_comment_index_1] = \
                        timestamp_dict[broken_comment_index_1]+v
                    logger.info(
                        f'attempting repair:{timestamp_dict[broken_comment_index_1]}'
                        )
                    timestamp_dict[k] = ''
                # full but with gap
                elif re.compile(
                        '^'+re.sub('[0-9]+','[0-9]+',timestamp_dict.get(broken_comment_index_1,''))
                        ).search(i) \
                        and \
                        re.compile(re_v+'$').search(i):
                            logger.info(
                                f'likely ending of fragment with middle gap {broken_comment_index_1}'
                                )
                            gap_finder = re.compile(
                                '^(?P<frag1>'+ \
                                timestamp_dict.get(broken_comment_index_1,'')+\
                                ')(?P<gap>.*)(?P<frag2>'+\
                                re_v+\
                                ')$')
                            gap_search = gap_finder.search(i)
                            gap_contents = gap_search.group('gap')
                            timestamp_dict[broken_comment_index_1] = \
                                timestamp_dict[broken_comment_index_1]+\
                                gap_contents+\
                                v
                            timestamp_dict[k] = ''
                            logger.info(
                                f'Fixed: {timestamp_dict[broken_comment_index_1]}'
                                )
    for k in list(timestamp_dict.keys()):
        if timestamp_dict[k] == '':
            timestamp_dict.pop(k)
    return timestamp_dict
        


def harmonize_timestamps(
        timestamp_dict,
        capture_version = None,
        translation_dict = None,
        logger = None
        ):
    
    if capture_version is not None:
        pass # customize the translation dict to reflect the capture version

    if translation_dict is None:
        # !!! consider moving to external settings, may need to address handling
        #     of timestamps to be omitted from the harmonized output
        translation_dict = {
            'Starting: Cal':'Calibration',
            'Finished: Cal':'Signal Preview-1',
            'Habituation':'Habituation',
            'Habituation-1':'Habituation-1',
            'Habituation-2':'Habituation-2',
            'Pre-Inject':'Pre-Inject',
            'Baseline':'Baseline',
            'Challenge':'Challenge',
            'Finished: On Anoxic':'Anoxic',
            'Finished: On Position':'Anoxic',
            'Starting: On Anoxic':'Prefill',
            'Starting: On Room Air':'Apnea(Arduino)',
            'Finished: On Room Air':'Recovery'
            }
        
    translated_results = {}
    for k_orig,v_orig in timestamp_dict.items():
        for k_trans,v_trans in translation_dict.items():
            if k_trans in v_orig:
                translated_results[k_orig] = v_trans
                logger.info(f'{k_orig}: matched to "{v_trans}"')
                break
        if k_orig not in translated_results.keys():
            logger.warning(f'unable to match : {k_orig}:{v_orig}')
        
    return translated_results



def get_pneumo_TV(tv,calv,act_calv):
    """
    Calculates pneumotacograph based tidal volume.
    
    Parameters
    ----------
    tv : Float
        uncorrected tidal volume (V)
    calv : Float
        uncorrected tidal volume from calibration period (V)
    act_calv : Float
        nominal calibration volume (mL)

    Returns
    -------
    Float
        corrected tidal volume (mL)

    """
    
    return tv / calv * act_calv



def calculate_irreg_score(input_series):
    """
    takes a numpy compatible series and calculates an irregularity score
    using the formula |x[n]-X[n-1]| / X[n-1]. A series of the irregularity 
    scores will be returned.
    First value will be zero as it has no comparison to change from.

    Parameters
    ----------
    input_series : Pandas.DataSeries of Floats
        Data to use for Irreg Score Calculation

    Returns
    -------
    output_series : Pandas.DataSeries of Floats
        Series of Irreg Scores, paired to input_series

        
    """
    output_series = numpy.insert(
        numpy.divide(
            numpy.abs(
                numpy.subtract(
                    list(input_series[1:]), list(input_series[:-1])
                    )
                ),
            list(input_series[:-1])
            ), 0, numpy.nan)
    return output_series



def multi_filter(input_df,index_col,filter_dict,logger = None):
    filter_df = pandas.DataFrame(input_df[index_col])
    for k,v in filter_dict.items():
        # k describes a comparison name
        # v should be a 3 part tuple indicatling in position [0]
        # the column name in input_df
        # in position [1] g,l,e,ge,le corresponding to >,<,==,>=,<= 
        # and indicating in position [2] the value to test against
        if v[1] == 'g':
            filter_df[k] = input_df[v[0]] > v[2]
        elif v[1] == 'ge':
            filter_df[k] = input_df[v[0]] >= v[2]
        elif v[1] == 'l':
            filter_df[k] = input_df[v[0]] < v[2]
        elif v[1] == 'le':
            filter_df[k] = input_df[v[0]] <= v[2]
        elif v[1] == 'e':
            filter_df[k] = input_df[v[0]] == v[2]
        elif logger:
            filter_df[k] = 1
            logger.warning(f'unable to apply filter {v} - filter skipped')
        
    filter_output = pandas.DataFrame(
        {
            'ts':input_df[index_col],
            'filt':filter_df[filter_dict.keys()].min(axis=1)
            }
        )
        
    return filter_output



def resample_and_merge_filters(
        filter1_orig,filter2_orig,sample_int,minimum_bout,logger = None
        ):
    # start = min(filter1['ts'].min(),filter2['ts'].min())
    # stop = max(filter1['ts'].max(),filter2['ts'].max())
    # resample_df = pandas.DataFrame(
    #     {'ts':numpy.arange(start,stop+sample_int,sample_int)}
    #     )
    filter1 = filter1_orig.copy()[filter1_orig['filt']].rename(
        {'filt':'f1','ts':'ts1'},axis='columns'
        )
    filter2 = filter2_orig.copy()[filter2_orig['filt']].rename(
        {'filt':'f2','ts':'ts2'},axis='columns'
        )
    precision = int(numpy.format_float_scientific(sample_int).split('e')[1])*-1
    filter1.loc[:,'round_ts'] = round(filter1['ts1'],precision)
    filter2.loc[:,'round_ts'] = round(filter2['ts2'],precision)
    
    resample_df = filter1.merge(filter2, how = 'outer',on = 'round_ts')
    
    resample_df['round_ts_as_sec'] = pandas.to_datetime(
        resample_df['round_ts'],
        unit='s'
        )
    
    resample_df = resample_df.set_index('round_ts_as_sec')
    
    resample_df = resample_df.sort_index()
    
    resample_df.loc[:,'f1'] = resample_df['f1'].ffill()
    resample_df.loc[:,'f2'] = resample_df['f2'].ffill()
    
    resample_df.loc[:,'f1_and_f2'] = resample_df['f1'] & resample_df['f2']
    
    # !!! unit testing would be ideal for this
    # rolling minimum window requires all samples in window to be true to 
    # be output as true, 'or' to combine a left and right justified filter
    # provides an output that passes with the minimum bout duration
    rolling_right = resample_df['f1_and_f2'].rolling(
        f'{int(minimum_bout)}s'
        ).min().fillna(0).astype(bool)
    # series is inverted for rolling window and inverted again for output
    # (rolling function only works right justified, workaround provides a 
    # left justified rolling window)
    rolling_left = resample_df.loc[::-1,'f1_and_f2'].rolling(
        f'{int(minimum_bout)}s'
        ).min().fillna(0).astype(bool).sort_index()
    resample_df.loc[:,'f1_and_f2'] = rolling_right | rolling_left
    
    filter1 = filter1_orig.merge(
        resample_df[['ts1','f1_and_f2']],
        how = 'left',left_on='ts',right_on='ts1'
        ).fillna(0).astype(bool)
    filter2 = filter2_orig.merge(
        resample_df[['ts2','f1_and_f2']],
        how = 'left',left_on='ts',right_on='ts2'
        ).fillna(0).astype(bool)
    
    logger.info(f'resample_and_merge_filters: f1 pass={filter1.filt.sum()}')
    logger.info(f'resample_and_merge_filters: f2 pass={filter2.filt.sum()}')
    logger.info(f'resample_and_merge_filters: f1_and_f2 f1 pass={filter1.f1_and_f2.sum()}')
    logger.info(f'resample_and_merge_filters: f1_and_f2 f1 pass={filter2.f1_and_f2.sum()}')
    
    if logger:
        if filter1['f1_and_f2'].sum() == 0 or filter2['f1_and_f2'].sum() == 0:
            logger.warning('resample_and_merge_filters yeild 0 passing')
    return filter1['f1_and_f2'],filter2['f1_and_f2'],resample_df[['round_ts','f1_and_f2']]



def get_ts_for_accumulated_value(
        input_df_orig,filter_series_orig,accum_col,target,ts_col
        ):
    input_df = input_df_orig.copy()
    filter_series = filter_series_orig.copy()
    input_df.loc[filter_series,'passing'] = input_df[filter_series][accum_col]
    input_df.loc[:,'accum'] = input_df['passing'].cumsum()
    ts = input_df[input_df['accum']>=target][ts_col].min()
    return ts

    
#%% define main

def main():
    #%%
    # collect filepaths
    #  collect as command line arguments
    parser = argparse.ArgumentParser(description='Automated Breath Caller')
    parser.add_argument('-s', action='append', help='Paths to signal files')
    #parser.add_argument('-v', action='append', help='Paths to  (ventilation) files')
    #parser.add_argument('-r', action='append', help='Paths to heartbeat (RR interval) files')
    parser.add_argument('-o', help='Path to directory for output files')
    parser.add_argument('-p', help='Path to Analysis Parameters File')
    
    args, others = parser.parse_known_args()
    
    #  collect through gui if not set in command line
    #  to settings
    if not args.p:
        settings_path = gui_open_filename({'title':'Select Analysis Settings'})
    # #  to breathlist
    # if not args.v:
    #     breathlist_paths = gui_open_filenames({'title':'Select Breath Lists'})
    # #  to beatlist
    # if not args.r:
    #     beatlist_paths = gui_open_filenames({'title':'Select Beat Lists'})
    #  to signals (with timestamps)
    if not args.s:
        signal_paths = gui_open_filenames({'title':'Select Signal Files'})
    #  to output directory
    if not args.o:
        output_path = gui_directory({'title':'Select Output Location'})
    
    
    # set up logging
    Logger = initialize_logger(os.path.join(output_path,'autores_log.log'))
    
    #%%
    
    # gather settings
    Settings = SETTINGS()
    Settings.load_from_file(settings_path,logger = Logger)
    
    # parse and match files
    file_groups = {}
    for f in signal_paths:
        try:
            ruid = extract_ruid(f,'txt')
            dirname = os.path.dirname(f)
            file_groups[ruid] = {
                'signal':f,
                'breathlist':os.path.join(dirname,f'{ruid}_all_breathlist.csv'),
                'beatlist':os.path.join(dirname,f'{ruid}_beats.csv')
                }
            Logger.info(f'loading data (breaths,beats,signals) for {ruid}')
            # gather signal file
            Signals = load_signal_data(f,Logger)
            # gather breathlist
            Breath_List = pandas.read_csv(file_groups[ruid]['breathlist'])
            # add BSD to Breath_List
            Signals.loc[:,'mov_avg_flow'] = Signals['flow'].rolling(
                int(1/(Signals['ts'].iloc[1]-Signals['ts'].iloc[0])), 
                center=True
                ).mean()
            # determine sample interval
            Sample_Interval = (Signals['ts'].iloc[1]-Signals['ts'].iloc[0])
            Breath_List.loc[:,'BSD'] = abs(Breath_List.merge(
                Signals,
                how = 'left',
                left_on = 'Timestamp_Inspiration',
                right_on ='ts'
                )['mov_avg_flow'])
            
            # gather beatlist
            Beat_List = pandas.read_csv(file_groups[ruid]['beatlist'])
            # add isRR to Beat_List
            Beat_List.loc[:,'isRR'] = calculate_irreg_score(Beat_List['RR'])
            # add HR to Beat_List
            Beat_List.loc[:,'HR'] = 60/Beat_List['RR']

            
            # collect timestamps
            Logger.info('collecting timestamps')
            Timestamp_Dict = dict(
                zip(
                    Signals.ts[Signals.comment.dropna().index],
                    [i[3:] for i in Signals.comment.dropna()]
                    )
                )
            # harmonize timestamps
            #%%
            Timestamp_Dict = fix_broken_timestamps(
                Timestamp_Dict,
                recognized_commands_re = None,
                logger = Logger
                )
            #%%
            Harmonized_Timestamps = harmonize_timestamps(
                Timestamp_Dict,
                logger = Logger
                )
            
            # identify challenge rounds
            Logger.info('extracting challenge round info')
            Challenge_Timestamp = None
            Challenge_List = []
            for k,v in Harmonized_Timestamps.items():
                if v == 'Challenge':
                    Challenge_Timestamp = k
                    break
            if Challenge_Timestamp is None:
                raise Exception('Challenge Mode Timestamp not found')
            
            open_challenge = False
            trial_counter = 0
            for k,v in Harmonized_Timestamps.items():
                if k <= Challenge_Timestamp:
                    continue
                if v == 'Prefill':
                    if open_challenge == True:
                        Logger.warning(
                            f'challenge trial timestamp anomoly -Prefill-{trial_counter}'
                            )
                    else:
                        trial_counter +=1
                        current_challenge = {
                            'trial_number':trial_counter,
                            'Prefill':k,
                            }
                        open_challenge = True
                elif v in current_challenge:
                    Logger.warning(
                        f'challenge trial timestamp anomoly - {v}-{trial_counter}'
                        )
                    current_challenge['trial_number'] = trial_counter
                    Challenge_List.append(current_challenge)
                    
                    trial_counter += 1
                    current_challenge = {
                        'trial_number':trial_counter,
                        v:k
                        }
                elif v =='Recovery':
                    current_challenge[v] = k
                    open_challenge = False
                    
                    # !!! would be better to move this list to a settings 
                    #     (probably shared with the setting for the 
                    #     harmonization dict)
                    if len(
                            set(current_challenge).intersection(
                                {
                                    
                                    'Prefill',
                                    'Anoxic',
                                    'Apnea(Arduino)',
                                    'Recovery'
                                    }
                                )
                            ) != 4: 
                        current_challenge['trial_number'] = trial_counter
                        Logger.warning(
                            f'Incomplete challenge timestamps -{trial_counter} - {current_challenge}'
                            )
                    Challenge_List.append(current_challenge)
                    
                    current_challenge = {}
                else:
                    current_challenge[v] = k
            # add last challenge if it was left open
            if current_challenge != {}:
                Challenge_List.append(current_challenge)
                
                    
                
            #%%
            # generate calibration values
            Calibration_start = max(
                [
                    k for k,v in Harmonized_Timestamps.items()
                    if v == 'Calibration'
                    ]
                )
            Calibration_end = min(
                [
                    k for k in Harmonized_Timestamps.keys() 
                    if k > Calibration_start
                    ]
                )
            
            Calibration_VT = Breath_List[
                (Breath_List['Timestamp_Inspiration']>Calibration_start)&
                (Breath_List['Timestamp_Inspiration']<Calibration_end)
                ]['Tidal_Volume_uncorrected'].mean()
            # fix calibrated volume columns in Breath_List
            Breath_List.loc[:,'VT__Tidal_Volume_corrected'] = \
                get_pneumo_TV(
                    Breath_List['Tidal_Volume_uncorrected'],
                    Calibration_VT,
                    Settings.cal_vol_mL
                    )
            Breath_List.loc[:,'VTpg__Tidal_Volume_per_gram_corrected'] = \
                Breath_List['VT__Tidal_Volume_corrected'] / \
                    Breath_List['Weight']
            Breath_List.loc[:,'VE__Ventilation'] = \
                Breath_List['VT__Tidal_Volume_corrected'] * \
                    Breath_List['VF']
            Breath_List['VEpg__Ventilation_per_gram'] = \
                Breath_List['VE__Ventilation'] / \
                    Breath_List['Weight']
                
            #%%
            # generate baseline values
            Baseline_start = max(
                [
                    k for k,v in Harmonized_Timestamps.items()
                    if v == Settings.condition_to_use_for_baseline
                    ]
                )
            Baseline_end = min(
                [
                    k for k in Harmonized_Timestamps.keys() 
                    if k > Baseline_start
                    ]
                )
            
            # !!! note post hoc analysis is using 'is' instead of 'cv' for 
            # variation acceptablility for inclusion
            Breath_Baseline_Filter = multi_filter(
                Breath_List,
                'Timestamp_Inspiration',
                {
                    'start':('Timestamp_Inspiration','ge',Baseline_start),
                    'end':('Timestamp_Inspiration','l',Baseline_end),
                    'VF':('VF','le',Settings.Baseline_VF),
                    'TT':('Breath_Cycle_Duration','le',Settings.Baseline_TT),
                    'isTT':('IS_TT','le',Settings.Baseline_isTT),
                    'BSD':('BSD','le',Settings.Baseline_BSD),
                    'DVTV':('DVTV','le',Settings.Baseline_DVTV)
                    },
                logger = Logger
                )
            
            Beat_Baseline_Filter = multi_filter(
                Beat_List,
                'ts',
                {
                    'start':('ts','ge',Baseline_start),
                    'end':('ts','l',Baseline_end),
                    'HR':('HR','le',Settings.Baseline_HR),
                    'RR':('RR','le',Settings.Baseline_RR),
                    'isRR':('isRR','le',Settings.Baseline_isRR)
                    },
                logger = Logger
                )
            #%%
            Logger.info('Deriving Quality Basline Data (note TT and RR used for recovery threshold calculations)')
            Quality_Breath,Quality_Beat = resample_and_merge_filters(
                Breath_Baseline_Filter,
                Beat_Baseline_Filter,
                Sample_Interval,
                Settings.Baseline_minimum_bout,
                logger = Logger
                )[0:2]
            
            # Baseline_VF = Breath_List[Quality_Breath]['VF'].mean()
            Baseline_TT = \
                Breath_List[Quality_Breath]['Breath_Cycle_Duration'].mean()
            Baseline_VF = 60/Baseline_TT
            # Baseline_HR = Beat_List[Quality_Beat]['HR'].mean()
            Baseline_RR = Beat_List[Quality_Beat]['RR'].mean()
            Baseline_HR = 60/Baseline_RR
            
            Logger.info('Populating Baseline Summary')
            
            # !!! add functionality to generate additional summaries, with or
            # without tunable filters (is this needed if BASSPRO can do it?)
            
            Baseline_Summary = {
                'VF':Breath_List[Quality_Breath]['VF'].mean(),
                'Breath Duration':Breath_List[Quality_Breath]['Breath_Cycle_Duration'].mean(),
                'VT':Breath_List[Quality_Breath]['VT__Tidal_Volume_corrected'].mean(),
                'VT/g':Breath_List[Quality_Breath]['VTpg__Tidal_Volume_per_gram_corrected'].mean(),
                'VE':Breath_List[Quality_Breath]['VE__Ventilation'].mean(),
                'VE/g':Breath_List[Quality_Breath]['VEpg__Ventilation_per_gram'].mean(),
                'HR':Beat_List[Quality_Beat]['HR'].mean(),
                'RR':Beat_List[Quality_Beat]['RR'].mean(),
                'Calibration_VT_voltage':Calibration_VT
                }
            
            #%%
            # identify derrived timestamps
            for i,v in enumerate(Challenge_List):
                
                try:
                    #
                    Logger.info(f'Deriving Timestamps for Challenge {v}')
                    Challenge_List[i]['Challenge_Start'] = v['Prefill']
                    Challenge_List[i]['Exposure_Start'] = v['Anoxic']
                    Challenge_List[i]['Apnea_BoB(Arduino)'] = \
                        v['Apnea(Arduino)'] - Settings.minimum_apnea_duration
                    Challenge_List[i]['Recovery_Gas'] = v['Recovery']
                    if i+1 == len(Challenge_List):
                        Challenge_List[i]['Challenge_End'] = \
                            Signals['ts'].iloc[-1]
                    else:
                        Challenge_List[i]['Challenge_End'] = \
                            Challenge_List[i+1]['Prefill']
                    
                    # search for breathlist apnea, filter by time, pif
                    Challenge_List[i]['Apnea_BoB(B)'] = Breath_List[
                        (Breath_List['Timestamp_Inspiration'] >= \
                         Challenge_List[i]['Exposure_Start']) &
                        (Breath_List['Timestamp_Inspiration'] < \
                         Challenge_List[i]['Recovery_Gas']) &
                        (Breath_List['Peak_Inspiratory_Flow'] >= \
                         Settings.minimum_PIF * 
                         Settings.challenge_pf_threshold_multiple)
                        ]['Timestamp_Inspiration'].iloc[-1]
                        
                    # search for post apnea gasps
                    # !!! make number of gasps tracked a tunable setting
                    Gasp_List = Breath_List[
                        (Breath_List['Timestamp_Inspiration'] > \
                         Challenge_List[i]['Apnea_BoB(B)']) &
                        (Breath_List['Timestamp_Inspiration'] < \
                         Challenge_List[i]['Challenge_End']) &
                        (Breath_List['Peak_Inspiratory_Flow'] >= \
                         Settings.minimum_PIF * 
                         Settings.challenge_pf_threshold_multiple)
                        ]
                    for g in range(10):
                        if g > len(Gasp_List):
                            Challenge_List[i][f'Gasp_{g+1}'] = 'NaN'
                        else:
                            Challenge_List[i][f'Gasp_{g+1}'] = \
                                Gasp_List.iloc[g]['Timestamp_Inspiration']
                            Challenge_List[i][f'Gasp_{g+1}_Volume'] = \
                                Gasp_List.iloc[g]['VT__Tidal_Volume_corrected']
                            Challenge_List[i][f'Gasp_{g+1}_Volume_per_g'] = \
                                Gasp_List.iloc[g]['VTpg__Tidal_Volume_per_gram_corrected']
                                 
                    
                    # generate summary for sub-challenge components
                    for subchallenge,timing in {
                            'prefill':[
                                Challenge_List[i]['Challenge_Start'],
                                Challenge_List[i]['Exposure_Start']
                                ],
                            'exposure minus delay':[
                                Challenge_List[i]['Exposure_Start']+ \
                                    float(Settings.\
                                          trim_for_hypervent_phase.split(',')\
                                              [0]),
                                Challenge_List[i]['Apnea_BoB(Arduino)']- \
                                    float(Settings.\
                                          trim_for_hypervent_phase.split(',')\
                                              [1])
                                ],
                            'early recovery':[
                                Challenge_List[i][
                                    f'Gasp_{int(Settings.early_recovery_starting_breath)}'
                                    ],
                                Challenge_List[i]['Challenge_End']- \
                                    Settings.late_recovery_start_from_end
                                ],
                            'late recovery':[
                                Challenge_List[i]['Challenge_End']- \
                                    Settings.late_recovery_start_from_end,
                                Challenge_List[i]['Challenge_End']
                                ]
                            }.items():
                        try:
                            sc_breaths = Breath_List[
                                (Breath_List['Timestamp_Inspiration']>=timing[0])&
                                (Breath_List['ts_end']<timing[1])
                                ]
                            sc_beats = Beat_List[
                                (Beat_List['ts']>=timing[0])&
                                (Beat_List['ts']<timing[1])
                                ]
                            
                            Challenge_List[i][f'{subchallenge}_VF'] = \
                                sc_breaths['VF'].mean()
                            Challenge_List[i][f'{subchallenge}_Breath_Duration'] = \
                                sc_breaths['Breath_Cycle_Duration'].mean()
                            Challenge_List[i][f'{subchallenge}_VT'] = \
                                sc_breaths['VT__Tidal_Volume_corrected'].mean()
                            Challenge_List[i][f'{subchallenge}_VT/g'] = \
                                sc_breaths['VTpg__Tidal_Volume_per_gram_corrected'].mean()
                            Challenge_List[i][f'{subchallenge}_VE'] = \
                                sc_breaths['VE__Ventilation'].mean()
                            Challenge_List[i][f'{subchallenge}_VE/g'] = \
                                sc_breaths['VEpg__Ventilation_per_gram'].mean()
                            Challenge_List[i][f'{subchallenge}_HR'] = \
                                sc_beats['HR'].mean()
                            Challenge_List[i][f'{subchallenge}_RR'] = \
                                sc_beats['RR'].mean()
                            
                        except Exception:
                            Logger.error(
                                f'sub-challenge "{subchallenge}" undefined for round {i+1}',
                                exc_info=True)
                            Challenge_List[i][f'{subchallenge}_VF'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_Breath_Duration'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_VT'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_VT/g'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_VE'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_VE/g'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_HR'] = \
                                'NaN'
                            Challenge_List[i][f'{subchallenge}_RR'] = \
                                'NaN'
                    

                    # create filter for recovered breaths and recovered beats
                    Breath_Recovery_Filter = multi_filter(
                        Breath_List,
                        'Timestamp_Inspiration',
                        {
                            'start':(
                                'Timestamp_Inspiration',
                                'ge',
                                Challenge_List[i]['Recovery_Gas']
                                ),
                            'end':(
                                'Timestamp_Inspiration',
                                'l',
                                Challenge_List[i]['Challenge_End']),
                            'VF':(
                                'VF',
                                'ge',
                                Settings.VF_recovery_threshold/100 * \
                                    Baseline_VF
                                )
                            },
                        logger = Logger
                        )

                    Beat_Recovery_Filter = multi_filter(
                        Beat_List,
                        'ts',
                        {
                            'start':(
                                'ts',
                                'ge',
                                Challenge_List[i]['Recovery_Gas']
                                ),
                            'end':(
                                'ts',
                                'l',
                                Challenge_List[i]['Challenge_End']
                                ),
                            'HR':(
                                'HR',
                                'ge',
                                Settings.HR_recovery_threshold/100 * \
                                    Baseline_HR
                                )
                            },
                        logger = Logger
                        )
                    
                    
                        
                    # merge breath and beat filters
                    Logger.info('Checking for "accumulated" recovery...')
                    Recovery_Filt_accum = \
                        resample_and_merge_filters(
                            Breath_Recovery_Filter,
                            Beat_Recovery_Filter,
                            Sample_Interval,
                            Settings.Accumulated_Recovery_Minimum_Bout,
                            logger = Logger
                            )[0]
                    Logger.info('Checking for "consecutive" recovery...')
                    Recovery_Filt_consec = \
                        resample_and_merge_filters(
                            Breath_Recovery_Filter,
                            Beat_Recovery_Filter,
                            Sample_Interval,
                            Settings.Consecutive_Recovery_Threshold,
                            logger = Logger
                            )[0]
                    
                    Logger.info('Checking for "Breathing Only" recovery...')
                    Breathing_Filt_accum = \
                        resample_and_merge_filters(
                            Breath_Recovery_Filter,
                            Breath_Recovery_Filter,
                            Sample_Interval,
                            Settings.Accumulated_Recovery_Minimum_Bout,
                            logger = Logger
                            )[0]
                    
                    Logger.info('Checking for "Heartbeat Only" recovery...')
                    Beating_Filt_accum = \
                        resample_and_merge_filters(
                            Beat_Recovery_Filter,
                            Beat_Recovery_Filter,
                            Sample_Interval,
                            Settings.Accumulated_Recovery_Minimum_Bout,
                            logger = Logger
                            )[0]
                    
                    # identify recovey timestamp
                    Challenge_List[i]['Accum Recovery Met'] = \
                        get_ts_for_accumulated_value(
                            Breath_List, 
                            Recovery_Filt_accum, 
                            'Breath_Cycle_Duration',
                            Settings.Accumulated_Recovery_Threshold,
                            'ts_end'
                            )
                    Challenge_List[i]['Accum Recovery Start'] = \
                        get_ts_for_accumulated_value(
                            Breath_List, 
                            Recovery_Filt_accum, 
                            'Breath_Cycle_Duration',
                            0,
                            'Timestamp_Inspiration'
                            )
                    Challenge_List[i]['Consec Recovery Met'] = \
                        get_ts_for_accumulated_value(
                            Breath_List, 
                            Recovery_Filt_consec, 
                            'Breath_Cycle_Duration',
                            Settings.Consecutive_Recovery_Threshold,
                            'ts_end'
                            )
                    Challenge_List[i]['Consec Recovery Start'] = \
                        get_ts_for_accumulated_value(
                            Breath_List, 
                            Recovery_Filt_consec, 
                            'Breath_Cycle_Duration',
                            0,
                            'Timestamp_Inspiration'
                            ) 
                    Challenge_List[i]['Breathing Only Recovery Start'] = \
                        get_ts_for_accumulated_value(
                            Breath_List, 
                            Breathing_Filt_accum, 
                            'Breath_Cycle_Duration',
                            0,
                            'Timestamp_Inspiration'
                            )
                    
                    Challenge_List[i]['Heartbeat Only Recovery Start'] = \
                        get_ts_for_accumulated_value(
                            Beat_List, 
                            Beating_Filt_accum, 
                            'RR',
                            0,
                            'ts'
                            )
                        
                    print(Challenge_List[i]['Accum Recovery Met'])
                
                    
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_Recovery_Gas'] = \
                        Challenge_List[i]['Recovery_Gas'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_1st_Gasp'] = \
                        Challenge_List[i]['Gasp_1'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    Challenge_List[i]['Latency_Exposure_to_Apnea_BoB(B)'] = \
                        Challenge_List[i]['Apnea_BoB(B)'] - \
                            Challenge_List[i]['Exposure_Start']
                    Challenge_List[i]['Duration_Challenge_Start_to_End'] = \
                        Challenge_List[i]['Challenge_End'] - \
                            Challenge_List[i]['Challenge_Start']
                    Challenge_List[i]['Discrep_Apnea_BoB_B_vs_Arduino'] = \
                        Challenge_List[i]['Apnea_BoB(B)'] - \
                            Challenge_List[i]['Apnea_BoB(Arduino)']
                    Challenge_List[i]['Latency_1st_to_2nd_Gasp'] = \
                        Challenge_List[i]['Gasp_2'] - \
                            Challenge_List[i]['Gasp_1']
                
                    # latency from apnea/gasp to HR recovery (1st instance at accum bout)
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_HR_Recovery'] = \
                        Challenge_List[i]['Heartbeat Only Recovery Start'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    # latency from apnea/gasp to VF recovery (1st instance accum bout)
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_VF_Recovery'] = \
                        Challenge_List[i]['Breathing Only Recovery Start'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    
                    # dual recovery
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_Accum_Recovery_Met'] = \
                        Challenge_List[i]['Accum Recovery Met'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_Accum_Recovery_Start'] = \
                        Challenge_List[i]['Accum Recovery Start'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_Consec_Recovery_Met'] = \
                        Challenge_List[i]['Consec Recovery Met'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                    Challenge_List[i]['Latency_Apnea_BoB(B)_to_Consec_Recovery_Start'] = \
                        Challenge_List[i]['Consec Recovery Start'] - \
                            Challenge_List[i]['Apnea_BoB(B)']
                
                
                except Exception:
                    Logger.error(
                        f'unable to derive full timestamp set - {i}',
                        exc_info=True
                        )
            #%%
            try:
                writer=pandas.ExcelWriter(os.path.join(
                    output_path,ruid+'.xlsx'
                    ),engine='xlsxwriter')
                pandas.DataFrame(
                    Baseline_Summary, index = [0]
                    ).to_excel(writer,'Baseline', index=False)
                pandas.DataFrame(Challenge_List).to_excel(
                    writer,'Challenge', index=False
                    )
                writer.save()
                Logger.info('\n\nOutput Saved - {}'.format(output_path))
            except Exception:
                Logger.error('!!! Unable to save file !!!',exc_info=True)
                
        except Exception:
            Logger.error(
                f'!!! unable to process {os.path.basename(f)}!!!',
                exc_info=True
                )

#%% run main

if __name__ == '__main__':
    main()
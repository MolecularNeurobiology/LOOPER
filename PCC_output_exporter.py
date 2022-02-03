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


#%% define functions
##

def gui_open_filename(kwargs={}):
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
    output_text = tkinter.filedialog.askopenfilename(
        **kwargs)
    root.destroy()
    return output_text


def load_signal_data(filename, local_logger):
    """
    creates a dataframe containing plethysmography signal data
    includes calls to several other functions that are required for proper
    parsing of an exported lab chart signal file

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


def extract_header_type(filename):
    """
    gathers information regarding the header format/column contents present
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
    
    with open(filename) as opfi:
        # check 1st ten rows to see if header is expected to include
        # date column with data
        for i in range(10):
            if "DateFormat=	M/d/yyyy" in opfi.readline():
                header_tuples = [
                   ('ts', float),
                   ('date', str),
                   ('vol', float),
                   ('o2', float),
                   ('co2', float),
                   ('temp', float),
                   ('ch5', float),
                   ('ch6', float),
                   ('ch7', float),
                   ('ch8', float),
                   ('comment', str)
                   ]
                break
            else:
                header_tuples = [
                   ('ts', float),
                   ('vol', float),
                   ('o2', float),
                   ('co2', float),
                   ('temp', float),
                   ('ch5', float),
                   ('ch6', float),
                   ('ch7', float),
                   ('ch8', float),
                   ('comment', str)
                   ]
    return header_tuples


def extract_header_locations(
        filename,
        header_text_fragment='Interval=',
        local_logger=None):
    """
    gathers information regarding the locations of header information
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
                        nrows=header_locations[i+1]-header_locations[i]-16,
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
    input_file = gui_open_filename({'title':'select file to extract'})
    
    # log initial inputs
    logger.info(f'file selected {input_file}')
    
    #%% extract the file
    signal_blocks = extract_header_locations(input_file,header_text_fragment="$$$",local_logger=logger)
    
    signal_data_pieces = read_exported_labchart_file(
        input_file,
        signal_blocks[1:],
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
        rows_to_skip = 16)
    
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
            skiprows=i,
            nrows=17,
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
            ) for i in signal_blocks[1:]
        ]
    signal_start_pieces = [
        i.time.iloc[1] for i in signal_header_pieces
        ]
    signal_mode_pieces = [
        i.mode_block.iloc[-1] for i in signal_header_pieces
        ]
    
    #%% add block timestamp column
    # set on a copy warning triggered by this. not sure why
    for i in range(len(signal_data_pieces)):
        signal_data_pieces[i].loc[:,'timestamp_comment'] = ''
        signal_data_pieces[i].loc[:,'timestamp_starttime'] = ''
        signal_data_pieces[i]['timestamp_comment'].iloc[0] = \
            signal_mode_pieces[i]
        signal_data_pieces[i]['timestamp_starttime'].iloc[0] = \
            signal_start_pieces[i]
        
 
    #%% export data as csv
    
    columns_for_export = [
        'time',
        'FLOW',
        'ECG',
        'arduino_comments',
        'timestamp_comment',
        'timestamp_starttime'
        ]
    
    
    experiment_time = 0
    sampling_interval = \
        signal_data_pieces[0]['time'].iloc[1] - \
            signal_data_pieces[0]['time'].iloc[0]
        
    for i in range(len(signal_data_pieces)):
        logger.info(f'Exporting Block {i} : {signal_mode_pieces[i]}')
        
        signal_data_pieces[i][columns_for_export].to_csv(
            input_file[:-4]+f"_{i}_{signal_mode_pieces[i]}.csv",
            index=False
            )
        
        # adjust timing so it doesn't reset to 0 between blocks
        signal_data_pieces[i].loc[:,'time'] = \
            signal_data_pieces[i]['time'] + experiment_time
        
        experiment_time = \
            signal_data_pieces[i]['time'].iloc[-1] = sampling_interval
        
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
                header=True
                )
    


#%% run main
##

if __name__ == '__main__':
    main()
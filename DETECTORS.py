# -*- coding: utf-8 -*-

__version__ = "0.1.0"

# %% import libraries
import numpy
from scipy import signal
import pandas

# %% define functions


# signal conditioners
def basicFilt(CT, sampleHz, f0, Q):
    b, a = signal.iirnotch(f0 / (sampleHz / 2), Q)

    notched = signal.lfilter(b, a, CT)
    # notched=CT
    b, a = signal.butter(1, 1 / (sampleHz / 2), btype="highpass")
    buttered = signal.lfilter(b, a, notched)
    return buttered


def notchFilt(CT, sampleHz, f0, Q):
    b, a = signal.iirnotch(f0 / (sampleHz / 2), Q)

    notched = signal.lfilter(b, a, CT)
    return notched


def butterFilt(CT, sampleHz):
    b, a = signal.butter(1, 1 / (sampleHz / 2), btype="highpass")
    buttered = signal.lfilter(b, a, CT)
    return buttered


# detectors
def basic_breathcall(
    CT, ts, base, thresh
):  # needs debugging for collisions between breaths
    #
    # note - the anticipated signal input duration is ~10sec with sliding repeat performed every 0.1 sec
    # performance can be improved with mdest loss of precision by downsampling input signal (minimum~50Hz)
    # find thresh crossing
    ##
    logic_AT = [1 if i > thresh else 0 for i in CT]
    logic_BB = [1 if i < base else 0 for i in CT]
    logic_Ins = [logic_AT[i + 1] - logic_AT[i] for i in range(len(CT) - 1)]
    index_i = [
        i + 1 for i in range(len(logic_Ins)) if logic_Ins[i] == 1
    ]  # index of inspiration threshold crosses
    BC = {}
    ##
    if len(index_i) == 0:
        return BC
    ##
    BC_list = []
    ##
    if sum(logic_BB) == 0:
        return BC
    ##
    index_b = [
        i for i in range(len(logic_BB)) if logic_BB[i] == 1
    ]  # index of below baseline values
    # check for closest baseline cross preceding, skip if prior baseline belongs to prev crossing
    #
    FIRST_BREATH_FOUND = False
    for i in range(len(index_i)):
        validbreath = False
        # skip until first base crossing is available
        if index_i[i] < index_b[0]:
            continue  # no baseline crossing found before current thresh crossing
        if FIRST_BREATH_FOUND == False:
            # scan back until baseline cross (CT[index_b[0]])
            for j in range(index_i[i], index_b[0], -1):
                if CT[j] > base:
                    continue
                else:
                    FIRST_BREATH_FOUND = True
                    validbreath = True
                    break
        else:
            for j in range(
                index_i[i], index_i[i - 1], -1
            ):  # skip if prior baseline belongs to prev crossing
                if j <= index_i[i - 1] + 1:
                    break  # skip segment - belongs to prior breath exp phase
                if CT[j] > base:
                    pass
                else:
                    validbreath = True
                    break
        if validbreath == False:
            continue

        BC[ts[j]] = {"TS-I": ts[j]}
        BC_list.append(ts[j])
        #
        # check for closest baseline cross following
        if index_i[i] != index_i[-1]:  # check if special case dealing with last breath
            for k in range(index_i[i], index_i[i + 1], 1):
                if CT[k] >= base:  # consider if should be >=
                    BC[ts[j]]["TS-E"] = ts[k]
                else:
                    break
        else:
            for k in range(index_i[i], len(CT), 1):
                if CT[k] >= base:  # consider if should be >=
                    BC[ts[j]]["TS-E"] = ts[k]
                else:
                    break
        BC[ts[j]]["j"] = j
        BC[ts[j]]["k"] = k
        # fill in BC measures TI PIF iTV
        BC[ts[j]]["TI"] = ts[k] - ts[j]
        # BC[ts[j]]['PIF']=max(CT[j:k])
        BC[ts[j]]["iTV"] = (
            sum(CT[j:k]) - len(CT[j:k]) * base
        )  # updated to reflect volume if baseline !=0
    # fill in BC measures TE PEF eTV
    for i in range(len(BC_list) - 1):
        BC[BC_list[i]]["TE"] = BC[BC_list[i + 1]]["TS-I"] - BC[BC_list[i]]["TS-E"]
        BC[BC_list[i]]["TT"] = BC[BC_list[i]]["TI"] + BC[BC_list[i]]["TE"]
        # BC[ts[BC_list[i]]]['PEF']=min(CT[BC[BC_list[i]]['k']:BC[BC_list[i+1]]['j']])
        BC[BC_list[i]]["eTV"] = (
            sum(CT[BC[BC_list[i]]["k"] : BC[BC_list[i + 1]]["j"]]) * -1
        ) + len(
            CT[BC[BC_list[i]]["k"] : BC[BC_list[i + 1]]["j"]]
        ) * base  # updated to reflect volume if baseline !=0
        BC[BC_list[i]]["DVTV"] = (
            abs(BC[BC_list[i]]["iTV"] - BC[BC_list[i]]["eTV"]) / BC[BC_list[i]]["iTV"]
        )
    ##
    return BC


def beat_caller(CT, TS, absthresh=0.74, minRR=0.10):
    """
    Extract R-R intervals and calculate heart rate from an ECG signal.
    This version uses scipy.signal.find_peaks function.
    Function and settings based on code from SLusk.

    Parameters:
    - CT (array-like): The raw ECG data.
    - TS (array-like): Timestamps corresponding to the ECG data points.
    - absthresh (float): Absolute Voltage Threshold for beat detection.
    - minRR (float): Minimum RR interval in seconds to consider for heart rate calculation.

    Returns:
    - DataFrame: DataFrame containing
        timestamps ['ts']
        RR intervals ['rr']
        heart rates ['hr']
    """

    # Convert CT to a numpy array if it isn't one already
    CT = numpy.array(CT)
    TS = numpy.array(TS)
    sampling_time = TS[1] - TS[0]

    peak_finding_distance = int(minRR / sampling_time)

    # Identify peaks in the ECG signal; adjust parameters as necessary for your data
    peaks, _ = signal.find_peaks(
        CT, height=absthresh, distance=peak_finding_distance
    )  # Adjust 'distance' as needed

    # Extract timestamps for the detected peaks
    timestamps_peaks = numpy.take(TS, peaks, axis=0)

    # Calculate RR intervals in seconds
    rr_intervals = numpy.diff(timestamps_peaks)

    # Calculate heart rate from rr intervals
    heart_rates = [60 / ri for ri in rr_intervals]

    # Prepare dataframe to return
    beat_df = pandas.DataFrame(
        {
            "ts": timestamps_peaks[:-1],  # Exclude the last timestamp
            "rr": rr_intervals,
            "hr": heart_rates,
        }
    )

    return beat_df

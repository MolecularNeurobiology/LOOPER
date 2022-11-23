<H1> Autoresuscitation </H1>
repository for neonate autoresuscitation assay project (code, schematics, protocols)

<H2>Code - PCC</H2>
Physiology Command Center
(C) 2019
@author: Christopher Ward (christow@bcm.edu, ward.chris.s@gmail.com)

Created as part of the Russell Ray Molecular Neurobiology Group's
Autoresuscitation Project

contributions to this project include code, concepts, or consultation from 
several individuals including Russell Ray, Eunice Aissi, Dipak Patel, 
Mariana Garcia Costa, Savannah Lusk, Brandon Ruiz, Kevin Jiang, and 
Shourya Munjal.


This software provides a graphical interface for I/O between an computer
and 1) Arduino Microcontroller, 2) LabJack Analog to Digital Converter.
Signals from the LabJack undergo signal processing to identify key features
used as triggers to execute programmed control sequences run by the Arduino.

The current implementation utilizes pneumotachography and electrocardiogram 
signals to monitor breathing and heart rate as part of a neonate 
autoresuscitation assay.

<H3>Inputs/Outputs</H3>
Inputs: currently none - all settings are coordinated within the GUI
Outputs: timeseries signal datafile 
    [calibration capture, animal signal capture] - this is currently one file 
    with seperate sections

<H3>Default Workflow (subject to change)</H3>

0-signal preview mode (adjust baseline and confirm tunable parameters)
**user confirmation for next step
1-calibration mode (receive calibration signals [20x30uL pulses])
**signal to DC out [trigger auto pipette and LED] upon start
**end upon timer (and confirmation from auto pipett upon complete?)
+++creates save file for calibration values
2-signal preview mode (adjust baseline and confirm tunable parameters)
**user confirmation for next step
3-habituation mode (wait 30 minutes for habituation)
**preview and capture signals for review later - consider updates to interval
4-baseline mode (capture 10 minutes of signal for baseline)
**preview and capture signals - consider criteria of 
    QUANTITY_OF_QUALITY signal...
    Q_O_Q : 10 seconds per interval of 'calm breathing', 
    sum of intervals is at least 1 minute
5-challenge mode (ANOXIA challenge until breath cessation, 
    Room Air until recovery....recovery based on >=X% HR and BPM recovery)
**preview and capture signals - include tags for ANOXIA vs ROOM AIR
**signal to DC/Serial out 
    [trigger to switch between modes (DC on for ANOXIA, DC off for ROOM AIR)]
**move to EXPERIMENT ENDED mode upon failure to recover breathing/hr
6-experiment ended mode 
**terminate preview and capture, send signal to notify user
**signal to DC out, or other Raspberry Pi notification

<H2>Code - AGE</H2>
Automated Gas Exchanger
Arduino Code
...

<H2>Schematics</H2>
...

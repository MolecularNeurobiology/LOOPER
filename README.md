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

<H3>Environment and Installation Notes</H3>
recommend usage of UV for python environment management
dependencies need to be installed
"sudo apt-get install erlang logrotate"
"sudo apt install rabbitmq-server"

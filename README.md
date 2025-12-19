# LOOPER
Live Observation and Operation of Physiology Experiments with Robotics

# What is it?
LOOPER is an automated data collection platform for neonate pneumotachography experiments focused on the Autoresuscitation Reflex Assay. It is primarily written in python, and arduino code (C++). Tools to aid in analysis of data collected with LOOPER is co-released at https://github.com/MolecularNeurobiology/Breathe_Easy

# Main Features
What does LOOPER do?

1. realtime data collection using a labjack analog to digital interface
1. realtime detection of breathing and heartbeat
1. automated control of experiment steps via communications with an arduino microcontroller and robotics components
  1. calibration air injections with a roboticly actuated micropipette
  1. initiation of gas challenges with valve controls and motorized placement of gas exposure outlets
  1. identification of sustained apnea
  1. automated transition back to room air
  1. automated detection of cardio-respiratory recovery
  1. repetition autoresuscitation challenges

# Where to get it?
Our software is available as source code compatible with Raspberry Pi 4 and Raspberry Pi 5 SBC's running Raspberry Pi OS.

# Where is the manual?
Access the full user manual for this software [here](https://realchrisward.github.io/LOOPER/User_Manual/_build/html/index.html).
Access the build guide for the robotics components [here]((https://realchrisward.github.io/LOOPER/doc/build/html/index.html).

# Dependencies
The environment needed to run LOOPER can be created using a python virtual enviroment tool (such as miniforge). A requirements.txt and pyproject.toml file enumerate the python packages and versions that are suggested. The platform is designed to work with a robotic system (described [here](https://realchrisward.github.io/LOOPER/)) - Arduino code needed for flashing the microcontroller is available in the ArduinoCode subfolder

## Installation and Usage - Python component
### Install Python3
Download python [here](https://www.python.org/downloads/)
or https://conda-forge.org/download/

### Install Python Dependencies
Activate Python virtual environment to help manage package installation.
```
# Posix
python3 -m venv <venv>
source <venv>/bin/activate
```

Install dependencies
```
pip install -r requirements.txt
```

### Running From source
```
# Posix
source venv/bin/activate
python3 PCC.py
```

# Licensing
'LOOPER' is dually licensed. The project is available under a 'GPLv3 or later' license as well as a commercial license (inquiries for commercial licensing may be directed to Russell.Ray@bcm.edu). 

    LOOPER - Live Observation and Operation of Physiology Experiments with Robotics
    Copyright (C) 2019  
    Christopher Ward, Nicoletta Memos, Savannah Lusk,
    Mariana Garcia Costa, Wenyu Zuo, Eunice Aissi, Brandon Ruiz, 
    Dipak Patel, Kevin Jiang, Andersen Chang, and Russell Ray.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

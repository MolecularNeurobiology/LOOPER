#!/bin/bash
cd /home/pi/git/Autoresuscitation
git fetch --tags
git checkout stable_2024-12-11a
git reset --hard stable_2024-12-11a
source activate py38
python /home/pi/git/Autoresuscitation/GEMouse.py &
python /home/pi/git/Autoresuscitation/PCC.py

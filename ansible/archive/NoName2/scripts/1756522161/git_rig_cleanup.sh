#!/bin/bash
source /home/pi/mambaforge/bin/activate py38
cd /home/pi/git/Autoresuscitation
git fetch
git reset --hard stable_2025-02-11b
python /home/pi/git/Autoresuscitation/rig_clean_up.py
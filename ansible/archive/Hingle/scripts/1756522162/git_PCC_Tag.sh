#!/bin/bash
source /home/pi/mambaforge/bin/activate py38
cd /home/pi/git/Autoresuscitation
git fetch
git reset --hard stable_2025-08-20a
python /home/pi/git/Autoresuscitation/PCC.py
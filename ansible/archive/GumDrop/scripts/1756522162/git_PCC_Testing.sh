#!/bin/bash
source /home/pi/mambaforge/bin/activate py38
cd /home/pi/git/Autoresuscitation
git fetch
git reset --hard dev_2025-07-15a
python /home/pi/git/Autoresuscitation/PCC.py
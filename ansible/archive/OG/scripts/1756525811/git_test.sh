#!/bin/bash
source /home/pi/mambaforge/bin/activate py38
cd /home/pi/git/Autoresuscitation
git fetch
git checkout challenge_timer_features
git pull
git reset --hard
python /home/pi/git/Autoresuscitation/PCC.py
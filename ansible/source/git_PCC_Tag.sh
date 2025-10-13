#!/bin/bash
# bash script to run PCC

tag="stable_2025-08-20a"

# go to repository directory, git reset to tag
cd $HOME/git/Autoresuscitation
git fetch --tags
git checkout stable
git pull
git checkout $tag
git reset --hard $tag
git clean

# set-up python environment and run
source /home/pi/mambaforge/bin/activate py38
python /home/pi/git/Autoresuscitation/PCC.py
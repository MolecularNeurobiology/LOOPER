#!/bin/bash
cd /home/pi/git/Autoresuscitation
git fetch
git reset --hard dev_2025-07-23b
uv run /home/pi/git/Autoresuscitation/GEMouse.py
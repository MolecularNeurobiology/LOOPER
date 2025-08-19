#!/bin/bash

# ==== IMPROVED RSYNC SCRIPT WITH NETWORK STABILITY CHECKS ====
today=$(date +"%y%m%d")
RIGNAME="RIGNAME"  # Change this value to set the rig name
source_dir="/media/pi/${RIGNAME}/"                
destination_dir="/home/pi/data2/Projects" 

output_file="/home/pi/Desktop/Rsync_Results/${today}_${RIGNAME}.txt"
logfile="/home/pi/Desktop/Rsync_Cron_Debug/${today}_${RIGNAME}.log"
error_file="/home/pi/Desktop/Rsync_Error/${today}_${RIGNAME}.txt"
network_test_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_test.log"
network_monitor_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_monitor.log"

max_attempts=3
target_host="10.20.16.88"

echo $source_dir

#!/bin/bash
 
 #Mount data2
 sudo mount -a
 
 #Systemctrl-Deamon
 sudo systemctl daemon-reload
 
 #Check to make sure data2 is mounted
 if ! mount | grep -q '/home/pi/data2'; then
 touch /home/pi/Desktop/Rsync_Error_RigName.txt #Don't forget to add the rig name at the end
 exit 1
 fi 
 
 #Set Variables
 SOURCE_DIR="/media/pi/Rig_Name/" #(path to external drive but make sure the "/" is at the end after the name)
 DESTINATION_DIR="/home/pi/data2/Projects"
 OUTPUT_FILE="/home/pi/Desktop/Rsync_Results_RigName.txt" #Don't forget to add the rig name at the end
 
 #Rsync Command
 sudo rsync -avz -i -c -itemize-changes --stats --human-readable $SOURCE_DIR $DESTINATION_DIR > $OUTPUT_FILE

#!/bin/sh -e
#

# Added execution and logging of the MTP-TeamB-2019 project
date_str="$(date +%Y-%m-%d_%k-%M-%S)"

stdbuf -oL python3 /home/pi/MTP-TeamB-2019/main.py > "/home/pi/MTP-TeamB-2019/logs/log__$date_str.log"

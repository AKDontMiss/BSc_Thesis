#!/bin/bash

echo "Starting Dual-Engine PMU Sequence..."

# Step 1: Data Broadcaster (Locked to Core 1, Highest Priority)
echo "Starting MulticastSV..."
screen -dmS MulticastSV bash -c 'cd /home/pi/OpenPMU-KTH/Multicast/SV/UDP_to_MC/ && sudo taskset -c 1 nice -n -20 python3 OpenPMU_UDP_to_MC.py'
sleep 2

# Step 2: Wave Logger
echo "Starting SVtoWave..."
screen -dmS SVtoWave bash -c 'cd /home/pi/OpenPMU-KTH/SVtoWave/ && python3 SVtoWave.py'
sleep 2

# Step 3: Math Engines (Locked to Cores 2 and 3, Highest Priority)
echo "Starting Estimators..."
screen -dmS PhasorEst01 bash -c 'cd /home/pi/OpenPMU-KTH/PhasorEst01/ && sudo taskset -c 2 nice -n -20 python3 StartEstimation.py'
screen -dmS PhasorEst02 bash -c 'cd /home/pi/OpenPMU-KTH/PhasorEst02/ && sudo taskset -c 3 nice -n -20 python3 StartEstimation.py'
sleep 3

# Step 4: Loggers and Telecom
echo "Starting CSV Loggers and Telecoms..."
screen -dmS CSVlogger01 bash -c 'cd /home/pi/OpenPMU-KTH/CSVlogger01/ && python3 CSVlogger.py'
screen -dmS CSVlogger02 bash -c 'cd /home/pi/OpenPMU-KTH/CSVlogger02/ && python3 CSVlogger.py'

screen -dmS Telecom01 bash -c 'cd /home/pi/OpenPMU-KTH/Telecom01/ && ./launchTC.sh'
screen -dmS Telecom02 bash -c 'cd /home/pi/OpenPMU-KTH/Telecom02/ && ./launchTC.sh'
sleep 3

# Step 5: CPU Logger
echo "Starting CPU Logger..."
screen -dmS CPUlogger bash -c '/home/pi/OpenPMU-KTH/CPULogger/launchCPU.sh'

echo "All 9 screens successfully launched! System is live."
# -*- coding: utf-8 -*-
"""
OpenPMU - CSVlogger
Copyright (C) 2022  www.OpenPMU.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Modified By Haron Akram Ahmed Mohammed for Bachelors' Thesis 2026
Email: haamo@kth.se
"""

from threading import Thread, Event
from queue import Queue
from datetime import datetime, timedelta
import json
import signal
import os
import time
import glob, shutil

import UDPphasor

# ###################################
# ------------- Threads -------------

# First function is threaded and puts received phasors into a queue
# Second function is called by main programme to get phasors from queue

def get_Phasor(queue_out, IP, Port):
    
    global stopThread
    
    # Set up an instance of the PMU Phasor Value receiver
    pmu = UDPphasor.Receiver(IP, Port)
    
    while not stopThread: 
        
        try:
            dataInfo = pmu.receive()    # Receive the latest frame of Phasor Values from the ADC.
        except:
            continue
        
        if dataInfo is None:        # If there's no frame of data, skip rest of loop and wait for next frame.
            continue
        
        dataInfo2 = dataInfo.copy()
        queue_out.put(dataInfo2)
        
def get_queue(queue_in):
         
    if not queue_in.empty():
        data = queue_in.get()
        data2 = data.copy()
    else:
        data2 = None
    
    return(data2)


# ###################################
# ------------ Functions ------------
        
# Keyboard Interrupt event handler (CTRL+C to quit)
def signal_handler(signal, frame):
    
    global stopThread
    
    stopThread = True
    print('You pressed Ctrl+C!')
    time.sleep(1)
    # pmu.close()
    # sys.exit(0)
    
# Load the config file    
def loadConfig(configFile="config.json"):
    with open(configFile) as jsonFile:
        return json.load(jsonFile)
    
# Covert OpenPMU ADC stream date/time to Python datetime object
def getPMUdatetime(dataInfo):
    
    return datetime.combine(datetime.strptime(dataInfo['Date'], "%Y-%m-%d").date(), datetime.strptime(dataInfo['Time'], "%H:%M:%S.%f").time())

# Covert the dictionary into a single, flat line of phasor values
# --- format is "Date,Time,Frame,<phKeys>*<phChannels>"
def makeCSVline(phDict, phChannels=[], precision=3, phKeys=["Mag", "Angle", "Freq", "ROCOF"]): 
        
    if len(phChannels) == 0:
        phChannels = list(range(phDict["Channels"]))
      
    # Get the datetime of the Phasor, format as ISO time
    phTime  = getPMUdatetime(phDict)
    timeISO = phTime.astimezone().isoformat('T', 'milliseconds')
    
    ExcelDate = str(phTime.date())
    ExcelTime = str(phTime.time())
        
    # CSV Line
    csvLine = str()                                     # Start new line
    csvLine += ExcelDate + "," + ExcelTime + ","        # Add Excel friendly format datetime
    csvLine += str(int(phDict["Frame"] / 2)) +","       # Add phasor frame number (0 = top of second)
    
    # Convert phasor dictionary into strings, append to CSV line  
    for i in phChannels:

        phLine = str()
        
        for key in phKeys:
            
            formatStr = ("{:." + str(precision) + "f}")        
            phLine += formatStr.format(phDict["Channel_%d" % i][key]) + ","
        
        csvLine += phLine
        
    csvLine = csvLine.rsplit(',',1)[0]                  # Remove trailing comma 
    
    return csvLine

# Makes the header for a new CSV file
def makeCSVheader(phChannels=[], phKeys=["Mag", "Angle", "Freq", "ROCOF"]):
    
    if len(phChannels) == 0:
        phChannels = list(range(phDict["Channels"]))
    
    header = str()
    header = 'Date,Time,Frame,'                     # Add initial fields
    
    for i in phChannels:                            # Loop phasor fields
        for key in phKeys:            
            header += key + str(i) + ','            # Add channel number to key          
    return header.rsplit(',',1)[0]                  # Remove trailing comma

# Creates a blank line filled with NaNs to keep time-series alignment perfect in case of Blackouts
def makeDroppedFrameLine(dropTime, phChannels):
    date_str = dropTime.strftime("%Y-%m-%d")
    time_str = dropTime.strftime("%H:%M:%S.%f")
    line = f"{date_str},{time_str},FRAME_DROP"
    for _ in phChannels:
        line += ",NaN,NaN,NaN,NaN"
    return line + "\n"

# Finds the floor datetime for a given interval, used to create CSV filenames
def floorTime(timeIn, interval):

    floorTime = timeIn - timedelta(minutes=timeIn.minute % interval,
                                 seconds=timeIn.second,
                                 microseconds=timeIn.microsecond)
    return floorTime

# Ensure the path to the wavefile exists, if not create the path         
def ensureDir(filePath):
    directory = os.path.dirname(filePath)
    if not os.path.exists(directory):
        os.makedirs(directory) 
        
# Generate CSV file path        
def makeCSVFilePath(csvFileTime, csvPathRoot):        
    csvPathYMD = csvFileTime.strftime("%Y-%m-%d") + "/"
    csvFileName = csvFileTime.strftime("%Y-%m-%d_%H-%M-02.csv")
    csvFilePath = os.path.join(csvPathRoot, "e-IpDFT", csvPathYMD, csvFileName)
    return csvFilePath.replace('\\', '/')
    
        
# Prints the header bar for the CLI progress ticker       
def printProgressHeader(csvTime, frameTime):
    print("CSV file time:", str(csvTime), "- Now:", str(frameTime.time()))
    print('0.........1.........2.........3.........4.........5.........|')

# Delete old records efficiently using the new folder naming convention
def deleteOldRecords(filePathRoot, daysToKeep, dateNow):
    deleteEpoch = dateNow.date() - timedelta(days=daysToKeep)
    print("\nChecking for USB logs older than:", deleteEpoch)    
    
    # glob.glob allows to search specifically for our new YYYY-MM-DD folders inside e-IpDFT
    for path in glob.glob(os.path.join(filePathRoot, "e-IpDFT", "*")):
        if os.path.isdir(path):
            try:
                # Extract just the date string from the folder name
                dateStr = os.path.basename(path)
                folderDate = datetime.strptime(dateStr, "%Y-%m-%d").date()
                
                if folderDate < deleteEpoch:
                    shutil.rmtree(path)
                    print(f"DELETED old log folder: {path}")
                else:
                    print(f"Retained active log folder: {path}")
                
            except Exception as e:
                # If the folder doesn't match our pattern, safely ignore it
                print(f"Skipping unknown folder {path}: {e}")       


    
# ####################################
# --------------- MAIN ---------------

if __name__ == '__main__':
    
    # Keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler)

    print("OpenPMU Phasor Logger")
    
    config = loadConfig("config.json")
    
    phasorQueue = Queue(3000)    
    t = Thread(target=get_Phasor, args=(phasorQueue, config["recvIP"], config["recvPort"]))
    t.start()
    
    # Initialise variables required in loop
    csvBuffer           = str()
    csvWriteBuffer      = str()
    csvFileTimeInUse    = datetime.fromisoformat("1955-11-12T22:04:00")
    frameTime           = datetime.fromisoformat("1955-11-12T22:04:00")
    
    firstLoop = True
    stopThread = False
    while not stopThread:
        
        dataInfo = get_queue(phasorQueue)       # Receive the latest frame of Phasor Values from the ADC.
        if dataInfo is None:                    # If there's no frame of data, skip rest of loop and wait for next frame.
           time.sleep(0.005)
           continue

        # Calculate frame time as Python datetime object
        preFrameTime = frameTime                # Set Previous Frame Time first
        frameTime    = getPMUdatetime(dataInfo)
        
        # Get CSV file time as the floor of the current time and csvInterval
        # csvInterval - Minutes between CSV files, starting at top of the hour        
        csvFileTime = floorTime(frameTime, config["csvInterval"])
        
        if firstLoop == True:
            firstLoop = False
            expected_interval = None
            # Print progress bar header
            printProgressHeader(csvFileTime, frameTime)
            for i in range(frameTime.second):
                print('-', end='')             
            
            continue    # Now that initialisation is complete, restart loop

        # Frame Drop & Blackout Detection
        # Dynamically learn if the PMU is reporting at 1ms or higher speeds
        if expected_interval is None:
            expected_interval = frameTime - preFrameTime 

        time_diff = frameTime - preFrameTime
        
        # If the gap is larger than 1.5x our normal speed, it dropped frames
        if time_diff > (expected_interval * 1.5) and time_diff.total_seconds() > 0:
            dropped_count = int(round(time_diff / expected_interval)) - 1
            
            if time_diff.total_seconds() > 5.0:
                # if long gap (Blackout), such as > 5 sec
                # Save it in a master event log on the USB stick
                event_log_path = os.path.join(config["csvPath"], "System_Events.log")
                ensureDir(event_log_path)
                with open(event_log_path, 'a') as evt_file:
                    evt_file.write(f"[{preFrameTime}] to [{frameTime}] - CRITICAL BLACKOUT: {time_diff.total_seconds()} seconds dropped.\n")
                
                # Write a single warning line in the CSV so it doesn't crash the CPU writing multiple NaNs
                csvBuffer += f"{preFrameTime.strftime('%Y-%m-%d')},{preFrameTime.strftime('%H:%M:%S.%f')},LONG_BLACKOUT" + (",NaN"*len(config["csvChannels"])*4) + "\n"
                
            elif dropped_count > 0:
                # short grap (frame drops)
                # Inject the exact number of missing rows to keep the CSV time-aligned
                for i in range(1, dropped_count + 1):
                    drop_time = preFrameTime + (expected_interval * i)
                    csvBuffer += makeDroppedFrameLine(drop_time, config["csvChannels"])

        
        # Check for second rollover, copy csvBuffer to csvWriteBuffer
        if frameTime.microsecond < preFrameTime.microsecond:
                                    
            csvWriteBuffer += csvBuffer
            csvBuffer = str()
            
            # Progress Bar
            # This updates the console with a tick each second based on received frameTime        
            if ( (frameTime.second - 1) % 10) == 0:
                print('|', end='', flush=True)
            else:
                print('.', end='', flush=True)
                
                
        # Check for minute rollover, write buffer to csvFile
        if frameTime.minute != preFrameTime.minute:            
            
            csvFilePath = makeCSVFilePath(csvFileTimeInUse, config["csvPath"])
            ensureDir(csvFilePath)                  # Make sure directory for CSV file exists
            with open(csvFilePath, 'a') as f:
                f.write(csvWriteBuffer)    
            csvWriteBuffer = str()                              # Clear csvWriteBuffer
        
            print('')                                           # Add a line break
            printProgressHeader(csvFileTime, frameTime)         # Print heartbeat debug info 
     

        # Initialise a new CSV file with header
        if csvFileTime != csvFileTimeInUse:
                        
            header = makeCSVheader(config["csvChannels"])
            
            csvFilePath = makeCSVFilePath(csvFileTime, config["csvPath"])
            ensureDir(csvFilePath)                  # Make sure directory for CSV file exists
            
            with open(csvFilePath, 'a') as f:
                f.write(header + '\n')
                
            csvFileTimeInUse = csvFileTime        
        
        # Check for day rollover (i.e. midnight)
        if frameTime.day != preFrameTime.day:                
            if config["allowDeletion"]:
                print("Deleting records older than %d days" % (config["daysToKeep"]))
                deleteOldRecords(config["csvPath"], config["daysToKeep"], frameTime)
        
        # 1 Second Buffer
        csvLine = makeCSVline(dataInfo, config["csvChannels"])  # Make one line of the CSV file using present phasor 
        csvBuffer += csvLine + "\n"                             # Append to buffer which is copied to csvWriteBuffer each second
        
         
    t.join()    # Join thread, wait for it to terminate
    print("End of programme. Exiting!")  
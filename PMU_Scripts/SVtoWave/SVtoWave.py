# -*- coding: utf-8 -*-
"""
OpenPMU - SVtoWave
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

Modified for 5-Minute Hourly Windowing By Haron Akram Ahmed Mohammed for Bachelors' Thesis
"""

import signal, sys
import time
import json
from datetime import datetime, timedelta
import numpy as np
import glob, shutil
import os

from threading import Thread, Event
from queue import Queue

import PMU
from wavewrite import WaveWrite
        
        
# Threads

# First function is threaded and puts received phasors into a queue
# Second function is called by main programme to get phasors from queue

def get_PMU(queue_out, IP, Port):
    
    global stopThread
    # Set up an instance of the PMU Sampled Value receiver
    
    pmu = PMU.Receiver(IP, Port, forward=False)  
    
    while not stopThread:      
        
        try:
            dataInfo = pmu.receive()    # Receive the latest frame of Sampled Values from the ADC.
        except:
            continue
        
        if dataInfo is None:        # If there's no frame of data, skip rest of loop and wait for next frame.    
            continue
       
        dataInfo2 = dataInfo.copy()        
        queue_out.put(dataInfo2)    
        
    pmu.close()
        
def get_queue(queue_in):
         
    if not queue_in.empty():
        data = queue_in.get()
        data2 = data.copy()
    else:
        data2 = None

    return(data2)
        
# Functions
        
# Keyboard Interrupt event handler (CTRL+C to quit)
def signal_handler(signal, frame):
    
    global stopThread
    
    stopThread = True
    print('You pressed Ctrl+C!')
    time.sleep(1)
    try:
        waveOut.close()
    except:
        pass
    
# Load the config file    
def loadConfig(configFile="config.json"):
    with open(configFile) as jsonFile:
        return json.load(jsonFile)
    
# Get the SV format data from OpenPMU ADC stream
def getSVFormat(dataInfo):
    
    SVformat = {}
    
    # Get SV format data
    SVformat["n"] = dataInfo['n']                   # Number of SVs in the payload
    SVformat["Fs"] = dataInfo['Fs']                 # Sampling rate
    SVformat["bits"] = dataInfo['bits']             # Bit depth
    SVformat["Channels"] = dataInfo['Channels']     # Number of channels
    
    return SVformat

# Get the SVs from the OpenPMU ADC stream, returning only the channels desired to record (recMask) 
def getSVs(dataInfo, recMask=[], SVtype='int16'):

    # dataInfo is the raw output of the PMU's ADC as a Python Dictionary
    # recMask is a list of the desired channel numbers in the order to be returned
    
    dataBuffer = np.zeros([dataInfo["Channels"], dataInfo["n"]], dtype=SVtype) 
    recBuffer = np.zeros([len(recMask), dataInfo["n"]], dtype=SVtype) 
    
    # read Sampled Value (SV) data
    for i in range(0, dataInfo["Channels"]):
        k = 'Channel_%d' % i
        if k in dataInfo.keys():
            # print(len(dataInfo[k]['Payload']),k)
            dataBuffer[i,] = (dataInfo[k]['PayloadRAW'])
    
    # Select the desired channels to return (empty list returns all)
    if len(recMask) > 0:
        i = 0
        for channel in recMask:
            recBuffer[i] = dataBuffer[channel]
            i += 1
    else:
        recBuffer = dataBuffer

    return recBuffer

# Covert OpenPMU ADC stream date/time to Python datetime object
def getPMUdatetime(dataInfo):
    
    return datetime.combine(datetime.strptime(dataInfo['Date'], "%Y-%m-%d").date(), datetime.strptime(dataInfo['Time'], "%H:%M:%S.%f").time())

# Prints the header bar for the CLI progress ticker
def printProgressHeader(fileTime, frameTime, forceHeader=False):
    
    elapsedMins = int((frameTime - fileTime).total_seconds() // 60)     # Integer number of minutes
    
    if elapsedMins == 0 or forceHeader:
        print("Wavefile time:", fileTime)
        print('HH:MM - 0.........1.........2.........3.........4.........5.........|')
    else:
        print('')   # No header required, but need a new line feed
    
    printHour = fileTime.hour
    printMin  = fileTime.minute + elapsedMins
    print('{:02d}:{:02d} - '.format(printHour, printMin), end='', flush=True)
    
    
# Finds the floor datetime for a given interval
def floorTime(timeIn, interval):

    floorTime = timeIn - timedelta(minutes=timeIn.minute % interval,
                                 seconds=timeIn.second,
                                 microseconds=timeIn.microsecond)
    return floorTime

# Delete old records
def deleteOldRecords(folderPath, daysToKeep, currentTime):
    """ Deletes folders older than daysToKeep """
    thresholdDate = currentTime - timedelta(days=daysToKeep)
    
    if os.path.exists(folderPath):
        for folder in os.listdir(folderPath):
            folder_path = os.path.join(folderPath, folder)
            if os.path.isdir(folder_path):
                try:
                    folderDate = datetime.strptime(folder, "%Y-%m-%d")
                    if folderDate.date() < thresholdDate.date():
                        print(f"Deleting old data: {folder_path}")
                        shutil.rmtree(folder_path)
                except ValueError:
                    pass # Ignore folders that aren't named as dates

# MAIN PROGRAM
if __name__ == '__main__':
    
    # Keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    config = loadConfig("config.json")
    
    wavePath        = config["wavePath"]
    recvIP          = config["recvIP"]
    recvPort        = config["recvPort"]
    IS_ALL_GROUPS   = config["IS_ALL_GROUPS"]
    recMask         = config["recMask"]
    waveFrmt        = 'flac'
    waveInterval    = 5


    waveBuffer = np.zeros((3, 15360)) # Number of Channels
    SVformat = {}
    
    print("--------------------------------------------------------")
    print("OpenPMU - Sampled Value (SV) to WAVE file Writer")
    print("Mode: 5-Minute Hourly Window Recording")
    print("--------------------------------------------------------\n")
     
    frameTime = datetime.fromisoformat("1955-11-12T22:04:00")
           
    stopThread = False
    pmuQueue = Queue(3000)    
    t = Thread(target=get_PMU, args=(pmuQueue, recvIP, recvPort))
    t.start()

    firstLoop = True
    stopThread = False

    # How many minutes per hours to record
    RECORDING_WINDOW_MINS = 5
    while not stopThread:
        
        # Receive the latest frame of Sampled Values from the ADC.
        dataInfo = get_queue(pmuQueue)
        
        # If there's no frame of data, skip rest of loop and wait for next frame.
        if dataInfo is None:
            time.sleep(0.005)
            continue
        dataInfo2 = dataInfo.copy()

        # We slice the string to instantly grab the minute without using heavy CPU math!
        current_minute = int(dataInfo['Time'].split(":")[1])

        # The Storage Saver: Only record for the first 5 minutes of the hour
        if current_minute >= RECORDING_WINDOW_MINS:
            if not firstLoop:
                # If it just crossed the 5-minute mark, safely close the file
                try:
                    waveOut.finalise()
                except Exception:
                    pass
                print(f"\n[+] Hourly recording window closed. Resting for {60-RECORDING_WINDOW_MINS} minutes...")
                firstLoop = True  # Reset this so it cleanly creates a new file next hour
            
            # Keep draining the queue but ignore the data; instantly discard the frame to save CPU.
            continue
        
        # Calculate frame time as Python datetime object
        frameTime = getPMUdatetime(dataInfo)

        # Check if the format of SV has changed, is so reinitialise everything
        if SVformat != getSVFormat(dataInfo):
            SVformat = getSVFormat(dataInfo)

            # Get SV format data
            n = SVformat["n"]                               # Number of SVs in the payload
            Fs = SVformat["Fs"]                             # Sampling rate
            bits = SVformat["bits"]                         # Bit depth
            Channels = SVformat["Channels"]                 # Number of channels
            
            totalFrames = int( Fs / n )         # Calculate total number of frames to expect
            validPeriod = n / Fs                # Calculate the valid period of payload
                                     
            # Initialise waveBuffer
            if len(waveBuffer) != len(recMask):
                waveBuffer = np.zeros((len(recMask), Fs))        
                       
        waveFileTime = floorTime(frameTime, waveInterval)
            
        # First loop sets up / initialises all the 'previous' variables
        if firstLoop == True:
            firstLoop = False

            # Set up instance of WaveWrite    
            waveBuffer = np.zeros((len(recMask), Fs))

            waveOut = WaveWrite(frameTime, SVformat["Fs"], len(recMask), wavePath, waveInterval, waveFrmt)  # Create new waveOut
            #waveOut.pad(initialPad)
            
            # Print progress bar header, force special case for first file
            printProgressHeader(waveOut.waveTime, frameTime, forceHeader=True)
            
            # Print dashes to file the 'missing' seconds before programme started
            dashes = int(waveOut.padSeconds % 60 + waveOut.waveLength % 60)
            for i in range(dashes):
                print('-', end='')

            # Initialize preFrameTime here so period math works on the next loop
            preFrameTime = frameTime
            continue  # Now that initialisation is complete, restart loop

        # First thing to do is to check for discontinuities

        # Check for discontinuities
        period = (frameTime - preFrameTime).total_seconds()        
        if period != validPeriod:
            
            # Discontinuties are classed into the following type
            # Type 1 - A small gap which occurs within the current second, 
            #          the normal waveBuffer process will deal with this naturally
            # Type 2 - A medium gap which occurs within the period spanned by the current file (i.e. interval),
            #          but spans more than the present second. Thus, need to pad the current file.
            # Type 3 - A large gap which is longer than the current period of the current file,
            #          meaning finalise the current file, and start a new file when stream resumes.
            
            print("> Discontinuity:", preFrameTime, frameTime, period)            
            print("> Wavefile time: ", waveOut.waveTime)
            
            if frameTime >= (waveOut.waveTime + timedelta(minutes = waveOut.waveMinutes)):
                print("> DISC: Type 3 (large), needs a NEW file")
                waveOut.append(waveBuffer)                                                  
                waveOut.finalise()                                                          
                
                waveOut = WaveWrite(frameTime, SVformat["Fs"], len(recMask), wavePath, waveInterval, waveFrmt)  
                waveBuffer = np.zeros((len(recBuffer), Fs))
                
            elif frameTime.second == preFrameTime.second:
                print("> DISC: Type 1 (small), waveBuffer will take care of it")
                # Do nothing, continue as normal
            
            else: # elif frameTime.minute == waveOut.waveTime.minute:
                print("> DISC: Type 2 (medium), need to PAD this file")                
                waveOut.append(waveBuffer)                                                  
                
                padLength = np.floor((frameTime - waveOut.waveTime).total_seconds()) - waveOut.getLength()
                
                if padLength < 0:                                                           
                    print("> ERROR: Pad length <0: ", padLength, frameTime.second, waveOut.getLength())
                else:
                    waveOut.pad(int(padLength))
                waveBuffer = np.zeros((len(recBuffer), Fs))                             # Create new empty waveBuffer
           
        else:   
            # No discontinuity, happy days!  The follow handles normal buffering and writing.

            # Check for second rollover
            if frameTime.microsecond < preFrameTime.microsecond:
                waveBufferTest = waveBuffer.copy()
                waveOut.append(waveBuffer)                                              # Write out existing waveBuffer                
                waveBuffer = np.zeros((len(recBuffer), Fs))                             # Create new empty waveBuffer 
             
                # Progress Bar
                # ~ This updates the console with a tick representing the time the waveBuffer
                # ~ which has just been appended represents (i.e. present second minus 1).
                # ~ i.e. on the 1st frameTime.second, append the waveBuffer containing 0th second.
                
                if ( (frameTime.second - 1) % 10) == 0:
                    print('|', end='', flush=True)
                else:
                    print('.', end='', flush=True)            

            # How the timing works:
            # ------------------------------
            # On the '0th second', the above IF statement writes out the waveBuffer which
            # is now full of the '59th second' to the wavefile. The IF statement below then
            # finalises the file and starts a new file.
                       
            
            # Check for file rollover and create new file
            # Else check for minute rollover to update console
            if waveFileTime != waveOut.waveTime:             
                waveOut.finalise()                                                      # Close existing waveOut
                waveOut = WaveWrite(waveFileTime, SVformat["Fs"], len(recMask), wavePath, waveInterval, waveFrmt)  # Create new waveOut
                print('')                                                               # Add a line break
                printProgressHeader(waveOut.waveTime, frameTime)                        # Print heartbeat debug info
            elif frameTime.minute != preFrameTime.minute:
                printProgressHeader(waveOut.waveTime, frameTime)                        # Print heartbeat debug info                  
        
            # Check for day rollover (i.e. midnight) to execute cleanup
            if frameTime.day != preFrameTime.day:                
                if config.get("allowDeletion", False):
                    print("Deleting records older than %d days" % (config["daysToKeep"]))
                    deleteOldRecords(config["wavePath"], config["daysToKeep"], frameTime) 
        
        # 1 Second Buffer
        recBuffer = getSVs(dataInfo, recMask)                                           # Get the SVs to record        
        thisFrame = dataInfo['Frame']                                                   # Get the frame number of this frame
        waveBuffer[0:len(recBuffer),128*thisFrame:128*(thisFrame+1)] = recBuffer        # Add the SVs to the 1 second buffer
        
        # Update previous time at the very end of the loop
        preFrameTime = frameTime

    t.join()
    print("Programme ended.")
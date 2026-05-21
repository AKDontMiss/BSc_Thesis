from __future__ import print_function
from estimation.method.Base import EstimatorBase
from estimation.method.LeastSquareOffline import LeastSquare as LeastSquareOffLine
from estimation.method.LeastSquareOnline import LeastSquare as LeastSquareOnline
from estimation.interface.tools import getLocalIP
import json
import signal, sys
import time
import os

__author__ = 'Xiaodong & OpenPMU Admin and modified by Haron Akram Ahmed Mohammed'

# Define Available Estimation Methods
estimationMethodList = {
    # Optimization: epsFre is set to 0.01 instead of 0.001.
    # This slightly reduces the frequency resolution of the offline matrix, 
    # but prevents the Raspberry Pi from running out of RAM and crashing during boot!
    "leastsquareoffline": lambda Fs, sampleLen: \
        LeastSquareOffLine(harmonicsNo=10, Fs=Fs, sampleLen=sampleLen, minFre=25, maxFre=75, epsFre=0.01, maxStep=5),
    "leastsquareonline": lambda Fs, sampleLen: \
        LeastSquareOnline(harmonicsNo=0, Fs=Fs, sampleLen=sampleLen, minFre=25, maxFre=75, epsFre=0.01, maxStep=2),
}

# Configuration Loader 
# Optimization: By using os.path.abspath, the script always knows exactly where 
# to find config.json, regardless of which folder the user launches it from.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(SCRIPT_DIR, "config.json")

def loadConfig():
    global receiveIP, receivePort, sendIP, sendPort, estimationFrequency, estimationMethod
    try:
        with open(config_file) as j:
            config = json.load(j)
            receiveIP = config["receiveIP"]
            receivePort = config["receivePort"]
            sendIP = config["sendIP"]
            sendPort = config["sendPort"]
            estimationFrequency = config["estimationFrequency"]
            estimationMethod = config["estimationMethod"]
    except Exception as e:
        print(f"Error loading config: {e}")

# Thread Setup & Execution
def phasorEstimation(receiveIP, receivePort, sendIP, sendPort, estimationFrequency, methodName):
    estimation = EstimatorBase(receiveIP, receivePort, sendIP, sendPort)  
    estimation.estimationFrequency = estimationFrequency
    estimation.estimationMethod = estimationMethodList.get(methodName)
    
    # Print the header for the console synchrophasor printout
    print("\tDate      \tTime      \tChannel \tMagnitude \tFrequency \tPhase angle \tROCOF")
    return estimation                  
                   
def signal_handler(signal, frame):
    print('\n[!] Ctrl+C detected. Safely stopping the Estimator thread...')
    estimation.stop()       
    time.sleep(1)           
    print('Exiting OpenPMU LSM Engine. Goodbye!')
    sys.exit(0)             

# Main Execution Block
if __name__ == "__main__":
    print("--------------------------------------------------------")
    print("Welcome to OpenPMU V2 - Phasor Estimator (LSM Edition)")
    print("--------------------------------------------------------\n")

    IP_list = getLocalIP()
    print("Local ip address is %s\n" % IP_list)       

    loadConfig()                                    

    print("---------------------Configuration---------------------")
    print("Phasor estimation frequency is:       %d" % estimationFrequency)
    print("Phasor estimation method is:          %s" % estimationMethod)
    print("Receiving Sampled Values (SV) from:   %s:%d" % (receiveIP, receivePort))
    print("Sending phasor result to:             %s:%d\n" % (sendIP, sendPort))

    estimation = phasorEstimation(receiveIP, receivePort, sendIP, sendPort, estimationFrequency, estimationMethod)          

    signal.signal(signal.SIGINT, signal_handler)
    estimation.start()

    while True:
        time.sleep(1)
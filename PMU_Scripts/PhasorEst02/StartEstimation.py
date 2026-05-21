from __future__ import print_function
from estimation.method.Base import EstimatorBase
from estimation.method.EnhancedIpDFT import Estimator as EnhancedIpDFT
from estimation.interface.tools import getLocalIP
import json
import signal, sys      
import time             
import os

__author__ = 'Xiaodong & OpenPMU Admin and modified by Haron Akram Ahmed Mohammed'

# Define Available Estimation Methods
estimationMethodList = {
    "enhancedipdft": lambda Fs, sampleLen: EnhancedIpDFT(Fs=Fs, sampleLen=sampleLen)
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
            estimationMethod = str(config["estimationMethod"]).lower()
    except Exception as e:
        print(f"Error loading config.json: {e}")
        sys.exit(1)

# Thread Setup & Execution
def phasorEstimation(receiveIP, receivePort, sendIP, sendPort, estimationFrequency, methodName):
    estimation = EstimatorBase(receiveIP, receivePort, sendIP, sendPort)  
    estimation.estimationFrequency = estimationFrequency
   
    method = estimationMethodList.get(methodName)
    if method is None:
        method = estimationMethodList["enhancedipdft"]
       
    estimation.estimationMethod = method

    # Print the header for the console synchrophasor printout
    print("\n\tDate      \tTime      \tChannel \tMagnitude \tFrequency \tPhase angle \tROCOF")
    return estimation                  
                   
def signal_handler(signal, frame):
    print('\n[!] Ctrl+C detected. Safely stopping the Estimator thread...')
    estimation.stop()       
    time.sleep(1)           
    print('Exiting OpenPMU. Goodbye!')
    sys.exit(0)             

# Main Execution Block
if __name__ == "__main__":
    print("--------------------------------------------------------")
    print("Welcome to OpenPMU V3 - Enhanced Phasor Estimator")
    print("Engine: e-IpDFT")
    print("--------------------------------------------------------\n")

    IP_list = getLocalIP()
    print("Local ip address is %s" % IP_list)       

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
"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Modified By Haron Akram Ahmed Mohammed for Bachelors' Thesis
| **Editor:** Haron Akram Ahmed Mohammed
| **Email:** haamo@kth.se

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module contains all basic configurations for the OpenPMU. 

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)
| 03-11-2022       Loading config from config.json in parent folder

"""

import json
import socket


##############################################################################################################################################
##############################################################################################################################################
# OPERATIONAL_MODE                  Available options: commanded or spontaneous
#                                   commanded:    OpenPMU Telecom block sends IEEE C37.118.2 messages only when commands
#                                                 are received (Similar as in commercial PMUs). OpenPMU will work in
#                                                 publish/subscribe fashion. This is done over TCP.
#			            spontaneous:  OpenPMU Telecom block continuously sends IEEE C37.118.2 messages to 
#                                                 the specified destination without waiting for command messages. 
#                                                 This is non-standard way and done over UDP.
#
# SPONTANEOUS_DESTINATION_IP        Destination IP address. Only used if the OPERATIONAL_MODE is specified as spontaneous.
# SPONTANEOUS_DESTINATION_Port      Destination UDP port number. Only used if the OPERATIONAL_MODE is specified as spontaneous. 
#                                   Default port number is 4713 according to IEEE C37.118.2-2011 standard
#
# SERVER_PORT_TCP                   Listening TCP port number for IEEE C37.118.2 commands. Only used if the OPERATIONAL_MODE is 
#                                   specified as commanded. Default port number is 4712 according to IEEE C37.118.2-2011 standard
#
# XML_UDP_Port                      Listening UDP port number for receiving XML formatted synchrophasors from OpenPMU Phasor Estimation Block.
#  
# STN                               Station Name (Max. 16 Bytes). Additional info required in IEEE C37.118.2 but not present in XML messages.
#                                   Leave blank to use hostname                                    
# IDCODE                            OpenPMU ID number (Range is 1-65534). Represents the data stream source. Additional info required in 
#                                   IEEE C37.118.2 but not present in XML messages.
# FNOM                              Must be 0 if nominal line frequency is 60 Hz. Must be 1 if nominal line frequency is 50 Hz. Specify 
#                                   it accordingly.
# REPORTING_RATE                    Number of messages OpenPMU is sending per second. Additional info required in IEEE C37.118.2 
#                                   but not present in XML messages.
#
# LogLevel                          Allowed values: debug, info, warning and error. Default value: debug
# LogColored                        Prints log in different colors. Allowed values: yes or no
##############################################################################################################################################
##############################################################################################################################################

# global OPERATIONAL_MODE, SPONTANEOUS_DESTINATION_IP, SPONTANEOUS_DESTINATION_Port, SERVER_PORT_TCP, XML_UDP_Port, STN, IDCODE, FNOM, REPORTING_RATE, LogLevel, LogColored
# global receiveIP, receivePort, sendIP, sendPort, estimationFrequency, estimationMethod
config_file = "config.json"

try:
    with open(config_file) as j:
        config = json.load(j)
        OPERATIONAL_MODE = config["OPERATIONAL_MODE"]
        SPONTANEOUS_DESTINATION_IP = config["SPONTANEOUS_DESTINATION_IP"]
        SPONTANEOUS_DESTINATION_Port = config["SPONTANEOUS_DESTINATION_Port"]
        SERVER_PORT_TCP = config["SERVER_PORT_TCP"]
        XML_UDP_Port = config["XML_UDP_Port"]
        STN = config["STN"]
        IDCODE = config["IDCODE"]
        FNOM = config["FNOM"]
        REPORTING_RATE = config["REPORTING_RATE"]
        LogLevel = config["LogLevel"]
        LogColored = config["LogColored"]

        if STN == "":
            STN = socket.gethostname()


except Exception as e:
    print(e)


##############################################################################################################################################
##############################################################################################################################################
#                                    ***** DON'T TOUCH BELOW CONFIGURATIONS *****
#
# Some are updated live when messages are received from the OpenPMU Phasor Estimation Block. 
# Some indicates how data should be packed by sender and unpacked by receiver.  
##############################################################################################################################################
##############################################################################################################################################

# A control variable controlling all software threads. All threads will close if its value changes to 0.
keepSoftwareRunning = 1

# OpenPMU IEEE C37.118.2 configurations generated and saved (value 1) or not saved yet (value 0).
IEEEC37_ConfigurationsSaved = 0	

# Resolution of FRACSEC timestamp. Second fractional part = FRACSEC/TIME_BASE. Keep it 1  (Don't modify).
TIME_BASE = 1000

# Everything (phasors, analogs, frequency, etc) are in floating point format and phasors in polar format. 
FORMAT = 0x000F 

# Number of phasor values (3 phasors are in the XML format).
PHNMR = 3

# Number of Analog values (e.g., control signal, transducer value, etc). Not used at present but included two values for future use. 
ANNMR = 0

# Number of Digital Status Words. 1 word = 16 bits = 16 digital status points/breakers. Not used at present but included 1 word (16 status points) for future use. 
DGNMR = 0

# It stores the names of all phasors and channels that the OpenPMU is sending inside data messages. These names are provided in the configuration message. It uses python dictionary concept.
CHNAM = {0: ""}

# It stores the conversion factor for phasor channels using python dictionary concept.
PHUNIT = {0: ""}

# It stores the conversion factor for analog channels using python dictionary concept.
ANUNIT = {0: ""}

# It stores the mask words for digital status words using python dictionary concept.
DIGUNIT = {0: ""}

# Configuration change count. It is incremented each time a change is made in the OpenPMU configurations.
CFGCNT = 1

# Number of PMUs. A PDC related feature. Must be 1 for OpenPMU.
NUM_PMU  = 1

# Rate at which the PMU is sending synchrophasors.
DATA_RATE = int(REPORTING_RATE)

# PMU IDCODE. A PDC related feature. In case of PMU, both IDCODEs must be same.
IDCODE_PMU = IDCODE
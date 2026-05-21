# -*- coding: utf-8 -*-
"""
OpenPMU - Multicast Tools
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
"""
import signal, sys
import socket
import struct
import json
from datetime import datetime

# Keyboard Interrupt event handler (CTRL+C to quit)
def signal_handler(signal, frame):
    global runLoop 
    runLoop = False
    print('You pressed Ctrl+C!')
    udpTxSock.close()
    mcRxSock.close()
    sys.exit(0)
  
# Load the config file
def loadConfig(configFile="config.json"):
    with open(configFile) as jsonFile:
        return json.load(jsonFile)
    
# Heartbeat 'tick' on console
def heartbeat(prev):
    now = datetime.now()
    if now.second != prev.second:
        print(".", end="", flush=True)
    return now

def MCreceive(MCAST_GRP, MCAST_PORT):
    mcRxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    mcRxSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mcRxSock.bind(('', MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY) # Many comments online say this method is wrong
    mcRxSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    mcRxSock.settimeout(1)                         # Timeout 1 second
    return mcRxSock

def UDPtransmit():
    udpTxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP 
    return udpTxSock

#-----------------
#####  MAIN  #####
if __name__ == '__main__':
    
    # Keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)
        
    print("OpenPMU - Multicast to UDP")
    
    config = loadConfig("config.json")
    
    UDP_IP        = config["UDP_IP"]
    UDP_PORT      = config["UDP_PORT"]
    MCAST_GRP       = config["MCAST_GRP"]
    MCAST_PORT      = config["MCAST_PORT"]
    
    # Setup MC Receive Socket
    mcRxSock = MCreceive(MCAST_GRP, MCAST_PORT)
    
    # Setup UDP Transmit Socket
    udpTxSock = UDPtransmit()
    
    print("Go!")
    
    # Loop forever (CTRL+C to quit)
    runLoop = True
    prev = datetime.now()
    while runLoop:
        try:
            # Receive from MC group, send to UDP
            data, addr = mcRxSock.recvfrom(10240)  # buffer size is 10240 bytes
            udpTxSock.sendto(data, (UDP_IP, UDP_PORT))
            # Heartbeat on console
            prev = heartbeat(prev)
        except Exception as e:
            print(e)
            pass
        
    udpTxSock.close()     
    mcRxSock.close()
        
        
    
    
    

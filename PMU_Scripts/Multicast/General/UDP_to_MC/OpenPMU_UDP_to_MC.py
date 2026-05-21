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
import json
from datetime import datetime

# Keyboard Interrupt event handler (CTRL+C to quit)
def signal_handler(signal, frame):
    global runLoop 
    runLoop = False
    print('You pressed Ctrl+C!')
    mcTxSock.close()
    udpRxSock.close()
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

def UDPreceive(UDP_IP, UDP_PORT):
    udpRxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # Internet, UDP
    
    # BUFFER EXPANSION 
    # Force Python to use a 4MB receive buffer to prevent dropped frames!
    udpRxSock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4194304)
    
    udpRxSock.bind((UDP_IP, UDP_PORT))
    udpRxSock.settimeout(1)                                         # Timeout 1 second
    return udpRxSock

def MCtransmit():
    mcTxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # BUFFER EXPANSION
    # Force Python to use a 4MB send buffer for the outbound Multicast traffic
    mcTxSock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4194304)
    
    mcTxSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    return mcTxSock

if __name__ == '__main__':
    
    # Keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)
        
    print("OpenPMU - UDP to Multicast")
    
    config = loadConfig("config.json")
    
    UDP_IP        = config["UDP_IP"]
    UDP_PORT      = config["UDP_PORT"]
    MCAST_GRP       = config["MCAST_GRP"]
    MCAST_PORT      = config["MCAST_PORT"]
        
    # Setup UDP Receive Socket
    udpRxSock = UDPreceive(UDP_IP, UDP_PORT)
    
    # # Setup MC Transmit Socket
    mcTxSock = MCtransmit()
    
    print("UDP_IP:       {:>15}   - UDP_PORT:    {}".format(UDP_IP, UDP_PORT))
    print("MCAST_GRP:    {:>15}   - MCAST_PORT:  {}".format(MCAST_GRP, MCAST_PORT))
    print("Go!")
    
    # Loop forever (CTRL+C to quit)
    prev = datetime.now()
    runLoop = True
    while runLoop:             
        try:
            # Receive UDP, send to MC group
            data, addr = udpRxSock.recvfrom(10240)  # buffer size is 10240 bytes
            mcTxSock.sendto(data, (MCAST_GRP, MCAST_PORT))
            # Heartbeat on console
            prev = heartbeat(prev)
        except Exception as e:
            print(e)
            pass
        
    mcTxSock.close()
    udpRxSock.close()
        
    
    
    

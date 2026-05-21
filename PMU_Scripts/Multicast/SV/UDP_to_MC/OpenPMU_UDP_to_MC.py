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
    print('\n[STOP] You pressed Ctrl+C! Shutting down Multicast relay...')
    mcTxSock.close()
    udpRxSock.close()
    sys.exit(0)
  
# Load the config file
def loadConfig(configFile="config.json"):
    with open(configFile) as jsonFile:
        return json.load(jsonFile)

def UDPreceive(UDP_IP, UDP_PORT):
    udpRxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    udpRxSock.bind((UDP_IP, UDP_PORT))
    udpRxSock.settimeout(1)                                         
    return udpRxSock

def MCtransmit():
    mcTxSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    mcTxSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    return mcTxSock

if __name__ == '__main__':
    
    signal.signal(signal.SIGINT, signal_handler)
    print("--------------------------------------------------------")
    print("OpenPMU - Advanced UDP to Multicast Relay")
    print("--------------------------------------------------------")
    
    config = loadConfig("config.json")
    
    UDP_IP        = config["UDP_IP"]
    UDP_PORT      = config["UDP_PORT"]
    MCAST_GRP     = config["MCAST_GRP"]
    MCAST_PORT    = config["MCAST_PORT"]
        
    udpRxSock = UDPreceive(UDP_IP, UDP_PORT)
    mcTxSock = MCtransmit()
    
    print(f"Listening for Hardware ADC on : {UDP_IP}:{UDP_PORT}")
    print(f"Broadcasting to Network on    : {MCAST_GRP}:{MCAST_PORT}")
    print("Waiting for data stream...\n")
    
    prev = datetime.now()
    runLoop = True
    
    while runLoop:             
        try:
            data, addr = udpRxSock.recvfrom(10240)  
            mcTxSock.sendto(data, (MCAST_GRP, MCAST_PORT))
            
            # UPGRADED UI HEARTBEAT WITH ANIMATED DOTS 
            now = datetime.now()
            if now.second != prev.second:
                
                # Create a growing string of dots (1 to 5 dots) that resets
                dots = "." * ((now.second % 5) + 1)
                padded_dots = dots.ljust(5) # Pads with spaces to clear old dots
                
                try:
                    # Decode the raw byte data into a readable string
                    xml_str = data.decode('utf-8', errors='ignore')
                    
                    channels = "Unknown"
                    if "<Channels>" in xml_str:
                        channels = xml_str.split("<Channels>")[1].split("</Channels>")[0]
                        
                    frame = "???"
                    if "<Frame>" in xml_str:
                        frame = xml_str.split("<Frame>")[1].split("</Frame>")[0]

                    # Print the live updating status bar WITH the animated dots
                    print(f"\r[LIVE] Frame: {frame:>3} | Forwarding {channels} Channels | -> {MCAST_GRP}:{MCAST_PORT} {padded_dots}", end="", flush=True)
                
                except Exception:
                    # Fallback if packet is malformed
                    print(f"\r[LIVE] Forwarding raw data... -> {MCAST_GRP}:{MCAST_PORT} {padded_dots}", end="", flush=True)
                
                prev = now
                
        except socket.timeout:
            pass # Ignore timeouts, just keep waiting
        except Exception as e:
            print(f"\n[ERROR] {e}")
            pass
        
    mcTxSock.close()
    udpRxSock.close()
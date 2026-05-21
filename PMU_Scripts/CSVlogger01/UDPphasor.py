# -*- coding: utf-8 -*-
"""
OpenPMU - UDP Receiver
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

import sys

import socket
import phasor

__author__ = 'Xiaodong, OpenPMU.org'


class Receiver():
    """
    UDP interface to receive phasor estimation results
    """

    def __init__(self, ip , port, intf_ip=''):
        """
        Check if IP is multicase, initialise accordingly
        """           
        
        if self.MCcheck(ip):
            # Multicast port
            self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socketIn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                # Use specified Interface IP (intf_ip)
                mreq = socket.inet_aton(ip) + socket.inet_aton(intf_ip)
            except:
                # No Interface IP specified, use default from routing table
                mreq = socket.inet_aton(ip) + socket.INADDR_ANY.to_bytes(4, 'little') # Zero, so endian doesn't matter
                
                # Alternative method, explicitedly get the host IP (default from routing table)
                # host = socket.gethostbyname(socket.gethostname())                
                # mreq = socket.inet_aton(ip) + socket.inet_aton(host)
            
            self.socketIn.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.socketIn.bind((intf_ip, port))
            self.socketIn.settimeout(10)                         # Timeout 1 second
            
        else:
            # Normal UDP port
            self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socketIn.bind((ip, port))
        
    def MCcheck(self, ip):
        """
        Checks if 'ip' is in multicast range
        """
        
        if int(ip.split(".")[0]) in range(224,240):
            return True
        else:
            return False
        
    def receive(self, ):
        """
        Receive phasor estimation results.

        :return: python dict of the result
        """
        xml, __address = self.socketIn.recvfrom(8192)
        return phasor.fromXML(xml)


class Sender():
    """
    UDP interface to send phasor estimation results
    """

    def __init__(self, ip, port):
        
        self.ip = ip
        self.port = port
        
        if self.MCcheck:
            # Multicast port
            self.socketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socketOut.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        else:
            # Normal UDP port
            self.socketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
    def MCcheck(self, ip):
        """
        Checks if 'ip' is in multicast range
        """
        
        if int(ip.split(".")[0]) in range(224,240):
            return True
        else:
            return False
        
    def send(self, resultDict):
        """
        send phasor estimation results

        :param resultDict: python dict of the result
        :return:
        """
        xml = phasor.toXML(resultDict)

        try:
            self.socketOut.sendto(xml, (self.ip, self.port))
        except:
            print("Error sending phasor, network not available.")

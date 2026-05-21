"""
OpenPMU - Phasor Estimator
Copyright (C) 2021  www.OpenPMU.org

Licensed under GPLv3.  See __init__.py
"""

import sys

import socket
import estimation.interface.phasor as phasor

__author__ = 'Xiaodong'


class Receiver():
    """
    UDP interface to receive phasor estimation results
    """

    def __init__(self, ip , port):
        """
        Check if IP is multicase, initialise accordingly
        """     
        
        print("Result of MCcheck is   ---   ", MCcheck)
        
        
        if self.MCcheck(ip):
            # Multicast port
            self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socketIn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socketIn.bind(('', port))
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            self.socketIn.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.socketIn.settimeout(1)                         # Timeout 1 second
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
        xml, __address = self.socketIn.recvfrom(65536)
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

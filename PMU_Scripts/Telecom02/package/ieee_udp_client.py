"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module manages UDP socket for sending IEEE C37.118.2 messages. 

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""

import package.configurations
import socket


sendSocket = None


def create_socket():
	"""
	It creates a UDP socket for sending messages.
	"""	
	# AF_INET = Internet Protocol address
	global sendSocket
	sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)


def udp_socket_sendData(data):
	"""
	It sends data on created UDP socket.

	:param data: Data to send
	"""
	global sendSocket

	sendSocket.sendto(data, (package.configurations.SPONTANEOUS_DESTINATION_IP, int(package.configurations.SPONTANEOUS_DESTINATION_Port) ))


def close_socket():
	"""
	It closes the socket after use.
	"""
	global sendSocket
	sendSocket.close()


def udpSendTestData(testData):
	"""
	It is defined just for testing purpose to see if UDP client/server is working correctly.
	"""
	# Calling all functions defined.
	create_socket()
	udp_socket_sendData(testData)
	close_socket()

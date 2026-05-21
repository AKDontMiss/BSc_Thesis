"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module manages UDP socket for receiving XML formatted synchrophasors from the OpenPMU. 

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""

import package.configurations

import socket
import errno


receiveSocket = None


def create_socket():
	"""
	It creates a UDP socket.
	"""
	# AF_INET = Internet Protocol address
	global receiveSocket
	receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	#receiveSocket.setblocking(False)


def bind_udp_socket():
	"""
	It binds created socket to specified port
	"""
	global receiveSocket
	# Allow multiple copies of this program on one machine
	receiveSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# Bind the socket to the port
	server_address = ('', int(package.configurations.XML_UDP_Port))    # No need to specify IP address as the server will always run on localhost.

	receiveSocket.bind(server_address)  


def udp_socket_receiveData():
	"""
	It reads messages if any received on the socket in a non-blocking mode. It extracts data and sender information and returns it to the software main file for processing.

	:return: **data:** Data received in the message, **sender:** Sender of the received message
	"""
	global receiveSocket
	data = None
	sender = None

	try:
		# Messages are read from the socket using recvfrom(), which returns the data as well as the address of the client from which it was sent.
		data, sender = receiveSocket.recvfrom(65535)
	except IOError as e:
		if e.errno == errno.EWOULDBLOCK:
			pass
	if data:
		return data, sender
	else:
		return "", ""


def close_socket():
	"""
	It closes the server socket after use.
	"""
	global receiveSocket
	receiveSocket.close()

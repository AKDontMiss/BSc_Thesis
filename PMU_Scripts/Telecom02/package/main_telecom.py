"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| The main software file from where different initializations, configurations loading, sockets creation, threads management, etc are performed.  

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""


import package.configurations
import package.dispatcher
import package.ieee_tcp_socket
import package.ieee_udp_client
import package.xml_udp_server
import package.logger

import logging
import threading
import time


# If it is 1, it means all necessary software initializations have been performed.
isAppInitializationsPerformed = 0


def SoftwareInitalization():
	"""
	This function performs basic software initialization.
	"""

	global isAppInitializationsPerformed
	print("----------------------------------------------------------------------------")

	package.logger.initializeLogger()

	# Start UDP Server Thread for receiving XML data from OpenPMU Phasor Estimation Block
	logging.debug('Starting UDP server thread for OpenPMU XML data')
	threads = []
	UDPServer_thread_XML = threading.Thread(target=udpLocalServerThread_XML)
	threads.append(UDPServer_thread_XML)
	UDPServer_thread_XML.start()
	logging.info('UDP server thread for OpenPMU XML data successfully started')

	# Start TCP Server Thread for IEEE C37.118.2 command messages
	logging.debug('Starting TCP server thread for IEEE C37.118.2 command messages')
	TCPServer_thread_IEEE = threading.Thread(target=tcpLocalServerThread_IEEE_C37)
	# Daemon thread exit when the main software exit.
	TCPServer_thread_IEEE.daemon = True
	threads.append(TCPServer_thread_IEEE)
	TCPServer_thread_IEEE.start()
	logging.info('TCP server thread for IEEE C37.118.2 command messages successfully started')

	# Create UDP socket for IEEE C37.118.2 messages - Only used if OpenPMU is working in spontaneous mode.
	if package.configurations.OPERATIONAL_MODE.lower()=="spontaneous":
		package.ieee_udp_client.create_socket()

	time.sleep(0.5) # Not necessary but give some time for all sockets to be properly created.
	isAppInitializationsPerformed = 1
	logging.info('Completed necessary software initializations...')
	print("----------------------------------------------------------------------------")


def udpLocalServerThread_XML():
	"""
	It creates a UDP server socket for receiving synchrophasor data in XML format from the OpenPMU Phasor Estimation Block.
	"""

	global isAppInitializationsPerformed

	# Start udp local server Thread
	package.xml_udp_server.create_socket()
	package.xml_udp_server.bind_udp_socket()

	# Loop, continuously get data from socket if any data is received.
	while package.configurations.keepSoftwareRunning == 1:
		# Process received data only if the software has been initialized.
		if isAppInitializationsPerformed == 1:
			# Checks if udp datagram is received in non-blocking way and gets the data and sender information.
			data, sender = package.xml_udp_server.udp_socket_receiveData()
			if data:
				#print 'Sender = ', sender,  ',    Data Received (HEX) = ', hex(bytes_to_long(data))
				logging.info("\r                                    ")
				logging.info("A message in XML format received from %s. Started decoding...", sender)
				retValue = package.dispatcher.process_XML_Message(data)
				if retValue == 1:
					logging.info('Received XML formatted message successfully processed.')
		else:
			time.sleep(0.05)

	package.xml_udp_server.close_socket()
	logging.info('UDP socket for XML closed')


def tcpLocalServerThread_IEEE_C37():
	"""
	It creates a TCP socket for receiving IEEE C37.118.2 command messages from PDC/Controller/WAMPAC applications.
	"""

	package.ieee_tcp_socket.create_socket()
	package.ieee_tcp_socket.bind_tcp_socket()
	package.ieee_tcp_socket.accept_connections()

"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module manages TCP socket for sending/receiving IEEE C37.118.2 messages. Creates socket, accepts connections, waits for TCP messages if received, gets the data and sender information, send TCP messages and closes TCP socket.

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""

import package.configurations
import package.logger
import package.dispatcher

import threading
import logging
import socket
import errno
import sys

# Keep track of devices/applications which are subscribed to the OpenPMU.
subscribers = set()

# Lock while editing the OpenPMU subscribers list.
subscribers_lock = threading.Lock()

# Each new connection/subscriber runs in a different thread.
# from thread import start_new_thread  # OLD SOLUTION FOR THREADING

tcpSocket = None


def create_socket():
	"""
	It creates a TCP socket.
	"""
	# AF_INET = Internet Protocol address
	global tcpSocket

	try:
		tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#tcpSocket.setblocking(False)
	except socket.error as msg:
		logging.error('Failed to create TCP socket for IEEE C37.118.2. %s Error: %s', str(msg[0]), str(msg[1]))
		sys.exit(0)		

	logging.debug('TCP socket created for IEEE C37.118.2')


def connect_socket():
	"""
	It establishes connection with the remote TCP peer. No need to call this function as OpenPMU will work in Publish/Subscribe fashion. Just wrote this fuction for any possible future use.
	"""
	global tcpSocket

	tcpSocket.connect((package.configurations.SPONTANEOUS_DESTINATION_IP, int(package.configurations.SERVER_PORT_TCP)))


def bind_tcp_socket():
	"""
	It binds created socket to specified port
	"""
	global tcpSocket
	
	# Allow multiple copies of this program on one machine
	tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# Bind the socket to the port
	server_address = ('', int(package.configurations.SERVER_PORT_TCP))    # No need to specify IP address as the server will always run on localhost.

	try:
		tcpSocket.bind(server_address)  
		logging.debug('Bounded TCP socket for IEEE C37.118.2 to port %s.', str(package.configurations.SERVER_PORT_TCP))
		
	except socket.error as msg:
		logging.error('Failed to bind TCP socket for IEEE C37.118.2. Error Code: %s Error: %s', str(msg[0]), str(msg[1]))
		sys.exit()

	# It listens for incoming connections.
	tcpSocket.listen(100)
	logging.debug('Listening for incoming IEEE C37.118.2 connections.....')
	

def accept_connections():
	"""
	It waits for new connections and accept them. It allows many WAMPAC applications to subscribe to the OpenPMU.
	"""

	global subscribers
	global subscribers_lock

	while package.configurations.keepSoftwareRunning == 1:
		# Wait for a connection - Blocking mode.
		connection, sender = tcpSocket.accept()
		connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		
		logging.info('A new device %s:%s connected to the OpenPMU.', str(sender[0]), str(sender[1]))

		with subscribers_lock:
			subscribers.add(connection)
		threading.Thread(target=tcp_socket_receiveData, args=(connection,)).start()
		# start_new_thread(tcp_socket_receiveData, (connection,))

	package.ieee_tcp_socket.close_socket()	
	logging.info('TCP socket for IEEE C37.118.2 closed')

		
def tcp_socket_receiveData(connection):
	"""
	It listens/reads messages if any received on the socket from accepted connections. It extracts data and sends it to dispatcher for processing.
	"""

	while connection.fileno() != -1: # As long as a specific connection/device is available or connected to the OpenPMU.
		try:
			# Receive the data
			data = connection.recv(8000)
			if data:
				logging.info("\r                                    ")
				logging.info("An IEEE C37.118.2 message received. Started decoding...")
				package.dispatcher.process_IEEE_C37_118_Message(data)
			else:
				# CRITICAL FIX: If data is empty, the client cleanly disconnected. Break the infinite loop!
				break

		except IOError as e:
			if e.errno == errno.EWOULDBLOCK:
				pass

	logging.warning("A connection to OpenPMU has terminated. %s", str(connection))

	with subscribers_lock:
		if connection in subscribers:
			subscribers.remove(connection)
		connection.close()

	
def tcp_socket_sendData(data):
	"""
	It sends data on created TCP socket.

	:param data: Data to send
	"""

	global subscribers
	global subscribers_lock

	with subscribers_lock:
		problematic_conn = None
		for connection in subscribers:
			try:
				connection.sendall(data)
				# connection.send(data)
			except:
				problematic_conn = connection
				logging.warning("Exception occured. Removed a device/application that probably unsubscribed from the OpenPMU.")
				break

		if problematic_conn != None:
			subscribers.remove(problematic_conn)
			problematic_conn.close()
			

def close_socket():
	"""
	It closes the server socket after use.
	"""
	global tcpSocket
	tcpSocket.close()

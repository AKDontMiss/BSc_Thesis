"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module receives messages from remote peers and delivers them to the correct component of the software responsible for handling them. It decouples the underlying communication protocols from the main software components.  

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""

import package.configurations
import package.DataMessage
import package.CommandMessage
import package.ConfigMessage
import package.logger

import logging
from struct import *


def process_XML_Message(receivedMessage):
	"""
	This function is responsible to process the received XML formatted messages. 

	:param receivedMessage: The message received from the OpenPMU Phasor Estimation Block.
	"""

	if package.configurations.IEEEC37_ConfigurationsSaved == 0:
		# IEEE C37.118.2 configurations not generated yet. Generate and save.
		package.ConfigMessage.save_IEEEC371182_Configuration(receivedMessage)
		
	else:
		package.DataMessage.IEEE_C37_118_DataMessage_Send(receivedMessage)


	



def process_IEEE_C37_118_Message(receivedMessage):
	"""
	This function is responsible to process the received IEEE C37.118.2 command messages. 
	Note, PMU can only receive command messages in IEEE C37.118.2 standard. Any other type of received message will be ignored.

	:param receivedMessage: The message received from the PDC/Controller/WAMPAC application.
	"""
	# Decode first 2 Bytes
	(SYNC,) = unpack('!H', receivedMessage[:2])
	
	msgType = (SYNC & 0x70) >> 4;

	if msgType==4:
		# Means IEEE C37.118.2 Command Message
		package.CommandMessage.decode(receivedMessage)

	else:
		logging.warning('Aborted decoding: PMU can only receive IEEE C37.118.2 command messages.')
		logging.warning('Received a non-supported message type.')

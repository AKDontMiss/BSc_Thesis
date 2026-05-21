"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Modified By Haron Akram Ahmed Mohammed for Bachelors' Thesis
| **Editor:** Haron Akram Ahmed Mohammed
| **Email:** haamo@kth.se

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module provides decoding of Command Messages according to IEEE C37.118.2-2011 standard. 

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)

"""

import package.ConfigMessage
import package.DataMessage
import package.configurations
import package.general_utils
import package.logger

import logging
from struct import *


SYNC_2005 = 0xAA41
"""
The first Byte of synchronization word is 0xAA and Second Byte of synchronization word is 0x41 for COMMAND messages as specified by IEEE C37.118.2-2005 version of standard.
"""

SYNC_2011 = 0xAA42
"""
The first Byte of synchronization word is 0xAA and Second Byte of synchronization word is 0x42 for COMMAND messages as specified by IEEE C37.118.2-2011 version of standard.
"""

CMD_TURN_DATA_STREAM_ON = 0X0002
"""
It instructs the OpenPMU to turn ON the transmission of data stream.
"""

CMD_TURN_DATA_STREAM_OFF = 0X0001
"""
It instructs the OpenPMU to turn OFF the transmission of data stream.
"""

CMD_SEND_HEADER = 0X0003
"""
It instructs the OpenPMU to send header message.
"""

CMD_SEND_CFG1 = 0X0004
"""
It instructs the OpenPMU to send CFG-1 configuration message.
"""

CMD_SEND_CFG2 = 0X0005
"""
It instructs the OpenPMU to send CFG-2 configuration message.
"""

CMD_SEND_CFG3 = 0X0006
"""
It instructs the OpenPMU to send CFG-3 configuration message.
"""


def decode(receivedMessage):
	"""
	It decodes and processes the received IEEE C37.118.2 command message.

	:param receivedMessage: The message received from remote peer.
	"""

	logging.debug('Received message identified as Command. Started decoding...')
	
	# All fields before Data have fixed size (in total 14 Bytes) and CHK is 2 Bytes.
	SYNC, MESSAGESIZE, IDCODE, SOC, FRACSEC, CMD, CHK = unpack('!HHHLLHH', receivedMessage[:])

	if package.configurations.IEEEC37_ConfigurationsSaved == 1:

		if CMD == CMD_TURN_DATA_STREAM_ON:
			logging.info('Received command message instructs to turn ON the transmission of data stream.')
			package.DataMessage.Data_Transmission_ON = 1

		elif CMD == CMD_TURN_DATA_STREAM_OFF:
			logging.info('Received command message instructs to turn OFF the transmission of data stream.')
			package.DataMessage.Data_Transmission_ON = 0

		elif CMD == CMD_SEND_HEADER:
			logging.info('Received command message instructs to send Header Message.')
			logging.warning('OpenPMU does not support Header Messages yet. Functionality yet to be implemented.')

		elif CMD == CMD_SEND_CFG1:
			logging.info('Received command message instructs to send CFG-1 Configuration message.')
			package.ConfigMessage.IEEE_C37_118_ConfigMsg2_Send()

		elif CMD == CMD_SEND_CFG2:
			logging.info('Received command message instructs to send CFG-2 Configuration message')
			package.ConfigMessage.IEEE_C37_118_ConfigMsg2_Send()

		elif CMD == CMD_SEND_CFG3:
			# At the moment, CFG-3 is not implemented. So send the CFG-2 message instead.
			logging.info('Received command message instructs to send CFG-3 Configuration message.')
			package.ConfigMessage.IEEE_C37_118_ConfigMsg2_Send()

		else:
			logging.warning('Received command message instructions either not identified or not implemented.')

	else:
		# IEEE C37.118.2 configurations not generated yet.
		logging.warning('OpenPMU configurations not saved yet. Probably, no message yet received from the OpenPMU Phasor Estimation Block.')
		logging.warning('Ignored the received IEEE C37.118.2 command message.')

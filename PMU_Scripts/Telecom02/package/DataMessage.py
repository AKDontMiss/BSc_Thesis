"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| **Editor:** Simon Weideskog
| **Email:** simonwei@kth.se

| Modified By Haron Akram Ahmed Mohammed for Bachelors' Thesis
| **Editor:** Haron Akram Ahmed Mohammed
| **Email:** haamo@kth.se

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module provides methods for encoding/sending IEEE C37.118.2 data messages. 

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)
| 20-10-2022       Changed to run with Python 3 and general bug fixes

"""

import package.configurations
import package.ConfigMessage
import package.general_utils
import package.ieee_udp_client
import package.ieee_tcp_socket
import package.logger
import package.phasor

import logging
from struct import *
import datetime
import binascii


SYNC = 0xAA02
"""
The first Byte of synchronization word is 0xAA and Second Byte of synchronization word is 0x02 for data messages as specified by IEEE C37.118.2-2011 version of standard
"""

Data_Transmission_ON = 0
"""
This control variable determines if this software should send data messages. It is only controlled by received command messages. If received command message instructs this software to start sending data messages then this variable is set to 1. If received command message instructs this software to stop sending data messages then this variable is set to 0.  
"""

def IEEE_C37_118_DataMessage_Send(receivedMessage):
	"""
	It packs and sends the data message (synchrophasors) to the remote peer according to the structure defined in IEEE C37.118.2-2011. 
	"""
	global SYNC

	# Convert received message from XML format into phasorDict
	phasorDict =  package.phasor.fromXML(receivedMessage)
	# print "phasorDict Content = ", phasorDict	

	########################################################################################################################################
	# A single PMU in IEEE C37.118.2 data message can carry only one frequency value. The frequency is different for all channels in 
	# OpenPMU XML provided by Leo, but I have included the frequency value of only first phasor (due to limitation of IEEE C37.118.2). 
	########################################################################################################################################

	Magnitude1 = phasorDict['Channel_0']['Mag']
	Angle1 = phasorDict['Channel_0']['Angle']
	Frequency1 = phasorDict['Channel_0']['Freq']

	Magnitude2 = phasorDict['Channel_1']['Mag']
	Angle2 = phasorDict['Channel_1']['Angle']
	Frequency2 = phasorDict['Channel_1']['Freq']
    
	Magnitude3 = phasorDict['Channel_2']['Mag']
	Angle3 = phasorDict['Channel_2']['Angle']
	Frequency3 = phasorDict['Channel_2']['Freq']    
    	
	Magnitude4 = 0.0
	Angle4 = 0.0
	Frequency4 = 0.0       
    
	Magnitude5 = 0.0
	Angle5 = 0.0
	Frequency5 = 0.0        
    
	Magnitude6 = 0.0
	Angle6 = 0.0
	Frequency6 = 0.0  
    
	ANALOG_VALUE1 = 0.0
	ANALOG_VALUE2 = 0.0
	DIGITAL_VALUE = 0
	
	# Calculate SOC (represents timestamp). It is the Second Of Century (SOC) count since epoch (00:00:00 on 01-01-1970).
	Date = phasorDict['Date']
	Time = phasorDict['Time']
	
	year, month, day = Date.split('-')
	hour, minute, secondFull = Time.split(':')
	second, fracSec = secondFull.split('.')

	t_epoch = int( datetime.datetime(1970,1,1).strftime("%s") )  # Number of seconds on epoch
	t_now = int( datetime.datetime(int(year),int(month),int(day)).strftime("%s") )  # Number of seconds at provided time
	SOC = (t_now + int(hour)*60*60 + int(minute)*60 + int(second)) - t_epoch  
	#SOC = int((datetime.datetime(int(year),int(month),int(day)) - datetime.datetime(1970,1,1)).total_seconds())

	# Represents time of measurement in microseconds for data messages or time of transmission for non-data messages. It consists of Time Quality (1 Byte) and Fraction of second (3 Bytes). Assume no leap second, none pending and time locked. Please refer to IEEE C37.118.2-2011 standard on how to calculate FRACSEC.
	FRACSEC = int(fracSec)
	
	# logging.error('Before = %s %s ,    After = %s  %s  %d', Date, Time, minute, second, FRACSEC)

	# Assume valid data, no PMU error, PMU sync, data sorted by time-stamp, no PMU trigger and best time quality. Equivalent to 0000 in Hexadecimal. Please refer to IEEE C37.118.2-2011 standard on how to get STAT value.
	STAT = 0x0000

	# NumberOfPhasors = 3
	PHASORS = pack('!ffffff', 
                   float(Magnitude1), (float(Angle1)*3.141592/180), 
                   float(Magnitude2), (float(Angle2)*3.141592/180), 
                   float(Magnitude3), (float(Angle3)*3.141592/180))

	ANALOGS = b''
	
	DIGITAL = b''

	# Frequency deviation from nominal in mHz if FREQ in int. Since we are using floating point FREQ so it represents the actual frequency.
	FREQ = float(Frequency1)

	# Rate Of Change Of Frequency (ROCOF) in Hertz per second times 100. Same for all channels. 
	# DFREQ = 1
	DFREQ = int(phasorDict['Channel_0']['ROCOF']*100)


	# Represents total number of Bytes in the message, including CHK. Maximum possible value is 65535. 
	# MESSAGESIZE includes SYNC=2, MESSAGESIZE=2, IDCODE=2, SOC=4, FRACSEC=4, numberOfPMUs x (STAT=2, PHASORS=VARIABLE, FREQ=2/4, DFREQ=2/4, ANALOG=VARIABLE, DIGITAL=VARIABLE), CHK=2.
	# Only in our specific case, MESSAGESIZE can be calculated as below:

	#  Number of bytes per part of message
	SYNC_byteNo = 2
	MESSAGESIZE_byteNo  = 2
	IDCODE_byteNo = 2
	SOC_byteNo = 4
	FRACSEC_byteNo = 4
	STAT_byteNo = 2
	FREQ_byteNo = 4
	DFREQ_byteNo = 4
	CHK_byteNo = 2
	# Total message size in bytes
	MESSAGESIZE = SYNC_byteNo + MESSAGESIZE_byteNo + IDCODE_byteNo + SOC_byteNo + FRACSEC_byteNo + \
				package.configurations.NUM_PMU * (STAT_byteNo + len(PHASORS) + FREQ_byteNo + DFREQ_byteNo + len(ANALOGS) + len(DIGITAL)) + CHK_byteNo
	
	# MESSAGESIZE = 2+2+2+4+4+ package.configurations.NUM_PMU*(2+len(PHASORS)+4+4+len(ANALOGS)+2) + 2

	# This will store content of all PMUs. (PDC related feature - only one PMU in our case)
	pmuContent = b''
	
	for x in range(0, package.configurations.NUM_PMU):
		pmuContent += pack('!H%dsff%ds%ds' % (len(PHASORS), len(ANALOGS), len(DIGITAL)),
						STAT,
						bytes(PHASORS),
						FREQ,
						DFREQ,
						bytes(ANALOGS),
						bytes(DIGITAL))

	msg_for_chk = pack('!HHHLL%ds' % (len(pmuContent)),
			SYNC,
			MESSAGESIZE,
			package.configurations.IDCODE,
			SOC,
			FRACSEC,
			pmuContent)

	# msg_for_chk_hex = msg_for_chk.hex()
	#calculate_crc16_ccitt('ABCD')
	CHK = binascii.crc_hqx(msg_for_chk,0xFFFF)
	
	message = pack('!HHHLL%dsH' % (len(pmuContent)),
			SYNC,
			MESSAGESIZE,
			package.configurations.IDCODE,
			SOC,
			FRACSEC,
			pmuContent,
			CHK)	

	global Data_Transmission_ON
	
	if package.configurations.OPERATIONAL_MODE.lower() == "commanded":
		if Data_Transmission_ON == 1:
			# OpenPMU commanded mode operates over TCP
			package.ieee_tcp_socket.tcp_socket_sendData(message)
			logging.debug('IEEE C37.118.2 data message sent over TCP.')
		else:
			logging.warning('No one yet requested OpenPMU to start data transmission.')
			
	elif package.configurations.OPERATIONAL_MODE.lower() == "spontaneous":
		# OpenPMU spontaneous mode operates over UDP
		# We have to send configuration message with each data message because PMU in spontaneous mode cannot receive commands (so receiver cannot request configurations). 
		package.ConfigMessage.IEEE_C37_118_ConfigMsg2_Send()
		# Now send the data message.	
		package.ieee_udp_client.udp_socket_sendData(message)
		logging.debug('IEEE C37.118.2 data message sent over UDP.')	

	else:
		logging.warning('Message sending failed. Check if the OpenPMU OPERATIONAL_MODE is specified correctly in configurations.py file.')

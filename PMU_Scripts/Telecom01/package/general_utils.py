"""
| **Author:** Dr. Rafiullah Khan 
| **Email:** rafiullah.khan@qub.ac.uk

| Version 1.0
| Date: 31-07-2018 

| **Description:**
| This module contains some general utilities used in other modules. It implements the functions which are common and will be used by several modules of the software.  

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)
| 20-10-2022       Small bug fix with SOC not being returned as int

"""

import time


def get_SOC():
	"""
	It returns time stamp. It is the Second Of Century (SOC) count since epoch (00:00:00 on 01-01-1970).

	:return: **SOC:** Time stamp
	"""

	def get_seconds_since_epoch():
		#t_epoch = int( datetime.datetime(1970,1,1).strftime("%s") )  # Number of seconds on epoch
		#t_now = int(datetime.datetime.now().strftime("%s"))          # Number of seconds now
		#SecondsSinceEpoch = t_now - t_epoch

		SecondsSinceEpoch = int(time.time())
		return SecondsSinceEpoch

	return get_seconds_since_epoch()


def calculate_crc16_ccitt(data):
	"""
	It calculates the Cyclic Redundency Code (CRC) for the data provided. 

	:param data: Data for which to calculate CRC value.
	:return: The calculated CRC value.
	"""
	crc = 0xFFFF
	msb = crc >> 8
	lsb = crc & 255
	for c in data:
		x = ord(c) ^ msb
		x ^= (x >> 4)
		msb = (lsb ^ (x >> 3) ^ (x << 4)) & 255
		lsb = (x ^ (x << 5)) & 255
	return (msb << 8) + lsb

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
| This module provides encoding of Configuration Messages according to IEEE C37.118.2-2011 standard.

| **CHANGE HISTORY**
| 31-07-2018       Released first version (1.0)
| 20-10-2022       Changed to run with Python 3 and general bug fixes

"""


import package.configurations
import package.phasor

import package.general_utils
import package.ieee_tcp_socket
import package.ieee_udp_client
import package.logger
import binascii

import logging
from struct import *


SYNC = 0xAA32
"""
The first Byte of synchronization word is 0xAA and Second Byte of synchronization word is 0x32 for CFG-2 messages as specified by IEEE C37.118.2-2011 version of standard.
"""


def save_IEEEC371182_Configuration(receivedMessage):
    """
    It generates and saves IEEE C37.118.2 configurations for OpenPMU from the received XML message.
    """

    # Convert received message from XML format into phasorDict
    phasorDict = package.phasor.fromXML(receivedMessage)
    # print "phasorDict Content = ", phasorDict

    Phasor1 = phasorDict['Channel_0']['Name'] + " "*16
    Phasor2 = phasorDict['Channel_1']['Name'] + " "*16
    Phasor3 = phasorDict['Channel_2']['Name'] + " "*16
    Phasor4 = "Empty_Channel   " + " "*16
    Phasor5 = "Empty_Channel   " + " "*16
    Phasor6 = "Empty_Channel   " + " "*16

    # Phasors and channels names in the order as included in data messages. Each name should be 16 Bytes. Total size = 16 x (PHNMR + ANNMR + 16 x DGNMR)
    package.configurations.CHNAM[0] = Phasor1[:16]
    package.configurations.CHNAM[1] = Phasor2[:16]
    package.configurations.CHNAM[2] = Phasor3[:16]
    package.configurations.CHNAM[3] = Phasor4[:16]
    package.configurations.CHNAM[4] = Phasor5[:16]
    package.configurations.CHNAM[5] = Phasor6[:16]
    package.configurations.CHNAM[6] = "Analog 1        "
    package.configurations.CHNAM[7] = "Analog 2        "
    package.configurations.CHNAM[8] = "Breaker 1 Status"
    package.configurations.CHNAM[9] = "Breaker 2 Status"
    package.configurations.CHNAM[10] = "Breaker 3 Status"
    package.configurations.CHNAM[11] = "Breaker 4 Status"
    package.configurations.CHNAM[12] = "Breaker 5 Status"
    package.configurations.CHNAM[13] = "Breaker 6 Status"
    package.configurations.CHNAM[14] = "Breaker 7 Status"
    package.configurations.CHNAM[15] = "Breaker 8 Status"
    package.configurations.CHNAM[16] = "Breaker 9 Status"
    package.configurations.CHNAM[17] = "Breaker A Status"
    package.configurations.CHNAM[18] = "Breaker B Status"
    package.configurations.CHNAM[19] = "Breaker C Status"
    package.configurations.CHNAM[20] = "Breaker D Status"
    package.configurations.CHNAM[21] = "Breaker E Status"
    package.configurations.CHNAM[22] = "Breaker F Status"
    package.configurations.CHNAM[23] = "Breaker G Status"

    # Make strings packable
    for i in range(0, 24):
        package.configurations.CHNAM[i] = bytes(
            package.configurations.CHNAM[i], 'utf-8')

    # Conversion factor for phasor channels. Please refer to IEEE C37.118.2-2011 standard for details.
    package.configurations.PHUNIT[0] = 0
    package.configurations.PHUNIT[1] = 0
    package.configurations.PHUNIT[2] = 0
    package.configurations.PHUNIT[3] = 0
    package.configurations.PHUNIT[4] = 0
    package.configurations.PHUNIT[5] = 0

    # Conversion factor for analog channels. Please refer to IEEE C37.118.2-2011 standard for details.
    package.configurations.ANUNIT[0] = 0
    package.configurations.ANUNIT[1] = 0

    # Mask words for digital status words. Please refer to IEEE C37.118.2-2011 standard for details.
    package.configurations.DIGUNIT[0] = 0x0000FFFF

    logging.debug('IEEE C37.118.2 configurations generated and saved for the received XML formatted message.')

    # Update the value. Indicating configurations have been saved.
    package.configurations.IEEEC37_ConfigurationsSaved = 1


def IEEE_C37_118_ConfigMsg2_Send():
    """
    It packs and sends the Configuration-type2 message to the remote peer according to the structure defined in IEEE C37.118.2-2011.
    """
    global SYNC
    SOC = package.general_utils.get_SOC()
    FRACSEC = 0x00000000

    # Dynamically assemble the CHNAM binary string for exactly 3 Phasors
    CHNAM_bytes = b''
    # 3 Phasors (Va, Vb, Vc)
    for i in range(0, 3):
        CHNAM_bytes += package.configurations.CHNAM[i]
        
    CHNAM = CHNAM_bytes

    PHUNIT = pack('!LLL',
                package.configurations.PHUNIT[0],
                package.configurations.PHUNIT[1],
                package.configurations.PHUNIT[2])
                
    ANUNIT = b''

    # This will store content of all PMUs (PDC related feature - only 1 PMU in our case)
    pmuContent = b''
    for x in range(0, package.configurations.NUM_PMU):
        # PMU/PDC ID number.
        IDCODE_PMU = package.configurations.IDCODE + x
        
        # If DGNMR is 0, we must omit the DIGUNIT (L) from the struct format
        pmuContent = pmuContent + pack('!%dsHHHHH%ds%ds%dsHH' % (16, len(CHNAM), len(PHUNIT), len(ANUNIT)),
                                       bytes(package.configurations.STN, 'utf-8'),
                                       IDCODE_PMU,
                                       package.configurations.FORMAT,
                                       package.configurations.PHNMR,
                                       package.configurations.ANNMR,
                                       package.configurations.DGNMR,
                                       CHNAM,
                                       PHUNIT,
                                       ANUNIT,
                                       package.configurations.FNOM,
                                       package.configurations.CFGCNT)

    MESSAGESIZE = 24 + len(pmuContent)

    # FIXED: Added the 'H' at the end of the format string for DATA_RATE
    msg_for_chk = pack('!HHHLLLH%dsH' % (len(pmuContent)),
                   SYNC,
                   MESSAGESIZE,
                   package.configurations.IDCODE,
                   SOC,
                   FRACSEC,
                   package.configurations.TIME_BASE,
                   package.configurations.NUM_PMU,
                   pmuContent,
                   package.configurations.DATA_RATE)

    CHK = binascii.crc_hqx(msg_for_chk,0xFFFF)

    message = pack('!HHHLLLH%dsHH' % (len(pmuContent)),
                   SYNC,
                   MESSAGESIZE,
                   package.configurations.IDCODE,
                   SOC,
                   FRACSEC,
                   package.configurations.TIME_BASE,
                   package.configurations.NUM_PMU,
                   pmuContent,
                   package.configurations.DATA_RATE,
                   CHK)

    if package.configurations.OPERATIONAL_MODE.lower() == "commanded":
        package.ieee_tcp_socket.tcp_socket_sendData(message)
        logging.debug('IEEE C37.118.2 CFG-2 configuration message sent over TCP.')
    elif package.configurations.OPERATIONAL_MODE.lower() == "spontaneous":
        package.ieee_udp_client.udp_socket_sendData(message)
        logging.debug('IEEE C37.118.2 CFG-2 configuration message sent over UDP.')
    else:
        logging.warning('Message sending failed.')
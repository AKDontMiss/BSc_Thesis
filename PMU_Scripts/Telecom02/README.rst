========================================
IEEE C37.118.2 TELECOM Module - OpenPMU
========================================

Description
-----------
This module is responsible for packaging phasor data according to the IEEE C37.118-2011 protocol and preparing it for network transmission. 

In this dual-engine PMU architecture, the Telecom module is duplicated to handle the separate mathematical streams:
* ``Telecom01``: Packages the time-domain Least Squares Method (LSM) stream. (Default: Port 4711, IDCODE 101)
* ``Telecom02``: Packages the frequency-domain Enhanced-IpDFT (e-IpDFT) stream. (Default: Port 4712, IDCODE 102)

Operational Modes
-----------------
The IEEE C37.118.2 Telecom Module supports two modes of operation:

1. **Commanded Mode (TCP):** The OpenPMU Telecom block sends IEEE C37.118.2 messages only when commands are received (similar to commercial PMUs). It operates in a publish/subscribe fashion.
2. **Spontaneous Mode (UDP):** The OpenPMU Telecom block continuously sends IEEE C37.118.2 messages to a specified destination without waiting for command messages.

Configuration
-------------
To change the operational mode, target ports, or IDCODE, edit the ``config.json`` file located in this directory.
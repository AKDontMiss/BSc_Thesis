========================================
CSV LOGGER Module - OpenPMU
========================================

Description
-----------
This module locally archives the calculated phasor estimations (Frequency, ROCOF, Amplitude, Phase) into CSV files. It acts as a hardware-level redundancy backup in the event of a wide-area network outage, ensuring no grid data is permanently lost.

In this dual-engine architecture, the logger is duplicated:
* ``CSVlogger01``: Logs the LSM data stream.
* ``CSVlogger02``: Logs the e-IpDFT data stream.

Storage & Retention Policy
--------------------------
The logger writes data directly to a mounted USB flash drive (typically ``/mnt/usb0``). 
Because continuous high-frequency logging quickly exhausts physical storage and accelerates NAND flash wear, an automated **30-day rolling retention policy** is programmed into this module. Files older than 30 days are automatically deleted to prevent filesystem crashes and ensure the long-term operational health of the embedded hardware.
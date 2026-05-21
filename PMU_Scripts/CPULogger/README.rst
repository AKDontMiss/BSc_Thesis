========================================
CPU LOGGER Module - OpenPMU
========================================

Description
-----------
The CPU Logger is a custom module developed specifically for this thesis. Because the PMU runs two heavy signal processing algorithms concurrently (LSM and e-IpDFT), this script monitors the processing strain on the Raspberry Pi's hardware.

It uses the ``psutil`` library to record the processor utilization of specific Python screens. To ensure the monitoring process itself does not introduce computational latency or drop the 10 kHz sampling rate, the script is configured to poll at safe 5-second intervals. 

Storage & Retention Policy
--------------------------
Data is logged to the local USB drive. Like all logging modules in this architecture, it incorporates a **30-day rolling retention policy** to automatically clear old files and prevent NAND flash wear.
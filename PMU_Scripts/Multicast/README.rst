========================================
MULTICAST SV Module - OpenPMU
========================================

Description
-----------
This module is the data entry point for the Raspberry Pi PMU software pipeline. It receives the raw 10,000 Hz User Datagram Protocol (UDP) sampled values from the BeagleBone Black analog-to-digital converter (ADC). 

It captures this incoming stream and securely re-transmits it to the Raspberry Pi's internal multicast IP routing group (e.g., 239.16.1.101). By using internal multicast, multiple mathematical algorithms and diagnostic tools can independently subscribe to the exact same raw waveform simultaneously without network collisions.
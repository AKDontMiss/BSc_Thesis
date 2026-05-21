========================================
SV TO WAVE (Audio Logger) - OpenPMU
========================================

Description
-----------
This module is a diagnostic and debugging tool. It subscribes to the raw 10 kHz sampled values on the internal multicast group and converts the numerical voltage data into standard ``.flac`` audio files. 

This allows researchers to visually and audibly inspect the raw analog grid noise and harmonic distortions using standard audio analysis software (such as Audacity).

Storage & Retention Policy
--------------------------
To conserve disk space on the local USB drive, this module only records the first 5 minutes of every hour. Additionally, it enforces an automated **30-day rolling retention policy**, deleting old audio files to prevent the Raspberry Pi from experiencing a storage-induced kernel panic.
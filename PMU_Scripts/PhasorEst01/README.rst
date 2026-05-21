========================================
PHASOR ESTIMATION 01 (LSM) - OpenPMU
========================================

Description
-----------
This is the baseline Phasor Estimation module for the OpenPMU architecture. It calculates synchrophasors (Amplitude, Phase, Frequency, and ROCOF) using a time-domain Least Squares Method (LSM). 

The algorithm reads raw 10 kHz sampled values from the internal multicast group and applies a pseudo-inverse observation matrix to extract the fundamental 50 Hz component. This module is written entirely in Python.
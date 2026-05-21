========================================
PHASOR ESTIMATION 02 (e-IpDFT) - OpenPMU
========================================

Description
-----------
This is the experimental frequency-domain Phasor Estimation module. It calculates synchrophasors using an Enhanced Interpolated Discrete Fourier Transform (e-IpDFT).

To meet IEEE C37.118 P-Class latency requirements and prevent CPU bottlenecks at a 10 kHz sampling rate, this module utilizes a cross-language architecture. The heavy mathematical processing (Hanning windowing, fractional bin interpolation, and negative-image interference cancellation) is executed in a compiled C++ shared library. The Python framework uses the ``ctypes`` library to pass raw memory addresses directly to the C++ engine, bypassing Python's native garbage collector.

Compilation Requirement
-----------------------
Before launching this module, the C++ mathematical engine must be compiled into a shared library.
Navigate to this directory and run the standard ``g++`` compile command to generate ``libEnhancedIpDFT.so``. The Python wrapper will fail to execute if this library is missing.
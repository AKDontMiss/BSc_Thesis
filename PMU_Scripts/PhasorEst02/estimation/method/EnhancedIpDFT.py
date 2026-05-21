"""
OpenPMU - Phasor Estimator (Enhanced IpDFT Edition)
Copyright (C) 2021  www.OpenPMU.org
Modified for Bachelor's Thesis Implementation by Haron Akram Ahmed Mohammed 2026
Email: haamo@kth.se
"""

import numpy as np
import ctypes
import os
import gc

# import the Base class required by OpenPMU architecture
from .Base import EstimationMethodBase

# Load the compiled C++ math engine
# Look in the current folder for the compiled libEnhancedIpDFT.so file
lib_path = os.path.join(os.path.dirname(__file__), "libEnhancedIpDFT.so")
eIpDFT_lib = ctypes.CDLL(lib_path)

# Explicitly tell Python what data types the C++ function expects so 
# Python doesnt send an integer when C++ expects a float, causing a crash.
eIpDFT_lib.run_eIpDFT_wrapper.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'), 
    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'), 
    ctypes.c_int,     
    ctypes.c_double,  
    ctypes.c_double,  
    ctypes.POINTER(ctypes.c_double), 
    ctypes.POINTER(ctypes.c_double), 
    ctypes.POINTER(ctypes.c_double)  
]

# The OpenPMU estimator class (Matches top of PMU.m)
class Estimator(EstimationMethodBase):
    def __init__(self, Fs=10000.0, sampleLen=400, *args, **kwargs):
        super(Estimator, self).__init__()
        
        # MATLAB: Algorithm Parameters (Top of PMU.m)
        self.f0 = 50.0
        self.Fs = float(Fs)
        self.Ts = 1.0 / self.Fs
        self.Fr = 50.0  # Reporting rate

        # MATLAB: Initialization Memory Variables
        self.fprev = self.f0           # fprev = f0;
        self.rocof_prev = 0.0          # rocof_prev = 0;
        self.is_first = True           # Equivalent to 'isnan(ph_prev_raw)' check

        # Buffer 4 full cycles (800 samples) to escape the DC Bin trap.
        # Optimization: In PMU.m, 'fifo' is dynamically updated. Here, we use a 
        # pre-allocated Numpy Circular Buffer to prevent Python memory thrashing.
        self.window_size = 800
        self.samples_received = 0

        # All using float64 to match standard IEEE C37.118 precision
        self.buffer = np.zeros(self.window_size, dtype=np.float64)
        self.raw_signal = np.zeros(self.window_size, dtype=np.float64)
        self.windowed_signal = np.zeros(self.window_size, dtype=np.float64)

        # Pre-calculate the Hanning window once (Periodic). 
        # MATLAB: applyWindow(fifo, 'hann');
        # Optimization: Doing this in __init__ instead of inside the fast loop 
        # saves the Raspberry Pi from calculating 640,000 cosines/sec.
        self.static_window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(self.window_size) / self.window_size))
        
        # Pre-multiply the calibration into a separate array to save math in the fast loop
        self.CALIBRATION_MULTIPLIER = 162.25
        self.calibrated_window = self.static_window * self.CALIBRATION_MULTIPLIER
        
        # These are empty C-type memory buckets we pass to C++ to hold the answers
        self.out_amp = ctypes.c_double(0.0)
        self.out_freq = ctypes.c_double(0.0)
        self.out_phase = ctypes.c_double(0.0)

    # The main loop called by OpenPMU every frame
    def getPhasor(self, samples):
        """ This function acts like the main loop in your PhasorEstimation_RunScript.m """
        
        # Convert incoming packet to a numpy array immediately
        new_samples = np.array(samples, dtype=np.float64)
        n_new = len(new_samples)

        # PACKET DROP DETECTOR
        # If the jump between the old buffer and the new network packet is unnatural (> 0.3V),
        # a UDP packet was dropped. Purge the history to prevent mathematical corruption.
        if len(new_samples) > 1 and np.max(np.abs(np.diff(new_samples))) > 0.3:
            self.samples_received = 0  # Purge corrupted history
        elif self.samples_received > 0:
            if abs(new_samples[0] - self.buffer[-1]) > 0.3:
                self.samples_received = 0  # Purge corrupted history
                
        # CIRCULAR BUFFER SHIFT
        # Shift the old data to the left, and insert the new data at the end
        self.buffer[:-n_new] = self.buffer[n_new:]
        self.buffer[-n_new:] = new_samples
        self.samples_received += n_new
        
        # If we haven't collected 4 full cycles yet, return safe defaults
        if self.samples_received < self.window_size:
            return [0.0, self.f0, 0.0, 0.0]
        
        # Define N (the size of the buffer) for the C++ call
        N = self.window_size 
        np.multiply(self.buffer, self.calibrated_window, out=self.windowed_signal)

        # Call the C++ library, handing it the array and the empty buckets.
        # MATLAB Equivalent: [A, ph, freq_raw] = estimate_eIpDFT(signal_win, f0, Ts, ...);
        eIpDFT_lib.run_eIpDFT_wrapper(
            self.windowed_signal, 
            self.static_window, 
            ctypes.c_int(N), 
            ctypes.c_double(self.f0), 
            ctypes.c_double(self.Ts), 
            ctypes.byref(self.out_amp), 
            ctypes.byref(self.out_freq), 
            ctypes.byref(self.out_phase)
        )

        # Extract the results from the C-buckets back into Python variables
        freq = self.out_freq.value

        # Convert to degrees for display
        ph_rad = self.out_phase.value
        ph_deg = ph_rad * (180.0 / np.pi)

        # MATLAB: meas.A = [meas.A, A/sqrt(2)]; (RMS Conversion)
        amp_peak = self.out_amp.value
        amp_rms = amp_peak / np.sqrt(2.0)

        # If the channel is dead/floating, C++ returns NaN. Catch it and output clean zeros.
        if np.isnan(freq) or np.isnan(amp_rms):
            freq = self.f0           # Default back to 50.00 Hz
            amp_rms = 0.0            # Force Voltage to 0.00 V
            ph_deg = 0.0             # Force Angle to 0.00 Deg
            self.is_first = True     # Reset the ROCOF filter memory so it doesn't spike on recovery

        # MATLAB: if isnan(ph_prev_raw) -> freq_smoothed = freq_raw; fprev = freq_raw;
        if self.is_first:
            self.fprev = freq
            self.freq_smoothed = freq  # Initialize the frequency filter
            self.is_first = False

        # DIGITAL LOW-PASS FILTER
        # We apply an Exponential Moving Average (EMA) to crush ADC white noise.
        
        # MATHLAB: Calculate filtered frequency
        # freq_smoothed = (alpha * freq_raw) + ((1 - alpha) * freq_prev_smoothed);
        # freq = freq_smoothed;
        alpha = 0.05 
        self.freq_smoothed = (alpha * freq) + ((1.0 - alpha) * self.freq_smoothed)
        freq = self.freq_smoothed

        # MATLAB: Calculate filtered ROCOF
        # rocof_raw = (freq - fprev) * Fr;
        # rocof_smoothed = (0.05 * rocof_raw) + (0.95 * rocof_prev);
        rocof_raw = (freq - self.fprev) * self.Fr
        rocof_smoothed = (alpha * rocof_raw) + ((1 - alpha) * self.rocof_prev)

        # MATLAB: fprev = freq; rocof_prev = rocof_smoothed;
        self.fprev = freq
        self.rocof_prev = rocof_smoothed

        # OpenPMU expects a list exactly in this order: [Mag, Freq, Phase, ROCOF]
        return [amp_rms, freq, ph_deg, rocof_smoothed]
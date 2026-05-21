/*
OpenPMU - Phasor Estimator (Enhanced IpDFT Edition)
Copyright (C) 2021  www.OpenPMU.org
Modified for Bachelor's Thesis Implementation by Haron Akram Ahmed Mohammed 2026
Email: haamo@kth.se
*/

#include <vector>
#include <complex>
#include <cmath>

const double PI = 3.14159265358979323846;

// A structured container to hold our three main outputs
struct PhasorResult {
    double amplitude;
    double phase;
    double frequency;
};

// HELPER: Matches MATLAB's 'wrapToPi()' to keep phase between -180 and +180 degrees (-pi to +pi)
double wrapToPi(double angle) {
    angle = std::fmod(angle + PI, 2.0 * PI);
    if (angle < 0.0) angle += 2.0 * PI;
    return angle - PI;
}

// The Core e-IpDFT Algorithm

// Use "const double* signal_ptr" to allow Python to pass raw memory directly to C++
PhasorResult estimate_eIpDFT(const double* signal_ptr, const double* window_ptr, int N, double f0, double Ts) {

    // MATLAB: k0 = round(f0 * N * Ts);
    double k0 = std::round(f0 * N * Ts);
    
    // MATLAB: G = 0.5; dF = 1 / (N * Ts);
    double G = 0.5; 
    double dF = 1.0 / (N * Ts);
    
    PhasorResult result;
    double freq_est = f0, A_est = 0.0, ph_est = 0.0;

    // Standard IpDFT 
    std::complex<double> X_main(0,0), X_right(0,0), X_left(0,0);

    // Pre-calculate constants for the loop
    double mult_main  = -2.0 * PI * k0 / N;
    double mult_right = -2.0 * PI * (k0 + 1.0) / N;
    double mult_left  = -2.0 * PI * (k0 - 1.0) / N;

    // OPTIMIZATION: Recursive Digital Oscillators. 
    // In MATLAB, the entire vector is generated at once: sum(signal_win .* exp(...))
    // To match this in C++ without putting slow std::cos/sin functions inside the loop, 
    // we calculate the complex "step" once, and multiply it iteratively (Euler's formula).
    std::complex<double> step_main(std::cos(mult_main), std::sin(mult_main));
    std::complex<double> step_right(std::cos(mult_right), std::sin(mult_right));
    std::complex<double> step_left(std::cos(mult_left), std::sin(mult_left));

    // For complex multiplication instead of trig
    std::complex<double> curr_main(1.0, 0.0);
    std::complex<double> curr_right(1.0, 0.0);
    std::complex<double> curr_left(1.0, 0.0);

    for(int n = 0; n < N; n++) {
        // Accumulate the bins
        X_main  += signal_ptr[n] * curr_main;
        X_right += signal_ptr[n] * curr_right;
        X_left  += signal_ptr[n] * curr_left;

        // Advance the oscillator to the next sample point
        curr_main *= step_main;
        curr_right *= step_right;
        curr_left *= step_left;
    }

    // MATLAB: mag_main = abs(X_main);
    double mag_main = std::abs(X_main), mag_right = std::abs(X_right), mag_left = std::abs(X_left);
    
    // MATLAB: if abs(X_right) > abs(X_left) ... direction = 1;
    double mag_neighbor, direction;
    if (mag_right > mag_left) { mag_neighbor = mag_right; direction = 1.0; } 
    else { mag_neighbor = mag_left; direction = -1.0; }

    // MATLAB: delta = direction * ((2 * mag_neighbor - mag_main) / (mag_neighbor + mag_main));
    double delta = direction * ((2.0 * mag_neighbor - mag_main) / (mag_neighbor + mag_main));
    
    // MATLAB: freq_est = (k0 + delta) * dF;
    freq_est = (k0 + delta) * dF;
    
    // MATLAB: if delta == 0; corr_factor = 1; else corr_factor = ...
    double corr_factor = (delta == 0.0) ? 1.0 : (PI * delta) / std::sin(PI * delta) * (1.0 - delta * delta);
    
    // MATLAB: A_est = abs(X_main * (2 / (G * N)) * corr_factor);
    A_est = std::abs(X_main * (2.0 / (G * N)) * corr_factor);
    ph_est = std::arg(X_main) - PI * delta;


    // Intelligent Ghost & Harmonic Cancellation (Iteration)
    // MATLAB: num_iterations = 2;
    int num_iterations = 2;
    double k2 = 2.0 * k0;
    double mult_k2 = -2.0 * PI * k2 / N;

    for(int iter = 0; iter < num_iterations; iter++) {
        std::complex<double> X_garb_main(0,0), X_garb_right(0,0), X_garb_left(0,0), X_h2(0,0);
        
        // Pre-calculate frequencies outside the loop to save CPU
        double w_freq = 2.0 * PI * freq_est * Ts;
        
        // Setup Recursive Oscillators for the Harmonic removal
        std::complex<double> step_fund(std::cos(w_freq), std::sin(w_freq));
        std::complex<double> curr_fund(std::cos(ph_est), std::sin(ph_est));
        std::complex<double> step_k2(std::cos(mult_k2), std::sin(mult_k2));
        std::complex<double> curr_k2(1.0, 0.0);

        for(int n = 0; n < N; n++) {
            // MATLAB: fund_signal = A_est * cos(2 * pi * freq_est * n * Ts + ph_est);
            // OPTIMIZATION: Extract the real part of the oscillator instead of calling cos()
            double fund_sample = A_est * curr_fund.real();
            
            // MATLAB: residual_win = signal_win - applyWindow(fund_signal, 'hann');
            double residual_sample = signal_ptr[n] - (fund_sample * window_ptr[n]);
            
            // MATLAB: X_h2 = sum(residual_win .* exp(-1i * 2 * pi * (k2)/N * n));
            X_h2 += residual_sample * curr_k2;

            curr_fund *= step_fund;
            curr_k2 *= step_k2;
        }
        
        // MATLAB: A_h2 = abs(X_h2 * (2 / (G * N)));
        double A_h2 = std::abs(X_h2 * (2.0 / (G * N)));
        double ph_h2 = std::arg(X_h2);
        
        double w_k2_freq = 2.0 * PI * (2.0 * freq_est) * Ts;
        
        // Setup Recursive Oscillators for Ghost removal
        std::complex<double> step_harm2(std::cos(w_k2_freq), std::sin(w_k2_freq));
        std::complex<double> curr_harm2(std::cos(ph_h2), std::sin(ph_h2));
        std::complex<double> step_ghost(std::cos(-w_freq), std::sin(-w_freq));
        std::complex<double> curr_ghost(std::cos(-ph_est), std::sin(-ph_est));

        curr_main = {1.0, 0.0};
        curr_right = {1.0, 0.0};
        curr_left = {1.0, 0.0};

        for(int n = 0; n < N; n++) {
            // MATLAB: ghost_signal = (A_est / 2) * exp(-1i * (2 * pi * freq_est * n * Ts + ph_est));
            std::complex<double> ghost_sample = (A_est / 2.0) * curr_ghost;
            
            // MATLAB: harm2_signal = A_h2 * cos(2 * pi * (k2*dF) * n * Ts + ph_h2);
            double harm2_sample = A_h2 * curr_harm2.real();
            
            // MATLAB: garbage_win = applyWindow(garbage_signal, 'hann');
            std::complex<double> garbage_windowed = (ghost_sample + harm2_sample) * window_ptr[n];
            
            // MATLAB: X_garb_main = sum(garbage_win .* exp(-1i * 2 * pi * (k0)/N * n));
            X_garb_main  += garbage_windowed * curr_main;
            X_garb_right += garbage_windowed * curr_right;
            X_garb_left  += garbage_windowed * curr_left;

            curr_ghost *= step_ghost;
            curr_harm2 *= step_harm2;
            curr_main *= step_main;
            curr_right *= step_right;
            curr_left *= step_left;
        }

        // MATLAB: X_clean_main = X_main - X_garb_main;
        std::complex<double> X_clean_main = X_main - X_garb_main;
        std::complex<double> X_clean_right = X_right - X_garb_right;
        std::complex<double> X_clean_left = X_left - X_garb_left;

        // MATLAB: mag_main = abs(X_clean_main); (and Direction logic)
        mag_main = std::abs(X_clean_main);
        if (std::abs(X_clean_right) > std::abs(X_clean_left)) { mag_neighbor = std::abs(X_clean_right); direction = 1.0; } 
        else { mag_neighbor = std::abs(X_clean_left); direction = -1.0; }

        // MATLAB: delta = direction * ((2 * mag_neighbor - mag_main) / (...));
        delta = direction * ((2.0 * mag_neighbor - mag_main) / (mag_neighbor + mag_main));
        freq_est = (k0 + delta) * dF;
        double corr_factor = (delta == 0.0) ? 1.0 : (PI * delta) / std::sin(PI * delta) * (1.0 - delta * delta);
        
        A_est = std::abs(X_clean_main * (2.0 / (G * N)) * corr_factor);
        ph_est = std::arg(X_clean_main) - PI * delta;
    }

    double time_shift_samples = (N - 1.0) / 2.0; 
    double phase_compensation = 2.0 * PI * freq_est * (time_shift_samples * Ts);
    ph_est += phase_compensation;

    // Output
    result.frequency = freq_est;
    result.amplitude = A_est;
    result.phase = wrapToPi(ph_est); 
    return result;
}

// ---------------------------------------------------------
// The Python Bridge (How Python talks to C++)
// ---------------------------------------------------------

extern "C" {
    void run_eIpDFT_wrapper(const double* signal_ptr, const double* window_ptr, int N, double f0, double Ts, double* out_amp, double* out_freq, double* out_phase) {
        // Call the math engine (Equivalent to MATLAB: [A, ph, freq_raw] = estimate_eIpDFT(...))
        PhasorResult res = estimate_eIpDFT(signal_ptr, window_ptr, N, f0, Ts);
        *out_amp = res.amplitude;
        *out_freq = res.frequency;
        *out_phase = res.phase;
    }
}
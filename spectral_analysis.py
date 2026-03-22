import numpy as np
from scipy.fft import fft, fftfreq


def perform_fft(signal_data, sampling_rate):
    """
    Apply FFT to calculate frequency spectrum
    
    Parameters:
    -----------
    signal_data : array-like
        Time domain signal data
    sampling_rate : float
        Sampling rate (Hz)
    
    Returns:
    --------
    tuple : (frequency array, frequency spectrum amplitude)
    """
    n = len(signal_data)
    # Apply Hanning window to reduce spectral leakage
    window = np.hanning(n)
    windowed_signal = signal_data * window
    # Window correction factor for amplitude normalization
    window_correction = np.mean(window)
    # Perform FFT
    fft_result = fft(windowed_signal)
    # Create frequency array
    freq = fftfreq(n, 1 / sampling_rate)
    # Select only positive frequencies (symmetric, so only half needed)
    half_n = n // 2
    freq = freq[:half_n]
    # Calculate amplitude spectrum (normalize magnitude with window correction)
    magnitude = 2.0 / (n * window_correction) * np.abs(fft_result[:half_n])

    return freq, magnitude


def detect_fault_frequencies(freq, magnitude, fault_freqs, tolerance=0.1):
    """
    Detect fault frequencies in frequency spectrum
    
    Parameters:
    -----------
    freq : array-like
        Frequency array
    magnitude : array-like
        Amplitude spectrum
    fault_freqs : dict
        Theoretical fault frequency values (BPFO, BPFI, BSF, FTF)
    tolerance : float
        Frequency range tolerance for fault detection
    
    Returns:
    --------
    dict : Detection results for each fault frequency
    """
    fault_detection = {}
    fault_peaks = {}

    # Check each fault frequency
    for fault_name, fault_freq in fault_freqs.items():
        if fault_name == 'FR':  # Skip rotation frequency
            continue

        # Detect fundamental frequency and harmonics
        harmonics = [1, 2, 3]  # Fundamental and 2x, 3x harmonics
        fault_detection[fault_name] = []
        fault_peaks[fault_name] = []

        for harmonic in harmonics:
            target_freq = fault_freq * harmonic
            # Find frequency indices within ±tolerance range of target frequency
            indices = np.where((freq >= target_freq - tolerance) & (freq <= target_freq + tolerance))[0]

            if len(indices) > 0:
                # Find index with highest amplitude in the range
                max_idx = indices[np.argmax(magnitude[indices])]
                detected_freq = freq[max_idx]
                peak_value = magnitude[max_idx]

                fault_detection[fault_name].append({
                    'harmonic': harmonic,
                    'theoretical_freq': target_freq,
                    'detected_freq': detected_freq,
                    'amplitude': peak_value,
                    'deviation': (detected_freq - target_freq) / target_freq * 100  # Deviation in %
                })

                fault_peaks[fault_name].append((detected_freq, peak_value))

    return fault_detection, fault_peaks
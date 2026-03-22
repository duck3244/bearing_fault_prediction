import numpy as np
from scipy import stats


def extract_time_domain_features(signal_data):
    """
    Extract features from time domain
    
    Parameters:
    -----------
    signal_data : array-like
        Time domain signal data
        
    Returns:
    --------
    dict : Time domain features
    """
    # Basic statistical features
    mean = np.mean(signal_data)
    std_dev = np.std(signal_data)
    rms = np.sqrt(np.mean(np.square(signal_data)))
    peak = np.max(np.abs(signal_data))
    
    # Kurtosis - useful for detecting abnormal peaks
    kurtosis = stats.kurtosis(signal_data)
    
    # Skewness - asymmetry of distribution
    skewness = stats.skew(signal_data)
    
    # Crest Factor - peak/RMS
    crest_factor = peak / rms if rms > 0 else 0
    
    # Cache repeated calculations
    mean_abs = np.mean(np.abs(signal_data))
    mean_sqrt_abs = np.mean(np.sqrt(np.abs(signal_data)))

    # Impulse Factor
    impulse_factor = peak / mean_abs if mean_abs > 0 else 0

    # Shape Factor
    shape_factor = rms / mean_abs if mean_abs > 0 else 0

    # Clearance Factor
    clearance_factor = peak / mean_sqrt_abs ** 2 if mean_sqrt_abs > 0 else 0
    
    # Energy
    energy = np.sum(np.square(signal_data))
    
    # Entropy (uncertainty of sample value distribution)
    # Calculate histogram bins
    hist, bin_edges = np.histogram(signal_data, bins=50, density=True)
    # Select only non-zero probabilities to calculate entropy
    non_zero_hist = hist[hist > 0]
    entropy = -np.sum(non_zero_hist * np.log2(non_zero_hist))
    
    # Range (max-min)
    range_val = np.max(signal_data) - np.min(signal_data)

    # Zero Crossing Rate
    zero_crossings = np.sum(np.diff(np.signbit(signal_data)))
    
    return {
        'mean': mean,
        'std_dev': std_dev,
        'rms': rms,
        'peak': peak,
        'kurtosis': kurtosis,
        'skewness': skewness,
        'crest_factor': crest_factor,
        'impulse_factor': impulse_factor,
        'shape_factor': shape_factor,
        'clearance_factor': clearance_factor,
        'energy': energy,
        'entropy': entropy,
        'range': range_val,
        'zero_crossing_rate': zero_crossings
    }


def extract_frequency_domain_features(freq, magnitude, fault_freqs):
    """
    Extract features from frequency domain
    
    Parameters:
    -----------
    freq : array-like
        Frequency array
    magnitude : array-like
        Amplitude spectrum
    fault_freqs : dict
        Theoretical fault frequency values (BPFO, BPFI, BSF, FTF)
        
    Returns:
    --------
    dict : Frequency domain features
    """
    # Spectrum statistical features
    mean_freq = np.mean(magnitude)
    std_freq = np.std(magnitude)
    max_freq = np.max(magnitude)
    
    # Spectral Centroid
    if np.sum(magnitude) > 0:
        spectral_centroid = np.sum(freq * magnitude) / np.sum(magnitude)
    else:
        spectral_centroid = 0
    
    # Frequency bandwidth
    if np.sum(magnitude) > 0:
        bandwidth = np.sqrt(np.sum(((freq - spectral_centroid) ** 2) * magnitude) / np.sum(magnitude))
    else:
        bandwidth = 0
    
    # Fault frequency features
    fault_features = {}
    
    # Calculate energy around fault frequencies
    for fault_name, fault_freq in fault_freqs.items():
        if fault_name == 'FR':  # Consider base rotation frequency as a basic fault frequency
            continue
            
        # Calculate energy for fundamental frequency and harmonics
        harmonics = [1, 2, 3]  # Fundamental and 2x, 3x harmonics
        for harmonic in harmonics:
            target_freq = fault_freq * harmonic
            # Find frequency indices within ±0.5Hz range of target frequency
            indices = np.where((freq >= target_freq - 0.5) & (freq <= target_freq + 0.5))[0]
            
            if len(indices) > 0:
                # Calculate energy in this range
                energy = np.sum(magnitude[indices] ** 2)
                fault_features[f'{fault_name}_h{harmonic}_energy'] = energy
            else:
                fault_features[f'{fault_name}_h{harmonic}_energy'] = 0
    
    # Low frequency (0-200Hz) energy ratio
    low_freq_idx = np.where(freq <= 200)[0]
    if len(magnitude) > 0:
        low_freq_energy_ratio = np.sum(magnitude[low_freq_idx] ** 2) / np.sum(magnitude ** 2)
    else:
        low_freq_energy_ratio = 0
    
    # Combine results
    features = {
        'mean_magnitude': mean_freq,
        'std_magnitude': std_freq,
        'max_magnitude': max_freq,
        'spectral_centroid': spectral_centroid,
        'bandwidth': bandwidth,
        'low_freq_energy_ratio': low_freq_energy_ratio
    }
    
    # Add fault frequency features
    features.update(fault_features)
    
    return features


def extract_wavelet_features(signal_data, wavelet='db4', level=5):
    """
    Extract features using wavelet transform
    
    Parameters:
    -----------
    signal_data : array-like
        Time domain signal data
    wavelet : str
        Type of wavelet to use
    level : int
        Decomposition level
        
    Returns:
    --------
    dict : Wavelet features
    """
    try:
        import pywt
    except ImportError:
        print("PyWavelets library is not installed. Skipping wavelet feature extraction.")
        return {}
    
    # Perform wavelet decomposition
    coeffs = pywt.wavedec(signal_data, wavelet, level=level)
    
    # Extract features for each level
    features = {}
    
    # Approximation coefficients (last level)
    cA = coeffs[0]
    features['wavelet_approx_energy'] = np.sum(cA ** 2)
    features['wavelet_approx_mean'] = np.mean(np.abs(cA))
    features['wavelet_approx_std'] = np.std(cA)
    
    # Detail coefficients (each level)
    for i, cD in enumerate(coeffs[1:], 1):
        features[f'wavelet_detail_{i}_energy'] = np.sum(cD ** 2)
        features[f'wavelet_detail_{i}_mean'] = np.mean(np.abs(cD))
        features[f'wavelet_detail_{i}_std'] = np.std(cD)
    
    return features
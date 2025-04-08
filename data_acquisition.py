import numpy as np
import requests
from io import BytesIO
import zipfile


def download_cwru_dataset():
    """
    Download the CWRU bearing dataset

    Returns:
    --------
    bool : Success or failure of download
    """
    print("Downloading CWRU bearing dataset...")
    url = "https://engineering.case.edu/sites/default/files/drive_end_2hp.zip"
    try:
        response = requests.get(url)
        zip_file = BytesIO(response.content)
        with zipfile.ZipFile(zip_file, 'r') as z:
            z.extractall('cwru_data')
        print("Dataset download completed")
        return True
    except Exception as e:
        print(f"Dataset download failed: {e}")
        print("Generating sample data instead")
        return False


def create_sample_data(num_samples=10000, sampling_rate=12000, rpm=1800, fault_type='all', noise_level=0.5):
    """
    Generate sample vibration data

    Parameters:
    -----------
    num_samples : int
        Number of samples to generate
    sampling_rate : float
        Sampling rate in Hz
    rpm : float
        Rotation speed in RPM
    fault_type : str
        Type of fault to generate ('normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault', or 'all')
    noise_level : float
        Level of noise to add (0.0-1.0)

    Returns:
    --------
    dict : Dictionary containing sample data
    """
    t = np.linspace(0, num_samples / sampling_rate, num_samples)

    # Rotation frequency (Hz)
    rotation_freq = rpm / 60  # Hz

    # Normal signal - rotation frequency component + noise
    normal_signal = np.sin(2 * np.pi * rotation_freq * t) + noise_level * np.random.randn(len(t))

    result = {
        'time': t,
        'sampling_rate': sampling_rate,
        'rpm': rpm
    }

    # If only one fault type is requested, create only that one
    if fault_type != 'all':
        # Always include normal signal
        result['normal'] = normal_signal

        if fault_type == 'normal':
            return result

    # BPFO fault signal (outer race fault)
    if fault_type == 'all' or fault_type == 'outer_fault':
        bpfo_freq = 3.5 * rotation_freq  # Outer race fault frequency (example value)
        outer_fault_signal = normal_signal + 1.2 * np.sin(2 * np.pi * bpfo_freq * t)
        # Add intermittent impacts (outer race fault characteristic)
        impact_idx = np.arange(0, len(t), int(sampling_rate / bpfo_freq))
        for idx in impact_idx:
            if idx < len(t):
                impact_len = 20  # Impact length
                if idx + impact_len < len(t):
                    outer_fault_signal[idx:idx + impact_len] += 2.0 * np.exp(-np.arange(impact_len) / 5)
        result['outer_fault'] = outer_fault_signal

    # BPFI fault signal (inner race fault)
    if fault_type == 'all' or fault_type == 'inner_fault':
        bpfi_freq = 5.4 * rotation_freq  # Inner race fault frequency (example value)
        inner_fault_signal = normal_signal + 1.5 * np.sin(2 * np.pi * bpfi_freq * t)
        # Inner race fault characteristic (amplitude modulation with rotation)
        inner_fault_signal *= (1 + 0.3 * np.sin(2 * np.pi * rotation_freq * t))
        # Add intermittent impacts (inner race fault characteristic)
        impact_idx = np.arange(0, len(t), int(sampling_rate / bpfi_freq))
        for idx in impact_idx:
            if idx < len(t):
                impact_len = 15  # Impact length
                if idx + impact_len < len(t):
                    inner_fault_signal[idx:idx + impact_len] += 2.5 * np.exp(-np.arange(impact_len) / 4)
        result['inner_fault'] = inner_fault_signal

    # Ball fault signal
    if fault_type == 'all' or fault_type == 'ball_fault':
        bsf_freq = 2.7 * rotation_freq  # Ball fault frequency (example value)
        ball_fault_signal = normal_signal + 1.0 * np.sin(2 * np.pi * bsf_freq * t)
        # Add irregular impacts (ball fault characteristic)
        impact_idx = np.arange(0, len(t), int(sampling_rate / bsf_freq))
        for idx in impact_idx:
            if idx < len(t) and np.random.rand() > 0.3:  # 30% chance to skip impact (irregularity)
                impact_len = 10  # Impact length
                if idx + impact_len < len(t):
                    ball_fault_signal[idx:idx + impact_len] += 1.8 * np.exp(-np.arange(impact_len) / 3)
        result['ball_fault'] = ball_fault_signal

    # Cage fault signal
    if fault_type == 'all' or fault_type == 'cage_fault':
        ftf_freq = 0.4 * rotation_freq  # Cage fault frequency (example value)
        cage_fault_signal = normal_signal + 0.8 * np.sin(2 * np.pi * ftf_freq * t)
        # Add low frequency modulation (cage fault characteristic)
        cage_fault_signal += 0.5 * np.sin(2 * np.pi * ftf_freq / 2 * t)
        result['cage_fault'] = cage_fault_signal

    return result
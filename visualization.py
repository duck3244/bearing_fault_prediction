import matplotlib.pyplot as plt
import numpy as np
from spectral_analysis import perform_fft


def visualize_time_domain_features(features_dict, signal_type):
    """
    Visualize time domain features
    
    Parameters:
    -----------
    features_dict : dict
        Dictionary of time domain features
    signal_type : str
        Signal type (normal, fault, etc.)
    """
    # Select features (only display important ones)
    selected_features = [
        'rms', 'peak', 'kurtosis', 'crest_factor', 
        'impulse_factor', 'shape_factor', 'entropy'
    ]
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Display features as bar chart
    values = [features_dict[feature] for feature in selected_features]
    bars = plt.bar(selected_features, values, color='skyblue')
    
    # Display values above bars
    for bar, value in zip(bars, values):
        if abs(value) < 0.01 or abs(value) > 1000:
            # Use scientific notation
            plt.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.1,
                f'{value:.2e}',
                ha='center', va='bottom', rotation=0, fontsize=9
            )
        else:
            plt.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.1,
                f'{value:.4f}',
                ha='center', va='bottom', rotation=0, fontsize=9
            )
    
    plt.title(f'Time Domain Features - {signal_type.replace("_", " ").title()}')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"time_domain_features_{signal_type}.png")
    plt.show()


def visualize_results(data, fault_freqs, fault_detection, fault_peaks, time_features, freq_features, signal_type='normal'):
    """
    Visualize FFT results and fault frequencies
    
    Parameters:
    -----------
    data : dict
        Original data (time, signals, sampling rate, etc.)
    fault_freqs : dict
        Theoretical fault frequency values
    fault_detection : dict
        Detected fault frequency information
    fault_peaks : dict
        Peak values at fault frequencies
    time_features : dict
        Time domain features
    freq_features : dict
        Frequency domain features
    signal_type : str
        Type of signal being analyzed
    """
    # Create 3x2 subplots (with additional row)
    fig, axs = plt.subplots(3, 2, figsize=(15, 18))

    # Plot original signal
    axs[0, 0].plot(data['time'], data[signal_type])
    axs[0, 0].set_title(f"{signal_type.replace('_', ' ').title()} - Time Domain Signal")
    axs[0, 0].set_xlabel('Time (seconds)')
    axs[0, 0].set_ylabel('Amplitude')
    axs[0, 0].grid(True)

    # Calculate FFT spectrum
    freq, magnitude = perform_fft(data[signal_type], data['sampling_rate'])

    # Full frequency spectrum
    axs[0, 1].plot(freq, magnitude)
    axs[0, 1].set_title(f"{signal_type.replace('_', ' ').title()} - Frequency Spectrum")
    axs[0, 1].set_xlabel('Frequency (Hz)')
    axs[0, 1].set_ylabel('Amplitude')
    axs[0, 1].grid(True)

    # Low frequency range zoom (0-200Hz)
    low_freq_idx = np.where(freq <= 200)[0]
    axs[1, 0].plot(freq[low_freq_idx], magnitude[low_freq_idx])
    axs[1, 0].set_title('Low Frequency Range (0-200Hz)')
    axs[1, 0].set_xlabel('Frequency (Hz)')
    axs[1, 0].set_ylabel('Amplitude')
    axs[1, 0].grid(True)

    # Mark fault frequencies
    for fault_name, peaks in fault_peaks.items():
        for freq_peak, ampl in peaks:
            if freq_peak <= 200:  # Only mark in low frequency plot
                axs[1, 0].plot(freq_peak, ampl, 'ro')
                axs[1, 0].text(freq_peak, ampl, f' {fault_name}', fontsize=9)

    # Fault frequency results summary
    axs[1, 1].axis('off')  # Hide axis
    summary_text = f"Bearing Fault Frequency Analysis Results ({signal_type})\n\n"
    summary_text += f"Rotation Speed: {data['rpm']} RPM ({fault_freqs['FR']:.2f} Hz)\n\n"

    for fault_name, detections in fault_detection.items():
        summary_text += f"{fault_name} (Theoretical: {fault_freqs[fault_name]:.2f} Hz):\n"

        if detections:
            for detection in detections:
                summary_text += f"  {detection['harmonic']}x: Detected {detection['detected_freq']:.2f} Hz, Error {detection['deviation']:.2f}%, Amplitude {detection['amplitude']:.4f}\n"
        else:
            summary_text += "  Not detected\n"

        summary_text += "\n"

    axs[1, 1].text(0, 1, summary_text, fontsize=10, va='top')

    # Visualize key time domain features
    selected_time_features = [
        'rms', 'kurtosis', 'crest_factor', 'impulse_factor'
    ]
    values = [time_features[feature] for feature in selected_time_features]
    axs[2, 0].bar(selected_time_features, values, color='lightgreen')
    axs[2, 0].set_title('Key Time Domain Features')
    axs[2, 0].set_ylabel('Value')
    axs[2, 0].grid(axis='y', linestyle='--', alpha=0.7)
    # Display values
    for i, v in enumerate(values):
        axs[2, 0].text(i, v + 0.02, f'{v:.3f}', ha='center')
    
    # Visualize key frequency domain features
    selected_freq_features = [
        'max_magnitude', 'spectral_centroid', 'low_freq_energy_ratio'
    ]
    # Add maximum fault energy
    fault_energies = {k: v for k, v in freq_features.items() if '_energy' in k}
    if fault_energies:
        max_energy_feature = max(fault_energies, key=fault_energies.get)
        if max_energy_feature not in selected_freq_features:
            selected_freq_features.append(max_energy_feature)
    
    values = [freq_features[feature] for feature in selected_freq_features]
    axs[2, 1].bar(selected_freq_features, values, color='lightsalmon')
    axs[2, 1].set_title('Key Frequency Domain Features')
    axs[2, 1].set_ylabel('Value')
    axs[2, 1].tick_params(axis='x', rotation=45)
    axs[2, 1].grid(axis='y', linestyle='--', alpha=0.7)
    # Display values
    for i, v in enumerate(values):
        if v < 0.001 or v > 1000:
            axs[2, 1].text(i, v + 0.02 * max(values), f'{v:.2e}', ha='center')
        else:
            axs[2, 1].text(i, v + 0.02 * max(values), f'{v:.3f}', ha='center')

    plt.tight_layout()
    plt.savefig(f"bearing_fault_{signal_type}.png")
    plt.show()
import numpy as np
import pytest

from app.core.spectral_analysis import detect_fault_frequencies, perform_fft


def test_fft_finds_known_sine_frequency():
    sr = 12_000
    n = 8192
    f0 = 150.0
    t = np.arange(n) / sr
    sig = np.sin(2 * np.pi * f0 * t)

    freq, mag = perform_fft(sig, sr)
    peak_idx = int(np.argmax(mag))
    # Bin resolution = sr/n ≈ 1.46 Hz — peak should land within ~2 bins of f0
    assert freq[peak_idx] == pytest.approx(f0, abs=2 * sr / n)


def test_fft_returns_half_spectrum():
    sr = 12_000
    n = 4096
    sig = np.random.default_rng(0).standard_normal(n)
    freq, mag = perform_fft(sig, sr)
    assert len(freq) == n // 2
    assert len(mag) == n // 2
    assert freq[0] >= 0
    # Last bin is just below Nyquist
    assert freq[-1] < sr / 2


def test_detect_fault_frequencies_finds_injected_tone():
    sr = 12_000
    n = 16_384
    t = np.arange(n) / sr
    bpfo = 162.0  # Hz, arbitrary fault frequency
    sig = np.sin(2 * np.pi * bpfo * t) + 0.05 * np.random.default_rng(0).standard_normal(n)

    freq, mag = perform_fft(sig, sr)
    detection, _ = detect_fault_frequencies(freq, mag, {'BPFO': bpfo, 'FR': 30}, tolerance=2.0)

    bpfo_hits = detection['BPFO']
    h1 = next((h for h in bpfo_hits if h['harmonic'] == 1), None)
    assert h1 is not None
    assert h1['detected_freq'] == pytest.approx(bpfo, abs=2.0)
    assert abs(h1['deviation']) < 2.0  # percent

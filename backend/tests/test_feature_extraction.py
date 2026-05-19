import math

import numpy as np
import pytest

from app.core.feature_extraction import (
    extract_frequency_domain_features,
    extract_time_domain_features,
)


def test_zero_crossing_rate_is_normalized():
    """For a clean sinusoid of k cycles, ZCR ≈ 2k / N."""
    n = 10_000
    k = 10  # 10 full cycles
    sig = np.sin(np.linspace(0, 2 * np.pi * k, n))
    feats = extract_time_domain_features(sig)
    # 2 crossings per cycle; tolerate ±1 sample
    expected = 2 * k / n
    assert feats['zero_crossing_rate'] == pytest.approx(expected, abs=1.5 / n)


def test_zero_crossing_rate_in_unit_range():
    rng = np.random.default_rng(0)
    sig = rng.standard_normal(5000)
    feats = extract_time_domain_features(sig)
    assert 0.0 <= feats['zero_crossing_rate'] <= 1.0


def test_rms_of_pure_sine_is_amplitude_over_sqrt2():
    n = 8192
    a = 2.0
    sig = a * np.sin(np.linspace(0, 200 * np.pi, n))
    feats = extract_time_domain_features(sig)
    assert feats['rms'] == pytest.approx(a / math.sqrt(2), rel=1e-3)


def test_constant_signal_has_zero_std():
    feats = extract_time_domain_features(np.ones(1024))
    assert feats['std_dev'] == pytest.approx(0.0, abs=1e-12)
    assert feats['rms'] == pytest.approx(1.0, abs=1e-12)


def test_low_freq_ratio_guarded_for_zero_magnitude():
    freq = np.linspace(0, 1000, 100)
    mag = np.zeros_like(freq)
    ff = {'BPFO': 100, 'BPFI': 150, 'BSF': 80, 'FTF': 12, 'FR': 30}
    feats = extract_frequency_domain_features(freq, mag, ff)
    # Must be 0, not NaN
    assert feats['low_freq_energy_ratio'] == 0.0
    assert not math.isnan(feats['low_freq_energy_ratio'])


def test_low_freq_ratio_between_zero_and_one():
    rng = np.random.default_rng(1)
    freq = np.linspace(0, 6000, 4096)
    mag = np.abs(rng.standard_normal(4096))
    ff = {'BPFO': 100, 'BPFI': 150, 'BSF': 80, 'FTF': 12, 'FR': 30}
    feats = extract_frequency_domain_features(freq, mag, ff)
    assert 0.0 <= feats['low_freq_energy_ratio'] <= 1.0


def test_harmonic_energy_features_present():
    freq = np.linspace(0, 1000, 1000)
    mag = np.ones_like(freq)
    ff = {'BPFO': 100, 'BPFI': 150, 'BSF': 80, 'FTF': 12, 'FR': 30}
    feats = extract_frequency_domain_features(freq, mag, ff)
    for fault in ('BPFO', 'BPFI', 'BSF', 'FTF'):
        for h in (1, 2, 3):
            assert f'{fault}_h{h}_energy' in feats

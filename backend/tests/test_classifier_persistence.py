import os

import numpy as np
import pytest
from scipy.io import savemat

from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.bearing_presets import preset_to_bearing_params
from app.core.fault_classifier import BearingFaultClassifier
from app.core.feature_extraction import (
    extract_frequency_domain_features,
    extract_time_domain_features,
)
from app.core.spectral_analysis import perform_fft


def _make_fake_mfpt_dir(tmp_path, n_per_class=2, length=24_000, sr=12_000):
    """Create a small MFPT-style dataset that lives entirely in tmp_path."""
    rng = np.random.default_rng(0)
    t = np.arange(length) / sr
    # Use the SKF preset frequencies so synthetic patterns match what the classifier
    # would compute via bearing_calculations.
    bp = preset_to_bearing_params('SKF-6205')
    ff = calculate_bearing_frequencies(1800, bp)

    def make(kind, idx):
        base = 0.3 * rng.standard_normal(length) + np.sin(2 * np.pi * 30 * t)
        if kind == 'baseline':
            sig = base
        elif kind == 'InnerRaceFault':
            sig = base + 1.5 * np.sin(2 * np.pi * ff['BPFI'] * t)
        elif kind == 'OuterRaceFault':
            sig = base + 1.2 * np.sin(2 * np.pi * ff['BPFO'] * t)
        path = tmp_path / f'{kind}_{idx}.mat'
        savemat(str(path), {'bearing': {'gs': sig, 'sr': float(sr), 'rate': 30.0, 'load': 0.0}})
        return path

    for kind in ('baseline', 'InnerRaceFault', 'OuterRaceFault'):
        for i in range(n_per_class):
            make(kind, i + 1)
    return tmp_path


def test_train_from_dataset_and_predict(tmp_path):
    data_dir = _make_fake_mfpt_dir(tmp_path)
    clf = BearingFaultClassifier()
    meta = clf.train_from_dataset(
        str(data_dir),
        bearing_params=preset_to_bearing_params('SKF-6205'),
        window=6000,
        hop=3000,
        default_rpm=1800,
        default_sampling_rate=12000,
    )
    assert meta['n_files'] == 6
    assert meta['n_windows'] > 0
    assert clf.is_trained
    assert set(clf.trained_classes) == {'normal', 'inner_fault', 'outer_fault'}
    assert clf.source and clf.source.startswith('dataset:')


def test_predict_returns_only_trained_classes(tmp_path):
    data_dir = _make_fake_mfpt_dir(tmp_path)
    clf = BearingFaultClassifier()
    clf.train_from_dataset(
        str(data_dir),
        bearing_params=preset_to_bearing_params('SKF-6205'),
        window=6000, hop=3000, default_rpm=1800, default_sampling_rate=12000,
    )

    # Build features for an out-of-distribution signal — predict() must not crash
    # on a 3-class model (this was the original IndexError).
    sig = np.random.default_rng(1).standard_normal(8192)
    tf = extract_time_domain_features(sig)
    freq, mag = perform_fft(sig, 12000)
    ff = calculate_bearing_frequencies(1800, preset_to_bearing_params('SKF-6205'))
    ffeat = extract_frequency_domain_features(freq, mag, ff)

    label, conf, probs = clf.predict(tf, ffeat)
    assert label in {'normal', 'inner_fault', 'outer_fault'}
    assert set(probs) == {'normal', 'inner_fault', 'outer_fault'}
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-6)


def test_amplitude_augmentation_multiplies_training_windows(tmp_path):
    data_dir = _make_fake_mfpt_dir(tmp_path)
    clf_no_aug = BearingFaultClassifier()
    meta_no = clf_no_aug.train_from_dataset(
        str(data_dir),
        bearing_params=preset_to_bearing_params('SKF-6205'),
        window=6000, hop=3000, default_rpm=1800, default_sampling_rate=12000,
        amplitude_augment=1,
    )
    clf_aug = BearingFaultClassifier()
    meta_aug = clf_aug.train_from_dataset(
        str(data_dir),
        bearing_params=preset_to_bearing_params('SKF-6205'),
        window=6000, hop=3000, default_rpm=1800, default_sampling_rate=12000,
        amplitude_augment=4,
    )
    assert meta_aug['n_windows'] == 4 * meta_no['n_windows']
    assert meta_aug['amplitude_augment'] == 4
    assert clf_aug.source.endswith('aug=4')


def test_amplitude_augmentation_rejects_invalid(tmp_path):
    data_dir = _make_fake_mfpt_dir(tmp_path)
    clf = BearingFaultClassifier()
    with pytest.raises(ValueError):
        clf.train_from_dataset(
            str(data_dir),
            bearing_params=preset_to_bearing_params('SKF-6205'),
            window=6000, hop=3000, default_rpm=1800, default_sampling_rate=12000,
            amplitude_augment=0,
        )


def test_save_and_load_roundtrip(tmp_path):
    data_dir = _make_fake_mfpt_dir(tmp_path)
    clf = BearingFaultClassifier()
    clf.train_from_dataset(
        str(data_dir),
        bearing_params=preset_to_bearing_params('SKF-6205'),
        window=6000, hop=3000, default_rpm=1800, default_sampling_rate=12000,
    )
    path = tmp_path / 'model.pkl'
    clf.save(str(path))
    assert os.path.isfile(path)

    loaded = BearingFaultClassifier.load(str(path))
    assert loaded.is_trained
    assert loaded.trained_classes == clf.trained_classes
    assert loaded.source == clf.source

    # Identical predictions on a fixed input
    rng = np.random.default_rng(2)
    sig = rng.standard_normal(8192)
    tf = extract_time_domain_features(sig)
    freq, mag = perform_fft(sig, 12000)
    ff = calculate_bearing_frequencies(1800, preset_to_bearing_params('SKF-6205'))
    ffeat = extract_frequency_domain_features(freq, mag, ff)
    assert clf.predict(tf, ffeat)[0] == loaded.predict(tf, ffeat)[0]

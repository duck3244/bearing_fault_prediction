import numpy as np
import pytest

from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.data_acquisition import create_sample_data
from app.core.fault_classifier import BearingFaultClassifier
from app.core.feature_extraction import (
    extract_frequency_domain_features,
    extract_time_domain_features,
)
from app.core.spectral_analysis import perform_fft


@pytest.fixture(scope='module')
def trained_classifier():
    clf = BearingFaultClassifier()
    clf.train(
        bearing_params={
            'ball_diameter': 7.94,
            'pitch_diameter': 39.04,
            'num_balls': 9,
            'contact_angle': 0,
        },
        num_samples=4000,  # smaller for test speed
        seed=42,
    )
    return clf


def _features_for(fault_type, seed):
    bp = {'ball_diameter': 7.94, 'pitch_diameter': 39.04, 'num_balls': 9, 'contact_angle': 0}
    d = create_sample_data(8000, 12000, 1800, fault_type, 0.3, seed=seed)
    sig = d[fault_type]
    tf = extract_time_domain_features(sig)
    freq, mag = perform_fft(sig, 12000)
    ff = calculate_bearing_frequencies(1800, bp)
    return tf, extract_frequency_domain_features(freq, mag, ff)


def test_feature_vector_dimension(trained_classifier):
    # 14 time-domain + 18 frequency-domain (6 generic + 4*3 harmonic)
    assert trained_classifier.model.n_features_in_ == 32


def test_classifier_is_trained(trained_classifier):
    assert trained_classifier.is_trained


@pytest.mark.parametrize('fault_type', ['inner_fault', 'outer_fault', 'cage_fault'])
def test_classifier_predicts_injected_fault(trained_classifier, fault_type):
    tf, ff = _features_for(fault_type, seed=123)
    label, conf, probs = trained_classifier.predict(tf, ff)
    assert label == fault_type
    assert 0.0 <= conf <= 1.0
    assert pytest.approx(sum(probs.values()), abs=1e-6) == 1.0


def test_untrained_classifier_returns_none():
    clf = BearingFaultClassifier()
    label, conf, probs = clf.predict({}, {})
    assert label is None
    assert conf == 0.0
    assert probs == {}

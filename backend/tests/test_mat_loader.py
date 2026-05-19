import io
import os

import numpy as np
import pytest
from scipy.io import savemat

from app.core.mat_loader import label_from_filename, load_mat_signal


def _write_mfpt_mat(path, signal, sr=48828.0, rate=25.0, load=0.0):
    """Write a minimal MFPT-style .mat with a 'bearing' struct."""
    savemat(path, {'bearing': {'gs': signal, 'sr': sr, 'rate': rate, 'load': load}})


def test_loads_mfpt_bearing_struct(tmp_path):
    sig = np.sin(np.linspace(0, 100 * np.pi, 10_000))
    p = tmp_path / 'fake.mat'
    _write_mfpt_mat(str(p), sig, sr=48828.0, rate=25.0)
    result = load_mat_signal(str(p))
    assert result['signal'].shape == (10_000,)
    assert result['sampling_rate'] == pytest.approx(48828.0)
    assert result['rpm'] == pytest.approx(1500.0)  # 25 Hz * 60


def test_loads_from_stream(tmp_path):
    sig = np.linspace(-1, 1, 1024)
    p = tmp_path / 'fake.mat'
    _write_mfpt_mat(str(p), sig)
    with open(p, 'rb') as f:
        result = load_mat_signal(f)
    assert result['signal'].shape == (1024,)


def test_rate_above_200_treated_as_rpm(tmp_path):
    sig = np.zeros(512)
    p = tmp_path / 'rpm_format.mat'
    _write_mfpt_mat(str(p), sig, sr=12000.0, rate=1800.0)  # value already in RPM
    result = load_mat_signal(str(p))
    assert result['rpm'] == pytest.approx(1800.0)


def test_missing_signal_raises(tmp_path):
    p = tmp_path / 'no_signal.mat'
    savemat(str(p), {'something_else': np.array([1.0, 2.0])})
    with pytest.raises(ValueError):
        load_mat_signal(str(p))


def test_real_mfpt_file_if_available():
    """Smoke test against a real MFPT file if the sibling project is present."""
    real_path = '/home/duck/PycharmProjects/bearing-fault-diagnosis/backend/MFPT_Dataset/train/baseline_1.mat'
    if not os.path.isfile(real_path):
        pytest.skip('Real MFPT dataset not available')
    r = load_mat_signal(real_path)
    assert r['signal'].ndim == 1
    assert r['signal'].size > 10_000
    assert r['sampling_rate'] > 0
    assert r['rpm'] > 0


@pytest.mark.parametrize('fname,expected', [
    ('baseline_1.mat', 'normal'),
    ('InnerRaceFault_vload_3.mat', 'inner_fault'),
    ('OuterRaceFault_3.mat', 'outer_fault'),
    ('ball_fault_test.mat', 'ball_fault'),
    ('cage_failure.mat', 'cage_fault'),
    ('random.mat', None),
])
def test_label_from_filename(fname, expected):
    assert label_from_filename(fname) == expected

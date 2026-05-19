import numpy as np
import pytest

from app.core.data_acquisition import create_sample_data


def test_seed_makes_output_deterministic():
    a = create_sample_data(2000, 12000, 1800, 'inner_fault', 0.5, seed=42)
    b = create_sample_data(2000, 12000, 1800, 'inner_fault', 0.5, seed=42)
    assert np.array_equal(a['inner_fault'], b['inner_fault'])


def test_different_seeds_yield_different_signals():
    a = create_sample_data(2000, 12000, 1800, 'inner_fault', 0.5, seed=1)
    b = create_sample_data(2000, 12000, 1800, 'inner_fault', 0.5, seed=2)
    assert not np.array_equal(a['inner_fault'], b['inner_fault'])


@pytest.mark.parametrize('bad_rpm', [0, -100])
def test_invalid_rpm_raises(bad_rpm):
    with pytest.raises(ValueError):
        create_sample_data(rpm=bad_rpm)


@pytest.mark.parametrize('bad_sr', [0, -1])
def test_invalid_sampling_rate_raises(bad_sr):
    with pytest.raises(ValueError):
        create_sample_data(sampling_rate=bad_sr)


def test_all_fault_types_present_for_fault_type_all():
    d = create_sample_data(2000, 12000, 1800, 'all', 0.3, seed=0)
    for key in ('outer_fault', 'inner_fault', 'ball_fault', 'cage_fault'):
        assert key in d
        assert d[key].shape == (2000,)


def test_specific_fault_type_includes_normal_and_target_only():
    d = create_sample_data(2000, 12000, 1800, 'ball_fault', 0.3, seed=0)
    assert 'ball_fault' in d
    assert 'normal' in d
    assert 'outer_fault' not in d
    assert 'inner_fault' not in d


def test_metadata_fields():
    d = create_sample_data(1024, 8000, 1500, 'normal', 0.1, seed=0)
    assert d['sampling_rate'] == 8000
    assert d['rpm'] == 1500
    assert d['time'].shape == (1024,)

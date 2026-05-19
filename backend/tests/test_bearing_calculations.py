import math

import pytest

from app.core.bearing_calculations import calculate_bearing_frequencies


@pytest.fixture
def std_params():
    # SKF 6205 reference geometry used as the project default
    return {
        'ball_diameter': 7.94,
        'pitch_diameter': 39.04,
        'num_balls': 9,
        'contact_angle': 0,
    }


def test_fault_frequency_ordering(std_params):
    """For contact_angle=0, BPFI > BPFO > FR > FTF should hold."""
    f = calculate_bearing_frequencies(1800, std_params)
    assert f['BPFI'] > f['BPFO']
    assert f['BPFO'] > f['FR']
    assert f['FR'] > f['FTF']


def test_fr_equals_rpm_over_60(std_params):
    for rpm in (600, 1200, 1800, 3000):
        f = calculate_bearing_frequencies(rpm, std_params)
        assert math.isclose(f['FR'], rpm / 60)


def test_bpfo_plus_bpfi_equals_num_balls_times_fr(std_params):
    """Algebraic identity: BPFO + BPFI = N * FR (any contact angle)."""
    f = calculate_bearing_frequencies(1800, std_params)
    assert math.isclose(f['BPFO'] + f['BPFI'], std_params['num_balls'] * f['FR'])


def test_scales_linearly_with_rpm(std_params):
    f1 = calculate_bearing_frequencies(1800, std_params)
    f2 = calculate_bearing_frequencies(3600, std_params)
    for key in ('BPFO', 'BPFI', 'BSF', 'FTF', 'FR'):
        assert math.isclose(f2[key], 2 * f1[key])

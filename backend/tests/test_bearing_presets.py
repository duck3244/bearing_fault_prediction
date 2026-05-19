import math

import pytest

from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.bearing_presets import BEARING_PRESETS, preset_to_bearing_params


def test_presets_contain_required_keys():
    for name, preset in BEARING_PRESETS.items():
        for key in ('ball_diameter', 'pitch_diameter', 'num_balls', 'contact_angle',
                    'default_rpm', 'default_sampling_rate'):
            assert key in preset, f'{name} missing {key}'


def test_skf6205_matches_cwru_drive_end_default():
    bp = preset_to_bearing_params('SKF-6205')
    f = calculate_bearing_frequencies(1800, bp)
    # CWRU published BPFO ≈ 107.36 Hz at 1797 rpm; tolerate the 0.6 Hz rpm offset
    assert f['BPFO'] == pytest.approx(107.36, abs=1.0)
    assert f['BPFI'] == pytest.approx(162.18, abs=1.5)


def test_mfpt_nice_matches_published_frequencies():
    bp = preset_to_bearing_params('MFPT-NICE')
    f = calculate_bearing_frequencies(1500, bp)
    # MFPT-published BPFO=81.125 Hz, BPFI=118.88 Hz (at 25 Hz shaft = 1500 rpm)
    assert f['BPFO'] == pytest.approx(81.125, abs=0.1)
    assert f['BPFI'] == pytest.approx(118.88, abs=0.1)

"""Known bearing geometries used by public bearing-fault datasets.

Lengths are millimetres, angles are degrees. The default RPM is the
nominal shaft speed used by the dataset; users can still override it per
request.
"""
from __future__ import annotations

BEARING_PRESETS: dict[str, dict] = {
    # SKF 6205 drive-end bearing (CWRU dataset, current project default)
    'SKF-6205': {
        'description': 'SKF 6205 deep-groove ball bearing — CWRU drive-end',
        'ball_diameter': 7.94,
        'pitch_diameter': 39.04,
        'num_balls': 9,
        'contact_angle': 0,
        'default_rpm': 1800,
        'default_sampling_rate': 12000,
    },
    # NICE bearing used by the MFPT dataset
    'MFPT-NICE': {
        'description': 'NICE bearing used by the MFPT benchmark',
        'ball_diameter': 5.969,
        'pitch_diameter': 31.623,
        'num_balls': 8,
        'contact_angle': 0,
        'default_rpm': 1500,
        'default_sampling_rate': 48828,
    },
}

DEFAULT_PRESET = 'SKF-6205'


def preset_to_bearing_params(name: str) -> dict:
    """Return the {ball_diameter, pitch_diameter, num_balls, contact_angle} subset."""
    p = BEARING_PRESETS[name]
    return {
        'ball_diameter': p['ball_diameter'],
        'pitch_diameter': p['pitch_diameter'],
        'num_balls': p['num_balls'],
        'contact_angle': p['contact_angle'],
    }

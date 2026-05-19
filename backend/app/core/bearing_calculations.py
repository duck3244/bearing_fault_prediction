import numpy as np


def calculate_bearing_frequencies(rpm, bearing_params):
    """
    Calculate bearing fault frequencies
    
    Parameters:
    -----------
    rpm : float
        Rotation speed (revolutions per minute)
    bearing_params : dict
        Bearing parameters (ball diameter, pitch diameter, number of balls, contact angle)
    
    Returns:
    --------
    dict : Fault frequencies (BPFO, BPFI, BSF, FTF)
    """
    ball_diameter = bearing_params['ball_diameter']  # Ball diameter
    pitch_diameter = bearing_params['pitch_diameter']  # Pitch diameter
    num_balls = bearing_params['num_balls']  # Number of balls
    contact_angle = bearing_params['contact_angle'] * np.pi / 180  # Contact angle (radians)

    # Rotation frequency (Hz)
    fr = rpm / 60

    # Diameter ratio
    diameter_ratio = ball_diameter / pitch_diameter

    # Ball Pass Frequency Outer race (BPFO)
    bpfo = (num_balls / 2) * fr * (1 - diameter_ratio * np.cos(contact_angle))

    # Ball Pass Frequency Inner race (BPFI)
    bpfi = (num_balls / 2) * fr * (1 + diameter_ratio * np.cos(contact_angle))

    # Ball Spin Frequency (BSF)
    bsf = (pitch_diameter / (2 * ball_diameter)) * fr * (1 - (diameter_ratio * np.cos(contact_angle)) ** 2)

    # Fundamental Train Frequency (FTF) - Cage fault
    ftf = fr * (1 - diameter_ratio * np.cos(contact_angle)) / 2

    return {
        'BPFO': bpfo,
        'BPFI': bpfi,
        'BSF': bsf,
        'FTF': ftf,
        'FR': fr
    }
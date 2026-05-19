"""MFPT-style .mat dataset loader.

Reads MATLAB v5 files containing a top-level `bearing` struct with fields
`gs` (signal), `sr` (sampling rate), `rate` (shaft frequency, Hz), and
optionally `load`. Falls back to flat-key conventions used by other
public datasets when the bearing struct is absent.
"""
from __future__ import annotations

import io
import os
from typing import Any, BinaryIO, Union

import numpy as np
from scipy.io import loadmat


_SIGNAL_KEYS = ('gs', 'signal', 'data', 'vibration', 'X')
_SR_KEYS = ('sr', 'fs', 'sample_rate', 'sampling_rate')
_RATE_KEYS = ('rate', 'rpm', 'shaft_rate')


def _to_scalar(value) -> float:
    arr = np.asarray(value).squeeze()
    if arr.size != 1:
        raise ValueError(f'expected scalar, got shape {arr.shape}')
    return float(arr)


def _to_1d(value) -> np.ndarray:
    arr = np.asarray(value).squeeze().astype(float)
    if arr.ndim != 1:
        raise ValueError(f'expected 1-D signal, got shape {arr.shape}')
    return arr


def _from_bearing_struct(struct):
    """Decode an MFPT-style bearing struct (1x1 record array)."""
    inner = struct[0, 0] if struct.shape == (1, 1) else struct
    names = inner.dtype.names or ()

    signal = None
    sr = None
    rate = None

    for k in _SIGNAL_KEYS:
        if k in names:
            signal = _to_1d(inner[k])
            break
    for k in _SR_KEYS:
        if k in names:
            sr = _to_scalar(inner[k])
            break
    for k in _RATE_KEYS:
        if k in names:
            rate = _to_scalar(inner[k])
            break

    return signal, sr, rate


def load_mat_signal(source: Union[str, bytes, BinaryIO]) -> dict:
    """Load a vibration signal from a .mat file.

    Parameters
    ----------
    source : path, bytes, or file-like
        Source of the .mat file.

    Returns
    -------
    dict with keys:
        signal : 1-D numpy array of vibration samples
        sampling_rate : float (Hz), or None if not found
        rpm : float or None — derived from shaft rate field if present
              (interpreted as Hz × 60; many bearing datasets store shaft rate in Hz)
        source : str or None
    """
    if hasattr(source, 'read'):
        raw = source.read()
        buf = io.BytesIO(raw)
        mat = loadmat(buf)
        name = getattr(source, 'filename', None) or getattr(source, 'name', None)
    elif isinstance(source, (bytes, bytearray)):
        mat = loadmat(io.BytesIO(source))
        name = None
    else:
        mat = loadmat(source)
        name = os.path.basename(str(source))

    user_keys = [k for k in mat.keys() if not k.startswith('__')]

    signal = sr = rate = None

    # 1. MFPT convention: top-level 'bearing' struct
    if 'bearing' in user_keys:
        try:
            signal, sr, rate = _from_bearing_struct(mat['bearing'])
        except Exception:
            pass

    # 2. Any other top-level struct
    if signal is None:
        for k in user_keys:
            v = mat[k]
            if isinstance(v, np.ndarray) and v.dtype == object and v.size == 1:
                try:
                    signal, sr, rate = _from_bearing_struct(v)
                    if signal is not None:
                        break
                except Exception:
                    continue

    # 3. Flat-key fallbacks
    if signal is None:
        for k in _SIGNAL_KEYS:
            if k in user_keys:
                signal = _to_1d(mat[k])
                break
    if sr is None:
        for k in _SR_KEYS:
            if k in user_keys:
                sr = _to_scalar(mat[k])
                break
    if rate is None:
        for k in _RATE_KEYS:
            if k in user_keys:
                rate = _to_scalar(mat[k])
                break

    if signal is None:
        raise ValueError(f'No vibration signal found in .mat (keys: {user_keys})')

    # Heuristic: 'rate' under MFPT is shaft frequency in Hz (typical value 25)
    # If it's >= 200, assume it's already RPM
    rpm = None
    if rate is not None:
        rpm = rate if rate >= 200 else rate * 60.0

    return {
        'signal': signal,
        'sampling_rate': sr,
        'rpm': rpm,
        'source': name,
    }


def label_from_filename(filename: str) -> str | None:
    """Guess fault label from MFPT filename conventions. Returns None if unknown."""
    s = os.path.basename(filename).lower()
    if 'baseline' in s or 'normal' in s:
        return 'normal'
    if 'innerrace' in s or 'inner_race' in s or 'inner_fault' in s:
        return 'inner_fault'
    if 'outerrace' in s or 'outer_race' in s or 'outer_fault' in s:
        return 'outer_fault'
    if 'ball' in s:
        return 'ball_fault'
    if 'cage' in s:
        return 'cage_fault'
    return None

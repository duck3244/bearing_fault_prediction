"""Shared helpers for API routers."""
from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.feature_extraction import (
    extract_frequency_domain_features,
    extract_time_domain_features,
)
from app.core.mat_loader import load_mat_signal
from app.core.spectral_analysis import detect_fault_frequencies, perform_fft
from app.core.fault_classifier import BearingFaultClassifier

PREDICT_WINDOW = 12000
PREDICT_HOP = 6000


def read_csv_signal(raw: bytes, signal_column: str | None) -> np.ndarray:
    if not raw:
        raise HTTPException(400, 'Uploaded file is empty')
    df = pd.read_csv(BytesIO(raw), header='infer')
    if df.shape[1] == 0:
        raise HTTPException(400, 'CSV has no columns')

    first_row_numeric = all(
        pd.to_numeric(pd.Series([c]), errors='coerce').notna().all()
        for c in df.columns
    )
    if first_row_numeric:
        df = pd.read_csv(BytesIO(raw), header=None)

    if signal_column and signal_column in df.columns:
        series = df[signal_column]
    elif df.shape[1] == 1:
        series = df.iloc[:, 0]
    else:
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        if not numeric_cols:
            raise HTTPException(400, 'No numeric column found in CSV')
        series = df[numeric_cols[-1]]

    signal_data = pd.to_numeric(series, errors='coerce').dropna().to_numpy()
    if signal_data.size == 0:
        raise HTTPException(400, 'Signal column has no numeric data')
    return signal_data


async def read_uploaded_signal(file: UploadFile, signal_column: str | None,
                               default_sampling_rate: int, default_rpm: int):
    """Return (signal_array, sampling_rate, rpm) tuple, honouring .mat metadata."""
    if not file.filename:
        raise HTTPException(400, 'No selected file')
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in {'csv', 'mat'}:
        raise HTTPException(400, 'Invalid file type. Only .csv/.mat are supported.')

    raw = await file.read()
    sampling_rate = default_sampling_rate
    rpm = default_rpm

    if ext == 'mat':
        try:
            mat = load_mat_signal(raw)
        except Exception as exc:
            raise HTTPException(400, f'Failed to read .mat file: {exc}')
        signal = mat['signal']
        if mat['sampling_rate'] is not None:
            sampling_rate = int(mat['sampling_rate'])
        if mat['rpm'] is not None:
            rpm = int(mat['rpm'])
    else:
        signal = read_csv_signal(raw, signal_column)

    return signal, sampling_rate, rpm


def process_signal(signal: np.ndarray, sampling_rate: int, fault_freqs: dict,
                   classifier: BearingFaultClassifier) -> dict:
    """Compute all features + run windowed prediction for an analysis response."""
    time_features = extract_time_domain_features(signal)
    freq, magnitude = perform_fft(signal, sampling_rate)
    freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)
    fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

    result = {
        'time_features': time_features,
        'freq_features': freq_features,
        'fault_detection': fault_detection,
        'signal_sample': signal[:1000].tolist(),
        'freq_sample': freq[:500].tolist(),
        'magnitude_sample': magnitude[:500].tolist(),
    }

    if classifier.is_trained:
        label, confidence, probs = predict_long_signal(
            signal, sampling_rate, fault_freqs, time_features, freq_features, classifier
        )
        result['prediction'] = {
            'label': label,
            'confidence': confidence,
            'probabilities': probs,
            'trained_classes': classifier.trained_classes,
        }
    return result


def predict_long_signal(signal, sampling_rate, fault_freqs,
                        time_features_full, freq_features_full,
                        classifier: BearingFaultClassifier):
    """Predict by averaging window-level probabilities for signals longer than 2x window."""
    if signal.size < 2 * PREDICT_WINDOW:
        return classifier.predict(time_features_full, freq_features_full)

    probs_sum = None
    n = 0
    for start in range(0, len(signal) - PREDICT_WINDOW + 1, PREDICT_HOP):
        seg = signal[start:start + PREDICT_WINDOW]
        tf = extract_time_domain_features(seg)
        freq, mag = perform_fft(seg, sampling_rate)
        ffeat = extract_frequency_domain_features(freq, mag, fault_freqs)
        _, _, probs = classifier.predict(tf, ffeat)
        arr = np.array([probs[c] for c in classifier.trained_classes])
        probs_sum = arr if probs_sum is None else probs_sum + arr
        n += 1
    mean_probs = probs_sum / n
    idx = int(np.argmax(mean_probs))
    label = classifier.trained_classes[idx]
    confidence = float(mean_probs[idx])
    prob_dict = {c: float(p) for c, p in zip(classifier.trained_classes, mean_probs)}
    return label, confidence, prob_dict

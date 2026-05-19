from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api._helpers import process_signal
from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.data_acquisition import create_sample_data
from app.deps import get_state
from app.schemas.analyze import (
    GenerateSampleRequest,
    SampleDataResponse,
)
from app.state import AppState

router = APIRouter()

ALL_FAULT_SIGNALS = ['normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault']


def _features_for_signals(data: dict, fault_freqs: dict, signal_types: list[str],
                          classifier) -> dict:
    out: dict = {}
    for st in signal_types:
        if st not in data:
            continue
        out[st] = process_signal(data[st], int(data['sampling_rate']), fault_freqs, classifier)
    return out


@router.get('/api/sample-data', response_model=SampleDataResponse)
def get_sample_data(rpm: int = Query(1800), s: AppState = Depends(get_state)):
    data = create_sample_data(rpm=rpm)
    fault_freqs = calculate_bearing_frequencies(rpm, s.default_bearing_params)
    features = _features_for_signals(data, fault_freqs, ALL_FAULT_SIGNALS, s.classifier)
    return {
        'fault_frequencies': fault_freqs,
        'sampling_rate': int(data['sampling_rate']),
        'rpm': int(data['rpm']),
        'features': features,
    }


@router.post('/api/generate-sample', response_model=SampleDataResponse)
def generate_sample(body: GenerateSampleRequest, s: AppState = Depends(get_state)):
    try:
        data = create_sample_data(
            num_samples=body.num_samples,
            sampling_rate=body.sampling_rate,
            rpm=body.rpm,
            fault_type=body.fault_type,
            noise_level=body.noise_level,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    fault_freqs = calculate_bearing_frequencies(body.rpm, s.default_bearing_params)
    signal_types = ALL_FAULT_SIGNALS if body.fault_type == 'all' else [body.fault_type]
    features = _features_for_signals(data, fault_freqs, signal_types, s.classifier)
    return {
        'fault_frequencies': fault_freqs,
        'sampling_rate': int(data['sampling_rate']),
        'rpm': int(data['rpm']),
        'features': features,
    }

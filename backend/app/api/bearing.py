from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.bearing_presets import BEARING_PRESETS, preset_to_bearing_params
from app.deps import get_state
from app.schemas.bearing import (
    BearingParams,
    BearingParamsResponse,
    BearingParamsUpdate,
    BearingPreset,
    BearingPresetApplyResponse,
    BearingPresetsResponse,
)
from app.state import AppState

router = APIRouter()


@router.get('/api/bearing-presets', response_model=BearingPresetsResponse)
def list_bearing_presets(s: AppState = Depends(get_state)):
    return {
        'presets': {name: BearingPreset(**p) for name, p in BEARING_PRESETS.items()},
        'current': s.current_preset,
    }


@router.post('/api/bearing-presets/{name}', response_model=BearingPresetApplyResponse)
def apply_bearing_preset(name: str, s: AppState = Depends(get_state)):
    if name not in BEARING_PRESETS:
        raise HTTPException(
            status_code=404,
            detail={'error': f'Unknown preset: {name}', 'available': list(BEARING_PRESETS)},
        )
    with s.lock:
        s.default_bearing_params.update(preset_to_bearing_params(name))
        s.current_preset = name
    return {
        'preset': name,
        'bearing_params': s.default_bearing_params,
        'default_rpm': BEARING_PRESETS[name]['default_rpm'],
        'default_sampling_rate': BEARING_PRESETS[name]['default_sampling_rate'],
    }


@router.post('/api/bearing-params', response_model=BearingParamsResponse)
def update_bearing_params(
    body: BearingParamsUpdate = Body(...),
    s: AppState = Depends(get_state),
):
    with s.lock:
        new = dict(s.default_bearing_params)
        for k in ('ball_diameter', 'pitch_diameter', 'num_balls', 'contact_angle'):
            v = getattr(body, k)
            if v is not None:
                new[k] = v
        if new['pitch_diameter'] <= 0 or new['ball_diameter'] <= 0 or new['num_balls'] <= 0:
            raise HTTPException(400, 'ball_diameter, pitch_diameter, num_balls must be positive')

        fault_freqs = calculate_bearing_frequencies(body.rpm, new)
        s.default_bearing_params.update(new)
    return {
        'fault_frequencies': fault_freqs,
        'bearing_params': BearingParams(**s.default_bearing_params),
    }

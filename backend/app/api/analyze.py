from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api._helpers import process_signal, read_uploaded_signal
from app.core.bearing_calculations import calculate_bearing_frequencies
from app.deps import get_state
from app.schemas.analyze import AnalyzeResponse
from app.state import AppState

router = APIRouter()


@router.post('/api/analyze', response_model=AnalyzeResponse)
async def analyze_data(
    file: UploadFile = File(...),
    rpm: int = Form(1800),
    sampling_rate: int = Form(12000),
    signal_column: str | None = Form(None),
    s: AppState = Depends(get_state),
):
    signal, sr, rpm_eff = await read_uploaded_signal(
        file, signal_column, default_sampling_rate=sampling_rate, default_rpm=rpm
    )
    fault_freqs = calculate_bearing_frequencies(rpm_eff, s.default_bearing_params)
    result = process_signal(signal, sr, fault_freqs, s.classifier)
    return {
        'filename': file.filename,
        'sampling_rate': sr,
        'rpm': rpm_eff,
        'fault_frequencies': fault_freqs,
        **result,
    }

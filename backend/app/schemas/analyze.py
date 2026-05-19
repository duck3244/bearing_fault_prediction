from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.bearing import FaultFrequencies


class TimeFeatures(BaseModel):
    mean: float
    std_dev: float
    rms: float
    peak: float
    kurtosis: float
    skewness: float
    crest_factor: float
    impulse_factor: float
    shape_factor: float
    clearance_factor: float
    energy: float
    entropy: float
    range: float
    zero_crossing_rate: float


class FaultDetectionHit(BaseModel):
    harmonic: int
    theoretical_freq: float
    detected_freq: float
    amplitude: float
    deviation: float


class Prediction(BaseModel):
    label: str | None
    confidence: float = Field(ge=0, le=1)
    probabilities: dict[str, float]
    trained_classes: list[str] = []


class AnalyzeResponse(BaseModel):
    filename: str
    sampling_rate: int
    rpm: int
    fault_frequencies: FaultFrequencies
    time_features: TimeFeatures
    freq_features: dict[str, float]
    fault_detection: dict[str, list[FaultDetectionHit]]
    signal_sample: list[float]
    freq_sample: list[float]
    magnitude_sample: list[float]
    prediction: Prediction | None = None


class SignalFeatures(BaseModel):
    signal_sample: list[float]
    time_features: TimeFeatures
    freq_features: dict[str, float]
    fault_detection: dict[str, list[FaultDetectionHit]]
    freq_sample: list[float]
    magnitude_sample: list[float]
    prediction: Prediction | None = None


class SampleDataResponse(BaseModel):
    fault_frequencies: FaultFrequencies
    sampling_rate: int
    rpm: int
    features: dict[str, SignalFeatures]


class GenerateSampleRequest(BaseModel):
    rpm: float = 1800
    sampling_rate: int = 12000
    num_samples: int = 10000
    fault_type: str = 'normal'
    noise_level: float = 0.5


class PredictRequest(BaseModel):
    time_features: dict[str, float]
    freq_features: dict[str, float]


class PredictResponse(BaseModel):
    prediction: Prediction

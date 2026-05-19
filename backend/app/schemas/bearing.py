from __future__ import annotations

from pydantic import BaseModel, Field


class BearingParams(BaseModel):
    ball_diameter: float = Field(gt=0)
    pitch_diameter: float = Field(gt=0)
    num_balls: int = Field(gt=0)
    contact_angle: float = 0.0


class FaultFrequencies(BaseModel):
    BPFO: float
    BPFI: float
    BSF: float
    FTF: float
    FR: float


class BearingParamsUpdate(BaseModel):
    ball_diameter: float | None = None
    pitch_diameter: float | None = None
    num_balls: int | None = None
    contact_angle: float | None = None
    rpm: float = 1800


class BearingParamsResponse(BaseModel):
    fault_frequencies: FaultFrequencies
    bearing_params: BearingParams


class BearingPreset(BaseModel):
    description: str
    ball_diameter: float
    pitch_diameter: float
    num_balls: int
    contact_angle: float
    default_rpm: int
    default_sampling_rate: int


class BearingPresetsResponse(BaseModel):
    presets: dict[str, BearingPreset]
    current: str


class BearingPresetApplyResponse(BaseModel):
    preset: str
    bearing_params: BearingParams
    default_rpm: int
    default_sampling_rate: int

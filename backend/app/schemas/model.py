from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    is_trained: bool
    source: str | None
    trained_classes: list[str]
    all_known_classes: list[str]
    model_path: str
    persisted: bool


class RetrainRequest(BaseModel):
    mode: Literal['synthetic', 'dataset'] = 'synthetic'
    save: bool = False

    # Synthetic options
    rpm: int | None = None
    sampling_rate: int | None = None

    # Dataset options
    dataset_dir: str | None = None
    window: int = 12000
    hop: int = 6000
    amplitude_augment: int = Field(default=4, ge=1)
    augment_scale_range: tuple[float, float] = (0.3, 3.0)


class RetrainResponse(BaseModel):
    source: str | None
    trained_classes: list[str]
    n_files: int | None = None
    n_windows: int | None = None
    amplitude_augment: int | None = None
    class_counts: dict[str, int] | None = None
    skipped_files: list[str] | None = None
    saved_to: str | None = None

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model_path: str = os.environ.get('MODEL_PATH', 'models/classifier.pkl')
    max_upload_bytes: int = int(os.environ.get('MAX_UPLOAD_BYTES', 64 * 1024 * 1024))
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',') if o.strip()
    )


settings = Settings()

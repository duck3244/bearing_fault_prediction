"""Process-local state for the single-user MVP.

Wraps the mutable references (classifier, default bearing params, current
preset) the API endpoints share. A simple module-level singleton is fine
for a single-user app; if we ever scale out, swap this for a per-request
dependency-injected store.
"""
from __future__ import annotations

import logging
import os
from threading import RLock

from app.core.bearing_presets import (
    BEARING_PRESETS,
    DEFAULT_PRESET,
    preset_to_bearing_params,
)
from app.core.fault_classifier import BearingFaultClassifier
from app.settings import settings

log = logging.getLogger(__name__)


class AppState:
    def __init__(self) -> None:
        self.lock = RLock()
        self.classifier: BearingFaultClassifier = BearingFaultClassifier()
        self.default_bearing_params: dict = preset_to_bearing_params(DEFAULT_PRESET)
        self.current_preset: str = DEFAULT_PRESET

    def bootstrap_classifier(self) -> None:
        """Load persisted model if available; else train on synthetic data."""
        with self.lock:
            path = settings.model_path
            if os.path.isfile(path):
                try:
                    self.classifier = BearingFaultClassifier.load(path)
                    log.info('Loaded classifier from %s (source=%s)', path, self.classifier.source)
                    return
                except Exception as exc:
                    log.error('Failed to load model from %s: %s', path, exc)
            try:
                self.classifier.train(self.default_bearing_params)
                log.info('Fault classifier trained on synthetic data')
            except Exception as exc:
                log.error('Failed to train classifier: %s', exc)


state = AppState()

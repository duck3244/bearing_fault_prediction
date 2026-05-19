"""FastAPI dependencies — thin wrappers over app.state for testability."""
from __future__ import annotations

from app.core.fault_classifier import BearingFaultClassifier
from app.state import AppState, state


def get_state() -> AppState:
    return state


def get_classifier() -> BearingFaultClassifier:
    return state.classifier

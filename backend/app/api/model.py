from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from app.core.bearing_presets import BEARING_PRESETS
from app.core.fault_classifier import BearingFaultClassifier
from app.deps import get_state
from app.schemas.analyze import PredictRequest, PredictResponse
from app.schemas.model import ModelInfo, RetrainRequest, RetrainResponse
from app.settings import settings
from app.state import AppState

router = APIRouter()


@router.get('/api/model/info', response_model=ModelInfo)
def model_info(s: AppState = Depends(get_state)):
    clf = s.classifier
    return {
        'is_trained': clf.is_trained,
        'source': clf.source,
        'trained_classes': clf.trained_classes,
        'all_known_classes': BearingFaultClassifier.FAULT_TYPES,
        'model_path': settings.model_path,
        'persisted': os.path.isfile(settings.model_path),
    }


@router.post('/api/model/retrain', response_model=RetrainResponse)
def retrain_model(body: RetrainRequest, s: AppState = Depends(get_state)):
    preset = BEARING_PRESETS[s.current_preset]
    new_clf = BearingFaultClassifier()
    meta: dict = {}

    if body.mode == 'synthetic':
        new_clf.train(
            s.default_bearing_params,
            rpm=body.rpm or preset['default_rpm'],
            sampling_rate=body.sampling_rate or preset['default_sampling_rate'],
        )
    else:  # dataset
        if not body.dataset_dir:
            raise HTTPException(400, 'mode=dataset requires "dataset_dir"')
        try:
            meta = new_clf.train_from_dataset(
                body.dataset_dir,
                bearing_params=s.default_bearing_params,
                window=body.window,
                hop=body.hop,
                default_rpm=preset['default_rpm'],
                default_sampling_rate=preset['default_sampling_rate'],
                amplitude_augment=body.amplitude_augment,
                augment_scale_range=tuple(body.augment_scale_range),
            )
        except FileNotFoundError as exc:
            raise HTTPException(404, f'Dataset not found: {exc}')
        except ValueError as exc:
            raise HTTPException(400, str(exc))

    with s.lock:
        s.classifier = new_clf

    if body.save:
        new_clf.save(settings.model_path)
        meta['saved_to'] = settings.model_path

    return {
        'source': new_clf.source,
        'trained_classes': new_clf.trained_classes,
        **meta,
    }


@router.post('/api/predict', response_model=PredictResponse)
def predict_fault(body: PredictRequest, s: AppState = Depends(get_state)):
    if not s.classifier.is_trained:
        raise HTTPException(503, 'Classifier is not trained yet')
    label, confidence, probs = s.classifier.predict(body.time_features, body.freq_features)
    return {
        'prediction': {
            'label': label,
            'confidence': confidence,
            'probabilities': probs,
            'trained_classes': s.classifier.trained_classes,
        }
    }

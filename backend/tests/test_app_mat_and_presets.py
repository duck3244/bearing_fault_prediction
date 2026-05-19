import io

import numpy as np
import pytest
from scipy.io import savemat


def _mfpt_mat_bytes(signal, sr=48828.0, rate=25.0):
    buf = io.BytesIO()
    savemat(buf, {'bearing': {'gs': signal, 'sr': sr, 'rate': rate, 'load': 0.0}})
    buf.seek(0)
    return buf


def _upload(buf, name='sample.mat'):
    return (name, buf, 'application/octet-stream')


def test_analyze_accepts_mat(client):
    rng = np.random.default_rng(0)
    sig = rng.standard_normal(20_000)
    r = client.post('/api/analyze', files={'file': _upload(_mfpt_mat_bytes(sig))})
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body['sampling_rate'] == 48828
    assert body['rpm'] == 1500


def test_list_presets(client):
    r = client.get('/api/bearing-presets')
    assert r.status_code == 200
    body = r.json()
    assert 'SKF-6205' in body['presets']
    assert 'MFPT-NICE' in body['presets']
    assert body['current'] in body['presets']


def test_apply_preset_changes_default_params(client):
    from app.state import state
    old = dict(state.default_bearing_params)
    try:
        r = client.post('/api/bearing-presets/MFPT-NICE')
        assert r.status_code == 200
        body = r.json()
        assert body['preset'] == 'MFPT-NICE'
        assert state.default_bearing_params['num_balls'] == 8
        assert state.default_bearing_params['ball_diameter'] == pytest.approx(5.969)
    finally:
        state.default_bearing_params.update(old)
        state.current_preset = 'SKF-6205'


def test_apply_unknown_preset(client):
    r = client.post('/api/bearing-presets/no-such-preset')
    assert r.status_code == 404


def test_model_info_reports_source(client):
    r = client.get('/api/model/info')
    assert r.status_code == 200
    body = r.json()
    assert body['is_trained'] is True
    assert isinstance(body['trained_classes'], list)


def test_retrain_synthetic(client):
    r = client.post('/api/model/retrain', json={'mode': 'synthetic'})
    assert r.status_code == 200
    assert r.json()['source'] == 'synthetic'


def test_retrain_dataset_requires_dir(client):
    r = client.post('/api/model/retrain', json={'mode': 'dataset'})
    assert r.status_code == 400


def test_retrain_dataset_missing_path(client):
    r = client.post('/api/model/retrain',
                    json={'mode': 'dataset', 'dataset_dir': '/tmp/does-not-exist-xyz'})
    assert r.status_code == 404

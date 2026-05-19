import io

import numpy as np
import pytest


def _make_sine_csv(with_header=True, two_col=True, n=2048):
    lines = []
    if with_header:
        lines.append('time,signal' if two_col else 'signal')
    for i in range(n):
        v = float(np.sin(i * 0.1))
        lines.append(f'{i * 1e-4},{v}' if two_col else f'{v}')
    return '\n'.join(lines)


def _upload(text):
    return ('test.csv', io.BytesIO(text.encode()), 'text/csv')


def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}


def test_sample_data_endpoint(client):
    r = client.get('/api/sample-data?rpm=1800')
    assert r.status_code == 200
    data = r.json()
    assert 'fault_frequencies' in data
    assert {'normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault'} <= set(data['features'])


@pytest.mark.parametrize('with_header,two_col', [(True, True), (True, False), (False, True), (False, False)])
def test_analyze_csv_variants(client, with_header, two_col):
    csv = _make_sine_csv(with_header=with_header, two_col=two_col)
    r = client.post(
        '/api/analyze',
        files={'file': _upload(csv)},
        data={'rpm': '1800', 'sampling_rate': '12000'},
    )
    assert r.status_code == 200, r.json()


def test_analyze_rejects_non_csv(client):
    r = client.post(
        '/api/analyze',
        files={'file': ('test.txt', io.BytesIO(b'noop'), 'text/plain')},
        data={'rpm': '1800'},
    )
    assert r.status_code == 400


def test_analyze_missing_file(client):
    r = client.post('/api/analyze', data={'rpm': '1800'})
    # FastAPI's File(...) validation returns 422 for missing required form file
    assert r.status_code in (400, 422)


def test_bearing_params_persisted(client):
    from app.state import state
    old = dict(state.default_bearing_params)
    try:
        r = client.post(
            '/api/bearing-params',
            json={'ball_diameter': 9.0, 'pitch_diameter': 40.0, 'num_balls': 8, 'contact_angle': 15, 'rpm': 1800},
        )
        assert r.status_code == 200
        assert state.default_bearing_params['ball_diameter'] == 9.0
        assert state.default_bearing_params['num_balls'] == 8
    finally:
        state.default_bearing_params.update(old)


def test_bearing_params_rejects_nonpositive(client):
    r = client.post(
        '/api/bearing-params',
        json={'ball_diameter': 0, 'pitch_diameter': 40.0, 'num_balls': 8, 'contact_angle': 0, 'rpm': 1800},
    )
    assert r.status_code == 400


def test_generate_sample_endpoint(client):
    r = client.post(
        '/api/generate-sample',
        json={'rpm': 1800, 'sampling_rate': 12000, 'num_samples': 4000, 'fault_type': 'inner_fault', 'noise_level': 0.3},
    )
    assert r.status_code == 200
    body = r.json()
    assert 'inner_fault' in body['features']


def test_predict_endpoint(client):
    time_features = {k: 0.1 for k in [
        'mean', 'std_dev', 'rms', 'peak', 'kurtosis', 'skewness',
        'crest_factor', 'impulse_factor', 'shape_factor', 'clearance_factor',
        'energy', 'entropy', 'range', 'zero_crossing_rate',
    ]}
    freq_features = {k: 0.1 for k in [
        'mean_magnitude', 'std_magnitude', 'max_magnitude',
        'spectral_centroid', 'bandwidth', 'low_freq_energy_ratio',
        'BPFO_h1_energy', 'BPFO_h2_energy', 'BPFO_h3_energy',
        'BPFI_h1_energy', 'BPFI_h2_energy', 'BPFI_h3_energy',
        'BSF_h1_energy', 'BSF_h2_energy', 'BSF_h3_energy',
        'FTF_h1_energy', 'FTF_h2_energy', 'FTF_h3_energy',
    ]}
    r = client.post('/api/predict', json={'time_features': time_features, 'freq_features': freq_features})
    assert r.status_code == 200
    assert 'prediction' in r.json()

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask.json.provider import DefaultJSONProvider
import os
import numpy as np
import pandas as pd
import json
import logging
from werkzeug.utils import secure_filename

# Import our modules
from data_acquisition import create_sample_data
from bearing_calculations import calculate_bearing_frequencies
from feature_extraction import extract_time_domain_features, extract_frequency_domain_features
from spectral_analysis import perform_fft, detect_fault_frequencies
from fault_classifier import BearingFaultClassifier


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'mat', 'txt', 'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Default bearing parameters
default_bearing_params = {
    'ball_diameter': 7.94,  # mm
    'pitch_diameter': 39.04,  # mm
    'num_balls': 9,
    'contact_angle': 0  # degrees
}

# Initialize ML classifier
classifier = BearingFaultClassifier()


def _train_classifier_if_needed():
    """Train the classifier if not already trained."""
    if not classifier.is_trained:
        try:
            classifier.train(default_bearing_params)
            app.logger.info('Fault classifier trained successfully')
        except Exception as e:
            app.logger.error(f'Failed to train classifier: {e}')


def _process_signals(data, fault_freqs, signal_types, train_classifier=False):
    """Common signal processing logic for sample and generated data."""
    if train_classifier:
        _train_classifier_if_needed()

    features = {}

    for signal_type in signal_types:
        if signal_type not in data:
            continue

        signal_sample = data[signal_type][:1000].tolist()

        time_features = extract_time_domain_features(data[signal_type])

        freq, magnitude = perform_fft(data[signal_type], data['sampling_rate'])

        freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

        fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

        freq_sample = freq[:500].tolist()
        magnitude_sample = magnitude[:500].tolist()

        signal_features = {
            'signal_sample': signal_sample,
            'time_features': time_features,
            'freq_features': freq_features,
            'fault_detection': fault_detection,
            'freq_sample': freq_sample,
            'magnitude_sample': magnitude_sample
        }

        # Add ML prediction if classifier is trained
        if classifier.is_trained:
            predicted_label, confidence, prob_dict = classifier.predict(time_features, freq_features)
            signal_features['prediction'] = {
                'label': predicted_label,
                'confidence': confidence,
                'probabilities': prob_dict
            }

        features[signal_type] = signal_features

    return features


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sample-data')
def get_sample_data():
    rpm = request.args.get('rpm', default=1800, type=int)

    data = create_sample_data(rpm=rpm)

    fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

    signal_types = ['normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault']
    features = _process_signals(data, fault_freqs, signal_types, train_classifier=True)

    response = {
        'fault_frequencies': fault_freqs,
        'sampling_rate': data['sampling_rate'],
        'rpm': data['rpm'],
        'features': features
    }

    return jsonify(response)


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        rpm = request.form.get('rpm', default=1800, type=int)

        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
                signal_data = df.iloc[:, 1].values
            else:
                return jsonify({'error': 'File type not supported yet'}), 400

            fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

            time_features = extract_time_domain_features(signal_data)

            sampling_rate = request.form.get('sampling_rate', default=12000, type=int)
            freq, magnitude = perform_fft(signal_data, sampling_rate)

            freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

            fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

            response = {
                'fault_frequencies': fault_freqs,
                'time_features': time_features,
                'freq_features': freq_features,
                'fault_detection': fault_detection,
                'signal_sample': signal_data[:1000].tolist(),
                'freq_sample': freq[:500].tolist(),
                'magnitude_sample': magnitude[:500].tolist(),
                'filename': filename
            }

            # Add ML prediction if classifier is trained
            _train_classifier_if_needed()
            if classifier.is_trained:
                predicted_label, confidence, prob_dict = classifier.predict(time_features, freq_features)
                response['prediction'] = {
                    'label': predicted_label,
                    'confidence': confidence,
                    'probabilities': prob_dict
                }

            return jsonify(response)

        except Exception as e:
            app.logger.error(f'Error analyzing file: {e}')
            return jsonify({'error': 'An error occurred while analyzing the file'}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/generate-sample', methods=['POST'])
def generate_sample_data():
    try:
        data = request.json

        rpm = float(data.get('rpm', 1800))
        sampling_rate = int(data.get('sampling_rate', 12000))
        num_samples = int(data.get('num_samples', 10000))
        fault_type = data.get('fault_type', 'normal')
        noise_level = float(data.get('noise_level', 0.5))

        sample_data = create_sample_data(num_samples, sampling_rate, rpm=rpm,
                                         fault_type=fault_type, noise_level=noise_level)

        fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

        signal_types = [fault_type] if fault_type != 'all' else [
            'normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault'
        ]

        features = _process_signals(sample_data, fault_freqs, signal_types, train_classifier=True)

        response = {
            'fault_frequencies': fault_freqs,
            'sampling_rate': sample_data['sampling_rate'],
            'rpm': sample_data['rpm'],
            'features': features
        }

        return jsonify(response)

    except Exception as e:
        app.logger.error(f'Error generating sample data: {e}')
        return jsonify({'error': 'An error occurred while generating sample data'}), 500


@app.route('/api/predict', methods=['POST'])
def predict_fault():
    try:
        data = request.json

        time_features = data.get('time_features', {})
        freq_features = data.get('freq_features', {})

        _train_classifier_if_needed()

        if not classifier.is_trained:
            return jsonify({'error': 'Classifier is not trained yet'}), 503

        predicted_label, confidence, prob_dict = classifier.predict(time_features, freq_features)

        return jsonify({
            'prediction': {
                'label': predicted_label,
                'confidence': confidence,
                'probabilities': prob_dict
            }
        })

    except Exception as e:
        app.logger.error(f'Error predicting fault: {e}')
        return jsonify({'error': 'An error occurred during prediction'}), 500


@app.route('/api/bearing-params', methods=['POST'])
def update_bearing_params():
    try:
        data = request.json

        bearing_params = {
            'ball_diameter': float(data.get('ball_diameter', default_bearing_params['ball_diameter'])),
            'pitch_diameter': float(data.get('pitch_diameter', default_bearing_params['pitch_diameter'])),
            'num_balls': int(data.get('num_balls', default_bearing_params['num_balls'])),
            'contact_angle': float(data.get('contact_angle', default_bearing_params['contact_angle']))
        }

        rpm = float(data.get('rpm', 1800))
        fault_freqs = calculate_bearing_frequencies(rpm, bearing_params)

        return jsonify({'fault_frequencies': fault_freqs})

    except Exception as e:
        app.logger.error(f'Error updating bearing params: {e}')
        return jsonify({'error': 'An error occurred while updating parameters'}), 500


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    app.run(debug=debug)

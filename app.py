from flask import Flask, jsonify, request, render_template, send_from_directory
from flask.json import JSONEncoder
import os
import numpy as np
import pandas as pd
import json
from werkzeug.utils import secure_filename

# Import our modules
from data_acquisition import create_sample_data
from bearing_calculations import calculate_bearing_frequencies
from feature_extraction import extract_time_domain_features, extract_frequency_domain_features
from spectral_analysis import perform_fft, detect_fault_frequencies


app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'mat', 'txt', 'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# NumPy 타입을 처리하는 JSONEncoder 확장
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(CustomJSONEncoder, self).default(obj)

# Flask 앱에 사용자 정의 JSONEncoder 설정
app.json_encoder = CustomJSONEncoder

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sample-data')
def get_sample_data():
    rpm = request.args.get('rpm', default=1800, type=int)

    # Generate sample data
    data = create_sample_data()

    # Calculate fault frequencies
    fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

    # Prepare response data
    response = {
        'fault_frequencies': fault_freqs,
        'sampling_rate': data['sampling_rate'],
        'rpm': data['rpm'],
    }

    # Process each signal type
    signal_types = ['normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault']
    features = {}

    for signal_type in signal_types:
        # Skip if this signal type wasn't generated
        if signal_type not in data:
            continue

        # Get a sample of the signal (to reduce data transfer)
        signal_sample = data[signal_type][:1000].tolist()

        # Extract time domain features
        time_features = extract_time_domain_features(data[signal_type])

        # Perform FFT
        freq, magnitude = perform_fft(data[signal_type], data['sampling_rate'])

        # Extract frequency domain features
        freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

        # Detect fault frequencies
        fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

        # Prepare sample of frequency data (to reduce data transfer)
        freq_sample = freq[:500].tolist()
        magnitude_sample = magnitude[:500].tolist()

        # Store all feature data
        features[signal_type] = {
            'signal_sample': signal_sample,
            'time_features': time_features,
            'freq_features': freq_features,
            'fault_detection': fault_detection,
            'freq_sample': freq_sample,
            'magnitude_sample': magnitude_sample
        }

    response['features'] = features

    return jsonify(response)


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get parameters from form
        rpm = request.form.get('rpm', default=1800, type=int)

        # Try to load the file (this is a simplified example)
        try:
            # For CSV files
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
                # Assuming the first column is time and the second is the signal
                signal_data = df.iloc[:, 1].values

            # For other file types, you would need specific loaders
            else:
                return jsonify({'error': 'File type not supported yet'}), 400

            # Calculate fault frequencies
            fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

            # Extract features
            time_features = extract_time_domain_features(signal_data)

            # Perform FFT (assuming sampling rate from form or default)
            sampling_rate = request.form.get('sampling_rate', default=12000, type=int)
            freq, magnitude = perform_fft(signal_data, sampling_rate)

            # Extract frequency domain features
            freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

            # Detect fault frequencies
            fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

            # Prepare response
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

            return jsonify(response)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/generate-sample', methods=['POST'])
def generate_sample_data():
    try:
        data = request.json

        # Get parameters from request
        rpm = float(data.get('rpm', 1800))
        sampling_rate = int(data.get('sampling_rate', 12000))
        num_samples = int(data.get('num_samples', 10000))
        fault_type = data.get('fault_type', 'normal')
        noise_level = float(data.get('noise_level', 0.5))

        # Create custom sample data
        sample_data = create_sample_data(num_samples, sampling_rate)

        # Calculate fault frequencies
        fault_freqs = calculate_bearing_frequencies(rpm, default_bearing_params)

        # Process the selected signal type
        features = {}

        # Determine which signal type to use for analysis
        # If specific fault_type was requested, use that
        # Otherwise if 'all' was requested, analyze each type
        signal_types = [fault_type] if fault_type != 'all' else ['normal', 'outer_fault', 'inner_fault', 'ball_fault',
                                                                 'cage_fault']

        for signal_type in signal_types:
            # Skip if this signal type wasn't generated
            if signal_type not in sample_data:
                continue

            # Extract time domain features
            time_features = extract_time_domain_features(sample_data[signal_type])

            # Perform FFT
            freq, magnitude = perform_fft(sample_data[signal_type], sample_data['sampling_rate'])

            # Extract frequency domain features
            freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

            # Detect fault frequencies
            fault_detection, _ = detect_fault_frequencies(freq, magnitude, fault_freqs)

            # Prepare sample of frequency data
            freq_sample = freq[:500].tolist()
            magnitude_sample = magnitude[:500].tolist()

            # Extract a sample of the signal (to reduce data transfer)
            signal_sample = sample_data[signal_type][:1000].tolist()

            # Store feature data
            features[signal_type] = {
                'signal_sample': signal_sample,
                'time_features': time_features,
                'freq_features': freq_features,
                'fault_detection': fault_detection,
                'freq_sample': freq_sample,
                'magnitude_sample': magnitude_sample
            }

        response = {
            'fault_frequencies': fault_freqs,
            'sampling_rate': sample_data['sampling_rate'],
            'rpm': sample_data['rpm'],
            'features': features
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bearing-params', methods=['POST'])
def update_bearing_params():
    try:
        data = request.json

        # Update bearing parameters
        bearing_params = {
            'ball_diameter': float(data.get('ball_diameter', default_bearing_params['ball_diameter'])),
            'pitch_diameter': float(data.get('pitch_diameter', default_bearing_params['pitch_diameter'])),
            'num_balls': int(data.get('num_balls', default_bearing_params['num_balls'])),
            'contact_angle': float(data.get('contact_angle', default_bearing_params['contact_angle']))
        }

        # Calculate new fault frequencies with the specified RPM
        rpm = float(data.get('rpm', 1800))
        fault_freqs = calculate_bearing_frequencies(rpm, bearing_params)

        return jsonify({'fault_frequencies': fault_freqs})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
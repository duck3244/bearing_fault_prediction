import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from data_acquisition import create_sample_data
from bearing_calculations import calculate_bearing_frequencies
from feature_extraction import extract_time_domain_features, extract_frequency_domain_features
from spectral_analysis import perform_fft, detect_fault_frequencies


class BearingFaultClassifier:
    """RandomForest-based bearing fault classifier."""

    FAULT_TYPES = ['normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault']

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.FAULT_TYPES)
        self.is_trained = False

    def _extract_feature_vector(self, time_features, freq_features):
        """Extract a flat feature vector from time and frequency domain features."""
        feature_keys_time = [
            'mean', 'std_dev', 'rms', 'peak', 'kurtosis', 'skewness',
            'crest_factor', 'impulse_factor', 'shape_factor', 'clearance_factor',
            'energy', 'entropy', 'range', 'zero_crossing_rate'
        ]
        feature_keys_freq = [
            'mean_magnitude', 'std_magnitude', 'max_magnitude',
            'spectral_centroid', 'bandwidth', 'low_freq_energy_ratio'
        ]

        vector = []
        for key in feature_keys_time:
            vector.append(float(time_features.get(key, 0)))
        for key in feature_keys_freq:
            vector.append(float(freq_features.get(key, 0)))

        return vector

    def train(self, bearing_params, rpm=1800, sampling_rate=12000, num_samples=10000):
        """Train the classifier using generated sample data with noise augmentation."""
        X = []
        y = []

        noise_levels = [0.3, 0.5, 0.7, 1.0]
        fault_freqs = calculate_bearing_frequencies(rpm, bearing_params)

        for noise_level in noise_levels:
            for fault_type in self.FAULT_TYPES:
                data = create_sample_data(
                    num_samples=num_samples,
                    sampling_rate=sampling_rate,
                    rpm=rpm,
                    fault_type=fault_type,
                    noise_level=noise_level
                )

                signal_key = fault_type if fault_type != 'normal' else 'normal'
                if signal_key not in data:
                    continue

                signal = data[signal_key]
                time_features = extract_time_domain_features(signal)
                freq, magnitude = perform_fft(signal, sampling_rate)
                freq_features = extract_frequency_domain_features(freq, magnitude, fault_freqs)

                feature_vector = self._extract_feature_vector(time_features, freq_features)
                X.append(feature_vector)
                y.append(fault_type)

        X = np.array(X)
        y_encoded = self.label_encoder.transform(y)

        self.model.fit(X, y_encoded)
        self.is_trained = True

    def predict(self, time_features, freq_features):
        """
        Predict fault type from extracted features.

        Returns:
            tuple: (predicted_label, confidence, per-class probabilities dict)
        """
        if not self.is_trained:
            return None, 0.0, {}

        feature_vector = self._extract_feature_vector(time_features, freq_features)
        feature_array = np.array([feature_vector])

        predicted_idx = self.model.predict(feature_array)[0]
        probabilities = self.model.predict_proba(feature_array)[0]

        predicted_label = self.label_encoder.inverse_transform([predicted_idx])[0]
        confidence = float(np.max(probabilities))

        prob_dict = {}
        for idx, fault_type in enumerate(self.label_encoder.classes_):
            prob_dict[fault_type] = float(probabilities[idx])

        return predicted_label, confidence, prob_dict

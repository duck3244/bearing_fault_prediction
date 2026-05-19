import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from app.core.data_acquisition import create_sample_data
from app.core.bearing_calculations import calculate_bearing_frequencies
from app.core.feature_extraction import (
    extract_frequency_domain_features,
    extract_time_domain_features,
)
from app.core.mat_loader import label_from_filename, load_mat_signal
from app.core.spectral_analysis import perform_fft


class BearingFaultClassifier:
    """RandomForest-based bearing fault classifier."""

    FAULT_TYPES = ['normal', 'outer_fault', 'inner_fault', 'ball_fault', 'cage_fault']

    def __init__(self):
        # class_weight='balanced' is a no-op on the balanced synthetic training set
        # but is essential when fitting on real-world data (e.g. MFPT) where class
        # counts can differ by >2x and the majority class would otherwise bias predictions.
        self.model = RandomForestClassifier(n_estimators=100, random_state=42,
                                            class_weight='balanced')
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.FAULT_TYPES)
        self.is_trained = False
        # Source describes how the current weights were produced
        # ('synthetic', 'dataset:<path>', or None).
        self.source: str | None = None

    @property
    def trained_classes(self) -> list[str]:
        """Return the labels the model was actually fit on (subset of FAULT_TYPES)."""
        if not self.is_trained:
            return []
        return list(self.label_encoder.inverse_transform(self.model.classes_))

    FEATURE_KEYS_TIME = [
        'mean', 'std_dev', 'rms', 'peak', 'kurtosis', 'skewness',
        'crest_factor', 'impulse_factor', 'shape_factor', 'clearance_factor',
        'energy', 'entropy', 'range', 'zero_crossing_rate'
    ]
    FEATURE_KEYS_FREQ = [
        'mean_magnitude', 'std_magnitude', 'max_magnitude',
        'spectral_centroid', 'bandwidth', 'low_freq_energy_ratio',
        'BPFO_h1_energy', 'BPFO_h2_energy', 'BPFO_h3_energy',
        'BPFI_h1_energy', 'BPFI_h2_energy', 'BPFI_h3_energy',
        'BSF_h1_energy', 'BSF_h2_energy', 'BSF_h3_energy',
        'FTF_h1_energy', 'FTF_h2_energy', 'FTF_h3_energy',
    ]

    def _extract_feature_vector(self, time_features, freq_features):
        """Extract a flat feature vector from time and frequency domain features."""
        vector = []
        for key in self.FEATURE_KEYS_TIME:
            vector.append(float(time_features.get(key, 0)))
        for key in self.FEATURE_KEYS_FREQ:
            vector.append(float(freq_features.get(key, 0)))
        return vector

    def train(self, bearing_params, rpm=1800, sampling_rate=12000, num_samples=10000, seed=42):
        """Train the classifier using generated sample data with noise augmentation."""
        X = []
        y = []

        noise_levels = [0.3, 0.5, 0.7, 1.0]
        fault_freqs = calculate_bearing_frequencies(rpm, bearing_params)

        for ni, noise_level in enumerate(noise_levels):
            for fi, fault_type in enumerate(self.FAULT_TYPES):
                sample_seed = None if seed is None else seed + ni * len(self.FAULT_TYPES) + fi
                data = create_sample_data(
                    num_samples=num_samples,
                    sampling_rate=sampling_rate,
                    rpm=rpm,
                    fault_type=fault_type,
                    noise_level=noise_level,
                    seed=sample_seed
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
        self.source = 'synthetic'

    def train_from_dataset(self, dataset_dir, bearing_params, window=12000, hop=6000,
                           default_rpm=1500, default_sampling_rate=48828,
                           amplitude_augment=1, augment_scale_range=(0.3, 3.0), seed=42):
        """Train from a directory of .mat files with MFPT-style filenames.

        Each file is windowed; each window becomes one training example.
        File label is derived from the filename via mat_loader.label_from_filename.

        Amplitude augmentation
        ----------------------
        When ``amplitude_augment > 1`` each window is duplicated that many
        times, with all but one copy scaled by a random factor sampled
        uniformly from ``augment_scale_range``. This forces the classifier
        to rely on amplitude-invariant patterns (e.g. BPFO/BPFI peak
        structure) rather than absolute signal magnitude, which on the MFPT
        training set happens to correlate with the label (inner_fault has
        roughly 2x the amplitude of outer_fault).
        """
        if not os.path.isdir(dataset_dir):
            raise FileNotFoundError(dataset_dir)
        if amplitude_augment < 1:
            raise ValueError('amplitude_augment must be >= 1')

        rng = np.random.default_rng(seed)

        X, y = [], []
        seen_files = 0
        skipped = []
        for fname in sorted(os.listdir(dataset_dir)):
            if not fname.lower().endswith('.mat'):
                continue
            label = label_from_filename(fname)
            if label is None:
                skipped.append(fname)
                continue
            path = os.path.join(dataset_dir, fname)
            mat = load_mat_signal(path)
            sig = mat['signal']
            sr = mat['sampling_rate'] or default_sampling_rate
            rpm = mat['rpm'] or default_rpm
            fault_freqs = calculate_bearing_frequencies(rpm, bearing_params)

            step = max(1, hop)
            for start in range(0, len(sig) - window + 1, step):
                seg = sig[start:start + window]
                # Original + (amplitude_augment - 1) random-scaled copies
                scales = [1.0]
                if amplitude_augment > 1:
                    scales += list(rng.uniform(augment_scale_range[0],
                                               augment_scale_range[1],
                                               size=amplitude_augment - 1))
                for scale in scales:
                    scaled = seg if scale == 1.0 else seg * scale
                    tf = extract_time_domain_features(scaled)
                    freq, mag = perform_fft(scaled, sr)
                    ffeat = extract_frequency_domain_features(freq, mag, fault_freqs)
                    X.append(self._extract_feature_vector(tf, ffeat))
                    y.append(label)
            seen_files += 1

        if not X:
            raise ValueError(f'No labelled .mat files found in {dataset_dir}')

        X = np.array(X)
        y_encoded = self.label_encoder.transform(y)
        self.model.fit(X, y_encoded)
        self.is_trained = True
        suffix = f' aug={amplitude_augment}' if amplitude_augment > 1 else ''
        self.source = f'dataset:{os.path.abspath(dataset_dir)}{suffix}'

        return {
            'n_files': seen_files,
            'n_windows': len(X),
            'amplitude_augment': amplitude_augment,
            'skipped_files': skipped,
            'class_counts': {lbl: int(c) for lbl, c in zip(*np.unique(y, return_counts=True))},
        }

    def save(self, path):
        """Persist the trained classifier (model + encoder + metadata) to disk."""
        if not self.is_trained:
            raise RuntimeError('Classifier is not trained')
        os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'label_encoder': self.label_encoder,
                'source': self.source,
                'feature_keys_time': self.FEATURE_KEYS_TIME,
                'feature_keys_freq': self.FEATURE_KEYS_FREQ,
            }, f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            blob = pickle.load(f)
        clf = cls()
        clf.model = blob['model']
        clf.label_encoder = blob['label_encoder']
        clf.source = blob.get('source')
        clf.is_trained = True
        return clf

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

        # Use the model's actual trained class indices so partial-class
        # models (e.g. trained on a 3-class subset) do not over-index.
        trained_labels = self.label_encoder.inverse_transform(self.model.classes_)
        prob_dict = {label: float(p) for label, p in zip(trained_labels, probabilities)}

        return predicted_label, confidence, prob_dict

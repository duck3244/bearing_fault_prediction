// Global variables
let currentData = null;
let currentSignalType = 'normal';
let charts = {};
let chartColors = {
    default: {
        backgroundColor: [
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 99, 132, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(75, 192, 192, 0.5)',
            'rgba(153, 102, 255, 0.5)',
            'rgba(255, 159, 64, 0.5)'
        ],
        borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)'
        ],
    }
};

// Chart.js global defaults
Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

// DOM Elements
const loadingOverlay = document.getElementById('loadingOverlay');
const btnLoadSample = document.getElementById('btnLoadSample');
const btnAnalyze = document.getElementById('btnAnalyze');
const fileUpload = document.getElementById('fileUpload');
const signalSelect = document.getElementById('signalSelect');
const darkModeSwitch = document.getElementById('darkModeSwitch');
const bearingParamsForm = document.getElementById('bearingParamsForm');
const vizSettingsForm = document.getElementById('vizSettingsForm');

// Initialize theme based on user preference
function initTheme() {
    if (localStorage.getItem('darkMode') === 'true' || darkModeSwitch.checked) {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
        darkModeSwitch.checked = true;
    } else {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
        darkModeSwitch.checked = false;
    }
    updateChartsTheme();
}

// Toggle dark/light theme
function toggleTheme() {
    if (darkModeSwitch.checked) {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
        localStorage.setItem('darkMode', 'true');
    } else {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
    }
    updateChartsTheme();
}

// Update chart themes
function updateChartsTheme() {
    const isDarkMode = document.body.classList.contains('dark-mode');

    // Update Chart.js defaults
    Chart.defaults.color = isDarkMode ? '#f8f9fa' : '#212529';
    Chart.defaults.borderColor = isDarkMode ? '#495057' : '#dee2e6';

    // Update existing charts
    Object.values(charts).forEach(chart => {
        if (chart && chart.options) {
            if (chart.options.scales && chart.options.scales.x) {
                chart.options.scales.x.grid.color = isDarkMode ? '#495057' : '#dee2e6';
                chart.options.scales.x.ticks.color = isDarkMode ? '#f8f9fa' : '#212529';
            }

            if (chart.options.scales && chart.options.scales.y) {
                chart.options.scales.y.grid.color = isDarkMode ? '#495057' : '#dee2e6';
                chart.options.scales.y.ticks.color = isDarkMode ? '#f8f9fa' : '#212529';
            }

            if (chart.options.plugins && chart.options.plugins.title) {
                chart.options.plugins.title.color = isDarkMode ? '#f8f9fa' : '#212529';
            }

            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = isDarkMode ? '#f8f9fa' : '#212529';
            }

            chart.update();
        }
    });
}

// Show loading overlay
function showLoading() {
    loadingOverlay.classList.remove('d-none');
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.classList.add('d-none');
}

// Load sample data from API
async function loadSampleData() {
    showLoading();

    try {
        const rpm = document.getElementById('rpmInput').value || 1800;
        const response = await fetch(`/api/sample-data?rpm=${rpm}`);

        if (!response.ok) {
            throw new Error('Failed to load sample data');
        }

        const data = await response.json();
        currentData = data;

        // Get available signal types and update dropdown
        const availableTypes = Object.keys(data.features);
        updateSignalTypeDropdown(availableTypes);

        // Update signal type from dropdown
        currentSignalType = signalSelect.value;

        // If current selection is not available, select the first available type
        if (!availableTypes.includes(currentSignalType) && availableTypes.length > 0) {
            currentSignalType = availableTypes[0];
            signalSelect.value = currentSignalType;
        }

        // Update UI with data
        updateUIWithData();

        // Enable analyze button
        btnAnalyze.disabled = false;

    } catch (error) {
        console.error('Error loading sample data:', error);
        alert('Error loading sample data. Please try again.');
    } finally {
        hideLoading();
    }
}

// Analyze uploaded data
async function analyzeUploadedData() {
    if (!fileUpload.files || fileUpload.files.length === 0) {
        alert('Please select a file to analyze.');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('file', fileUpload.files[0]);
        formData.append('rpm', document.getElementById('rpmInput').value || 1800);
        formData.append('sampling_rate', 12000);

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to analyze data');
        }

        const data = await response.json();

        // Create structure similar to sample data
        const uploadedFeatures = {
            signal_sample: data.signal_sample,
            time_features: data.time_features,
            freq_features: data.freq_features,
            fault_detection: data.fault_detection,
            freq_sample: data.freq_sample,
            magnitude_sample: data.magnitude_sample
        };

        if (data.prediction) {
            uploadedFeatures.prediction = data.prediction;
        }

        currentData = {
            fault_frequencies: data.fault_frequencies,
            rpm: data.rpm || 1800,
            sampling_rate: data.sampling_rate || 12000,
            features: {
                uploaded: uploadedFeatures
            }
        };

        // Set current signal type to uploaded
        currentSignalType = 'uploaded';

        // Update UI
        updateUIWithData();

    } catch (error) {
        console.error('Error analyzing data:', error);
        alert('Error analyzing data. Please try again.');
    } finally {
        hideLoading();
    }
}

// Update UI with data
function updateUIWithData() {
    if (!currentData || !currentData.features) {
        console.error('Invalid data structure');
        return;
    }

    // Check if currentSignalType exists in the data
    if (!currentData.features[currentSignalType]) {
        const availableTypes = Object.keys(currentData.features);
        if (availableTypes.length === 0) {
            console.error('No signal types available in the data');
            return;
        }
        currentSignalType = availableTypes[0];

        if (signalSelect.value !== currentSignalType) {
            signalSelect.value = currentSignalType;
        }
    }

    const features = currentData.features[currentSignalType];

    // Update status cards
    document.getElementById('signalStatus').textContent = currentSignalType.replaceAll('_', ' ').toUpperCase();
    document.getElementById('rpmStatus').textContent = currentData.rpm + ' RPM';

    // Update fault status and confidence from ML prediction
    if (features.prediction) {
        const pred = features.prediction;
        const hasFault = pred.label !== 'normal';
        document.getElementById('faultStatus').textContent = hasFault ? pred.label.replaceAll('_', ' ').toUpperCase() : 'NO';
        document.getElementById('faultStatus').style.color = hasFault ? 'var(--danger-color)' : 'var(--success-color)';
        document.getElementById('confidenceStatus').textContent = (pred.confidence * 100).toFixed(1) + '%';
    } else {
        const hasFault = currentSignalType !== 'normal';
        document.getElementById('faultStatus').textContent = hasFault ? 'YES' : 'NO';
        document.getElementById('faultStatus').style.color = hasFault ? 'var(--danger-color)' : 'var(--success-color)';
        document.getElementById('confidenceStatus').textContent = 'N/A';
    }

    // Update charts
    updateTimeSignalChart(features.signal_sample);
    updateFreqSpectrumChart(features.freq_sample, features.magnitude_sample);
    updateTimeFeatureChart(features.time_features);
    updateFreqFeatureChart(features.freq_features);

    // Update tables
    updateTimeFeatureTable(features.time_features);
    updateFreqFeatureTable(features.freq_features);
    updateFaultFreqTable(currentData.fault_frequencies);
    updateDetectedFaultTable(features.fault_detection);

    // Additional charts for specific tabs
    updateRawSignalChart(features.signal_sample);
    updateFullSpectrumChart(features.freq_sample, features.magnitude_sample);
    updateLowFreqChart(features.freq_sample, features.magnitude_sample);
    updateTimeFeatureRadarChart(features.time_features);
    updateFaultSeverityChart(features);
    updateFaultComparisonChart();
}

// Time Signal Chart
function updateTimeSignalChart(signalData) {
    const ctx = document.getElementById('timeSignalChart').getContext('2d');
    const timeArray = Array.from({length: signalData.length}, (_, i) => i / 1000);

    if (charts.timeSignal) {
        charts.timeSignal.destroy();
    }

    charts.timeSignal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeArray,
            datasets: [{
                label: 'Amplitude',
                data: signalData,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                pointRadius: 0
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Time (s)' }
                },
                y: {
                    title: { display: true, text: 'Amplitude' }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${currentSignalType.replaceAll('_', ' ').toUpperCase()} - Time Domain Signal`
                }
            },
            animation: { duration: 1000 }
        }
    });
}

// Frequency Spectrum Chart
function updateFreqSpectrumChart(freqData, magnitudeData) {
    const ctx = document.getElementById('freqSpectrumChart').getContext('2d');

    if (charts.freqSpectrum) {
        charts.freqSpectrum.destroy();
    }

    charts.freqSpectrum = new Chart(ctx, {
        type: 'line',
        data: {
            labels: freqData,
            datasets: [{
                label: 'Magnitude',
                data: magnitudeData,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                pointRadius: 0
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Frequency (Hz)' }
                },
                y: {
                    title: { display: true, text: 'Magnitude' }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${currentSignalType.replaceAll('_', ' ').toUpperCase()} - Frequency Spectrum`
                }
            },
            animation: { duration: 1000 }
        }
    });
}

// Time Feature Chart
function updateTimeFeatureChart(timeFeatures) {
    const ctx = document.getElementById('timeFeatureChart').getContext('2d');

    const selectedFeatures = ['rms', 'kurtosis', 'crest_factor', 'impulse_factor'];
    const featureLabels = selectedFeatures.map(f => f.replaceAll('_', ' ').toUpperCase());
    const featureValues = selectedFeatures.map(f => timeFeatures[f]);

    if (charts.timeFeature) {
        charts.timeFeature.destroy();
    }

    charts.timeFeature = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: featureLabels,
            datasets: [{
                label: 'Value',
                data: featureValues,
                backgroundColor: chartColors.default.backgroundColor.slice(0, 4),
                borderColor: chartColors.default.borderColor.slice(0, 4),
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Value' }
                }
            },
            plugins: {
                title: { display: true, text: 'Key Time Domain Features' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Frequency Feature Chart
function updateFreqFeatureChart(freqFeatures) {
    const ctx = document.getElementById('freqFeatureChart').getContext('2d');

    const selectedFeatures = ['max_magnitude', 'spectral_centroid', 'low_freq_energy_ratio'];
    const featureLabels = selectedFeatures.map(f => f.replaceAll('_', ' ').toUpperCase());
    const featureValues = selectedFeatures.map(f => freqFeatures[f]);

    if (charts.freqFeature) {
        charts.freqFeature.destroy();
    }

    charts.freqFeature = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: featureLabels,
            datasets: [{
                label: 'Value',
                data: featureValues,
                backgroundColor: chartColors.default.backgroundColor.slice(2, 5),
                borderColor: chartColors.default.borderColor.slice(2, 5),
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Value' }
                }
            },
            plugins: {
                title: { display: true, text: 'Key Frequency Domain Features' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Raw Signal Chart (Time Domain Tab)
function updateRawSignalChart(signalData) {
    const ctx = document.getElementById('rawSignalChart').getContext('2d');
    const timeArray = Array.from({length: signalData.length}, (_, i) => i / 1000);

    if (charts.rawSignal) {
        charts.rawSignal.destroy();
    }

    charts.rawSignal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeArray,
            datasets: [{
                label: 'Amplitude',
                data: signalData,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                pointRadius: 0
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Time (s)' }
                },
                y: {
                    title: { display: true, text: 'Amplitude' }
                }
            },
            plugins: {
                title: { display: true, text: 'Full Time Domain Signal' },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'xy',
                    }
                }
            },
            animation: { duration: 1000 }
        }
    });
}

// Full Spectrum Chart (Frequency Domain Tab)
function updateFullSpectrumChart(freqData, magnitudeData) {
    const ctx = document.getElementById('fullSpectrumChart').getContext('2d');

    if (charts.fullSpectrum) {
        charts.fullSpectrum.destroy();
    }

    charts.fullSpectrum = new Chart(ctx, {
        type: 'line',
        data: {
            labels: freqData,
            datasets: [{
                label: 'Magnitude',
                data: magnitudeData,
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1,
                pointRadius: 0
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Frequency (Hz)' }
                },
                y: {
                    title: { display: true, text: 'Magnitude' }
                }
            },
            plugins: {
                title: { display: true, text: 'Full Frequency Spectrum' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Low Frequency Chart (Frequency Domain Tab)
function updateLowFreqChart(freqData, magnitudeData) {
    const ctx = document.getElementById('lowFreqChart').getContext('2d');

    const lowFreqThreshold = 200;
    const lowFreqData = freqData.filter(freq => freq <= lowFreqThreshold);
    const lowFreqIndices = freqData.map((freq, index) => freq <= lowFreqThreshold ? index : -1).filter(idx => idx !== -1);
    const lowFreqMagnitudes = lowFreqIndices.map(idx => magnitudeData[idx]);

    if (charts.lowFreq) {
        charts.lowFreq.destroy();
    }

    charts.lowFreq = new Chart(ctx, {
        type: 'line',
        data: {
            labels: lowFreqData,
            datasets: [{
                label: 'Magnitude',
                data: lowFreqMagnitudes,
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1,
                pointRadius: 1
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Frequency (Hz)' }
                },
                y: {
                    title: { display: true, text: 'Magnitude' }
                }
            },
            plugins: {
                title: { display: true, text: 'Low Frequency Range (0-200Hz)' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Time Feature Radar Chart
function updateTimeFeatureRadarChart(timeFeatures) {
    const ctx = document.getElementById('timeFeatureRadarChart').getContext('2d');

    const selectedFeatures = ['rms', 'kurtosis', 'crest_factor', 'impulse_factor', 'shape_factor', 'peak'];
    const featureLabels = selectedFeatures.map(f => f.replaceAll('_', ' ').toUpperCase());

    const maxValues = {
        rms: 2,
        kurtosis: 10,
        crest_factor: 5,
        impulse_factor: 5,
        shape_factor: 3,
        peak: 5
    };

    const normalizedValues = selectedFeatures.map(f => {
        const value = timeFeatures[f];
        return Math.min(value / maxValues[f], 1);
    });

    if (charts.timeFeatureRadar) {
        charts.timeFeatureRadar.destroy();
    }

    charts.timeFeatureRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: featureLabels,
            datasets: [{
                label: currentSignalType.replaceAll('_', ' ').toUpperCase(),
                data: normalizedValues,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(54, 162, 235, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1
                }
            },
            plugins: {
                title: { display: true, text: 'Time Domain Feature Patterns' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const actualValue = timeFeatures[selectedFeatures[index]];
                            return `${selectedFeatures[index]}: ${actualValue.toFixed(4)}`;
                        }
                    }
                }
            },
            animation: { duration: 1000 }
        }
    });
}

// Fault Severity Chart
function updateFaultSeverityChart(features) {
    const ctx = document.getElementById('faultSeverityChart').getContext('2d');

    const faultTypes = ['Normal', 'Outer Race', 'Inner Race', 'Ball', 'Cage'];
    let severityScores;

    // Use ML prediction probabilities if available
    if (features.prediction && features.prediction.probabilities) {
        const probs = features.prediction.probabilities;
        severityScores = [
            probs['normal'] || 0,
            probs['outer_fault'] || 0,
            probs['inner_fault'] || 0,
            probs['ball_fault'] || 0,
            probs['cage_fault'] || 0
        ];
    } else {
        severityScores = [0, 0, 0, 0, 0];
        if (currentSignalType === 'normal') {
            severityScores[0] = 0.9;
        } else if (currentSignalType === 'outer_fault') {
            severityScores[1] = 0.8;
        } else if (currentSignalType === 'inner_fault') {
            severityScores[2] = 0.7;
        } else if (currentSignalType === 'ball_fault') {
            severityScores[3] = 0.75;
        } else if (currentSignalType === 'cage_fault') {
            severityScores[4] = 0.6;
        } else {
            const kurtosis = features.time_features.kurtosis;
            if (kurtosis > 5) {
                severityScores[2] = 0.6;
            } else if (features.time_features.crest_factor > 4) {
                severityScores[1] = 0.5;
            } else {
                severityScores[0] = 0.4;
            }
        }
    }

    if (charts.faultSeverity) {
        charts.faultSeverity.destroy();
    }

    charts.faultSeverity = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faultTypes,
            datasets: [{
                label: 'Probability',
                data: severityScores,
                backgroundColor: [
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 159, 64, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    title: { display: true, text: 'Probability (0-1)' }
                }
            },
            plugins: {
                title: { display: true, text: 'Fault Type Probability' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Fault Comparison Chart
function updateFaultComparisonChart() {
    const ctx = document.getElementById('faultComparisonChart').getContext('2d');

    if (!currentData || !currentData.features) {
        return;
    }

    const comparisonFeatures = ['rms', 'kurtosis', 'crest_factor'];
    const labels = comparisonFeatures.map(f => f.replaceAll('_', ' ').toUpperCase());

    const datasets = [];
    const colors = chartColors.default.backgroundColor;
    const borderColors = chartColors.default.borderColor;

    const currentFeatures = currentData.features[currentSignalType].time_features;
    datasets.push({
        label: currentSignalType.replaceAll('_', ' ').toUpperCase(),
        data: comparisonFeatures.map(f => currentFeatures[f]),
        backgroundColor: colors[0],
        borderColor: borderColors[0],
        borderWidth: 1
    });

    const syntheticMultipliers = {
        'normal': [0.8, 0.3, 0.7],
        'outer_fault': [1.2, 1.5, 1.3],
        'inner_fault': [1.1, 2.0, 1.4],
        'ball_fault': [1.0, 1.2, 1.1],
        'cage_fault': [0.9, 0.8, 0.9]
    };

    const signalTypes = Object.keys(syntheticMultipliers);
    const comparisonTypes = signalTypes.filter(type => type !== currentSignalType);

    comparisonTypes.slice(0, 2).forEach((type, idx) => {
        const multipliers = syntheticMultipliers[type];
        datasets.push({
            label: type.replaceAll('_', ' ').toUpperCase(),
            data: comparisonFeatures.map((f, i) => currentFeatures[f] * multipliers[i]),
            backgroundColor: colors[idx + 1],
            borderColor: borderColors[idx + 1],
            borderWidth: 1
        });
    });

    if (charts.faultComparison) {
        charts.faultComparison.destroy();
    }

    charts.faultComparison = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            elements: {
                line: { tension: 0.2 }
            },
            plugins: {
                title: { display: true, text: 'Feature Comparison Across Fault Types' }
            },
            animation: { duration: 1000 }
        }
    });
}

// Update Time Feature Table
function updateTimeFeatureTable(timeFeatures) {
    const table = document.getElementById('timeFeatureTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    const sortedFeatures = Object.keys(timeFeatures).sort();

    sortedFeatures.forEach(feature => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = feature.replaceAll('_', ' ').toUpperCase();

        const valueCell = document.createElement('td');
        const value = timeFeatures[feature];
        valueCell.textContent = typeof value === 'number'
            ? (Math.abs(value) < 0.001 || Math.abs(value) > 10000
                ? value.toExponential(4)
                : value.toFixed(4))
            : value;

        row.appendChild(nameCell);
        row.appendChild(valueCell);
        tbody.appendChild(row);
    });
}

// Update Frequency Feature Table
function updateFreqFeatureTable(freqFeatures) {
    const table = document.getElementById('freqFeatureTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    const generalFeatures = {};
    const faultEnergyFeatures = {};

    Object.keys(freqFeatures).forEach(feature => {
        if (feature.includes('_energy')) {
            faultEnergyFeatures[feature] = freqFeatures[feature];
        } else {
            generalFeatures[feature] = freqFeatures[feature];
        }
    });

    const sortedGeneralFeatures = Object.keys(generalFeatures).sort();
    sortedGeneralFeatures.forEach(feature => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = feature.replaceAll('_', ' ').toUpperCase();

        const valueCell = document.createElement('td');
        const value = generalFeatures[feature];
        valueCell.textContent = typeof value === 'number'
            ? (Math.abs(value) < 0.001 || Math.abs(value) > 10000
                ? value.toExponential(4)
                : value.toFixed(4))
            : value;

        row.appendChild(nameCell);
        row.appendChild(valueCell);
        tbody.appendChild(row);
    });

    if (Object.keys(faultEnergyFeatures).length > 0) {
        const separatorRow = document.createElement('tr');
        const separatorCell = document.createElement('td');
        separatorCell.colSpan = 2;
        separatorCell.textContent = 'FAULT ENERGY FEATURES';
        separatorCell.style.fontWeight = 'bold';
        separatorCell.style.backgroundColor = 'rgba(0,0,0,0.05)';
        separatorRow.appendChild(separatorCell);
        tbody.appendChild(separatorRow);

        const sortedFaultFeatures = Object.keys(faultEnergyFeatures).sort();
        sortedFaultFeatures.forEach(feature => {
            const row = document.createElement('tr');

            const nameCell = document.createElement('td');
            nameCell.textContent = feature.replaceAll('_', ' ').toUpperCase();

            const valueCell = document.createElement('td');
            const value = faultEnergyFeatures[feature];
            valueCell.textContent = typeof value === 'number'
                ? (Math.abs(value) < 0.001 || Math.abs(value) > 10000
                    ? value.toExponential(4)
                    : value.toFixed(4))
                : value;

            row.appendChild(nameCell);
            row.appendChild(valueCell);
            tbody.appendChild(row);
        });
    }
}

// Update Fault Frequency Table
function updateFaultFreqTable(faultFreqs) {
    const table = document.getElementById('faultFreqTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    Object.keys(faultFreqs).forEach(faultType => {
        const row = document.createElement('tr');

        const typeCell = document.createElement('td');
        typeCell.textContent = faultType;

        const freqCell = document.createElement('td');
        freqCell.textContent = faultFreqs[faultType].toFixed(2) + ' Hz';

        row.appendChild(typeCell);
        row.appendChild(freqCell);
        tbody.appendChild(row);
    });
}

// Update Detected Fault Table
function updateDetectedFaultTable(faultDetection) {
    const table = document.getElementById('detectedFaultTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    let hasDetections = false;

    Object.keys(faultDetection).forEach(faultType => {
        const detections = faultDetection[faultType];

        if (detections && detections.length > 0) {
            hasDetections = true;

            detections.forEach(detection => {
                const row = document.createElement('tr');

                const typeCell = document.createElement('td');
                typeCell.textContent = faultType;

                const harmonicCell = document.createElement('td');
                harmonicCell.textContent = detection.harmonic + 'x';

                const detectedCell = document.createElement('td');
                detectedCell.textContent = detection.detected_freq.toFixed(2) + ' Hz';

                const errorCell = document.createElement('td');
                errorCell.textContent = detection.deviation.toFixed(2) + '%';

                const amplitudeCell = document.createElement('td');
                amplitudeCell.textContent = detection.amplitude.toFixed(4);

                row.appendChild(typeCell);
                row.appendChild(harmonicCell);
                row.appendChild(detectedCell);
                row.appendChild(errorCell);
                row.appendChild(amplitudeCell);

                tbody.appendChild(row);
            });
        }
    });

    if (!hasDetections) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 5;
        cell.textContent = 'No fault frequencies detected';
        cell.classList.add('text-center');
        row.appendChild(cell);
        tbody.appendChild(row);
    }
}

// Update bearing parameters and recalculate fault frequencies
async function updateBearingParams(event) {
    event.preventDefault();

    const formData = {
        rpm: parseFloat(document.getElementById('rpmInput').value),
        ball_diameter: parseFloat(document.getElementById('ballDiameter').value),
        pitch_diameter: parseFloat(document.getElementById('pitchDiameter').value),
        num_balls: parseInt(document.getElementById('numBalls').value),
        contact_angle: parseFloat(document.getElementById('contactAngle').value)
    };

    try {
        const response = await fetch('/api/bearing-params', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to update parameters');
        }

        const data = await response.json();

        if (currentData) {
            currentData.fault_frequencies = data.fault_frequencies;
            updateFaultFreqTable(data.fault_frequencies);
            alert('Bearing parameters updated successfully.');
        }

    } catch (error) {
        console.error('Error updating parameters:', error);
        alert('Error updating parameters. Please try again.');
    }
}

// Update visualization settings
function updateVizSettings(event) {
    event.preventDefault();

    const colorScheme = document.getElementById('chartColorsSelect').value;
    const showGridLines = document.getElementById('showGridLines').checked;
    const showTooltips = document.getElementById('showTooltips').checked;
    const animateCharts = document.getElementById('animateCharts').checked;

    Chart.defaults.animation.duration = animateCharts ? 1000 : 0;

    Object.values(charts).forEach(chart => {
        if (chart && chart.options) {
            if (chart.options.scales && chart.options.scales.x) {
                chart.options.scales.x.grid.display = showGridLines;
            }

            if (chart.options.scales && chart.options.scales.y) {
                chart.options.scales.y.grid.display = showGridLines;
            }

            if (chart.options.plugins && chart.options.plugins.tooltip) {
                chart.options.plugins.tooltip.enabled = showTooltips;
            }

            chart.update();
        }
    });

    alert('Visualization settings updated successfully.');
}

// Generate custom sample data
async function generateSampleData() {
    const faultType = document.getElementById('sampleFaultType').value;
    const rpm = parseFloat(document.getElementById('sampleRPM').value);
    const samplingRate = parseInt(document.getElementById('sampleSamplingRate').value);
    const dataLength = parseInt(document.getElementById('sampleDataLength').value);
    const noiseLevel = parseFloat(document.getElementById('sampleNoiseLevel').value);

    if (isNaN(rpm) || rpm <= 0) {
        alert('Please enter a valid RPM value.');
        return;
    }

    if (isNaN(samplingRate) || samplingRate <= 0) {
        alert('Please enter a valid sampling rate.');
        return;
    }

    if (isNaN(dataLength) || dataLength < 1000) {
        alert('Please enter a valid data length (minimum 1000 samples).');
        return;
    }

    if (isNaN(noiseLevel) || noiseLevel < 0 || noiseLevel > 1) {
        alert('Please enter a valid noise level between 0 and 1.');
        return;
    }

    const modal = bootstrap.Modal.getInstance(document.getElementById('generateSampleModal'));
    modal.hide();

    showLoading();

    try {
        const response = await fetch('/api/generate-sample', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fault_type: faultType,
                rpm: rpm,
                sampling_rate: samplingRate,
                num_samples: dataLength,
                noise_level: noiseLevel
            })
        });

        if (!response.ok) {
            throw new Error('Failed to generate sample data');
        }

        const data = await response.json();
        currentData = data;

        if (faultType === 'all') {
            currentSignalType = signalSelect.value;
            updateSignalTypeDropdown(Object.keys(data.features));
        } else {
            currentSignalType = faultType;
            updateSignalTypeDropdown(Object.keys(data.features));
            signalSelect.value = currentSignalType;
        }

        updateUIWithData();
        btnAnalyze.disabled = false;

    } catch (error) {
        console.error('Error generating sample data:', error);
        alert('Error generating sample data. Please try again.');
    } finally {
        hideLoading();
    }
}

// Update signal type dropdown with available options
function updateSignalTypeDropdown(availableTypes) {
    signalSelect.innerHTML = '';

    const signalTypeLabels = {
        'normal': 'Normal',
        'outer_fault': 'Outer Race Fault',
        'inner_fault': 'Inner Race Fault',
        'ball_fault': 'Ball Fault',
        'cage_fault': 'Cage Fault',
        'uploaded': 'Uploaded Data'
    };

    availableTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = signalTypeLabels[type] || type.replaceAll('_', ' ').toUpperCase();
        signalSelect.appendChild(option);
    });
}

// Update noise level value display
function updateNoiseLevel() {
    const noiseLevel = document.getElementById('sampleNoiseLevel').value;
    document.getElementById('noiseLevelValue').textContent = noiseLevel;
}

// Export data as CSV
function exportData() {
    if (!currentData) {
        alert('No data available to export.');
        return;
    }

    try {
        const features = currentData.features[currentSignalType];

        const allFeatures = {
            ...features.time_features,
            ...features.freq_features
        };

        let csv = 'Feature,Value\n';
        Object.keys(allFeatures).forEach(feature => {
            csv += `${feature},${allFeatures[feature]}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `bearing_features_${currentSignalType}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Error exporting data. Please try again.');
    }
}

// Export all charts as PNG images
async function exportCharts() {
    const activeCharts = Object.entries(charts).filter(([_, chart]) => chart != null && chart.canvas);

    if (activeCharts.length === 0) {
        alert('No charts available to export. Please load data first.');
        return;
    }

    try {
        const chartNames = {
            timeSignal: 'Time Signal',
            freqSpectrum: 'Frequency Spectrum',
            timeFeature: 'Time Domain Features',
            freqFeature: 'Frequency Domain Features',
            rawSignal: 'Raw Signal',
            fullSpectrum: 'Full Spectrum',
            lowFreq: 'Low Frequency',
            timeFeatureRadar: 'Time Feature Radar',
            faultSeverity: 'Fault Severity',
            faultComparison: 'Fault Comparison'
        };

        // Filter to only charts with valid canvas dimensions
        const validCharts = activeCharts.filter(([_, chart]) => {
            const c = chart.canvas;
            return c && c.width > 0 && c.height > 0;
        });

        if (validCharts.length === 0) {
            alert('No visible charts to export. Please load data first.');
            return;
        }

        const padding = 20;
        const cols = 2;
        const rows = Math.ceil(validCharts.length / cols);
        const cellWidth = 600;
        const cellHeight = 400;
        const titleHeight = 30;
        const totalWidth = cols * cellWidth + (cols + 1) * padding;
        const totalHeight = rows * (cellHeight + titleHeight) + (rows + 1) * padding;

        const canvas = document.createElement('canvas');
        canvas.width = totalWidth;
        canvas.height = totalHeight;
        const ctx = canvas.getContext('2d');

        const isDark = document.body.classList.contains('dark-mode');
        ctx.fillStyle = isDark ? '#1a1a2e' : '#ffffff';
        ctx.fillRect(0, 0, totalWidth, totalHeight);

        // Load all chart images first, then draw
        const loadImage = (src) => new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });

        const images = await Promise.all(
            validCharts.map(([_, chart]) => loadImage(chart.toBase64Image()))
        );

        validCharts.forEach(([key, _], index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            const x = padding + col * (cellWidth + padding);
            const y = padding + row * (cellHeight + titleHeight + padding);

            ctx.fillStyle = isDark ? '#f8f9fa' : '#212529';
            ctx.font = 'bold 14px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(chartNames[key] || key, x + cellWidth / 2, y + 18);

            ctx.drawImage(images[index], x, y + titleHeight, cellWidth, cellHeight);
        });

        const link = document.createElement('a');
        link.download = `bearing_charts_${currentSignalType}.png`;
        link.href = canvas.toDataURL('image/png');
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (error) {
        console.error('Error exporting charts:', error);
        alert('Error exporting charts. Please try again.');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();

    // Dark mode toggle
    darkModeSwitch.addEventListener('change', toggleTheme);

    // Load sample data button
    btnLoadSample.addEventListener('click', loadSampleData);

    // Generate custom sample data button
    document.getElementById('btnGenerateSampleData').addEventListener('click', generateSampleData);

    // Update noise level display
    document.getElementById('sampleNoiseLevel').addEventListener('input', updateNoiseLevel);

    // Signal type change
    signalSelect.addEventListener('change', function() {
        if (currentData && currentData.features) {
            currentSignalType = this.value;
            updateUIWithData();
        }
    });

    // File upload
    fileUpload.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
            btnAnalyze.disabled = false;
        } else {
            btnAnalyze.disabled = true;
        }
    });

    // Analyze button
    btnAnalyze.addEventListener('click', analyzeUploadedData);

    // Export data button
    document.getElementById('btnExportData').addEventListener('click', exportData);

    // Export charts button
    document.getElementById('btnExportCharts').addEventListener('click', exportCharts);

    // Bearing parameters form
    bearingParamsForm.addEventListener('submit', updateBearingParams);

    // Visualization settings form
    vizSettingsForm.addEventListener('submit', updateVizSettings);
});

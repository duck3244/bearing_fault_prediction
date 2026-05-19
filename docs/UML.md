# UML 다이어그램

베어링 결함 예측 시스템의 주요 UML 다이어그램을 Mermaid 표기로 정리합니다. GitHub/GitLab/VS Code Mermaid Preview에서 그대로 렌더링됩니다.

---

## 1. Use Case Diagram (유스케이스)

```mermaid
flowchart LR
    user((사용자))
    op((운영자 / 데이터 사이언티스트))

    subgraph System["베어링 결함 예측 시스템"]
        UC1[CSV/.mat 업로드 분석]
        UC2[합성 신호 생성·분석]
        UC3[모델 상태 조회]
        UC4[베어링 프리셋 전환]
        UC5[합성 데이터로 재학습]
        UC6[MFPT 데이터셋으로 재학습]
        UC7[모델 영속화 - MODEL_PATH]
        UC8[CLI 재학습 - train_mfpt.py]
    end

    user --> UC1
    user --> UC2
    user --> UC3
    user --> UC4
    user --> UC5
    op   --> UC6
    op   --> UC7
    op   --> UC8

    UC1 -. include .-> UC3
    UC2 -. include .-> UC3
    UC5 -. extend .-> UC7
    UC6 -. extend .-> UC7
```

---

## 2. Component Diagram (컴포넌트)

```mermaid
flowchart TB
    subgraph Browser["Browser (localhost:5173)"]
        FE_App[App.tsx<br/>Tab Router]
        FE_Analyze[features/analyze/*]
        FE_Generate[features/generate/*]
        FE_Model[features/model/ModelDialog]
        FE_Lib[lib/api.ts<br/>ApiError, fetch wrapper]
        FE_RQ[(TanStack Query Cache)]
        FE_App --> FE_Analyze
        FE_App --> FE_Generate
        FE_App --> FE_Model
        FE_Analyze --> FE_Lib
        FE_Generate --> FE_Lib
        FE_Model --> FE_Lib
        FE_Analyze -.uses.-> FE_RQ
        FE_Generate -.uses.-> FE_RQ
        FE_Model -.uses.-> FE_RQ
    end

    subgraph Server["FastAPI Server (localhost:8000)"]
        Main[app/main.py<br/>lifespan + CORS]
        subgraph API["app/api/*"]
            R_Analyze[analyze.py]
            R_Sample[sample.py]
            R_Bearing[bearing.py]
            R_Model[model.py]
            R_Health[health.py]
            R_Helpers[_helpers.py]
        end
        subgraph Core["app/core/*"]
            C_DA[data_acquisition]
            C_BC[bearing_calculations]
            C_BP[bearing_presets]
            C_FE[feature_extraction]
            C_SA[spectral_analysis]
            C_FC[fault_classifier]
            C_ML[mat_loader]
        end
        subgraph Schemas["app/schemas/*"]
            S_A[analyze.py]
            S_B[bearing.py]
            S_M[model.py]
        end
        State[app/state.py<br/>AppState singleton]
        Settings[app/settings.py]
        Main --> API
        API -->|Depends| State
        API --> Schemas
        R_Analyze --> R_Helpers
        R_Sample --> R_Helpers
        R_Helpers --> C_FE
        R_Helpers --> C_SA
        R_Helpers --> C_ML
        R_Helpers --> C_FC
        R_Bearing --> C_BC
        R_Bearing --> C_BP
        R_Model --> C_FC
        R_Sample --> C_DA
        State --> C_FC
        State --> C_BP
        Main --> Settings
    end

    Disk[(models/*.pkl<br/>MODEL_PATH)]
    Dataset[(MFPT_Dataset/*.mat<br/>filesystem)]

    FE_Lib -- HTTP /api/* --> Main
    C_FC -- save/load --> Disk
    C_FC -- train_from_dataset --> Dataset

    classDef ext fill:#fef9c3,stroke:#a16207;
    class Disk,Dataset ext;
```

---

## 3. Class Diagram (백엔드 핵심 클래스)

```mermaid
classDiagram
    direction LR

    class AppState {
      +RLock lock
      +BearingFaultClassifier classifier
      +dict default_bearing_params
      +str current_preset
      +bootstrap_classifier() void
    }

    class Settings {
      <<frozen dataclass>>
      +str model_path
      +int max_upload_bytes
      +tuple~str~ cors_origins
    }

    class BearingFaultClassifier {
      +list~str~ FAULT_TYPES$
      +list~str~ FEATURE_KEYS_TIME$
      +list~str~ FEATURE_KEYS_FREQ$
      +RandomForestClassifier model
      +LabelEncoder label_encoder
      +bool is_trained
      +str~None~ source
      +trained_classes() list~str~
      +train(bearing_params, rpm, sampling_rate, num_samples, seed) void
      +train_from_dataset(dataset_dir, bearing_params, window, hop, amplitude_augment, ...) dict
      +predict(time_features, freq_features) tuple
      +save(path) void
      +load(path)$ BearingFaultClassifier
      -_extract_feature_vector(time_features, freq_features) list~float~
    }

    class BearingParams {
      <<Pydantic>>
      +float ball_diameter
      +float pitch_diameter
      +int num_balls
      +float contact_angle
    }

    class FaultFrequencies {
      <<Pydantic>>
      +float BPFO
      +float BPFI
      +float BSF
      +float FTF
      +float FR
    }

    class TimeFeatures {
      <<Pydantic>>
      +float mean
      +float std_dev
      +float rms
      +float peak
      +float kurtosis
      +float skewness
      +float crest_factor
      +float impulse_factor
      +float shape_factor
      +float clearance_factor
      +float energy
      +float entropy
      +float range
      +float zero_crossing_rate
    }

    class Prediction {
      <<Pydantic>>
      +str~None~ label
      +float confidence
      +dict~str,float~ probabilities
      +list~str~ trained_classes
    }

    class AnalyzeResponse {
      <<Pydantic>>
      +str filename
      +int sampling_rate
      +int rpm
      +FaultFrequencies fault_frequencies
      +TimeFeatures time_features
      +dict freq_features
      +dict fault_detection
      +list signal_sample
      +list freq_sample
      +list magnitude_sample
      +Prediction~None~ prediction
    }

    class ModelInfo {
      <<Pydantic>>
      +bool is_trained
      +str~None~ source
      +list~str~ trained_classes
      +list~str~ all_known_classes
      +str model_path
      +bool persisted
    }

    class RetrainRequest {
      <<Pydantic>>
      +Literal mode
      +bool save
      +int~None~ rpm
      +int~None~ sampling_rate
      +str~None~ dataset_dir
      +int window
      +int hop
      +int amplitude_augment
      +tuple augment_scale_range
    }

    AppState "1" --> "1" BearingFaultClassifier : owns
    AppState ..> Settings : reads model_path
    AnalyzeResponse "1" --> "1" FaultFrequencies
    AnalyzeResponse "1" --> "1" TimeFeatures
    AnalyzeResponse "0..1" --> "1" Prediction
    BearingFaultClassifier ..> TimeFeatures : consumes dict
    BearingFaultClassifier ..> FaultFrequencies : via fault freqs
```

---

## 4. Sequence Diagram — 파일 업로드 분석

```mermaid
sequenceDiagram
    autonumber
    actor U as 사용자
    participant UI as React UI<br/>(AnalyzePage)
    participant API as POST /api/analyze<br/>(analyze.py)
    participant H as _helpers
    participant ML as mat_loader / CSV
    participant FE as feature_extraction
    participant SA as spectral_analysis
    participant BC as bearing_calculations
    participant CLF as BearingFaultClassifier
    participant S as AppState

    U->>UI: drag&drop file
    UI->>API: multipart (file, rpm, sampling_rate)
    API->>S: Depends(get_state)
    API->>H: read_uploaded_signal(file, ...)
    alt .mat
        H->>ML: load_mat_signal(raw)
        ML-->>H: {signal, sr, rpm}
    else .csv
        H->>ML: read_csv_signal(raw, signal_column)
        ML-->>H: signal[]
    end
    H-->>API: (signal, sr, rpm_eff)
    API->>BC: calculate_bearing_frequencies(rpm, preset_params)
    BC-->>API: {BPFO, BPFI, BSF, FTF, FR}
    API->>H: process_signal(signal, sr, fault_freqs, classifier)
    H->>FE: extract_time_domain_features(signal)
    H->>SA: perform_fft(signal, sr)
    H->>FE: extract_frequency_domain_features(freq, mag, fault_freqs)
    H->>SA: detect_fault_frequencies(freq, mag, fault_freqs)
    alt signal.size ≥ 2 × WINDOW
        loop windows (12000 / hop 6000)
            H->>FE: extract_time_domain_features(seg)
            H->>SA: perform_fft(seg, sr)
            H->>FE: extract_frequency_domain_features(...)
            H->>CLF: predict(tf, ffeat)
            CLF-->>H: probabilities[]
        end
        H->>H: average probabilities
    else short signal
        H->>CLF: predict(tf_full, ffeat_full)
        CLF-->>H: (label, confidence, probs)
    end
    H-->>API: {time_features, freq_features, fault_detection, samples..., prediction}
    API-->>UI: AnalyzeResponse (JSON)
    UI->>UI: render SignalChart / SpectrumChart / FeatureGrid / PredictionCard
```

---

## 5. Sequence Diagram — 모델 재학습 (Dataset 모드)

```mermaid
sequenceDiagram
    autonumber
    actor U as 사용자
    participant UI as ModelDialog
    participant API as POST /api/model/retrain
    participant S as AppState
    participant New as new BearingFaultClassifier
    participant ML as mat_loader
    participant FE as feature_extraction
    participant SA as spectral_analysis
    participant SET as settings

    U->>UI: 'Retrain' 클릭 (mode=dataset, dataset_dir=…)
    UI->>API: JSON RetrainRequest
    API->>S: Depends(get_state) → preset, default_bearing_params
    API->>New: __init__()
    API->>New: train_from_dataset(dir, params, window, hop, augment, …)
    loop 디렉터리의 .mat 파일들
        New->>ML: load_mat_signal(path)
        ML-->>New: {signal, sr, rpm}
        New->>New: label_from_filename(name)
        loop 윈도우 슬라이딩
            loop 진폭 augmentation 사본
                New->>FE: extract_time_domain_features(seg*scale)
                New->>SA: perform_fft(seg*scale, sr)
                New->>FE: extract_frequency_domain_features(...)
                New->>New: X.append(feature_vector)
                New->>New: y.append(label)
            end
        end
    end
    New->>New: model.fit(X, y_encoded)
    New->>New: is_trained = True
    New->>New: source = "dataset:[path] aug=N"
    New-->>API: meta {n_files, n_windows, class_counts, ...}
    API->>S: with lock: state.classifier = new_clf
    opt body.save=True
        API->>SET: settings.model_path
        API->>New: save(model_path)
    end
    API-->>UI: RetrainResponse
    UI->>UI: invalidateQueries(['model','info']) → 헤더 칩 갱신
```

---

## 6. Sequence Diagram — 서버 부트스트랩

```mermaid
sequenceDiagram
    autonumber
    participant U as uvicorn
    participant App as FastAPI
    participant S as AppState
    participant SET as settings
    participant FS as filesystem
    participant CLF as BearingFaultClassifier

    U->>App: import app.main
    App->>S: AppState() (module import)
    S->>CLF: BearingFaultClassifier()  // 비학습 인스턴스
    U->>App: lifespan startup
    App->>S: bootstrap_classifier()
    S->>SET: settings.model_path
    S->>FS: os.path.isfile(model_path)
    alt 파일 있음
        S->>CLF: BearingFaultClassifier.load(model_path)
        CLF-->>S: 학습된 분류기
    else 파일 없음 또는 로드 실패
        S->>CLF: train(default_bearing_params)
        CLF-->>S: 학습 완료 (source='synthetic')
    end
    App-->>U: 서빙 시작 (모델 ready)
```

---

## 7. State Diagram — 분류기 라이프사이클

```mermaid
stateDiagram-v2
    [*] --> Untrained: BearingFaultClassifier()

    Untrained --> SyntheticTrained: train(bearing_params)
    Untrained --> DatasetTrained: train_from_dataset(dir, ...)
    Untrained --> Loaded: BearingFaultClassifier.load(path)

    SyntheticTrained --> SyntheticTrained: predict / save
    DatasetTrained   --> DatasetTrained:   predict / save
    Loaded           --> Loaded:           predict / save

    SyntheticTrained --> DatasetTrained: retrain(mode=dataset)
    DatasetTrained   --> SyntheticTrained: retrain(mode=synthetic)
    Loaded           --> SyntheticTrained: retrain(mode=synthetic)
    Loaded           --> DatasetTrained:   retrain(mode=dataset)

    SyntheticTrained --> Persisted: save(MODEL_PATH)
    DatasetTrained   --> Persisted: save(MODEL_PATH)
    Persisted --> Loaded: (다음 서버 부트스트랩)

    note right of SyntheticTrained
      source = 'synthetic'
    end note
    note right of DatasetTrained
      source = 'dataset:<path> aug=N'
    end note
```

---

## 8. ER-Style — 베어링 프리셋 데이터 모델

```mermaid
erDiagram
    BEARING_PRESET ||--o{ TRAIN_RUN : produces
    BEARING_PRESET {
        string name PK "SKF-6205, MFPT-NICE …"
        string description
        float ball_diameter "mm"
        float pitch_diameter "mm"
        int num_balls
        float contact_angle "deg"
        int default_rpm
        int default_sampling_rate "Hz"
    }
    TRAIN_RUN {
        string source "synthetic | dataset:<path> aug=N"
        string trained_classes "list[str]"
        string model_path "pkl"
        bool persisted
    }
    FAULT_FREQUENCIES {
        float BPFO "Hz"
        float BPFI "Hz"
        float BSF  "Hz"
        float FTF  "Hz"
        float FR   "Hz = rpm/60"
    }
    BEARING_PRESET ||--|| FAULT_FREQUENCIES : computes
```

---

## 9. API 엔드포인트 요약 표

| 메서드 / 경로 | 요청 스키마 | 응답 스키마 | 비고 |
|---|---|---|---|
| `GET  /api/health` | — | `{status: "ok"}` | 헬스체크 |
| `POST /api/analyze` | multipart (`file`, `rpm`, `sampling_rate`, `signal_column?`) | `AnalyzeResponse` | `.mat` 메타데이터가 form 값보다 우선 |
| `GET  /api/sample-data` | query `rpm` | `SampleDataResponse` | 모든 결함 유형 합성 |
| `POST /api/generate-sample` | `GenerateSampleRequest` | `SampleDataResponse` | 단일 결함 유형 |
| `GET  /api/bearing-presets` | — | `BearingPresetsResponse` | 사용 가능한 프리셋 + 현재값 |
| `POST /api/bearing-presets/{name}` | path `name` | `BearingPresetApplyResponse` | 프리셋 전환 |
| `POST /api/bearing-params` | `BearingParamsUpdate` | `BearingParamsResponse` | 베어링 사양 수동 변경 |
| `GET  /api/model/info` | — | `ModelInfo` | 현재 분류기 상태 |
| `POST /api/model/retrain` | `RetrainRequest` | `RetrainResponse` | mode = `synthetic` / `dataset` |
| `POST /api/predict` | `PredictRequest` | `PredictResponse` | 사전 추출된 피처 dict 직접 예측 |

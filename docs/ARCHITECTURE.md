# 아키텍처 (Architecture)

베어링 진동 신호에서 시간/주파수 도메인 특징을 추출하고, RandomForest 분류기로 결함 유형을 예측하는 풀스택 웹 애플리케이션의 전체 아키텍처를 정리한 문서입니다.

---

## 1. 시스템 개요

```
┌────────────────────┐        HTTP/JSON · multipart        ┌──────────────────────────┐
│   React SPA        │  ─────────────────────────────▶     │  FastAPI Backend         │
│   (Vite, TS, RQ)   │  ◀─────────────────────────────     │  (uvicorn, Pydantic v2)  │
│   localhost:5173   │        OpenAPI 자동 생성             │  localhost:8000          │
└────────────────────┘                                     └─────────────┬────────────┘
                                                                         │
                            ┌────────────────────────────────────────────┼────────────┐
                            ▼                                            ▼            ▼
                  ┌─────────────────┐                          ┌─────────────────┐  ┌──────────────┐
                  │ Core (pure)     │                          │  AppState       │  │  models/*.pkl│
                  │  - signal/FFT   │                          │  (singleton)    │  │  (persisted) │
                  │  - features     │                          │   · classifier  │  │              │
                  │  - classifier   │                          │   · preset      │  └──────────────┘
                  │  - mat_loader   │                          │   · RLock       │
                  └─────────────────┘                          └─────────────────┘
```

- **Frontend**: 브라우저에서 동작하는 React SPA. `Vite` 개발 서버가 `/api/*` 호출을 백엔드로 프록시.
- **Backend**: FastAPI 단일 프로세스. 시작 시 영속화된 `.pkl` 모델을 로드하거나, 없으면 합성 데이터로 즉시 학습.
- **Core**: FastAPI 무관한 순수 도메인 로직 모듈 묶음. 단위 테스트가 직접 호출하는 부분.
- **Persistence**: 학습된 모델은 `MODEL_PATH`(기본 `backend/models/classifier.pkl`) 로 영속화.

---

## 2. 디렉터리 구조

```
bearing_fault_prediction/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 인스턴스, lifespan, CORS, 라우터 등록
│   │   ├── settings.py          # 환경변수 기반 Settings (frozen dataclass)
│   │   ├── state.py             # AppState 모듈-수준 싱글턴, RLock 보호
│   │   ├── deps.py              # FastAPI Depends 헬퍼 (get_state, get_classifier)
│   │   ├── api/                 # HTTP 어댑터 (얇은 컨트롤러)
│   │   │   ├── analyze.py       # POST /api/analyze
│   │   │   ├── sample.py        # GET /api/sample-data, POST /api/generate-sample
│   │   │   ├── bearing.py       # 베어링 프리셋/파라미터 라우터
│   │   │   ├── model.py         # /api/model/info, /api/model/retrain, /api/predict
│   │   │   ├── health.py        # /api/health
│   │   │   └── _helpers.py      # CSV/.mat 읽기, 윈도우 예측, 공통 process_signal
│   │   ├── core/                # 도메인 로직 (FastAPI 미사용)
│   │   │   ├── bearing_calculations.py  # BPFO/BPFI/BSF/FTF 이론식
│   │   │   ├── bearing_presets.py       # SKF-6205, MFPT-NICE
│   │   │   ├── data_acquisition.py      # 합성 신호 생성
│   │   │   ├── fault_classifier.py      # BearingFaultClassifier (RF)
│   │   │   ├── feature_extraction.py    # 시간/주파수/웨이블릿 특징
│   │   │   ├── mat_loader.py            # MFPT-style .mat 파서
│   │   │   └── spectral_analysis.py     # FFT, 결함 주파수 검출
│   │   └── schemas/             # Pydantic v2 요청/응답
│   ├── scripts/train_mfpt.py    # 데이터셋 재학습 CLI
│   ├── tests/                   # pytest
│   ├── models/                  # 학습된 .pkl (gitignored)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # ReactDOM, QueryClientProvider
│   │   ├── App.tsx              # Tab 라우팅, 모델 상태 칩, ModelDialog
│   │   ├── api/                 # OpenAPI 자동 생성 + 친화적 별칭
│   │   ├── lib/api.ts           # fetch 래퍼 (ApiError, JSON/FormData 분기)
│   │   ├── components/          # Card, Modal, charts/*
│   │   └── features/
│   │       ├── analyze/         # 파일 분석 화면
│   │       ├── generate/        # 합성 신호 화면
│   │       └── model/           # 모델 패널 다이얼로그
│   ├── e2e/                     # Playwright 시나리오
│   └── vite.config.ts
│
└── docs/                        # 본 문서
```

---

## 3. 백엔드 레이어

```
HTTP 어댑터 (app/api/*)        ─→   얇은 컨트롤러, 입력 검증, 응답 직렬화만 담당
        │
        ▼
공유 헬퍼 (app/api/_helpers)    ─→   CSV/.mat 파싱, 윈도우 슬라이딩 예측, process_signal
        │
        ▼
도메인 코어 (app/core/*)        ─→   순수 numpy/scikit-learn 로직 (FastAPI 의존 X)
        │
        ▼
프로세스 상태 (app/state)       ─→   AppState 싱글턴, classifier · preset · RLock
        │
        ▼
영속화 (BearingFaultClassifier.save/load)  ─→   pickle 직렬화 → MODEL_PATH
```

### 핵심 컴포넌트

| 레이어 | 모듈 | 책임 |
|---|---|---|
| 진입점 | `app/main.py` | FastAPI 인스턴스, `lifespan` 훅에서 `state.bootstrap_classifier()` 호출, CORS, `StarletteHTTPException` 핸들러 등록 |
| 설정 | `app/settings.py` | `MODEL_PATH`, `MAX_UPLOAD_BYTES`, `CORS_ORIGINS` 등을 env에서 읽는 frozen dataclass |
| 상태 | `app/state.py` | `AppState` — `BearingFaultClassifier`, `current_preset`, `default_bearing_params`, `RLock` |
| DI | `app/deps.py` | `get_state()`, `get_classifier()` — 테스트에서 의존성 오버라이드 가능 |
| 라우터 | `app/api/*` | 각 라우터가 `Depends(get_state)`로 상태를 받음 |
| 도메인 | `app/core/*` | numpy/scipy/sklearn 함수 — 어떤 웹 프레임워크에도 묶이지 않음 |
| 스키마 | `app/schemas/*` | Pydantic v2 모델로 OpenAPI 자동 생성 |

### 분류기 (`BearingFaultClassifier`)

- `RandomForestClassifier(n_estimators=100, class_weight='balanced')` + `LabelEncoder`
- 32차원 피처 벡터 (시간 14 + 주파수 18: BPFO/BPFI/BSF/FTF 각 3 고조파 에너지 + 6개 스펙트럼 통계)
- `train(...)` 합성 데이터 학습 / `train_from_dataset(...)` MFPT 데이터셋 윈도우 학습 (진폭 augmentation 지원)
- `save/load` 시 `model`, `label_encoder`, `source`, `feature_keys_*` 함께 pickle
- `source` 필드로 `"synthetic"` / `"dataset:<path> aug=N"` 추적

### 신호 처리 파이프라인 (`_helpers.process_signal`)

```
업로드 신호 (CSV/.mat → numpy 1-D)
        │
        ▼
extract_time_domain_features(signal)         ─→  14개 통계 (mean, RMS, kurtosis…)
        │
        ▼
perform_fft(signal, sampling_rate)           ─→  Hanning window + FFT
        │
        ▼
extract_frequency_domain_features(freq, mag, fault_freqs)
        │                                        BPFO/BPFI/BSF/FTF × {1,2,3} 고조파 에너지
        ▼
detect_fault_frequencies(freq, mag, fault_freqs)  ─→  결함 주파수 피크 검출 & 편차
        │
        ▼
classifier.predict(time_features, freq_features)
        │   ※ 신호 길이 ≥ 2 × PREDICT_WINDOW(12000) 일 때
        │     → predict_long_signal: 윈도우 슬라이딩 후 확률 평균
        ▼
{ time_features, freq_features, fault_detection, signal_sample,
  freq_sample, magnitude_sample, prediction }
```

---

## 4. 프론트엔드 레이어

```
main.tsx (QueryClientProvider, StrictMode)
        │
        ▼
App.tsx — 탭 라우팅 (analyze / generate) + ModelStatusChip + ModelDialog
        │
        ├─▶ features/analyze/AnalyzePage.tsx
        │     ├─ UploadDropzone     (drag&drop)
        │     ├─ useAnalyze         (TanStack Query mutation → POST /api/analyze)
        │     └─ AnalysisResultView (SignalChart, SpectrumChart, FeatureGrid, FaultFreqTable, PredictionCard)
        │
        ├─▶ features/generate/GeneratePage.tsx
        │     ├─ useGenerateSample  (POST /api/generate-sample)
        │     └─ AnalysisResultView (analyze 와 동일 컴포넌트 재사용)
        │
        └─▶ features/model/ModelDialog.tsx
              ├─ useModelInfo       (GET /api/model/info)
              ├─ useBearingPresets  (GET /api/bearing-presets)
              ├─ useApplyPreset     (POST /api/bearing-presets/{name})
              └─ useRetrain         (POST /api/model/retrain)
```

### 주요 결정

- **데이터 페칭**: TanStack Query — `staleTime: 30s`, `retry: 1`, `refetchOnWindowFocus: false`. 변형(mutation) 성공 시 `invalidateQueries`로 모델 상태/프리셋 캐시 무효화.
- **타입 안전성**: 백엔드 OpenAPI → `pnpm gen:api` → `src/api/schema.d.ts` 자동 생성. `src/api/types.ts`가 친화적 별칭을 export.
- **에러 경계**: `ApiError`로 HTTP 응답 본문(`{error: ...}`)을 보존해 UI에서 사람이 읽을 수 있는 메시지로 표시.
- **차트**: `plotly.js-cartesian-dist-min` 만 번들에 포함해 용량 절감.
- **개발 프록시**: Vite `server.proxy['/api'] = http://localhost:8000` — 운영 시 `VITE_API_URL` 또는 동일 origin 배포.

---

## 5. 핵심 데이터 흐름

### 5-1. 파일 업로드 분석 흐름 (Analyze)

```
사용자 (drag&drop .csv/.mat)
        │
        ▼ multipart/form-data
[UploadDropzone] → useAnalyze.mutate → POST /api/analyze
        │
        ▼
[FastAPI router: analyze.py]
   read_uploaded_signal(file, ...)
        ├─ .csv  : read_csv_signal() → numpy 1-D
        └─ .mat  : load_mat_signal() → MFPT bearing struct 파싱 (sr/rpm 자동 추출)
        │
   calculate_bearing_frequencies(rpm, preset_params)
        │
   process_signal(signal, sr, fault_freqs, classifier)
        │   (시간 특징 + FFT + 주파수 특징 + 결함 검출 + 윈도우 예측)
        ▼
AnalyzeResponse (Pydantic)
        │
        ▼ JSON
[AnalysisResultView] — Plotly 시간/스펙트럼 차트, FeatureGrid, FaultFreqTable, PredictionCard
```

### 5-2. 모델 재학습 흐름 (Retrain)

```
[ModelDialog] → useRetrain.mutate({ mode, dataset_dir?, save, … })
        │
        ▼ JSON
POST /api/model/retrain
   ├─ mode='synthetic' → new_clf.train(bearing_params, rpm, sr)
   └─ mode='dataset'   → new_clf.train_from_dataset(dir, window, hop, amplitude_augment, …)
        │
   with state.lock:  state.classifier = new_clf
   if body.save:     new_clf.save(settings.model_path)
        │
        ▼
RetrainResponse { source, trained_classes, n_files?, n_windows?, class_counts?, saved_to? }
        │
        ▼
useRetrain.onSuccess → invalidateQueries(['model','info']) → 헤더 칩 즉시 갱신
```

### 5-3. 시작(부트스트랩) 흐름

```
uvicorn 실행
        │
        ▼
FastAPI lifespan 진입
        │
        ▼
state.bootstrap_classifier()
   if exists(MODEL_PATH):
        try   → BearingFaultClassifier.load(path)         # 영속 모델 사용
        except → 합성 학습으로 fallback
   else:
        classifier.train(default_bearing_params)         # 합성 학습
        │
        ▼
API 서빙 시작 (모델 항상 학습된 상태로 진입 가능)
```

---

## 6. 영속화와 상태

- **클래스 다이어그램 보존 포맷** (pickle):
  ```python
  {
    'model':              RandomForestClassifier,
    'label_encoder':      LabelEncoder,
    'source':             'synthetic' | 'dataset:<path> aug=N',
    'feature_keys_time':  [...],   # 호환성 확인용
    'feature_keys_freq':  [...],
  }
  ```
- **동시성**: `AppState.lock = RLock()`. 재학습/프리셋 교체 시 `with state.lock` 블록 안에서 참조 교체. 라우터는 짧은 임계 영역만 락을 잡고 무거운 학습은 락 바깥에서 수행.
- **싱글 프로세스 가정**: 모듈-수준 싱글턴. 멀티 워커가 필요해지면 외부 스토리지(Redis 등)나 메시지 기반 모델 갱신 패턴으로 전환 필요.

---

## 7. 환경 변수와 설정

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MODEL_PATH` | `models/classifier.pkl` | 학습된 분류기의 영속화 경로 |
| `MAX_UPLOAD_BYTES` | `67108864` (64 MiB) | 업로드 최대 크기 (요청 검증) |
| `CORS_ORIGINS` | `http://localhost:5173` | 허용 도메인 (콤마 구분) |
| `VITE_API_URL` | (없음) | 프론트엔드 빌드/개발 시 API 베이스. 미설정 시 동일 origin 또는 dev 프록시 사용 |

---

## 8. 보안과 입력 검증

- 업로드 확장자 화이트리스트: `.csv`, `.mat` 만 허용 (`_helpers.read_uploaded_signal`).
- Pydantic v2가 모든 요청 본문/응답을 검증하고 OpenAPI 스키마를 자동 생성.
- `BearingParams`는 `gt=0` 제약으로 0/음수 값을 차단.
- CORS는 화이트리스트 origin 만 허용.
- `.mat` 파싱은 신뢰할 수 없는 입력 가능성이 있으므로 `try/except` + 명시적 `HTTPException(400)` 응답.

---

## 9. 테스트 전략

- **단위 테스트** (`backend/tests/`): 도메인 코어 함수(특징 추출, FFT, 결함 주파수 계산, MFPT 라벨링)를 직접 호출.
- **API 라우트 테스트**: FastAPI `TestClient` + 픽스처로 `AppState`를 매번 새로 만들어 격리.
- **분류기 영속성 테스트**: `save → 다른 인스턴스에서 load → 동일 예측` 라운드트립 검증.
- **E2E** (`frontend/e2e/verify-analyze.mjs`): Playwright Chromium으로 실제 분석/생성 플로우 + 모델 다이얼로그 시나리오 검증.

---

## 10. 확장 포인트

| 요구 | 현재 위치 | 확장 방법 |
|---|---|---|
| 새 베어링 프리셋 추가 | `core/bearing_presets.py:BEARING_PRESETS` | dict에 항목 추가 후 테스트 |
| 새 특징(feature) | `core/feature_extraction.py` + `FEATURE_KEYS_*` | 추출 함수 추가 → 분류기 `FEATURE_KEYS_*` 업데이트 → 재학습 필요 |
| 다른 분류기 알고리즘 | `core/fault_classifier.py:BearingFaultClassifier` | 동일 `predict/train/save/load` 인터페이스로 교체 |
| 새 데이터셋 포맷 | `core/mat_loader.py` 와 `_helpers.read_uploaded_signal` | 확장자 분기 + 로더 함수 추가 |
| 멀티 워커 배포 | `app/state.py` | 외부 스토리지 + 모델 갱신 이벤트 버스로 교체 |

---

## 11. 기술 스택 요약

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.10 · FastAPI 0.116 · Uvicorn · Pydantic v2 · scikit-learn · scipy · numpy · pandas |
| 프론트엔드 | Node 18 · pnpm 9 · React 18 · Vite 5 · TypeScript 5.6 · Tailwind 3.4 · TanStack Query 5 · Plotly.js |
| 데이터 포맷 | CSV, MATLAB v5 (`.mat`, MFPT bearing struct) |
| 테스트 | pytest 68+ · Playwright (Chromium) |
| 직렬화 | pickle (모델 영속화), OpenAPI 3 (API 계약) |
| 베어링 프리셋 | SKF-6205 (CWRU), MFPT-NICE |

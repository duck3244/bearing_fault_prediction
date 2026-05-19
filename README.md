# 베어링 결함 예측 시스템 (Bearing Fault Prediction)

진동 신호로부터 시간/주파수 도메인 특징을 추출하고, RandomForest 분류기로 베어링 결함 유형 — **정상 · 외륜(BPFO) · 내륜(BPFI) · 볼(BSF) · 케이지(FTF)** — 을 예측하는 풀스택 웹 애플리케이션입니다. CSV 와 MFPT 스타일 `.mat` 파일을 모두 지원하며, 합성 신호 생성 / 모델 재학습 / 프리셋 전환을 한 화면에서 다룰 수 있습니다.

![demo](demo.png)

---

## 빠른 시작

```bash
# 1) 백엔드 (터미널 1)
conda activate py310_pt
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2) 프론트엔드 (터미널 2)
cd frontend
pnpm install
pnpm dev                # http://localhost:5173 (Vite proxy → :8000)
```

- UI: <http://localhost:5173>
- OpenAPI 인터랙티브 문서: <http://localhost:8000/docs>

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.10 · FastAPI 0.116 · Uvicorn · Pydantic v2 · scikit-learn · scipy · numpy · pandas |
| 프론트엔드 | Node 18 · pnpm 9 · React 18 · Vite 5 · TypeScript 5.6 · Tailwind 3.4 · TanStack Query 5 · Plotly.js |
| 데이터 포맷 | CSV, MATLAB v5 `.mat` (MFPT `bearing.gs/sr/rate` 구조체) |
| 베어링 프리셋 | SKF-6205 (CWRU 드라이브 엔드), MFPT-NICE |
| 테스트 | pytest (68+ 케이스) · Playwright (Chromium) |

---

## 주요 기능

- **파일 업로드 분석** (`.csv` / `.mat`): 시간 도메인 특징, FFT 스펙트럼, 결함 주파수(BPFO/BPFI/BSF/FTF) 검출, ML 예측을 한 화면에서 확인. `.mat` 은 샘플레이트/RPM 메타데이터를 자동 추출합니다.
- **합성 신호 탐색**: 결함 유형, RPM, 샘플레이트, 노이즈 레벨 조합으로 합성 진동 신호를 생성한 뒤 업로드와 동일한 파이프라인으로 분석.
- **모델 패널**: 헤더의 모델 상태 칩을 클릭해 모달에서 현재 분류기 상태(소스/학습 클래스/영속 경로), 베어링 프리셋 전환, 합성/데이터셋 재학습, 그리고 `MODEL_PATH` 로의 영속화를 한 곳에서 처리.
- **현장 데이터 재학습**: MFPT 같은 실측 `.mat` 데이터셋으로 분류기를 학습 (`scripts/train_mfpt.py` CLI 또는 `/api/model/retrain`).
- **윈도우 단위 예측**: 학습 윈도우(12,000 샘플)보다 긴 신호는 자동으로 윈도우 슬라이딩(hop 6,000) 후 확률 평균으로 안정적으로 예측.

---

## 프로젝트 구조

```
bearing_fault_prediction/
├── backend/                       # FastAPI 서비스
│   ├── app/
│   │   ├── main.py                # FastAPI 인스턴스, lifespan, CORS
│   │   ├── settings.py            # 환경변수 기반 frozen-dataclass 설정
│   │   ├── state.py               # AppState (분류기, 프리셋, RLock)
│   │   ├── deps.py                # FastAPI Depends 헬퍼 (get_state/get_classifier)
│   │   ├── api/                   # 라우터 (analyze · sample · bearing · model · health)
│   │   ├── core/                  # 도메인 로직 (FastAPI 미사용)
│   │   │   ├── bearing_calculations.py
│   │   │   ├── bearing_presets.py
│   │   │   ├── data_acquisition.py
│   │   │   ├── fault_classifier.py
│   │   │   ├── feature_extraction.py
│   │   │   ├── mat_loader.py
│   │   │   └── spectral_analysis.py
│   │   └── schemas/               # Pydantic v2 요청/응답 모델
│   ├── scripts/train_mfpt.py      # MFPT 재학습 CLI
│   ├── tests/                     # pytest
│   ├── models/                    # 영속화된 .pkl (gitignored)
│   └── requirements.txt
│
├── frontend/                      # React SPA
│   ├── src/
│   │   ├── api/                   # OpenAPI 자동 생성 + 친화적 별칭
│   │   ├── lib/api.ts             # fetch 래퍼 + ApiError
│   │   ├── components/            # Card, Modal, charts/
│   │   ├── features/
│   │   │   ├── analyze/           # 파일 분석 플로우
│   │   │   ├── generate/          # 합성 신호 플로우
│   │   │   └── model/             # 모델 패널 다이얼로그
│   │   └── App.tsx
│   ├── e2e/                       # Playwright 검증 스크립트
│   └── package.json
│
└── docs/                          # 아키텍처 / UML 문서
    ├── ARCHITECTURE.md
    └── UML.md
```

---

## 요구 사항

- Python **3.10** (검증 환경: miniconda `py310_pt`)
- Node **18.20+** · pnpm **9** (corepack 권장)
- 선택: Playwright용 Chromium (`pnpm exec playwright install chromium`)

---

## 설치 및 실행

### 백엔드

```bash
conda activate py310_pt
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> 첫 실행 시 `MODEL_PATH` 위치에 `.pkl` 이 없으면 합성 데이터로 자동 학습합니다. 학습된 모델은 다음 부팅에서 자동 로드됩니다.

#### 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MODEL_PATH` | `models/classifier.pkl` | 분류기 영속화 경로 |
| `MAX_UPLOAD_BYTES` | `67108864` (64 MiB) | 업로드 최대 크기 |
| `CORS_ORIGINS` | `http://localhost:5173` | 허용 도메인 (콤마 구분) |

### 프론트엔드

```bash
cd frontend
pnpm install
pnpm dev                # http://localhost:5173
```

| 스크립트 | 설명 |
|---|---|
| `pnpm dev` | Vite 개발 서버 (proxy `/api` → `:8000`) |
| `pnpm build` | `tsc -b` + `vite build` |
| `pnpm lint` | ESLint |
| `pnpm typecheck` | `tsc -b --noEmit` |
| `pnpm format` | Prettier write |
| `pnpm gen:api` | OpenAPI → `src/api/schema.d.ts` 재생성 (백엔드 동작 중 필요) |

운영 빌드 시 백엔드 URL이 다른 origin 이라면 `VITE_API_URL` 을 설정합니다.

### 테스트

```bash
# 백엔드 단위/통합 테스트
cd backend && pytest -q

# 프론트엔드 E2E (실측 MFPT 데이터로 두 플로우 + 모델 다이얼로그 검증)
cd frontend && node e2e/verify-analyze.mjs
```

---

## MFPT 데이터셋으로 재학습

### CLI

```bash
cd backend
python scripts/train_mfpt.py /path/to/MFPT_Dataset/train \
    --test-dir /path/to/MFPT_Dataset/test \
    --out models/classifier.pkl \
    --augment 4
```

`--augment 4` 는 각 윈도우를 4 배로 진폭 augmentation 해, 데이터셋 내 클래스 간 신호 크기 차이에 의한 shortcut learning 을 억제합니다. 학습 결과는 다음 서버 부팅 시 자동 로드됩니다.

### UI에서 재학습

헤더 우측 **모델 상태 칩** → 모달 → **Dataset** 모드 선택 → `dataset_dir` 입력 → `Persist to MODEL_PATH on success` 체크(선택) → **Retrain**.

---

## API 엔드포인트

| 메서드 / 경로 | 설명 |
|---|---|
| `GET  /api/health` | 헬스체크 |
| `POST /api/analyze` | `.csv` / `.mat` 업로드 → 시간·주파수 특징, 결함 주파수 검출, 예측 |
| `GET  /api/sample-data?rpm=...` | 모든 결함 유형의 합성 데이터를 한 번에 |
| `POST /api/generate-sample` | 단일 결함 유형 합성 (RPM/노이즈/샘플수/SR 조절) |
| `GET  /api/bearing-presets` | 사용 가능한 베어링 프리셋 + 현재값 |
| `POST /api/bearing-presets/{name}` | 프리셋 적용 |
| `POST /api/bearing-params` | 베어링 사양 수동 변경 |
| `GET  /api/model/info` | 현재 분류기 상태 (source/classes/persisted) |
| `POST /api/model/retrain` | 재학습 (`mode: synthetic \| dataset`, `save: bool`) |
| `POST /api/predict` | 사전 추출된 피처 dict 로 직접 예측 |

전체 OpenAPI 스키마는 백엔드 동작 중 <http://localhost:8000/openapi.json> 또는 <http://localhost:8000/docs> 에서 확인할 수 있습니다.

---

## 아키텍처 문서

설계 / 데이터 흐름 / UML 다이어그램은 `docs/` 폴더를 참고하세요.

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 시스템 토폴로지, 백엔드 레이어, 신호 처리 파이프라인, 영속화·동시성, 환경 변수, 확장 포인트
- [`docs/UML.md`](docs/UML.md) — Use Case · Component · Class · Sequence (Analyze / Retrain / Bootstrap) · State · ER 다이어그램 (Mermaid)

---

## 지원하는 베어링 결함 유형

| 클래스 | 한글 | 약자 | 설명 |
|---|---|---|---|
| `normal` | 정상 | — | 결함 없음 |
| `outer_fault` | 외륜 결함 | **BPFO** | Ball Pass Frequency Outer race |
| `inner_fault` | 내륜 결함 | **BPFI** | Ball Pass Frequency Inner race |
| `ball_fault` | 볼 결함 | **BSF** | Ball Spin Frequency |
| `cage_fault` | 케이지 결함 | **FTF** | Fundamental Train Frequency |

이론 결함 주파수는 `core/bearing_calculations.py:calculate_bearing_frequencies` 가 RPM 과 베어링 기하학(볼 지름 / 피치 지름 / 볼 수 / 접촉각)으로부터 계산합니다.

---

## 라이선스

MIT. 자세한 내용은 [`LICENSE`](LICENSE) 를 참고하세요.

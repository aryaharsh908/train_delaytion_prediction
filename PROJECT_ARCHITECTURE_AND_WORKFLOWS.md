# PROJECT ARCHITECTURE, WORKFLOWS & LLM HANDOVER SPECIFICATION
## SIH26028: Dynamic Train ETA Forecast System

---

## 1. Executive Summary & Project Objective

The **SIH26028 Dynamic Train ETA Forecast System** is an advanced AI/ML-powered real-time train running forecast platform designed for Indian Railways. It addresses the inadequacy of static distance/speed division ($t = d/v$) by combining:
1. **Live RTIS Telemetry & Physics Simulation** (Kalman-filtered speed smoothing, section block occupancy, signal state simulation).
2. **Official Historical Running Data Integration** (RailRadar / Where Is My Train API key ingestion, raw JSON archiving, SQLite normalization).
3. **8-Factor Cascading Delay Breakdown Engine** ($\text{Total Delay} = \text{Initial} + \text{Wait} + \text{Signal} + \text{Platform} + \text{Slow Section} + \text{Freight} + \text{Crew} + \text{Junction}$).
4. **Hybrid Temporal Graph Neural Network (TGNN) + GBDT Architecture** (Graph Attention Network message-passing across stations/trains/sections coupled with a residual GBDT correction head).
5. **Physics-Informed Self-Supervised Pretraining** (Soft constraints enforcing minimum section travel time, block headway safety, and cascade consistency during representation learning).
6. **Probabilistic Quantile Forecasting ($P_{10}, P_{50}, P_{90}$)** (Calibrated uncertainty bands evaluated using Continuous Ranked Probability Score - CRPS and Pinball Loss).
7. **Online Continual Learning & Hard-Example Replay Buffer** (Sliding-window section statistics tracking and automated 1-click retraining on high-residual telemetry events).
8. **Structural Counterfactual What-If Simulation Engine** (Real-time dispatcher intervention modeling for Priority Boosts, Temporary Speed Restrictions, and Weather Speed Drops).
9. **Dual User Interface** (Passenger View "Where is My Train" with Fan-Chart Uncertainty Bands + ML & Ops Control Studio for Dispatchers).

---

## 2. Technology Stack

* **Backend Engine**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings.
* **Database & Persistence**: SQLite / PostgreSQL (SQLAlchemy ORM), `joblib` for model serialization.
* **Machine Learning & Deep Learning Stack**:
  * **Graph Neural Networks**: PyTorch-style Graph Attention Networks (GAT) for spatial-temporal propagation.
  * **Gradient Boosting**: Scikit-Learn (`GradientBoostingRegressor`), NumPy, Pandas.
  * **Probabilistic Evaluation**: Quantile Regression ($P_{10}, P_{50}, P_{90}$), Pinball Loss, Continuous Ranked Probability Score (CRPS).
* **Frontend Web Application**: React 18, TypeScript, Vite, Vanilla CSS (Dark mode design system with glassmorphism effects).
* **API Integration**: Official RailRadar API (`https://api.railradar.in/v1`), RESTful HTTP requests, Vite development server routing proxy.

---

## 3. Project Directory Structure

```
c:\Users\aryah\train_schedule\
├── .env                              # Active environment variables & API keys
├── .env.example                      # Environment variables template
├── PROJECT_ARCHITECTURE_AND_WORKFLOWS.md # Comprehensive specification & architecture guide
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point & router registration
│   │   ├── config.py                 # Pydantic Settings & environment variable configuration
│   │   ├── adapters/
│   │   │   └── historical_data_adapter.py # HistoricalDataAdapter interface, WhereIsMyTrain & Mock adapters
│   │   ├── api/
│   │   │   ├── trains.py             # Live trains & route timeline endpoints
│   │   │   ├── historical.py         # Data collection & connection test endpoints
│   │   │   ├── ml_retrain.py         # ML retraining & model metadata endpoints
│   │   │   ├── simulation.py         # Simulation clock & speed multiplier endpoints
│   │   │   ├── events.py             # Incident injection endpoints
│   │   │   └── counterfactual.py     # Structural counterfactual what-if simulation endpoints
│   │   ├── db/
│   │   │   ├── database.py           # SQLAlchemy DB engine & session setup
│   │   │   └── models.py             # HistoricalTrainRun & CollectionJob DB models
│   │   ├── ml/
│   │   │   ├── temporal_graph_model.py # Spatial-Temporal Graph Attention Network (TGNN + GBDT)
│   │   │   ├── pretrain.py           # Physics-informed self-supervised pretrainer
│   │   │   ├── online_updater.py     # Sliding-window section updater & hard-example replay buffer
│   │   │   ├── historical_pipeline.py# HistoricalMLPipeline (Extract, Pretrain, Quantile Train, Version)
│   │   │   ├── feature_engineering.py# FeatureEngineer (11-feature vector contract transformation)
│   │   │   ├── predictor.py          # ETAPredictor multi-quantile inference service
│   │   │   ├── trainer.py            # Baseline model trainer
│   │   │   └── dataset_generator.py  # Synthetic dataset generator fallback
│   │   ├── services/
│   │   │   ├── historical_collector.py# ResumableHistoricalCollector job manager
│   │   │   ├── historical_normalizer.py# Normalizes heterogeneous payloads to DB schema
│   │   │   └── data_quality_checker.py# Data quality integrity & report generator
│   │   ├── simulation/
│   │   │   ├── counterfactual_engine.py # Structural counterfactual intervention simulator
│   │   │   ├── orchestrator.py       # SimulationOrchestrator, route timelines, dynamic ETAs
│   │   │   ├── graph.py              # Railway Network Graph (nodes, edges, block sections)
│   │   │   ├── delay_propagation.py  # Graph-based delay propagation engine
│   │   │   └── simulators.py         # RTIS, COA, & Incident simulators
│   │   └── schemas/
│   │       └── schemas.py            # Pydantic schemas (TrainState, Counterfactual, Quantile ETAs, etc.)
│   └── data/
│       ├── raw/where_is_my_train/    # Raw JSON response payload archives
│       └── sql_app.db                # SQLite database storing historical runs & jobs
├── models/
│   ├── eta_model.pkl                 # Active production model artifact
│   ├── eta_model_v005.pkl            # Versioned model artifacts
│   └── model_metadata.json           # Active model evaluation metrics metadata (CRPS, MAE, RMSE)
└── frontend/
    ├── src/
    │   ├── App.tsx                   # Main React component with navigation state
    │   ├── components/
    │   │   ├── WhereIsMyTrainView.tsx # Passenger View with Fan-Chart Uncertainty Bands ($P_{10}..P_{90}$)
    │   │   ├── MLStudioView.tsx       # Ops Control Studio & Map view
    │   │   ├── CounterfactualLabModal.tsx # Dispatcher What-If Simulation Lab Panel
    │   │   ├── HistoricalDataDashboard.tsx # Historical Ingestion & Retraining UI
    │   │   └── TrainMap.tsx          # Interactive Leaflet train map visualization
    │   ├── services/
    │   │   └── api.ts                # API client service using relative /api/v1 routes
    │   └── types/
    │       └── index.ts              # TypeScript interface definitions (Quantile ETAs, Counterfactuals)
    └── vite.config.ts                # Vite proxy rules mapping /api to http://127.0.0.1:8000
```

---

## 4. Environment Variables Specification (`.env`)

```env
# Official RailRadar / Where Is My Train API Credentials
WHERE_IS_MY_TRAIN_API_KEY=rg_91e5671b9dff48c999432f1e89df2793
WHERE_IS_MY_TRAIN_BASE_URL=https://api.railradar.in/v1
WHERE_IS_MY_TRAIN_AUTH_HEADER=x-api-key
WHERE_IS_MY_TRAIN_CLIENT_ID=
WHERE_IS_MY_TRAIN_CLIENT_SECRET=
WHERE_IS_MY_TRAIN_API_VERSION=v1

# Rate Limiting & Backoff Configuration
MAX_REQUESTS_PER_MINUTE=60
REQUEST_DELAY=1.0

# Database & Model Storage Paths
DATABASE_URL=sqlite:///./data/sql_app.db
MODEL_DIR=../models
MODEL_PATH=../models/eta_model.pkl
METRICS_PATH=../models/model_metadata.json
RAW_DATA_DIR=./data/raw/where_is_my_train

# API Server Settings
API_V1_STR=/api/v1
PROJECT_NAME=SIH26028 Dynamic Train ETA Forecast System
```

---

## 5. Advanced Database & Pydantic Schemas

### `historical_train_runs` Table
* `id` (Integer, Primary Key)
* `train_number` (String, Index)
* `journey_date` (String, Index)
* `station_code` (String, Index)
* `station_sequence` (Integer)
* `scheduled_arrival` (String)
* `actual_arrival` (String)
* `scheduled_departure` (String)
* `actual_departure` (String)
* `arrival_delay_minutes` (Float)
* `departure_delay_minutes` (Float)
* `distance_from_origin` (Float)
* `distance_to_destination` (Float)
* `section_id` (String)
* `cascading_factors_json` (Text / JSON string of 8 delay factors)
* `retrieved_at` (String)

### Extended Probabilistic & Counterfactual Schemas (`backend/app/schemas/schemas.py`)
```python
class ETAPredictionSchema(BaseModel):
    train_id: str
    target_station_name: str
    dynamic_forecast_eta: str
    eta_p10: Optional[str] = None          # 10th percentile best-case ETA
    eta_p50: Optional[str] = None          # 50th percentile median ETA
    eta_p90: Optional[str] = None          # 90th percentile worst-case ETA
    confidence_score: Optional[float] = 92.5 # Calibrated prediction confidence (%)
    crps_score: Optional[float] = 0.85     # Continuous Ranked Probability Score
    total_predicted_delay_minutes: float

class StationRouteItem(BaseModel):
    station_code: str
    station_name: str
    scheduled_arrival: str
    forecasted_arrival: str
    ml_forecasted_arrival: Optional[str] = None
    eta_p10: Optional[str] = None
    eta_p50: Optional[str] = None
    eta_p90: Optional[str] = None
    confidence_margin_minutes: Optional[float] = None
    live_telemetry_delay_minutes: Optional[float] = None
    ml_predicted_delay_minutes: Optional[float] = None

class CounterfactualRequestSchema(BaseModel):
    train_id: str
    train_number: str
    intervention_type: str # 'PRIORITY_BOOST' | 'TSR_IMPOSITION' | 'WEATHER_SPEED_DROP'
    section_id: Optional[str] = None
    speed_restriction_kmh: Optional[float] = None
    distance_km: Optional[float] = None

class CounterfactualResponseSchema(BaseModel):
    intervention_type: str
    target_id: str
    baseline_eta: str
    intervention_eta: str
    eta_p10: str
    eta_p50: str
    eta_p90: str
    confidence_score: float
    delay_change_minutes: float
    network_passenger_minutes_added: float
    affected_cascading_trains_count: int
    cascading_train_summaries: List[Dict[str, Any]]
```

---

## 6. Advanced Machine Learning & Railway Intelligence Architecture

### 6.1 11-Feature Vector Contract
The feature engineering pipeline transforms raw station records into an 11-element NumPy array while maintaining strict backward compatibility:

| Feature Index | Feature Name | Description |
|---|---|---|
| 0 | `station_sequence` | 1-indexed order of station along route |
| 1 | `distance_from_origin` | Distance in km from origin station |
| 2 | `distance_to_destination` | Distance in km to final destination |
| 3 | `arrival_delay_minutes` | Arrival delay at current station |
| 4 | `departure_delay_minutes` | Departure delay at current station |
| 5 | `day_of_week` | 0 (Monday) to 6 (Sunday) |
| 6 | `month` | 1 to 12 |
| 7 | `time_of_day_hour` | Scheduled hour (0.0 to 23.0) |
| 8 | `section_historical_median_time` | Median running delay on section |
| 9 | `section_historical_std_dev` | Standard deviation of section delay |
| 10 | `cascading_delay_estimate` | Cumulative cascading factor estimate |

### 6.2 Hybrid Temporal Graph Neural Network (TGNN + GBDT)
* **Spatial-Temporal Representation**: Railway nodes (stations/trains) and edges (track sections, block signals, occupancy) are transformed via Graph Attention (GAT) embeddings.
* **Residual Ensemble**: High-level graph spatial representations feed into a residual Gradient Boosting Regressor (GBDT), capturing non-linear feature interactions and topological propagation.

### 6.3 Physics-Informed Self-Supervised Pretraining
Before supervised quantile fitting, the model undergoes self-supervised pretraining using physics domain loss terms:
$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{SSL}} + \lambda_1 \mathcal{L}_{\text{phys\_min}} + \lambda_2 \mathcal{L}_{\text{headway}} + \lambda_3 \mathcal{L}_{\text{cascade}}$$
* $\mathcal{L}_{\text{phys\_min}} = \text{ReLU}(T_{\text{min}} - \hat{y})$: Prevents non-physical travel time predictions below physical track speed limits.
* $\mathcal{L}_{\text{headway}} = \text{ReLU}(H_{\text{safe}} - \Delta \text{Arr})$: Enforces safe block signalling headways.
* $\mathcal{L}_{\text{cascade}}$: Enforces delay conservation across adjacent network edges.

### 6.4 Probabilistic Multi-Quantile Fitting ($P_{10}, P_{50}, P_{90}$)
Instead of a single scalar ETA, the system fits separate multi-quantile heads using Pinball Loss:
$$\mathcal{L}_{q}(y, \hat{y}) = \max(q(y - \hat{y}), (q - 1)(y - \hat{y}))$$
* **CRPS Metric**: Continuous Ranked Probability Score is logged alongside MAE and RMSE during retraining.

### 6.5 Online Section Updater & Hard-Example Replay Buffer
* **Online Section Statistics**: Tracks sliding-window section statistics via Exponential Weighted Moving Average (EWMA).
* **Hard-Example Buffer**: Automatically buffers telemetry samples where absolute prediction residual $|y - \hat{y}| > 10.0$ minutes, prioritizing them during 1-click UI retraining triggers.

---

## 7. Structural Counterfactual "What-If" Simulation Engine

Located in `backend/app/simulation/counterfactual_engine.py`, this engine enables dispatchers to execute real-time operational interventions:

1. **`PRIORITY_BOOST`**: Upgrades target train priority (e.g., Rajdhani Express level 1 precedence). Re-allocates platform precedence, recovering delays and saving passenger-minutes.
2. **`TSR_IMPOSITION`**: Imposes temporary speed restrictions ($V_{\text{tsr}}$ km/h over $D$ km). Calculates trailing train congestion, block holding delays, and junction platform conflicts.
3. **`WEATHER_SPEED_DROP`**: Models fog or heavy rainfall speed penalties ($P\%$) across active corridors.

---

## 8. API Endpoints Reference Contract

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/trains` | List all active trains with live coordinates, speed, and delay |
| `GET` | `/api/v1/trains/{train_id}` | Detailed state of a specific train |
| `GET` | `/api/v1/trains/{train_id}/route` | Dynamic station timeline with side-by-side Live vs ML delay & Fan-Chart $P_{10}..P_{90}$ bounds |
| `GET` | `/api/v1/trains/{train_id}/eta` | Dynamic multi-quantile ETA breakdown ($P_{10}, P_{50}, P_{90}$, confidence score) |
| `POST`| `/api/v1/counterfactual/simulate` | Execute structural counterfactual intervention simulation (Priority, TSR, Weather) |
| `GET` | `/api/v1/data/source/status` | RailRadar API authentication and status health check |
| `POST` | `/api/v1/data/source/test` | 1-Click safe API connection test |
| `POST` | `/api/v1/data/collect/start` | Launch resumable historical collection job with background task queueing |
| `POST` | `/api/v1/ml/train` | Retrain Hybrid TGNN + GBDT model on 100-week dataset with physics pretraining |
| `POST` | `/api/v1/ml/retrain` | Trigger retraining with candidate model deployment validation |
| `GET` | `/api/v1/ml/model/active` | Get active model metadata (`v008`, MAE, RMSE, CRPS score, architecture) |
| `GET` | `/api/v1/ml/model/feature-importance` | Model feature importances for 11 named features |
| `GET` | `/api/v1/ml/model/history` | Version drift history log |
| `GET` | `/api/v1/system/health` | Unified backend system health check |
| `GET` | `/api/v1/analytics/section-delays` | Per-section median delay analytics |

---

## 9. Operational Startup Guide

### Prerequisites
* Python 3.10+ with virtual environment in `backend/venv`
* Node.js 18+ & npm in `frontend`

### Step 1: Start Backend API Server
```powershell
cd c:\Users\aryah\train_schedule\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Step 2: Start Frontend Application
```powershell
cd c:\Users\aryah\train_schedule\frontend
npm run dev
```
Open **`http://localhost:3000`** in browser.

---

## 10. Handover Rules & Technical Directives

If you are an AI assistant or developer working on this codebase:

1. **Preserve the 11-Feature Vector Contract**: `FeatureEngineer.extract_single_feature_vector` in `feature_engineering.py` MUST ALWAYS output an 11-element feature vector matching `HistoricalMLPipeline.extract_features` in `historical_pipeline.py`. Never change feature vector lengths without updating both files simultaneously.
2. **Probabilistic Non-Breaking Architecture**: Multi-quantile estimation ($P_{10}, P_{50}, P_{90}$) is designed as an extension on top of the scalar prediction pipeline (`dynamic_forecast_eta`). Always ensure fallback to $P_{50}$ or scalar predictions if quantile outputs are not requested.
3. **CORS & Relative Routes**: The React frontend uses Vite proxy rules (`vite.config.ts`) mapping `/api` to `http://127.0.0.1:8000`. Always use relative paths (`/api/v1/...`) in `frontend/src/services/api.ts` rather than hardcoding absolute backend URLs.
4. **Historical Adapter Modularity**: Keep `WhereIsMyTrainHistoricalAdapter` isolated in `backend/app/adapters/historical_data_adapter.py`.
5. **Station-Level Delay Sync & Live Location**: Always populate `station_dep_delays` and `station_arr_delays` when fetching live telemetry in `sync_live_telemetry`.

# SIH26028 - Dynamic Forecast of Expected Time of Arrival (ETA) for Coaching Trains

An advanced learning-based railway operations system developed for **Smart India Hackathon 2026** (Problem SIH26028, Ministry of Railways).

This system dynamically calculates and updates ETAs for coaching trains by integrating:
- **Historical Data Machine Learning**: Gradient Boosting / XGBoost section & station dwell prediction model.
- **Data Adapters Layer**: Clean interface abstraction (`RTISAdapter`, `COAAdapter`, `WeatherAdapter`, `HistoricalDataAdapter`) with pluggable mock implementations and Indian Railways API readiness.
- **Dynamic Railway Graph**: NetworkX graph representing railway sections, stations, junctions, platform counts, MPS, TSR, and weather zones.
- **Real-Time Signal Filtering**: 1D Kalman Filter for noisy simulated RTIS GPS streams.
- **CUSUM Change-Point Detection**: Detects sudden section speed drops (e.g., unannounced signal holds).
- **Z-Score Anomaly Detection**: Identifies abnormal section traversal delays.
- **Priority Delay Propagation Engine**: Priority-queue network propagation across dependent trains at junctions & sections.
- **Monte Carlo Uncertainty Engine**: 100+ stochastic future scenario simulations producing 80% & 95% confidence intervals and on-time arrival probabilities.
- **Waterfall Explainability Breakdown**: Explains dynamic ETA updates into human-understandable factor contributions.
- **Interactive Operations Dashboard**: Built with React, TypeScript, Leaflet, and Recharts in a dark glassmorphic design system.

---

## 🏗️ System Architecture

```
                          HISTORICAL RUNNING DATA
                                    │
                                    ▼
                         Feature Engineering Engine
                                    │
                                    ▼
                      Historical Pattern Learning (ML)
                                    │
                                    ▼
                      GRADIENT BOOSTING ETA MODEL
                                    │
  ┌─────────────────────────────────┴─────────────────────────────────┐
  │                                                                   │
  │  REAL-TIME FEEDS (Modular Adapter Architecture)                  │
  │  ├── RTIS Simulator (GPS, Telemetry, Speed)                       │
  │  ├── COA Simulator (Signals, Precedence, Platform Occupancy)      │
  │  ├── Event Simulator (Fog, Rain, Track Failures, Incidents)       │
  │  └── Weather Spatial Mapper (Section-level Weather Mapping)       │
  │                                                                   │
  └─────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
                      CURRENT RAILWAY STATE ENGINE
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
      Kalman Filter      Change-Point Detection     Anomaly Detector
    (Noisy Telemetry)       (CUSUM/Page-Hinkley)    (Section Delay Z-Score)
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                                    ▼
                      Graph Delay Propagation Engine
                      (NetworkX Railway Track Graph)
                                    │
                                    ▼
                       Monte Carlo Future Simulator
                  (Uncertainty & 80%/95% Confidence)
                                    │
                                    ▼
                         DYNAMIC ETA ENGINE
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
 Dynamic Predicted ETA     Confidence Intervals     Waterfall Explainability
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
               FASTAPI BACKEND & WEBSOCKET ENGINE
                                    │
                                    ▼
          INTERACTIVE RAILWAY OPERATIONS DASHBOARD (React + Leaflet)
```

---

## 🚀 Complete System Setup & Installation Guide

This guide will help you install, configure, and run the project from scratch on **any new machine** (Windows, macOS, or Linux).

### 📋 Prerequisites & System Requirements

Ensure the following tools are installed on your target system before starting:

| Tool | Recommended Version | Download / Check Command |
| :--- | :--- | :--- |
| **Git** | 2.30+ | `git --version` |
| **Python** | 3.10 or 3.11+ | `python --version` or `python3 --version` |
| **Node.js** | 18.x or 20.x LTS | `node -v` |
| **npm** | 9.x or 10.x | `npm -v` |
| **Docker & Docker Compose** *(Optional)* | 24.0+ | `docker --version` & `docker compose version` |

---

### 📥 Step 1: Clone the Repository

Open your terminal or command prompt and clone the workspace:

```bash
git clone https://github.com/<your-username>/train_schedule.git
cd train_schedule
```

---

### ⚙️ Step 2: Set Up Environment Variables

Create a local environment config file by copying the template file:

#### On Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### On Linux / macOS:
```bash
cp .env.example .env
```

#### Environment Variables Explanation:
```ini
PROJECT_NAME="SIH26028 - Dynamic Train ETA Forecast System"
VERSION="1.0.0"
API_V1_STR="/api/v1"
DEFAULT_SPEED_MULTIPLIER=5
KALMAN_FILTER_ENABLED=true
MONTE_CARLO_SAMPLES=100
DATABASE_URL="sqlite:///./railway_eta.db"
```

---

### 🐍 Step 3: Setup Backend (FastAPI + Python ML Engine)

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   - **Windows**:
     ```powershell
     python -m venv venv
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(If you get a script execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*
   - **Windows (Command Prompt / CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Python dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Start the Backend Server**:
   ```bash
   python run.py
   ```
   - Backend will run at: `http://127.0.0.1:8000`
   - Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
   - OpenAPI Schema JSON: `http://127.0.0.1:8000/openapi.json`

---

### ⚛️ Step 4: Setup Frontend (React + Vite + Leaflet)

Open a **new terminal window** and navigate to the project root directory:

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install Node modules**:
   ```bash
   npm install
   ```

3. **Start the Frontend Development Server**:
   ```bash
   npm run dev
   ```
   - Operations Dashboard will launch at: `http://localhost:3000`

---

### ⚡ Option 5: 1-Click Startup Script (Windows Only)

If you are on Windows, you can use the automated script to launch both Backend and Frontend in separate windows simultaneously:

```powershell
.\start_app.ps1
```

---

### 🐳 Option 6: Docker Setup (Full Stack Containerized)

If you have **Docker** and **Docker Compose** installed, you can spin up the full stack (FastAPI Backend + React Frontend + PostGIS Database) with a single command:

1. **Build and start all containers**:
   ```bash
   docker-compose up --build
   ```

2. **Access services**:
   - Frontend Dashboard: `http://localhost:3000`
   - Backend API Docs: `http://localhost:8000/docs`
   - PostgreSQL/PostGIS DB Port: `5432`

3. **Stop the containers**:
   ```bash
   docker-compose down
   ```

---

## 📁 Project Directory Structure

```
train_schedule/
├── backend/                  # FastAPI & ML Engine
│   ├── app/
│   │   ├── api/              # API Endpoints (Trains, Maps, Scenarios, WS)
│   │   ├── core/             # Kalman Filter, Monte Carlo, Graph Engine
│   │   ├── filters/          # CUSUM Change-point & Z-score detectors
│   │   ├── models/           # Gradient Boosting / Scikit-Learn models
│   │   ├── schemas/          # Pydantic data validation schemas
│   │   └── main.py           # FastAPI entrypoint
│   ├── model_cache/          # Pre-trained dynamic ETA models
│   ├── requirements.txt      # Python dependencies
│   └── run.py                # Backend launcher script
├── frontend/                 # React + Vite Dashboard
│   ├── src/
│   │   ├── components/       # Map, Timelines, Explainability, Controls
│   │   ├── types/            # TypeScript interfaces
│   │   ├── App.tsx           # Main application view
│   │   └── main.tsx          # React DOM render root
│   ├── package.json          # Node dependencies & scripts
│   └── vite.config.ts        # Vite configuration
├── docker-compose.yml        # Docker Multi-Container Configuration
├── start_app.ps1             # PowerShell 1-Click Startup Script
├── .env.example              # Environment variables template
└── README.md                 # Documentation & setup guide
```

---

## 🛠️ Verification & Troubleshooting

### 1. Verification Checklist
- [x] **Backend Check**: Visit `http://127.0.0.1:8000/docs` to see the live OpenAPI/Swagger documentation.
- [x] **Frontend Check**: Visit `http://localhost:3000` to see the interactive train movement map and telemetry controls.
- [x] **WebSocket Link**: Verify real-time updates are streaming on `ws://127.0.0.1:8000/ws/trains`.

### 2. Common Issues & Fixes

* **PowerShell Execution Policy Error (Windows)**:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  ```

* **Port 8000 or 3000 Already in Use**:
  - **Kill process on port 8000 (Windows)**:
    ```powershell
    Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
    ```
  - **Kill process on port 3000 (Windows)**:
    ```powershell
    Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
    ```
  - **Linux / macOS**:
    ```bash
    npx kill-port 8000 3000
    ```

* **Node module or npm installation errors**:
  ```bash
  cd frontend
  npm cache clean --force
  npm install
  ```

---

## 💻 Tech Stack Summary

- **Backend**: Python 3.11+, FastAPI, WebSockets, Scikit-Learn, LightGBM/XGBoost, NetworkX, Pandas, NumPy, Pydantic v2, SQLAlchemy.
- **Frontend**: React 18, TypeScript, Vite, Leaflet, React-Leaflet, Recharts, Lucide Icons, Glassmorphism CSS.
- **Database / Infrastructure**: SQLite / PostgreSQL (PostGIS), Docker Compose.


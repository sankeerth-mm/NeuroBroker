# NeuroBroker System Architecture

NeuroBroker is an end-to-end, resource-aware centralized compute brokerage engine designed for volunteer distributed deep learning training.

---

## 1. High-Level Architecture

```text
                               ┌─────────────────────────┐
                               │       USER / ADMIN      │
                               │                         │
                               │ React Web Dashboard     │
                               │ Upload Model Package    │
                               │ Upload Dataset          │
                               │ Configure Training      │
                               │ Monitor Telemetry       │
                               │ Download .pth Weights   │
                               └────────────┬────────────┘
                                            │
                                            │ HTTPS / WebSocket
                                            ▼
              ┌────────────────────────────────────────────────────────────┐
              │                     NEUROBROKER SERVER                     │
              │                                                            │
              │ FastAPI + SQLAlchemy + WebSockets + Uvicorn                │
              │                                                            │
              │ ┌────────────────────────────────────────────────────────┐ │
              │ │ Authentication (JWT + Bcrypt RBAC)                     │ │
              │ │ Job State Machine & Orchestrator                       │ │
              │ │ Dataset Manager & Stratified Partitioner               │ │
              │ │ Model Package & Versioning Manager                     │ │
              │ │ Volunteer Fleet & Telemetry Watchdog                   │ │
              │ │ Multi-Objective Resource-Aware Scheduler               │ │
              │ │ Network-Aware Transfer Time Estimator                  │ │
              │ │ Dynamic Trust & Reliability Tracker                    │ │
              │ │ Fairness & Worker Contribution Balancer                │ │
              │ │ Anomaly & Hardware Degradation Detector                │ │
              │ │ Pluggable DRL / Hybrid Scheduler                       │ │
              │ │ State Dict Validator (NaN/Inf & Shape Guard)           │ │
              │ │ Weighted FedAvg Aggregation Engine                     │ │
              │ │ Fault Tolerance & Dropout Recovery Manager             │ │
              │ │ Checkpointing & State Restoration                      │ │
              │ │ Explainability & Audit Log Engine                      │ │
              │ └────────────────────────────────────────────────────────┘ │
              │                                                            │
              │ PostgreSQL / SQLite + Local Storage File Tree              │
              └──────────────┬─────────────┬─────────────┬─────────────────┘
                             │             │             │
                      HTTPS / WS           │             │
                             │             │             │
              ┌──────────────▼──┐   ┌──────▼──────┐   ┌──▼──────────────┐
              │ Volunteer Node  │   │Volunteer Node│   │ Volunteer Node  │
              │ NODE-01 (GPU)   │   │NODE-02 (GPU)│   │ NODE-03 (GPU)   │
              │ RTX 4090        │   │RTX 3060     │   │ GTX 1650        │
              │ 64 GB RAM       │   │16 GB RAM    │   │ 8 GB RAM        │
              │ Local PyTorch   │   │Local PyTorch│   │ Local PyTorch   │
              └─────────────────┘   └─────────────┘   └─────────────────┘
                             │                           │
              ┌──────────────▼──┐                 ┌──────▼──────────────┐
              │ Volunteer Node  │                 │ Volunteer Node      │
              │ NODE-04 (CPU)   │                 │ NODE-05 (GPU)       │
              │ Intel i5 CPU    │                 │ RTX 2060            │
              │ 8 GB RAM        │                 │ 16 GB RAM           │
              │ Local PyTorch   │                 │ Local PyTorch       │
              └─────────────────┘                 └─────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Central Broker Server (`backend/app/`)
* **`api/`**: REST endpoints for authentication, volunteer management, datasets, models, training jobs, and administrative inspection.
* **`ws/`**: High-performance WebSocket hubs for bi-directional worker communication and real-time dashboard updates.
* **`scheduler/`**: Multi-objective decision engine that scores available volunteer nodes and allocates data chunks based on live telemetry.
* **`partitioning/`**: Stratified partitioning engine for image folders and CSV datasets ensuring per-class representation.
* **`aggregation/`**: Mathematically exact Weighted FedAvg engine with strict tensor shape, key, and NaN/Inf validation.
* **`fault_tolerance/`**: Dropout recovery manager and versioned checkpoint system for crash resilience.

### 2.2 Volunteer Node Client (`volunteer_node/`)
* **`main.py`**: CLI entrypoint (`python main.py --server <URL> --token <TOKEN>`).
* **`resource_monitor.py`**: Hardware discovery and 5-second periodic telemetry heartbeats.
* **`benchmark.py`**: Startup compute, memory, and matrix multiplication micro-benchmark.
* **`task_manager.py`**: Coordinates artifact downloads, sandbox execution, and update uploads.
* **`trainer.py`**: Executes real PyTorch local epochs with SGD/Adam and CrossEntropyLoss on GPU (CUDA/MPS) or CPU.
* **`security.py`**: Ensures sandbox isolation and prevents directory traversal outside the task directory.

### 2.3 Web Dashboard (`frontend/`)
* Built with React, Vite, Lucide Icons, and Recharts.
* Provides live KPI metric cards, interactive convergence graphs, volunteer fleet telemetry cards, explainable scheduler breakdowns, and 1-click model weight downloads.

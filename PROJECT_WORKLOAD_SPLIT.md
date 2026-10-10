# NeuroBroker: Project Workload & Contribution Breakdown (4 Members)

**Project Title:** NeuroBroker — Distributed Heterogeneous Deep Learning Orchestration Framework  
**Team Size:** 4 Members  

---

## 👥 Executive Summary of Member Responsibilities

```
+-----------------------------------------------------------------------------------+
|                                  NEUROBROKER                                      |
+-------------------+-------------------+-------------------+-----------------------+
|  MEMBER 1 (25%)   |  MEMBER 2 (25%)   |  MEMBER 3 (25%)   |   MEMBER 4 (25%)      |
| Core Broker API,  | Volunteer Client, | Dynamic Scheduler,| Frontend Dashboard,   |
| DB Models & Auth  | Local Trainer &   | Stratified Data   | WebSockets & Fault    |
| Security          | Hardware Profiler | Partitioner & FL  | Tolerance Watchdog    |
|                   |                   | Weight Aggregation|                       |
+-------------------+-------------------+-------------------+-----------------------+
```

---

## 📄 Member 1: Core Broker Backend, Database Schema & Authentication System
**Primary Focus:** Central Broker System Architecture, REST APIs, Database Management & Security

### Key Modules & Responsibilities:
1. **Central FastAPI Broker Architecture (`backend/app/main.py`)**:
   - Designed the REST API gateway connecting model owners, administrators, and volunteer worker nodes.
   - Built asynchronous database connection lifecycle and lifecycle initialization routines.
2. **Database Models & ORM Schema (`backend/app/models/`)**:
   - Engineered SQLAlchemy ORM schemas for `User`, `TrainingJob`, `TrainingTask`, `ModelPackage`, `Dataset`, and `VolunteerNode`.
   - Designed relational mappings for multi-round job checkpoints, weight file storage paths, and evaluation metrics.
3. **Authentication & Authorization (`backend/app/security/` & `backend/app/auth/`)**:
   - Implemented JWT token generation and validation for registered platform users.
   - Created volunteer node authentication tokens (`X-Volunteer-Token`) to verify volunteer registrations securely.
4. **Model Package & Dataset Management Services (`backend/app/api/models.py`, `backend/app/api/datasets.py`)**:
   - Built model archive inspector (`inspect_model_package`) to extract PyTorch architecture declarations dynamically.
   - Designed checksum verification routines (SHA-256) for dataset uploads and global `.pth` model downloads.

---

## 💻 Member 2: Volunteer Node Engine, Execution Sandbox & Hardware Monitoring
**Primary Focus:** Volunteer Edge Node Client, Hardware Micro-Benchmarking, Local Trainer & DataLoader

### Key Modules & Responsibilities:
1. **Volunteer Client Daemon (`volunteer_node/node_client.py` & `volunteer_node/main.py`)**:
   - Developed the lightweight Python client daemon running on volunteer desktop/laptop nodes.
   - Built automatic HTTP/WebSocket re-connection logic, exponential backoff retries, and task polling fallbacks.
2. **Hardware Micro-Benchmarking Engine (`volunteer_node/hardware_monitor.py`)**:
   - Implemented real-time system hardware profiling (CPU core counts, RAM availability, GPU VRAM & FLOPS scoring).
   - Designed the composite **Capability Score** formula ($0.0 - 10.0$) sent during node registration to inform scheduling decisions.
3. **Local PyTorch Trainer & DataLoader Pipeline (`volunteer_node/trainer.py`, `volunteer_node/dataset_loader.py`)**:
   - Created `LocalTrainer` to execute PyTorch local training epochs over heterogeneous CPU, CUDA, and Apple Silicon MPS devices.
   - Designed `variable_length_collate_fn` and `NumpyFeatureDataset` to dynamically handle 1D/2D audio spectrograms, MFCC features, and tabular matrices without shape stack mismatches.
4. **Code Sandboxing & Security Verification (`volunteer_node/security.py`)**:
   - Built AST-based security parser to inspect user-submitted model code and restrict hazardous imports (`os.system`, `subprocess`, `socket`).

---

## 🧠 Member 3: Resource-Aware Scheduler, Dataset Partitioner & Weight Aggregation
**Primary Focus:** Scheduling Algorithms, Data Partitioning, Federated Averaging & Anomaly Detection

### Key Modules & Responsibilities:
1. **Resource-Aware Task Scheduler (`backend/app/scheduler/`)**:
   - Formulated the hybrid multi-criteria scheduling algorithm combining hardware capability scores, historical reliability, network latency penalties, and fairness disparity factors.
   - Implemented dynamic node allocation algorithms (`calculate_data_allocations`) to balance workloads proportionally across fast and slow nodes.
2. **Stratified Dataset Partitioner (`backend/app/partitioning/stratified.py`)**:
   - Developed multi-format dataset partitioning engine for CSV tabular datasets, image directory trees, and `.npy` feature arrays.
   - Built row-level array partitioning (`partition_npy_dataset`) ensuring 100% data utilization without class imbalance or sample drop-off.
3. **Federated Weight Aggregation Engine (`backend/app/aggregation/fedavg.py`)**:
   - Implemented weighted `FedAvg` (Federated Averaging) algorithm to aggregate local PyTorch state dicts based on verified sample counts.
   - Built `UpdateValidator` ([`update_validator.py`](file:///Users/sankeerth/Documents/NeuroBroker/backend/app/aggregation/update_validator.py)) to verify SHA-256 checksums, tensor shape sanity, and prevent gradient corruption.
4. **Node Reliability & Anomaly Detector (`backend/app/monitoring/anomaly_detector.py`)**:
   - Developed anomaly scoring logic to flag nodes exhibiting CPU/RAM spikes, unhandled exceptions, or toxic weight updates.

---

## 🎨 Member 4: Real-Time Web Dashboard, WebSockets & Fault-Tolerance Watchdog
**Primary Focus:** User Interface & UX, Live WebSockets, Job Orchestration & Heartbeat Watchdog

### Key Modules & Responsibilities:
1. **Frontend Web Dashboard (`frontend/src/`)**:
   - Designed and built the modern React + Vite glassmorphic web interface ([`AdminDashboard.jsx`](file:///Users/sankeerth/Documents/NeuroBroker/frontend/src/pages/AdminDashboard.jsx), [`UserDashboard.jsx`](file:///Users/sankeerth/Documents/NeuroBroker/frontend/src/pages/UserDashboard.jsx), [`TrainingView.jsx`](file:///Users/sankeerth/Documents/NeuroBroker/frontend/src/pages/TrainingView.jsx)).
   - Implemented responsive telemetry cards, training loss curves, active volunteer node monitors, and interactive model/dataset submitters.
2. **WebSocket Real-Time Communication (`backend/app/websocket/`, `frontend/src/services/websocket.js`)**:
   - Built dual-channel WebSocket manager handling live volunteer node heartbeats and real-time dashboard state broadcasts (`node_status_change`, `task_progress`, `job_status_change`).
3. **Heartbeat Watchdog & Node Health Monitor (`backend/app/main.py`)**:
   - Implemented background async watchdog task to monitor active node telemetry and automatically flag stale nodes as `OFFLINE`.
4. **Job Orchestration & Fault Tolerance Manager (`backend/app/jobs/orchestrator.py`, `backend/app/fault_tolerance/`)**:
   - Developed multi-round federated training state machine (`PARTITIONING` -> `TRAINING` -> `AGGREGATING` -> `CHECKPOINTING`).
   - Built dynamic task reassignment logic to recover from dropped or timed-out volunteer nodes without aborting training jobs.

---

## 📊 Summary Workload Matrix (For Viva / Evaluation)

| Member | Primary System Module | Codebase Locations | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Member 1** | Central Broker & Auth | `backend/app/api/`, `backend/app/models/`, `backend/app/security/` | REST APIs, Database Schema, JWT Auth, File Checksums |
| **Member 2** | Volunteer Node Engine | `volunteer_node/` | Node Client Daemon, Hardware Benchmark, PyTorch Trainer, AST Sandbox |
| **Member 3** | Scheduler, Partitioner & FL | `backend/app/scheduler/`, `backend/app/partitioning/`, `backend/app/aggregation/` | Resource Scheduler, Stratified `.npy`/CSV Partitioner, `FedAvg` Engine |
| **Member 4** | Dashboard & Orchestrator | `frontend/src/`, `backend/app/jobs/`, `backend/app/websocket/` | React Web Dashboard, Real-time WebSockets, Orchestrator Watchdog |

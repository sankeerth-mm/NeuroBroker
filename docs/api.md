# NeuroBroker REST & WebSocket API Specification

This document lists the primary REST endpoints and WebSocket protocols exposed by the NeuroBroker FastAPI backend.

---

## 1. Authentication Endpoints

* `POST /auth/register`: Register a new user (`name`, `email`, `password`, `role`). Returns JWT access token and user object.
* `POST /auth/login`: Login with email and password (`email`, `password`). Returns JWT access token.
* `GET /auth/me`: Fetch authenticated user profile and permissions.

---

## 2. Volunteer Node Endpoints

* `POST /api/nodes/register`: Volunteer registers hardware specifications (`token`, `cpu_cores`, `ram_total_mb`, `gpu_name`, `cuda_available`).
* `POST /api/nodes/heartbeat`: Periodic telemetry update (`node_id`, `cpu_usage`, `ram_usage_percent`, `gpu_usage_percent`, `latency_ms`).
* `POST /api/nodes/{node_id}/benchmark`: Upload initial micro-benchmark score breakdown.
* `GET /api/nodes`: List all volunteer nodes with status counts (`total`, `online_count`, `busy_count`, `unhealthy_count`, `offline_count`).
* `GET /api/nodes/{node_id}`: Detailed telemetry metrics for a single worker.
* `GET /api/nodes/{node_id}/history`: Recent time-series telemetry metrics for charting.
* `GET /api/nodes/client/download`: Stream entire `volunteer_node` client package as `neurobroker_volunteer_client.zip`.

---

## 3. Dataset Endpoints

* `POST /api/datasets/upload`: Upload dataset (`name`, `dataset_type`, `file` `.zip` or `.csv`). Computes SHA-256 and detects class imbalance.
* `GET /api/datasets`: List uploaded datasets.
* `GET /api/datasets/{dataset_id}`: Inspect dataset details and class distribution.
* `GET /api/datasets/partitions/{partition_id}/download`: Download specific stratified partition (used by volunteer nodes).

---

## 4. Model Package Endpoints

* `POST /api/models/upload`: Upload `model_package.zip` containing `model.py`, `train.py`, `config.json`.
* `GET /api/models`: List uploaded model packages.
* `GET /api/models/{model_id}/download`: Download model package archive.
* `GET /api/models/jobs/{job_id}/final`: Download final aggregated `.pth` model weights.

---

## 5. Training Jobs Endpoints

* `POST /api/jobs`: Create training job (`model_package_id`, `dataset_id`, `max_rounds`, `local_epochs`, `batch_size`, `learning_rate`, `target_accuracy`, `min_volunteer_nodes`).
* `GET /api/jobs`: List user or cluster training jobs.
* `GET /api/jobs/{job_id}`: Full detail with live metrics, rounds, and task progression.
* `POST /api/jobs/{job_id}/start`: Start orchestrator background loop.
* `POST /api/jobs/{job_id}/pause`: Pause training after current round.
* `POST /api/jobs/{job_id}/resume`: Resume paused training job.
* `POST /api/jobs/{job_id}/stop`: Stop and cancel training job.
* `GET /api/jobs/{job_id}/rounds`: List all model versions and accuracies across rounds.
* `GET /api/jobs/{job_id}/report`: Generate comprehensive audit report dictionary.
* `POST /api/jobs/{job_id}/tasks/{task_id}/progress`: Volunteer streams local epoch loss/accuracy.
* `POST /api/jobs/{job_id}/tasks/{task_id}/complete`: Volunteer uploads trained `state_dict` weights.

---

## 6. Admin Endpoints

* `GET /api/admin/stats`: Get cluster metrics overview (jobs, nodes, reliability, rounds).
* `GET /api/admin/users`: List all user accounts.
* `GET /api/admin/logs`: Query system logs with optional level/component filters.
* `GET /api/admin/scheduler-decisions`: Query explainable scheduler decisions log.

---

## 7. WebSockets

* `WS /ws/user/{user_id}`: Real-time broadcast channel for user web dashboards.
  * Events: `node_connected`, `node_disconnected`, `node_telemetry`, `job_status_change`, `task_progress`, `task_completed`, `round_completed`.
* `WS /ws/volunteer`: Real-time bi-directional messaging channel for volunteer compute workers.
  * Actions: `assign_task`, `ping`/`pong`.

# Remote Volunteer Node Setup Guide

This guide explains how to install and run the standalone **Volunteer Node Program** on any computer in your college lab or home network.

---

## 1. Quick Download via Web Dashboard

1. Open the NeuroBroker Web Dashboard in your web browser: `http://<BROKER_SERVER_IP>:5173` (or `http://<BROKER_SERVER_IP>:8000`).
2. Click the **"Volunteer Client (.zip)"** button in the top navbar.
3. Extract the downloaded `neurobroker_volunteer_client.zip` to a folder on your computer.

---

## 2. Manual Installation & Run

### Prerequisites
* Python 3.9+ installed (`python --version` or `python3 --version`)
* Network connectivity (WiFi or LAN) to the central server IP

### Step 1: Install Dependencies
Open a terminal / command prompt inside the `volunteer_node` folder and run:

```bash
pip install -r requirements.txt
```

*(If you have an NVIDIA GPU, ensure PyTorch with CUDA is installed so hardware acceleration is automatically detected).*

### Step 2: Connect to Broker Server
Run:

```bash
python main.py --server http://<BROKER_SERVER_IP>:8000 --token NB_VOLUNTEER_SECRET_2026
```

Replace `<BROKER_SERVER_IP>` with your central server's local IP address (e.g. `http://192.168.1.100:8000`).

---

## 3. What Happens on Startup

1. **Hardware Discovery:**
   * Node queries CPU cores, RAM available, GPU name (CUDA / Apple MPS / CPU), and disk capacity.
2. **Micro-Benchmark:**
   * Runs a 1-second matrix multiplication and memory bandwidth benchmark to compute normalized capability scores.
3. **Registration:**
   * Connects to the Broker Server with your registration token and receives an assigned `NODE-XX` ID.
4. **Live Heartbeat:**
   * Streams telemetry heartbeats every 5 seconds over WebSocket/HTTP.
5. **Distributed Training:**
   * When a user starts a training job, your node automatically downloads its assigned dataset partition, trains locally in PyTorch, and uploads its updated model weights (`state_dict`) for FedAvg aggregation!

---

## 4. Optional Command Flags

| Flag | Default | Description |
|---|---|---|
| `--server` | `http://127.0.0.1:8000` | URL of the central broker server |
| `--token` | `NB_VOLUNTEER_SECRET_2026` | Secret registration token |
| `--node-id` | Auto-assigned | Explicit unique name (e.g. `--node-id LAB-DESKTOP-04`) |
| `--heartbeat-interval` | `5` | Telemetry broadcast frequency in seconds |
| `--docker` | `False` | Run training code inside an isolated Docker container |

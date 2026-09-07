# NeuroBroker User Guide

This guide walks through the complete end-to-end workflow of creating and running a distributed deep learning job using NeuroBroker.

---

## Complete Workflow Steps

```text
1. USER REGISTERS / LOGS IN
       ↓
2. UPLOAD MODEL PACKAGE (.zip)
       ↓
3. UPLOAD DATASET (.zip or .csv)
       ↓
4. CONFIGURE HYPERPARAMETERS & CREATE JOB
       ↓
5. BROKER VALIDATES PACKAGE + DATASET
       ↓
6. SCHEDULER SCORES CONNECTED VOLUNTEERS
       ↓
7. DATASET PARTITIONED STRATIFIED ACROSS SELECTED NODES
       ↓
8. MODEL + PARTITIONS DISTRIBUTED OVER NETWORK
       ↓
9. VOLUNTEERS EXECUTE LOCAL PYTORCH EPOCHS
       ↓
10. VOLUNTEERS STREAM PROGRESS & UPLOAD STATE_DICT
       ↓
11. BROKER VALIDATES TENSORS (NAN/INF & SHAPE GUARDS)
       ↓
12. WEIGHTED FEDAVG AGGREGATES GLOBAL MODEL
       ↓
13. CHECKPOINT PERSISTED & BROADCAST TO DASHBOARD
       ↓
14. ROUNDS REPEAT UNTIL TARGET ACCURACY / MAX ROUNDS
       ↓
15. USER DOWNLOADS FINAL .pth MODEL
```

---

## 1. Quick Demonstration Workflow

1. Start the backend:
   ```bash
   bash scripts/start_backend.sh
   ```
2. Start the frontend:
   ```bash
   bash scripts/start_frontend.sh
   ```
3. Start the simulated 4–5 volunteer fleet (or connect real lab computers):
   ```bash
   python demo.py
   ```
4. Open the Web Dashboard at `http://localhost:5173`.
5. Click **"Admin Demo"** or **"User Demo"** on the login screen to sign in instantly.
6. Click **"New Training Job"**, select `MNIST_CNN_Classifier` and `MNIST Sample Dataset`, configure 5 rounds, and click **"Start Distributed Training"**.
7. Watch the live convergence curves, per-node epoch progress bars, and WebSocket event log.
8. Upon completion, click **"Download Final Model (.pth)"** to obtain your trained PyTorch weights.

# NeuroBroker Volunteer Compute Node

This is the standalone Python client for volunteer compute computers participating in **NeuroBroker** distributed deep learning training.

## Requirements
* Python 3.9+
* PyTorch (`torch`, `torchvision`)
* Network connectivity to the central NeuroBroker Server

## Installation & Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Connect to the NeuroBroker Broker Server:**
   ```bash
   python main.py --server http://<BROKER_SERVER_IP>:8000 --token NB_VOLUNTEER_SECRET_2026
   ```

3. **Optional Flags:**
   * `--node-id NODE-01`: Explicitly request a specific node identifier
   * `--heartbeat-interval 5`: Set telemetry update frequency (seconds)
   * `--docker`: Enable Docker container isolation for training jobs

## What Happens When Running:
1. Discovers hardware: CPU cores, RAM, GPU (NVIDIA CUDA / Apple MPS), and disk space.
2. Registers with the central broker and runs a quick 2-second compute & memory micro-benchmark.
3. Streams live resource utilization heartbeats every 5 seconds.
4. Listens for training task assignments via WebSocket.
5. Securely downloads assigned dataset partitions, executes local PyTorch epochs, and returns trained model weights (`state_dict`) for FedAvg aggregation.

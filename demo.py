import os
import sys
import time
import json
import asyncio
import threading
import argparse
from pathlib import Path
import websockets
import requests

from volunteer_node.node_client import NodeClient
from volunteer_node.task_manager import TaskManager
from volunteer_node.logger import logger

NODE_PROFILES = [
    {
        "node_id": "NODE-01",
        "hostname": "volunteer-alpha-4090",
        "cpu_name": "Intel Core i9-13900K",
        "cpu_cores": 24,
        "ram_total_mb": 65536.0,
        "gpu_name": "NVIDIA GeForce RTX 4090",
        "gpu_memory_total_mb": 24576.0,
        "disk_total_gb": 1000.0,
        "cuda_available": True,
        "cuda_version": "12.2",
        "compute_score": 4.8,
        "memory_score": 4.5,
        "gpu_score": 5.0,
        "network_score": 4.5,
        "overall_capability_score": 4.85,
        "base_cpu_usage": 18.0,
        "base_ram_usage": 25.0,
        "base_gpu_usage": 10.0,
        "speed_factor": 1.5,
    },
    {
        "node_id": "NODE-02",
        "hostname": "volunteer-beta-3060",
        "cpu_name": "AMD Ryzen 7 5800X",
        "cpu_cores": 16,
        "ram_total_mb": 16384.0,
        "gpu_name": "NVIDIA GeForce RTX 3060",
        "gpu_memory_total_mb": 12288.0,
        "disk_total_gb": 512.0,
        "cuda_available": True,
        "cuda_version": "12.0",
        "compute_score": 3.6,
        "memory_score": 3.2,
        "gpu_score": 3.8,
        "network_score": 3.5,
        "overall_capability_score": 3.60,
        "base_cpu_usage": 32.0,
        "base_ram_usage": 45.0,
        "base_gpu_usage": 20.0,
        "speed_factor": 1.2,
    },
    {
        "node_id": "NODE-03",
        "hostname": "volunteer-gamma-1650",
        "cpu_name": "Intel Core i5-11400",
        "cpu_cores": 12,
        "ram_total_mb": 8192.0,
        "gpu_name": "NVIDIA GeForce GTX 1650",
        "gpu_memory_total_mb": 4096.0,
        "disk_total_gb": 256.0,
        "cuda_available": True,
        "cuda_version": "11.8",
        "compute_score": 2.4,
        "memory_score": 2.2,
        "gpu_score": 2.2,
        "network_score": 2.8,
        "overall_capability_score": 2.40,
        "base_cpu_usage": 42.0,
        "base_ram_usage": 60.0,
        "base_gpu_usage": 35.0,
        "speed_factor": 1.0,
    },
    {
        "node_id": "NODE-04",
        "hostname": "volunteer-delta-cpu",
        "cpu_name": "Intel Core i5-8250U",
        "cpu_cores": 8,
        "ram_total_mb": 8192.0,
        "gpu_name": "CPU Only",
        "gpu_memory_total_mb": 0.0,
        "disk_total_gb": 256.0,
        "cuda_available": False,
        "cuda_version": None,
        "compute_score": 1.6,
        "memory_score": 1.8,
        "gpu_score": 0.0,
        "network_score": 2.0,
        "overall_capability_score": 1.45,
        "base_cpu_usage": 55.0,
        "base_ram_usage": 70.0,
        "base_gpu_usage": 0.0,
        "speed_factor": 0.8,
    },
    {
        "node_id": "NODE-05",
        "hostname": "volunteer-epsilon-2060",
        "cpu_name": "AMD Ryzen 5 3600",
        "cpu_cores": 12,
        "ram_total_mb": 16384.0,
        "gpu_name": "NVIDIA GeForce RTX 2060",
        "gpu_memory_total_mb": 6144.0,
        "disk_total_gb": 500.0,
        "cuda_available": True,
        "cuda_version": "12.0",
        "compute_score": 3.0,
        "memory_score": 3.0,
        "gpu_score": 3.2,
        "network_score": 3.0,
        "overall_capability_score": 3.05,
        "base_cpu_usage": 28.0,
        "base_ram_usage": 38.0,
        "base_gpu_usage": 15.0,
        "speed_factor": 1.1,
    }
]

class SimulatedVolunteerWorker:
    def __init__(self, profile: dict, server_url: str, token: str, base_work_dir: Path):
        self.profile = profile
        self.node_id = profile["node_id"]
        self.server_url = server_url
        self.token = token
        self.work_dir = base_work_dir / self.node_id
        self.client = NodeClient(server_url=server_url, token=token, node_id=self.node_id)
        self.task_manager = TaskManager(client=self.client, work_dir=self.work_dir)
        self.is_running = True

    async def run(self):
        # 1. Register with broker
        reg_payload = {
            "hostname": self.profile["hostname"],
            "cpu_name": self.profile["cpu_name"],
            "cpu_cores": self.profile["cpu_cores"],
            "ram_total_mb": self.profile["ram_total_mb"],
            "gpu_name": self.profile["gpu_name"],
            "gpu_memory_total_mb": self.profile["gpu_memory_total_mb"],
            "disk_total_gb": self.profile["disk_total_gb"],
            "os_info": "Linux Ubuntu 22.04 (Simulated Worker)",
            "python_version": "3.11.8",
            "pytorch_version": "2.2.0",
            "cuda_available": self.profile["cuda_available"],
            "cuda_version": self.profile["cuda_version"]
        }
        
        try:
            self.client.register(reg_payload)
            logger.info(f"[{self.node_id}] Registered as {self.profile['gpu_name']} ({self.profile['cpu_cores']} cores)")
            
            # Send benchmark scores
            self.client.send_benchmark({
                "compute_score": self.profile["compute_score"],
                "memory_score": self.profile["memory_score"],
                "gpu_score": self.profile["gpu_score"],
                "network_score": self.profile["network_score"],
                "overall_capability_score": self.profile["overall_capability_score"],
            })
        except Exception as e:
            logger.error(f"[{self.node_id}] Registration error: {e}")
            return
            
        # 2. Heartbeat coroutine
        async def heartbeat_loop():
            import random
            while self.is_running:
                try:
                    cpu = min(95.0, max(5.0, self.profile["base_cpu_usage"] + random.uniform(-5, 8)))
                    ram = min(95.0, max(10.0, self.profile["base_ram_usage"] + random.uniform(-3, 5)))
                    gpu = min(98.0, max(0.0, self.profile["base_gpu_usage"] + random.uniform(-4, 6)))
                    
                    telemetry = {
                        "cpu_usage": float(cpu),
                        "ram_usage_percent": float(ram),
                        "ram_available_mb": float(self.profile["ram_total_mb"] * (1.0 - ram / 100.0)),
                        "gpu_usage_percent": float(gpu),
                        "gpu_memory_available_mb": float(self.profile["gpu_memory_total_mb"] * (1.0 - gpu / 100.0)),
                        "disk_available_gb": float(self.profile["disk_total_gb"] * 0.85),
                        "network_upload_mbps": float(100.0 * self.profile["network_score"]),
                        "network_download_mbps": float(150.0 * self.profile["network_score"]),
                        "latency_ms": float(15.0 / max(0.5, self.profile["network_score"])),
                    }
                    self.client.send_heartbeat(telemetry)
                except Exception as e:
                    logger.warning(f"[{self.node_id}] Heartbeat error: {e}")
                await asyncio.sleep(5)
                
        # 3. WebSocket listener coroutine
        async def ws_loop():
            ws_url = self.client.ws_url
            while self.is_running:
                try:
                    async with websockets.connect(ws_url) as ws:
                        await ws.send(json.dumps({"node_id": self.node_id}))
                        while self.is_running:
                            msg_text = await ws.recv()
                            msg = json.loads(msg_text)
                            if msg.get("type") == "assign_task":
                                task_data = msg.get("data", {})
                                logger.info(f"[{self.node_id}] Executing training Task {task_data.get('task_id')}...")
                                loop = asyncio.get_running_loop()
                                await loop.run_in_executor(None, self.task_manager.execute_task, task_data)
                except Exception as e:
                    await asyncio.sleep(3)
                    
        await asyncio.gather(heartbeat_loop(), ws_loop())

def main():
    parser = argparse.ArgumentParser(description="NeuroBroker Heterogeneous Multi-Node Simulation Demo")
    parser.add_argument("--server", type=str, default="http://127.0.0.1:8000", help="Broker Server URL")
    parser.add_argument("--token", type=str, default="NB_VOLUNTEER_SECRET_2026", help="Registration token")
    parser.add_argument("--nodes", type=int, default=5, help="Number of simulated nodes to launch (1 to 5)")
    args = parser.parse_args()
    
    print("""
========================================================================
       _   __                      ____             __             
      / | / /__  __  ___________  / __ )_________  / /_____  _____ 
     /  |/ / _ \/ / / / ___/ __ \/ __  / ___/ __ \/ //_/ _ \/ ___/ 
    / /|  /  __/ /_/ / /  / /_/ / /_/ / /  / /_/ / ,< /  __/ /     
   /_/ |_/\___/\__,_/_/   \____/_____/_/   \____/_/|_|\___/_/      
                                                                   
   HETEROGENEOUS VOLUNTEER FLEET SIMULATION DEMONSTRATOR
========================================================================
    """)
    
    node_count = min(len(NODE_PROFILES), max(1, args.nodes))
    logger.info(f"Launching {node_count} simulated heterogeneous volunteer workers against {args.server}...")
    
    base_work_dir = Path(__file__).resolve().parent / "storage" / "simulated_nodes"
    base_work_dir.mkdir(parents=True, exist_ok=True)
    
    workers = [
        SimulatedVolunteerWorker(
            profile=NODE_PROFILES[i],
            server_url=args.server,
            token=args.token,
            base_work_dir=base_work_dir
        )
        for i in range(node_count)
    ]
    
    async def run_all():
        tasks = [asyncio.create_task(w.run()) for w in workers]
        await asyncio.gather(*tasks)
        
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("Simulated volunteer fleet terminated.")

if __name__ == "__main__":
    main()

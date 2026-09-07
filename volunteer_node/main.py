import os
import sys
import json
import time
import asyncio
import websockets
from pathlib import Path

# Add project root to sys.path if running within repo
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from volunteer_node.config import config
from volunteer_node.logger import logger
from volunteer_node.resource_monitor import resource_monitor
from volunteer_node.benchmark import volunteer_benchmark
from volunteer_node.node_client import NodeClient
from volunteer_node.task_manager import TaskManager

async def heartbeat_loop(client: NodeClient, interval_sec: int):
    """Background coroutine sending telemetry heartbeat to broker every N seconds."""
    while True:
        try:
            telemetry = resource_monitor.get_live_telemetry()
            client.send_heartbeat(telemetry)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
        await asyncio.sleep(interval_sec)

async def websocket_listener(client: NodeClient, task_manager: TaskManager):
    """Listens for real-time task assignments from broker server via WebSocket."""
    ws_url = client.ws_url
    logger.info(f"Connecting to Broker WebSocket: {ws_url} ...")
    
    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                # Send identification
                await ws.send(json.dumps({"node_id": client.node_id}))
                logger.info(f"Connected to NeuroBroker WebSocket! Ready to receive training tasks.")
                
                while True:
                    msg_text = await ws.recv()
                    msg = json.loads(msg_text)
                    msg_type = msg.get("type")
                    data = msg.get("data", {})
                    
                    if msg_type == "assign_task":
                        logger.info(f"Received task assignment from broker! Task ID: {data.get('task_id')}")
                        # Run task asynchronously in executor to avoid blocking event loop
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, task_manager.execute_task, data)
                    elif msg_type == "ping":
                        await ws.send(json.dumps({"type": "pong"}))
                        
        except (websockets.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"WebSocket disconnected ({e}). Reconnecting in 3 seconds...")
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await asyncio.sleep(3)

def main():
    config.load_from_args()
    
    print("""
========================================================================
       _   __                      ____             __             
      / | / /__  __  ___________  / __ )_________  / /_____  _____ 
     /  |/ / _ \/ / / / ___/ __ \/ __  / ___/ __ \/ //_/ _ \/ ___/ 
    / /|  /  __/ /_/ / /  / /_/ / /_/ / /  / /_/ / ,< /  __/ /     
   /_/ |_/\___/\__,_/_/   \____/_____/_/   \____/_/|_|\___/_/      
                                                                   
   VOLUNTEER DISTRIBUTED DEEP LEARNING COMPUTE NODE CLIENT
========================================================================
    """)
    
    logger.info("Initializing volunteer node...")
    specs = resource_monitor.get_hardware_specs()
    logger.info(f"  Hostname:        {specs['hostname']}")
    logger.info(f"  CPU Cores:       {specs['cpu_cores']} ({specs['cpu_name']})")
    logger.info(f"  RAM Total:       {specs['ram_total_mb']:.0f} MB")
    logger.info(f"  GPU Name:        {specs['gpu_name']} (VRAM: {specs['gpu_memory_total_mb']:.0f} MB)")
    logger.info(f"  CUDA Available:  {specs['cuda_available']}")
    logger.info(f"  PyTorch Version: {specs['pytorch_version']}")
    logger.info(f"  OS:              {specs['os_info']}")
    
    client = NodeClient(server_url=config.server_url, token=config.token, node_id=config.node_id)
    
    # 1. Register with broker
    logger.info(f"Connecting to Broker Server at {config.server_url}...")
    try:
        reg_data = client.register(specs)
        logger.info(f"Registration SUCCESSFUL! Assigned Node ID: {client.node_id}")
    except Exception as e:
        logger.critical(f"Registration failed: {e}")
        logger.critical("Check that the broker server is running and the token is valid.")
        sys.exit(1)
        
    # 2. Run initial micro-benchmark
    try:
        bench_scores = volunteer_benchmark.run_micro_benchmark()
        client.send_benchmark(bench_scores)
    except Exception as e:
        logger.warning(f"Micro-benchmark upload failed: {e}")
        
    # 3. Create Task Manager
    task_manager = TaskManager(client=client, work_dir=config.work_dir)
    
    # 4. Start Event Loop with Heartbeat & WebSocket Tasks
    async def runner():
        hb_task = asyncio.create_task(heartbeat_loop(client, config.heartbeat_interval))
        ws_task = asyncio.create_task(websocket_listener(client, task_manager))
        await asyncio.gather(hb_task, ws_task)
        
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        logger.info("Volunteer node stopped by user.")

if __name__ == "__main__":
    main()

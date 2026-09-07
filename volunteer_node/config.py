import os
import argparse
from pathlib import Path
from typing import Optional
import yaml

class VolunteerConfig:
    def __init__(self):
        self.server_url: str = "http://127.0.0.1:8000"
        self.token: str = "NB_VOLUNTEER_SECRET_2026"
        self.node_id: Optional[str] = None
        self.heartbeat_interval: int = 5
        self.work_dir: Path = Path(__file__).resolve().parent / "workspace"
        self.use_docker: bool = False

    def load_from_args(self):
        parser = argparse.ArgumentParser(description="NeuroBroker Volunteer Compute Node Client")
        parser.add_argument("--server", type=str, default=os.getenv("BROKER_SERVER", self.server_url), help="NeuroBroker Central Server URL")
        parser.add_argument("--token", type=str, default=os.getenv("VOLUNTEER_TOKEN", self.token), help="Volunteer Registration Secret Token")
        parser.add_argument("--node-id", type=str, default=os.getenv("NODE_ID", self.node_id), help="Optional unique Node ID")
        parser.add_argument("--heartbeat-interval", type=int, default=5, help="Heartbeat interval in seconds")
        parser.add_argument("--docker", action="store_true", help="Enable Docker container isolation")
        
        args, _ = parser.parse_known_args()
        self.server_url = args.server.rstrip("/")
        self.token = args.token
        self.node_id = args.node_id
        self.heartbeat_interval = args.heartbeat_interval
        self.use_docker = args.docker
        
        # Load config.yaml if exists
        cfg_file = Path(__file__).resolve().parent / "config.yaml"
        if cfg_file.exists():
            try:
                with open(cfg_file, "r") as f:
                    data = yaml.safe_load(f) or {}
                    if not args.server and "server" in data:
                        self.server_url = data["server"].rstrip("/")
                    if not args.token and "token" in data:
                        self.token = data["token"]
            except Exception:
                pass

config = VolunteerConfig()

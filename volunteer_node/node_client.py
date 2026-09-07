import os
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pathlib import Path
from typing import Dict, Any, Optional
from volunteer_node.logger import logger

class NodeClient:
    def __init__(self, server_url: str, token: str, node_id: Optional[str] = None):
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.node_id = node_id
        self.ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/volunteer"
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def register(self, hardware_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Register volunteer node with the broker server."""
        url = f"{self.server_url}/api/nodes/register"
        payload = {
            "token": self.token,
            "node_id": self.node_id,
            **hardware_specs
        }
        resp = self.session.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Registration failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        self.node_id = data["node_id"]
        return data

    def send_heartbeat(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Send periodic telemetry heartbeat to broker."""
        url = f"{self.server_url}/api/nodes/heartbeat"
        payload = {
            "node_id": self.node_id,
            **telemetry
        }
        try:
            resp = self.session.post(url, json=payload, timeout=5)
            if resp.status_code != 200:
                logger.warning(f"Heartbeat rejected: {resp.text}")
                return {"status": "error"}
            return resp.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            # Recreate session in case of stale pooled TCP socket
            self._init_session()
            resp = self.session.post(url, json=payload, timeout=5)
            if resp.status_code != 200:
                logger.warning(f"Heartbeat rejected: {resp.text}")
                return {"status": "error"}
            return resp.json()

    def send_benchmark(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Upload initial benchmark scores."""
        url = f"{self.server_url}/api/nodes/{self.node_id}/benchmark"
        payload = {
            "node_id": self.node_id,
            **scores
        }
        resp = self.session.post(url, json=payload, timeout=10)
        return resp.json()

    def download_file(self, relative_url: str, dest_path: Path) -> Path:
        """Download a file (model package, checkpoint, or partition) from the broker."""
        full_url = f"{self.server_url}{relative_url}"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = self.session.get(full_url, stream=True, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download {relative_url}: {resp.status_code}")
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        return dest_path

    def report_task_progress(self, job_id: int, task_id: int, epoch: int, loss: float, acc: float, progress_pct: float):
        """Send live epoch progress to broker."""
        url = f"{self.server_url}/api/jobs/{job_id}/tasks/{task_id}/progress"
        data = {
            "epoch": epoch,
            "loss": loss,
            "accuracy": acc,
            "progress_percent": progress_pct
        }
        try:
            self.session.post(url, data=data, timeout=5)
        except Exception as e:
            logger.warning(f"Failed to report progress: {e}")

    def upload_task_completion(
        self,
        job_id: int,
        task_id: int,
        loss: float,
        acc: float,
        sample_count: int,
        training_time_sec: float,
        weights_path: Path
    ) -> Dict[str, Any]:
        """Upload trained local state_dict weights and completion metrics to broker."""
        url = f"{self.server_url}/api/jobs/{job_id}/tasks/{task_id}/complete"
        data = {
            "loss": loss,
            "accuracy": acc,
            "sample_count": sample_count,
            "training_time_seconds": training_time_sec,
        }
        with open(weights_path, "rb") as f:
            files = {"weights_file": (weights_path.name, f, "application/octet-stream")}
            resp = self.session.post(url, data=data, files=files, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to upload model update: {resp.text}")
        return resp.json()

import os
import json
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pathlib import Path
from typing import Dict, Any, Optional, List
from volunteer_node.logger import logger

class NodeClient:
    def __init__(self, server_url: str, token: str, node_id: Optional[str] = None):
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.node_id = node_id
        self.ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/volunteer"
        self.last_hardware_specs: Optional[Dict[str, Any]] = None
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _headers(self) -> Dict[str, str]:
        return {"X-Volunteer-Token": self.token}

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self.server_url}{endpoint}"

    def register(self, hardware_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Register volunteer node with the broker server."""
        self.last_hardware_specs = hardware_specs
        url = self._build_url("/api/nodes/register")
        payload = {
            "token": self.token,
            "node_id": self.node_id,
            **hardware_specs
        }
        resp = self.session.post(url, json=payload, headers=self._headers(), timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Registration failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        self.node_id = data["node_id"]
        return data

    def send_heartbeat(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Send periodic telemetry heartbeat to broker. Auto-reregisters if broker lost node state."""
        url = self._build_url("/api/nodes/heartbeat")
        payload = {
            "node_id": self.node_id,
            **telemetry
        }
        
        for attempt in range(2):
            try:
                resp = self.session.post(url, json=payload, headers=self._headers(), timeout=5)
                if resp.status_code == 404 and self.last_hardware_specs:
                    logger.warning("Broker server returned 404 for heartbeat. Attempting re-registration...")
                    self.register(self.last_hardware_specs)
                    payload["node_id"] = self.node_id
                    continue
                if resp.status_code != 200:
                    logger.warning(f"Heartbeat rejected ({resp.status_code}): {resp.text}")
                    return {"status": "error"}
                return resp.json()
            except requests.exceptions.RequestException as e:
                self._init_session()
                if attempt == 1:
                    logger.warning(f"Heartbeat failed: {e}")
                    return {"status": "error"}
                time.sleep(1)
        return {"status": "error"}

    def send_benchmark(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Upload initial benchmark scores."""
        url = self._build_url(f"/api/nodes/{self.node_id}/benchmark")
        payload = {
            "node_id": self.node_id,
            **scores
        }
        try:
            resp = self.session.post(url, json=payload, headers=self._headers(), timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.warning(f"Failed to send benchmark: {e}")
            return {}

    def download_file(self, relative_url: str, dest_path: Path, max_retries: int = 5) -> Path:
        """Download a file with automatic exponential backoff retries for connection stability."""
        full_url = self._build_url(relative_url)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(full_url, headers=self._headers(), stream=True, timeout=60)
                if resp.status_code == 200:
                    with open(dest_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            f.write(chunk)
                    return dest_path
                else:
                    last_exception = RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                last_exception = e
                self._init_session()

            backoff = min(2 ** (attempt - 1), 16)
            logger.warning(f"Download attempt {attempt}/{max_retries} failed for {relative_url}: {last_exception}. Retrying in {backoff}s...")
            time.sleep(backoff)

        raise RuntimeError(f"Failed to download {relative_url} after {max_retries} attempts: {last_exception}")

    def report_task_progress(self, job_id: int, task_id: int, epoch: int, loss: float, acc: float, progress_pct: float):
        """Send live epoch progress to broker."""
        url = self._build_url(f"/api/jobs/{job_id}/tasks/{task_id}/progress")
        data = {
            "epoch": epoch,
            "loss": loss,
            "accuracy": acc,
            "progress_percent": progress_pct
        }
        try:
            self.session.post(url, data=data, headers=self._headers(), timeout=5)
        except Exception as e:
            logger.warning(f"Failed to report progress: {e}")

    def report_task_failure(self, job_id: int, task_id: int, error_message: str):
        """Notify broker server immediately of task execution failure."""
        url = self._build_url(f"/api/jobs/{job_id}/tasks/{task_id}/fail")
        try:
            self.session.post(url, data={"error_message": error_message}, headers=self._headers(), timeout=5)
        except Exception as e:
            logger.warning(f"Failed to report task failure: {e}")

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Fetch pending tasks assigned to this node if WebSocket reconnects."""
        if not self.node_id:
            return []
        url = self._build_url(f"/api/nodes/{self.node_id}/tasks/pending")
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=5)
            if resp.status_code == 200:
                return resp.json().get("tasks", [])
        except Exception as e:
            logger.warning(f"Failed to fetch pending tasks: {e}")
        return []

    def upload_task_completion(
        self,
        job_id: int,
        task_id: int,
        loss: float,
        accuracy: float,
        sample_count: int,
        training_time_sec: float,
        weights_path: Path,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """Upload trained local state_dict weights and completion metrics with retry backoff."""
        url = self._build_url(f"/api/jobs/{job_id}/tasks/{task_id}/complete")
        data = {
            "loss": loss,
            "accuracy": accuracy,
            "sample_count": sample_count,
            "training_time_seconds": training_time_sec,
        }
        
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                with open(weights_path, "rb") as f:
                    files = {"weights_file": (weights_path.name, f, "application/octet-stream")}
                    resp = self.session.post(url, data=data, files=files, headers=self._headers(), timeout=60)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    last_exception = RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                last_exception = e
                self._init_session()

            backoff = min(2 ** (attempt - 1), 16)
            logger.warning(f"Upload attempt {attempt}/{max_retries} for task {task_id} failed: {last_exception}. Retrying in {backoff}s...")
            time.sleep(backoff)

        raise RuntimeError(f"Failed to upload model update after {max_retries} attempts: {last_exception}")


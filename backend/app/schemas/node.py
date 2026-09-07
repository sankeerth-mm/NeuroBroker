from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class NodeRegisterRequest(BaseModel):
    node_id: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    token: str = Field(..., description="Volunteer registration token")
    
    cpu_name: Optional[str] = None
    cpu_cores: int = 1
    ram_total_mb: float = 1024.0
    
    gpu_name: Optional[str] = "CPU Only"
    gpu_memory_total_mb: float = 0.0
    disk_total_gb: float = 50.0
    
    os_info: Optional[str] = None
    python_version: Optional[str] = None
    pytorch_version: Optional[str] = None
    cuda_available: bool = False
    cuda_version: Optional[str] = None

class NodeHeartbeatRequest(BaseModel):
    node_id: str
    cpu_usage: float
    ram_usage_percent: float
    ram_available_mb: float
    gpu_usage_percent: Optional[float] = 0.0
    gpu_memory_available_mb: Optional[float] = 0.0
    disk_available_gb: Optional[float] = 50.0
    network_upload_mbps: Optional[float] = 100.0
    network_download_mbps: Optional[float] = 100.0
    latency_ms: Optional[float] = 10.0
    current_task_id: Optional[int] = None
    progress_percent: Optional[float] = None

class NodeBenchmarkScoreUpdate(BaseModel):
    node_id: str
    compute_score: float
    memory_score: float
    gpu_score: float
    network_score: float
    overall_capability_score: float

class NodeResponse(BaseModel):
    id: int
    node_id: str
    hostname: Optional[str]
    ip_address: Optional[str]
    
    cpu_name: Optional[str]
    cpu_cores: int
    cpu_usage: float
    
    ram_total_mb: float
    ram_available_mb: float
    ram_usage_percent: float
    
    gpu_name: Optional[str]
    gpu_memory_total_mb: float
    gpu_memory_available_mb: float
    gpu_usage_percent: float
    
    disk_total_gb: float
    disk_available_gb: float
    
    network_upload_mbps: float
    network_download_mbps: float
    latency_ms: float
    
    os_info: Optional[str]
    python_version: Optional[str]
    pytorch_version: Optional[str]
    cuda_available: bool
    cuda_version: Optional[str]
    
    compute_score: float
    memory_score: float
    gpu_score: float
    network_score: float
    overall_capability_score: float
    reliability_score: float
    
    status: str
    current_task_id: Optional[int]
    current_job_id: Optional[int]
    tasks_completed: int
    tasks_failed: int
    total_training_time_seconds: float
    total_samples_processed: int
    rounds_participated: int
    
    last_heartbeat: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NodeListResponse(BaseModel):
    total: int
    online_count: int
    busy_count: int
    idle_count: int
    unhealthy_count: int
    offline_count: int
    nodes: List[NodeResponse]

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from backend.app.schemas.auth import UserResponse
from backend.app.schemas.node import NodeResponse
from backend.app.schemas.job import JobResponse

class SystemLogResponse(BaseModel):
    id: int
    level: str
    component: str
    message: str
    details: Dict[str, Any]
    job_id: Optional[int]
    node_id: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    target_type: str
    target_id: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

class SchedulerDecisionResponse(BaseModel):
    id: int
    job_id: int
    round_number: int
    node_id: str
    is_selected: bool
    overall_score: float
    cpu_score: float
    ram_score: float
    gpu_score: float
    network_score: float
    reliability_score: float
    fairness_score: float
    estimated_transfer_time_sec: float
    estimated_training_time_sec: float
    rationale: str
    timestamp: datetime

    class Config:
        from_attributes = True

class AdminDashboardStats(BaseModel):
    total_users: int
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_nodes: int
    online_nodes: int
    busy_nodes: int
    unhealthy_nodes: int
    offline_nodes: int
    avg_node_reliability: float
    total_rounds_trained: int

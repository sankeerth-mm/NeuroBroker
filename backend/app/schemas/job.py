from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from backend.app.schemas.dataset import DatasetResponse
from backend.app.schemas.model_pkg import ModelPackageResponse, ModelVersionResponse

class JobCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    model_package_id: int
    dataset_id: int
    
    max_rounds: int = Field(5, ge=1, le=100)
    local_epochs: int = Field(2, ge=1, le=50)
    batch_size: int = Field(32, ge=1, le=1024)
    learning_rate: float = Field(0.001, gt=0.0)
    target_accuracy: float = Field(95.0, ge=1.0, le=100.0)
    min_volunteer_nodes: int = Field(2, ge=1)

class JobTaskResponse(BaseModel):
    id: int
    job_id: int
    round_number: int
    node_id: str
    partition_id: int
    status: str
    local_epochs: int
    batch_size: int
    learning_rate: float
    progress_percent: float
    current_epoch: int
    current_loss: float
    current_accuracy: float
    samples_processed: int
    training_time_seconds: float
    retry_count: int
    assigned_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: int
    job_code: str
    user_id: int
    name: str
    description: Optional[str]
    model_package_id: int
    dataset_id: int
    status: str
    
    current_round: int
    max_rounds: int
    local_epochs: int
    batch_size: int
    learning_rate: float
    target_accuracy: float
    min_volunteer_nodes: int
    
    global_accuracy: float
    global_loss: float
    estimated_remaining_seconds: float
    total_training_time_seconds: float
    error_message: Optional[str]
    
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    dataset: Optional[DatasetResponse] = None
    model_package: Optional[ModelPackageResponse] = None
    versions: List[ModelVersionResponse] = []
    tasks: List[JobTaskResponse] = []

class JobActionRequest(BaseModel):
    action: str = Field(..., pattern="^(start|stop|pause|resume)$")

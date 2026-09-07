from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class ModelPackageResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    framework: str
    config_json: Dict[str, Any]
    checksum_sha256: str
    is_validated: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ModelVersionResponse(BaseModel):
    id: int
    job_id: int
    round_number: int
    version_tag: str
    accuracy: float
    loss: float
    sample_count: int
    checksum_sha256: str
    participating_nodes: List[str]
    aggregation_time_seconds: float
    created_at: datetime

    class Config:
        from_attributes = True

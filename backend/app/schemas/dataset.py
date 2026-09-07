from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class DatasetPartitionResponse(BaseModel):
    id: int
    dataset_id: int
    job_id: Optional[int]
    node_id: Optional[str]
    partition_index: int
    sample_count: int
    class_distribution: Dict[str, Any]
    checksum_sha256: str
    is_assigned: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    dataset_type: str
    total_samples: int
    total_size_bytes: int
    class_distribution: Dict[str, Any]
    label_column: Optional[str]
    checksum_sha256: str
    is_validated: bool
    is_non_iid: bool
    created_at: datetime

    class Config:
        from_attributes = True

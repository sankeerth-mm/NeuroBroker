from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from backend.app.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    dataset_type = Column(String(64), default="image_classification", nullable=False) # image_classification, csv_classification
    file_path = Column(String(512), nullable=False)
    
    total_samples = Column(Integer, default=0, nullable=False)
    total_size_bytes = Column(Integer, default=0, nullable=False)
    class_distribution = Column(JSON, default=dict) # e.g. {"0": 1000, "1": 1000, ...}
    label_column = Column(String(64), nullable=True)
    
    checksum_sha256 = Column(String(64), nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    is_non_iid = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DatasetPartition(Base):
    __tablename__ = "dataset_partitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    node_id = Column(String(64), nullable=True, index=True)
    
    partition_index = Column(Integer, default=0, nullable=False)
    sample_count = Column(Integer, default=0, nullable=False)
    class_distribution = Column(JSON, default=dict)
    
    file_path = Column(String(512), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    is_assigned = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

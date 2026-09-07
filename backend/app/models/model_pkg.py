from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from backend.app.database import Base

class ModelPackage(Base):
    __tablename__ = "model_packages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    framework = Column(String(32), default="pytorch", nullable=False)
    file_path = Column(String(512), nullable=False)
    config_json = Column(JSON, default=dict)
    
    checksum_sha256 = Column(String(64), nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    round_number = Column(Integer, default=0, nullable=False)
    version_tag = Column(String(32), nullable=False) # e.g. 'v0', 'v1', 'v2'
    
    accuracy = Column(Float, default=0.0) # Percentage (0-100)
    loss = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)
    
    checkpoint_path = Column(String(512), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    participating_nodes = Column(JSON, default=list) # List of node_ids
    aggregation_time_seconds = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

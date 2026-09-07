from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class VolunteerNode(Base):
    __tablename__ = "volunteer_nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(String(64), unique=True, index=True, nullable=False) # e.g. NODE-01 or UUID
    hostname = Column(String(128), nullable=True)
    ip_address = Column(String(64), nullable=True)
    
    # Hardware Specifications & Current Telemetry
    cpu_name = Column(String(128), nullable=True)
    cpu_cores = Column(Integer, default=1, nullable=False)
    cpu_usage = Column(Float, default=0.0) # Percentage (0-100)
    
    ram_total_mb = Column(Float, default=1024.0)
    ram_available_mb = Column(Float, default=1024.0)
    ram_usage_percent = Column(Float, default=0.0)
    
    gpu_name = Column(String(128), default="CPU Only")
    gpu_memory_total_mb = Column(Float, default=0.0)
    gpu_memory_available_mb = Column(Float, default=0.0)
    gpu_usage_percent = Column(Float, default=0.0)
    
    disk_total_gb = Column(Float, default=50.0)
    disk_available_gb = Column(Float, default=50.0)
    
    network_upload_mbps = Column(Float, default=100.0)
    network_download_mbps = Column(Float, default=100.0)
    latency_ms = Column(Float, default=10.0)
    
    os_info = Column(String(128), nullable=True)
    python_version = Column(String(32), nullable=True)
    pytorch_version = Column(String(32), nullable=True)
    cuda_available = Column(Boolean, default=False)
    cuda_version = Column(String(32), nullable=True)
    
    # Capability & Trust Scores (Dynamic & Benchmarked)
    compute_score = Column(Float, default=1.0)
    memory_score = Column(Float, default=1.0)
    gpu_score = Column(Float, default=0.0)
    network_score = Column(Float, default=1.0)
    overall_capability_score = Column(Float, default=1.0)
    reliability_score = Column(Float, default=1.0) # 0.0 to 1.0 (starts at 1.0)
    
    # Status & Activity
    status = Column(String(32), default="ONLINE", index=True) # ONLINE, IDLE, BUSY, UNHEALTHY, OFFLINE
    current_task_id = Column(Integer, nullable=True)
    current_job_id = Column(Integer, nullable=True)
    
    # Historical Contributions (Fairness tracking)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_training_time_seconds = Column(Float, default=0.0)
    total_samples_processed = Column(Integer, default=0)
    rounds_participated = Column(Integer, default=0)
    
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NodeMetricHistory(Base):
    __tablename__ = "node_metric_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(String(64), index=True, nullable=False)
    cpu_usage = Column(Float, default=0.0)
    ram_usage_percent = Column(Float, default=0.0)
    gpu_usage_percent = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

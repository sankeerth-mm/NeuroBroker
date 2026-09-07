from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class TrainingJob(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_code = Column(String(32), unique=True, index=True, nullable=False) # e.g. JOB-1001
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    model_package_id = Column(Integer, ForeignKey("model_packages.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    
    # State Machine
    # CREATED, UPLOADING, QUEUED, PARTITIONING, SCHEDULING, DISTRIBUTING, TRAINING, AGGREGATING, CHECKPOINTING, COMPLETED, FAILED, CANCELLED, PAUSED
    status = Column(String(32), default="CREATED", index=True, nullable=False)
    
    # Hyperparameters
    current_round = Column(Integer, default=0, nullable=False)
    max_rounds = Column(Integer, default=5, nullable=False)
    local_epochs = Column(Integer, default=2, nullable=False)
    batch_size = Column(Integer, default=32, nullable=False)
    learning_rate = Column(Float, default=0.001, nullable=False)
    target_accuracy = Column(Float, default=95.0, nullable=False) # In percent, e.g. 95.0%
    min_volunteer_nodes = Column(Integer, default=2, nullable=False)
    
    # Live Training Global Metrics
    global_accuracy = Column(Float, default=0.0) # Percentage
    global_loss = Column(Float, default=0.0)
    
    estimated_remaining_seconds = Column(Float, default=0.0)
    total_training_time_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

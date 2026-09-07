from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from backend.app.database import Base

class TrainingTask(Base):
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    round_number = Column(Integer, default=1, nullable=False)
    node_id = Column(String(64), nullable=False, index=True)
    partition_id = Column(Integer, ForeignKey("dataset_partitions.id"), nullable=False)
    
    # State: ASSIGNED, RUNNING, COMPLETED, FAILED, TIMEOUT, RETRYING
    status = Column(String(32), default="ASSIGNED", nullable=False, index=True)
    
    local_epochs = Column(Integer, default=2, nullable=False)
    batch_size = Column(Integer, default=32, nullable=False)
    learning_rate = Column(Float, default=0.001, nullable=False)
    
    progress_percent = Column(Float, default=0.0) # 0 to 100%
    current_epoch = Column(Integer, default=0)
    current_loss = Column(Float, default=0.0)
    current_accuracy = Column(Float, default=0.0)
    samples_processed = Column(Integer, default=0)
    training_time_seconds = Column(Float, default=0.0)
    
    update_file_path = Column(String(512), nullable=True)
    update_checksum_sha256 = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

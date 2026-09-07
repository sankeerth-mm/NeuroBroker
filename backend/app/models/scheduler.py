from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from backend.app.database import Base

class SchedulerDecision(Base):
    __tablename__ = "scheduler_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    round_number = Column(Integer, default=1, nullable=False)
    node_id = Column(String(64), nullable=False, index=True)
    
    is_selected = Column(Boolean, default=False, nullable=False)
    overall_score = Column(Float, default=0.0)
    
    cpu_score = Column(Float, default=0.0)
    ram_score = Column(Float, default=0.0)
    gpu_score = Column(Float, default=0.0)
    network_score = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    fairness_score = Column(Float, default=0.0)
    
    estimated_transfer_time_sec = Column(Float, default=0.0)
    estimated_training_time_sec = Column(Float, default=0.0)
    
    rationale = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

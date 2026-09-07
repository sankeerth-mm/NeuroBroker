from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from backend.app.database import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(String(16), default="INFO", index=True, nullable=False) # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(32), default="broker", index=True, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    
    job_id = Column(Integer, nullable=True, index=True)
    node_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False)
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

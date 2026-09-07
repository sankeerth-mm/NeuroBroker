from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.models.log import SystemLog, AuditLog
from backend.app.models.scheduler import SchedulerDecision
from backend.app.schemas.auth import UserResponse
from backend.app.schemas.admin import (
    AdminDashboardStats,
    SystemLogResponse,
    AuditLogResponse,
    SchedulerDecisionResponse,
)
from backend.app.auth.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["Administrator"])

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id.asc()))
    return result.scalars().all()

@router.get("/stats", response_model=AdminDashboardStats)
async def get_admin_dashboard_stats(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    u_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    j_count = (await db.execute(select(func.count(TrainingJob.id)))).scalar() or 0
    running_jobs = (await db.execute(select(func.count(TrainingJob.id)).where(TrainingJob.status.in_(["TRAINING", "SCHEDULING", "PARTITIONING", "AGGREGATING"])))).scalar() or 0
    completed_jobs = (await db.execute(select(func.count(TrainingJob.id)).where(TrainingJob.status == "COMPLETED"))).scalar() or 0
    failed_jobs = (await db.execute(select(func.count(TrainingJob.id)).where(TrainingJob.status == "FAILED"))).scalar() or 0
    
    nodes = (await db.execute(select(VolunteerNode))).scalars().all()
    online_count = sum(1 for n in nodes if n.status in ("ONLINE", "IDLE"))
    busy_count = sum(1 for n in nodes if n.status == "BUSY")
    unhealthy_count = sum(1 for n in nodes if n.status == "UNHEALTHY")
    offline_count = sum(1 for n in nodes if n.status == "OFFLINE")
    
    avg_rel = (sum(n.reliability_score for n in nodes) / len(nodes)) if nodes else 1.0
    rounds_sum = sum(n.rounds_participated for n in nodes)
    
    return AdminDashboardStats(
        total_users=u_count,
        total_jobs=j_count,
        running_jobs=running_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        total_nodes=len(nodes),
        online_nodes=online_count,
        busy_nodes=busy_count,
        unhealthy_nodes=unhealthy_count,
        offline_nodes=offline_count,
        avg_node_reliability=float(avg_rel),
        total_rounds_trained=rounds_sum,
    )

@router.get("/logs", response_model=List[SystemLogResponse])
async def get_system_logs(
    level: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(SystemLog).order_by(desc(SystemLog.timestamp)).limit(limit)
    if level:
        query = query.where(SystemLog.level == level.upper())
    if component:
        query = query.where(SystemLog.component == component.lower())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/scheduler-decisions", response_model=List[SchedulerDecisionResponse])
async def get_scheduler_decisions(
    job_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(SchedulerDecision).order_by(desc(SchedulerDecision.timestamp)).limit(limit)
    if job_id:
        query = query.where(SchedulerDecision.job_id == job_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

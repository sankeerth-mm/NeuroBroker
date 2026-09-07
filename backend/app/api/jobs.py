import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.user import User
from backend.app.models.job import TrainingJob
from backend.app.models.dataset import Dataset
from backend.app.models.model_pkg import ModelPackage, ModelVersion
from backend.app.models.task import TrainingTask
from backend.app.schemas.job import (
    JobCreateRequest,
    JobResponse,
    JobDetailResponse,
    JobTaskResponse,
)
from backend.app.schemas.model_pkg import ModelVersionResponse
from backend.app.auth.dependencies import get_current_active_user
from backend.app.jobs.orchestrator import orchestrator
from backend.app.reports.report_generator import report_generator
from backend.app.security.checksum import compute_sha256
from backend.app.ws.user_ws import user_ws_manager
from backend.app.logging.logger import log_event

router = APIRouter(prefix="/api/jobs", tags=["Training Jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify dataset exists
    d_query = select(Dataset).where(Dataset.id == job_in.dataset_id)
    dataset = (await db.execute(d_query)).scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Verify model package exists
    m_query = select(ModelPackage).where(ModelPackage.id == job_in.model_package_id)
    model_pkg = (await db.execute(m_query)).scalars().first()
    if not model_pkg:
        raise HTTPException(status_code=404, detail="Model package not found")
        
    count_res = await db.execute(select(func.count(TrainingJob.id)))
    job_num = (count_res.scalar() or 0) + 1
    job_code = f"JOB-{job_num:04d}"
    
    job = TrainingJob(
        job_code=job_code,
        user_id=current_user.id,
        name=job_in.name,
        description=job_in.description,
        model_package_id=job_in.model_package_id,
        dataset_id=job_in.dataset_id,
        status="CREATED",
        max_rounds=job_in.max_rounds,
        local_epochs=job_in.local_epochs,
        batch_size=job_in.batch_size,
        learning_rate=job_in.learning_rate,
        target_accuracy=job_in.target_accuracy,
        min_volunteer_nodes=job_in.min_volunteer_nodes,
        created_at=datetime.utcnow()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    await log_event(
        level="INFO",
        component="job",
        message=f"Training job '{job.name}' ({job.job_code}) created by user {current_user.email}.",
        job_id=job.id,
        db_session=db
    )
    
    return job

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(TrainingJob).order_by(desc(TrainingJob.created_at))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(TrainingJob).where(TrainingJob.id == job_id)
    result = await db.execute(query)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    dataset = (await db.execute(select(Dataset).where(Dataset.id == job.dataset_id))).scalars().first()
    model_pkg = (await db.execute(select(ModelPackage).where(ModelPackage.id == job.model_package_id))).scalars().first()
    versions = (await db.execute(select(ModelVersion).where(ModelVersion.job_id == job_id).order_by(ModelVersion.round_number.asc()))).scalars().all()
    tasks = (await db.execute(select(TrainingTask).where(TrainingTask.job_id == job_id).order_by(desc(TrainingTask.id)))).scalars().all()
    
    detail = JobDetailResponse.model_validate(job)
    detail.dataset = dataset
    detail.model_package = model_pkg
    detail.versions = [ModelVersionResponse.model_validate(v) for v in versions]
    detail.tasks = [JobTaskResponse.model_validate(t) for t in tasks]
    return detail

@router.post("/{job_id}/start")
async def start_training_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    job = (await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))).scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    await orchestrator.start_job(job_id)
    return {"message": f"Job {job.job_code} started successfully."}

@router.post("/{job_id}/stop")
async def stop_training_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await orchestrator.stop_job(job_id)
    return {"message": f"Job {job_id} stopping."}

@router.post("/{job_id}/pause")
async def pause_training_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await orchestrator.pause_job(job_id)
    return {"message": f"Job {job_id} pausing."}

@router.post("/{job_id}/resume")
async def resume_training_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await orchestrator.resume_job(job_id)
    return {"message": f"Job {job_id} resuming."}

@router.get("/{job_id}/rounds", response_model=List[ModelVersionResponse])
async def get_job_rounds(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ModelVersion).where(ModelVersion.job_id == job_id).order_by(ModelVersion.round_number.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}/tasks", response_model=List[JobTaskResponse])
async def get_job_tasks(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(TrainingTask).where(TrainingTask.job_id == job_id).order_by(desc(TrainingTask.id))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}/report")
async def get_job_report(job_id: int, db: AsyncSession = Depends(get_db)):
    report = await report_generator.generate_job_report(job_id, db)
    return report

@router.get("/{job_id}/checkpoints/latest")
async def download_latest_checkpoint(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ModelVersion).where(ModelVersion.job_id == job_id).order_by(desc(ModelVersion.round_number))
    result = await db.execute(query)
    ver = result.scalars().first()
    if not ver or not Path(ver.checkpoint_path).exists():
        raise HTTPException(status_code=404, detail="Latest checkpoint not found")
    return FileResponse(ver.checkpoint_path, filename=Path(ver.checkpoint_path).name)

@router.post("/{job_id}/tasks/{task_id}/progress")
async def report_task_progress(
    job_id: int,
    task_id: int,
    epoch: int = Form(...),
    loss: float = Form(...),
    accuracy: float = Form(...),
    progress_percent: float = Form(...),
    db: AsyncSession = Depends(get_db)
):
    query = select(TrainingTask).where(TrainingTask.id == task_id, TrainingTask.job_id == job_id)
    task = (await db.execute(query)).scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.current_epoch = epoch
    task.current_loss = loss
    task.current_accuracy = accuracy
    task.progress_percent = progress_percent
    task.status = "RUNNING"
    if not task.started_at:
        task.started_at = datetime.utcnow()
        
    await db.commit()
    
    # Broadcast to dashboard
    await user_ws_manager.broadcast("task_progress", {
        "job_id": job_id,
        "task_id": task_id,
        "node_id": task.node_id,
        "epoch": epoch,
        "loss": loss,
        "accuracy": accuracy,
        "progress_percent": progress_percent
    })
    return {"status": "ok"}

@router.post("/{job_id}/tasks/{task_id}/complete")
async def report_task_complete(
    job_id: int,
    task_id: int,
    loss: float = Form(...),
    accuracy: float = Form(...),
    sample_count: int = Form(...),
    training_time_seconds: float = Form(...),
    weights_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    query = select(TrainingTask).where(TrainingTask.id == task_id, TrainingTask.job_id == job_id)
    task = (await db.execute(query)).scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Save uploaded weights
    saved_dir = settings.NODE_UPDATES_DIR / f"job_{job_id}" / f"round_{task.round_number}"
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_file_path = saved_dir / f"{task.node_id}_update.pth"
    
    with open(saved_file_path, "wb") as f:
        shutil.copyfileobj(weights_file.file, f)
        
    checksum = compute_sha256(saved_file_path)
    
    task.status = "COMPLETED"
    task.current_loss = loss
    task.current_accuracy = accuracy
    task.samples_processed = sample_count
    task.training_time_seconds = training_time_seconds
    task.progress_percent = 100.0
    task.update_file_path = str(saved_file_path)
    task.update_checksum_sha256 = checksum
    task.completed_at = datetime.utcnow()
    
    await db.commit()
    
    await log_event(
        "INFO", "task",
        f"Node {task.node_id} completed task {task_id} for Round {task.round_number} ({sample_count} samples, {training_time_seconds:.1f}s, Acc: {accuracy:.2f}%)",
        job_id=job_id, node_id=task.node_id, db_session=db
    )
    
    await user_ws_manager.broadcast("task_completed", {
        "job_id": job_id,
        "task_id": task_id,
        "node_id": task.node_id,
        "loss": loss,
        "accuracy": accuracy,
        "training_time": training_time_seconds
    })
    
    return {"status": "ok", "checksum": checksum}

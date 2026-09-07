import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.job import TrainingJob
from backend.app.models.dataset import Dataset
from backend.app.models.model_pkg import ModelPackage, ModelVersion
from backend.app.models.task import TrainingTask
from backend.app.models.scheduler import SchedulerDecision
from backend.app.models.node import VolunteerNode

class TrainingReportGenerator:
    @staticmethod
    async def generate_job_report(job_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Generates comprehensive structured dictionary report for a training job."""
        job = (await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))).scalars().first()
        if not job:
            return {"error": "Job not found"}
            
        dataset = (await db.execute(select(Dataset).where(Dataset.id == job.dataset_id))).scalars().first()
        model_pkg = (await db.execute(select(ModelPackage).where(ModelPackage.id == job.model_package_id))).scalars().first()
        
        versions = (await db.execute(
            select(ModelVersion).where(ModelVersion.job_id == job_id).order_by(ModelVersion.round_number.asc())
        )).scalars().all()
        
        tasks = (await db.execute(
            select(TrainingTask).where(TrainingTask.job_id == job_id).order_by(TrainingTask.round_number.asc())
        )).scalars().all()
        
        decisions = (await db.execute(
            select(SchedulerDecision).where(SchedulerDecision.job_id == job_id).order_by(SchedulerDecision.round_number.asc())
        )).scalars().all()
        
        # Calculate node contributions
        node_contrib = {}
        for t in tasks:
            if t.status == "COMPLETED":
                if t.node_id not in node_contrib:
                    node_contrib[t.node_id] = {"samples": 0, "training_time": 0.0, "tasks_completed": 0}
                node_contrib[t.node_id]["samples"] += t.samples_processed
                node_contrib[t.node_id]["training_time"] += t.training_time_seconds
                node_contrib[t.node_id]["tasks_completed"] += 1
                
        report = {
            "job_summary": {
                "job_id": job.id,
                "job_code": job.job_code,
                "name": job.name,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "total_duration_sec": job.total_training_time_seconds,
                "rounds_completed": job.current_round,
                "max_rounds": job.max_rounds,
                "target_accuracy": job.target_accuracy,
                "final_accuracy": job.global_accuracy,
                "final_loss": job.global_loss,
            },
            "model_and_dataset": {
                "model_name": model_pkg.name if model_pkg else "Unknown",
                "framework": model_pkg.framework if model_pkg else "PyTorch",
                "dataset_name": dataset.name if dataset else "Unknown",
                "dataset_type": dataset.dataset_type if dataset else "Unknown",
                "total_samples": dataset.total_samples if dataset else 0,
                "is_non_iid": dataset.is_non_iid if dataset else False,
            },
            "hyperparameters": {
                "local_epochs": job.local_epochs,
                "batch_size": job.batch_size,
                "learning_rate": job.learning_rate,
                "min_volunteer_nodes": job.min_volunteer_nodes,
            },
            "round_convergence": [
                {
                    "round": v.round_number,
                    "accuracy": v.accuracy,
                    "loss": v.loss,
                    "samples": v.sample_count,
                    "participating_nodes": v.participating_nodes,
                }
                for v in versions
            ],
            "node_contributions": node_contrib,
            "scheduling_decisions_summary": [
                {
                    "round": d.round_number,
                    "node_id": d.node_id,
                    "selected": d.is_selected,
                    "score": d.overall_score,
                    "rationale": d.rationale,
                }
                for d in decisions
            ],
        }
        return report

report_generator = TrainingReportGenerator()

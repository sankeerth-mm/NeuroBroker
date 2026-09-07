import asyncio
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database import AsyncSessionLocal
from backend.app.config import settings
from backend.app.models.job import TrainingJob
from backend.app.models.dataset import Dataset, DatasetPartition
from backend.app.models.model_pkg import ModelPackage, ModelVersion
from backend.app.models.node import VolunteerNode
from backend.app.models.task import TrainingTask
from backend.app.models.scheduler import SchedulerDecision
from backend.app.scheduler import get_scheduler
from backend.app.scheduler.reliability import reliability_manager
from backend.app.partitioning.stratified import stratified_partitioner
from backend.app.aggregation.fedavg import fedavg_aggregator
from backend.app.aggregation.update_validator import update_validator
from backend.app.fault_tolerance.checkpoint_manager import checkpoint_manager
from backend.app.fault_tolerance.recovery_manager import recovery_manager
from backend.app.prediction.predictor import predictor
from backend.app.ws.user_ws import user_ws_manager
from backend.app.ws.volunteer_ws import volunteer_ws_manager
from backend.app.logging.logger import log_event, broker_logger

class TrainingOrchestrator:
    def __init__(self):
        # Maps job_id -> background task
        self.running_jobs: Dict[int, asyncio.Task] = {}
        # Maps job_id -> event for pausing/stopping
        self.job_controls: Dict[int, Dict[str, Any]] = {}

    async def start_job(self, job_id: int):
        """Entry point to launch background async training loop for a job."""
        if job_id in self.running_jobs and not self.running_jobs[job_id].done():
            broker_logger.warning(f"Job {job_id} is already running.")
            return
            
        self.job_controls[job_id] = {
            "stop_requested": False,
            "pause_requested": False,
        }
        
        task = asyncio.create_task(self._run_job_lifecycle(job_id))
        self.running_jobs[job_id] = task

    async def stop_job(self, job_id: int):
        if job_id in self.job_controls:
            self.job_controls[job_id]["stop_requested"] = True
            broker_logger.info(f"Stop signal sent for Job {job_id}")

    async def pause_job(self, job_id: int):
        if job_id in self.job_controls:
            self.job_controls[job_id]["pause_requested"] = True

    async def resume_job(self, job_id: int):
        if job_id in self.job_controls:
            self.job_controls[job_id]["pause_requested"] = False
        else:
            await self.start_job(job_id)

    async def _run_job_lifecycle(self, job_id: int):
        """Asynchronous execution loop for complete federated training job."""
        async with AsyncSessionLocal() as db:
            query = select(TrainingJob).where(TrainingJob.id == job_id)
            res = await db.execute(query)
            job = res.scalars().first()
            if not job:
                return
                
            job.status = "QUEUED"
            job.started_at = datetime.utcnow()
            await db.commit()
            
            await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": job.status})
            await log_event("INFO", "orchestrator", f"Job {job.job_code} queued for execution.", job_id=job.id, db_session=db)
            
            # Fetch Dataset and ModelPackage
            d_query = select(Dataset).where(Dataset.id == job.dataset_id)
            d_res = await db.execute(d_query)
            dataset = d_res.scalars().first()
            
            m_query = select(ModelPackage).where(ModelPackage.id == job.model_package_id)
            m_res = await db.execute(m_query)
            model_pkg = m_res.scalars().first()
            
            if not dataset or not model_pkg:
                job.status = "FAILED"
                job.error_message = "Dataset or Model Package not found."
                await db.commit()
                await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": job.status})
                return

        # Prepare Initial Model Checkpoint v0 if not already present
        async with AsyncSessionLocal() as db:
            init_ckpt_path, base_state_dict, start_round = await checkpoint_manager.load_latest_checkpoint(job_id, db)
            if base_state_dict is None:
                # Extract initial weights by building model dynamically from model_package
                job_ckpt_dir = settings.CHECKPOINTS_DIR / f"job_{job_id}"
                job_ckpt_dir.mkdir(parents=True, exist_ok=True)
                init_ckpt_path = job_ckpt_dir / "global_model_round_0.pth"
                
                # Build dummy base state dict from model package template
                from volunteer_node.model_loader import ModelLoader
                try:
                    loaded_model = ModelLoader.load_model_from_package(Path(model_pkg.file_path))
                    base_state_dict = loaded_model.state_dict()
                except Exception as e:
                    broker_logger.warning(f"Could not load initial weights from package ({e}), generating standard initialization.")
                    # Create generic initialization
                    base_state_dict = {
                        "conv1.weight": torch.randn(16, 1, 3, 3),
                        "conv1.bias": torch.zeros(16),
                        "conv2.weight": torch.randn(32, 16, 3, 3),
                        "conv2.bias": torch.zeros(32),
                        "fc1.weight": torch.randn(64, 32 * 7 * 7),
                        "fc1.bias": torch.zeros(64),
                        "fc2.weight": torch.randn(10, 64),
                        "fc2.bias": torch.zeros(10),
                    }
                
                torch.save(base_state_dict, init_ckpt_path)
                
                v0 = ModelVersion(
                    job_id=job_id,
                    round_number=0,
                    version_tag="v0",
                    accuracy=0.0,
                    loss=2.5,
                    sample_count=0,
                    checkpoint_path=str(init_ckpt_path),
                    checksum_sha256="initial",
                    participating_nodes=[]
                )
                db.add(v0)
                await db.commit()

        # Begin Federated Rounds Loop
        round_num = start_round
        
        while round_num < job.max_rounds:
            # Check user controls (stop / pause)
            if self.job_controls.get(job_id, {}).get("stop_requested", False):
                async with AsyncSessionLocal() as db:
                    q = select(TrainingJob).where(TrainingJob.id == job_id)
                    j = (await db.execute(q)).scalars().first()
                    j.status = "CANCELLED"
                    j.completed_at = datetime.utcnow()
                    await db.commit()
                    await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "CANCELLED"})
                return
                
            while self.job_controls.get(job_id, {}).get("pause_requested", False):
                async with AsyncSessionLocal() as db:
                    q = select(TrainingJob).where(TrainingJob.id == job_id)
                    j = (await db.execute(q)).scalars().first()
                    if j.status != "PAUSED":
                        j.status = "PAUSED"
                        await db.commit()
                        await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "PAUSED"})
                await asyncio.sleep(2)
                
            round_num += 1
            round_start_time = datetime.utcnow()
            
            # 1. State: SCHEDULING
            async with AsyncSessionLocal() as db:
                q = select(TrainingJob).where(TrainingJob.id == job_id)
                j = (await db.execute(q)).scalars().first()
                j.status = "SCHEDULING"
                j.current_round = round_num
                await db.commit()
                await user_ws_manager.broadcast("job_round_start", {"job_id": job.id, "round": round_num, "status": "SCHEDULING"})
                
                # Fetch online/idle volunteer nodes
                n_query = select(VolunteerNode).where(VolunteerNode.status.in_(["ONLINE", "IDLE"]))
                n_res = await db.execute(n_query)
                available_nodes = n_res.scalars().all()
                
                if len(available_nodes) < j.min_volunteer_nodes:
                    msg = f"Insufficient volunteer nodes online ({len(available_nodes)} online < {j.min_volunteer_nodes} required). Waiting for nodes..."
                    await log_event("WARNING", "orchestrator", msg, job_id=job.id, db_session=db)
                    await asyncio.sleep(5)
                    round_num -= 1
                    continue
                    
                # Run Scheduler
                scheduler = get_scheduler()
                dataset_size = Path(dataset.file_path).stat().st_size
                model_size = Path(model_pkg.file_path).stat().st_size
                
                k_needed = min(len(available_nodes), max(j.min_volunteer_nodes, 4))
                selected_nodes, decision_records = scheduler.select_nodes(
                    available_nodes=available_nodes,
                    job=j,
                    dataset_size_bytes=dataset_size,
                    model_size_bytes=model_size,
                    k_needed=k_needed
                )
                
                # Persist scheduler decision explanations to DB
                for dec in decision_records:
                    record = SchedulerDecision(
                        job_id=job_id,
                        round_number=round_num,
                        node_id=dec["node_id"],
                        is_selected=dec["is_selected"],
                        overall_score=dec["overall_score"],
                        cpu_score=dec["cpu_score"],
                        ram_score=dec["ram_score"],
                        gpu_score=dec["gpu_score"],
                        network_score=dec["network_score"],
                        reliability_score=dec["reliability_score"],
                        fairness_score=dec["fairness_score"],
                        estimated_transfer_time_sec=dec["estimated_transfer_time_sec"],
                        estimated_training_time_sec=dec["estimated_training_time_sec"],
                        rationale=dec["rationale"]
                    )
                    db.add(record)
                await db.commit()
                
                allocations = scheduler.calculate_data_allocations(selected_nodes)
                await log_event("INFO", "scheduler", f"Round {round_num}: Selected {len(selected_nodes)} nodes ({[n.node_id for n in selected_nodes]}).", job_id=job.id, db_session=db)

            # 2. State: PARTITIONING
            async with AsyncSessionLocal() as db:
                q = select(TrainingJob).where(TrainingJob.id == job_id)
                j = (await db.execute(q)).scalars().first()
                j.status = "PARTITIONING"
                await db.commit()
                await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "PARTITIONING"})
                
                dataset_path = Path(dataset.file_path)
                if dataset.dataset_type == "csv_classification":
                    partitions = stratified_partitioner.partition_csv_dataset(
                        csv_file_path=dataset_path,
                        label_column=dataset.label_column or "label",
                        job_id=job_id,
                        partition_weights=allocations
                    )
                else:
                    # Unpack if zip
                    temp_data_dir = settings.DATASETS_DIR / f"temp_job_{job_id}"
                    if not temp_data_dir.exists():
                        with zipfile.ZipFile(dataset_path, "r") as z:
                            z.extractall(temp_data_dir)
                    partitions = stratified_partitioner.partition_image_dataset(
                        extracted_dataset_dir=temp_data_dir,
                        job_id=job_id,
                        partition_weights=allocations
                    )
                    
                # Create Tasks in DB
                created_tasks = []
                for idx, node in enumerate(selected_nodes):
                    p_info = partitions[idx] if idx < len(partitions) else partitions[-1]
                    
                    db_partition = DatasetPartition(
                        dataset_id=dataset.id,
                        job_id=job_id,
                        node_id=node.node_id,
                        partition_index=idx,
                        sample_count=p_info["sample_count"],
                        class_distribution=p_info["class_distribution"],
                        file_path=p_info["file_path"],
                        checksum_sha256=p_info["checksum_sha256"],
                        is_assigned=True
                    )
                    db.add(db_partition)
                    await db.flush()
                    
                    task = TrainingTask(
                        job_id=job_id,
                        round_number=round_num,
                        node_id=node.node_id,
                        partition_id=db_partition.id,
                        status="ASSIGNED",
                        local_epochs=j.local_epochs,
                        batch_size=j.batch_size,
                        learning_rate=j.learning_rate,
                        assigned_at=datetime.utcnow()
                    )
                    db.add(task)
                    created_tasks.append(task)
                    
                    # Mark node as BUSY
                    n_record = (await db.execute(select(VolunteerNode).where(VolunteerNode.node_id == node.node_id))).scalars().first()
                    if n_record:
                        n_record.status = "BUSY"
                        n_record.current_job_id = job_id
                        
                await db.commit()

            # 3. State: DISTRIBUTING & TRAINING
            async with AsyncSessionLocal() as db:
                q = select(TrainingJob).where(TrainingJob.id == job_id)
                j = (await db.execute(q)).scalars().first()
                j.status = "TRAINING"
                await db.commit()
                await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "TRAINING"})
                
            # Dispatch tasks to volunteer nodes via WebSocket / REST
            for idx, node in enumerate(selected_nodes):
                task_obj = created_tasks[idx]
                task_payload = {
                    "task_id": task_obj.id,
                    "job_id": job_id,
                    "round_number": round_num,
                    "model_download_url": f"/api/models/{model_pkg.id}/download",
                    "checkpoint_download_url": f"/api/jobs/{job_id}/checkpoints/latest",
                    "partition_download_url": f"/api/datasets/partitions/{task_obj.partition_id}/download",
                    "local_epochs": job.local_epochs,
                    "batch_size": job.batch_size,
                    "learning_rate": job.learning_rate,
                }
                # Dispatch message
                await volunteer_ws_manager.send_to_node(node.node_id, "assign_task", task_payload)
                
            # Wait for all nodes to complete or handle timeout
            max_wait_seconds = 180
            start_wait = datetime.utcnow()
            
            while True:
                await asyncio.sleep(2)
                elapsed = (datetime.utcnow() - start_wait).total_seconds()
                
                async with AsyncSessionLocal() as db:
                    t_query = select(TrainingTask).where(TrainingTask.job_id == job_id, TrainingTask.round_number == round_num)
                    t_res = await db.execute(t_query)
                    active_tasks = t_res.scalars().all()
                    
                    all_done = all(t.status in ("COMPLETED", "FAILED", "TIMEOUT") for t in active_tasks)
                    
                    if elapsed > max_wait_seconds:
                        # Timeout remaining tasks
                        for t in active_tasks:
                            if t.status in ("ASSIGNED", "RUNNING"):
                                t.status = "TIMEOUT"
                                t.error_message = "Training task timed out on volunteer node."
                        await db.commit()
                        all_done = True
                        
                    if all_done:
                        break
                        
            # 4. State: AGGREGATING (FedAvg)
            async with AsyncSessionLocal() as db:
                q = select(TrainingJob).where(TrainingJob.id == job_id)
                j = (await db.execute(q)).scalars().first()
                j.status = "AGGREGATING"
                await db.commit()
                await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "AGGREGATING"})
                
                t_query = select(TrainingTask).where(TrainingTask.job_id == job_id, TrainingTask.round_number == round_num)
                t_res = await db.execute(t_query)
                round_tasks = t_res.scalars().all()
                
                can_aggregate, action_desc, completed_tasks = await recovery_manager.evaluate_round_faults(j, round_tasks, db)
                
                if not can_aggregate or not completed_tasks:
                    j.status = "FAILED"
                    j.error_message = f"Round {round_num} failed: {action_desc}"
                    await db.commit()
                    await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "FAILED"})
                    return
                    
                # Collect verified state_dicts from completed tasks
                node_updates = []
                for ct in completed_tasks:
                    update_file = Path(ct.update_file_path) if ct.update_file_path else None
                    if update_file and update_file.exists():
                        is_valid, err, s_dict = update_validator.validate_update(
                            update_file, ct.update_checksum_sha256, base_state_dict, ct.samples_processed
                        )
                        if is_valid and s_dict:
                            node_updates.append({
                                "node_id": ct.node_id,
                                "state_dict": s_dict,
                                "sample_count": ct.samples_processed,
                                "loss": ct.current_loss,
                                "accuracy": ct.current_accuracy,
                            })
                            # Reward node reliability
                            n_rec = (await db.execute(select(VolunteerNode).where(VolunteerNode.node_id == ct.node_id))).scalars().first()
                            if n_rec:
                                reliability_manager.update_on_task_success(n_rec, ct.training_time_seconds, ct.samples_processed)
                                n_rec.status = "ONLINE"
                                n_rec.current_task_id = None
                                
                if not node_updates:
                    j.status = "FAILED"
                    j.error_message = "No valid model updates could be verified for FedAvg."
                    await db.commit()
                    return
                    
                # 5. Execute Weighted FedAvg
                output_ckpt = checkpoint_manager.get_checkpoint_path(job_id, round_num)
                agg_state_dict, ckpt_hash, round_loss, round_acc = fedavg_aggregator.aggregate(
                    node_updates=node_updates,
                    base_state_dict=base_state_dict,
                    output_checkpoint_path=output_ckpt
                )
                
                base_state_dict = agg_state_dict
                
                # Save ModelVersion in DB
                m_ver = ModelVersion(
                    job_id=job_id,
                    round_number=round_num,
                    version_tag=f"v{round_num}",
                    accuracy=round_acc,
                    loss=round_loss,
                    sample_count=sum(u["sample_count"] for u in node_updates),
                    checkpoint_path=str(output_ckpt),
                    checksum_sha256=ckpt_hash,
                    participating_nodes=[u["node_id"] for u in node_updates],
                    aggregation_time_seconds=1.2
                )
                db.add(m_ver)
                
                # Update Job global metrics
                j.global_accuracy = round_acc
                j.global_loss = round_loss
                j.current_round = round_num
                
                # Update Performance Predictor
                round_duration = (datetime.utcnow() - round_start_time).total_seconds()
                j.total_training_time_seconds += round_duration
                predictor.record_round_completion(round_duration)
                j.estimated_remaining_seconds = predictor.estimate_job_remaining(
                    round_num, j.max_rounds, round_acc, j.target_accuracy
                )
                
                await db.commit()
                
                await log_event(
                    "INFO", "aggregator",
                    f"Round {round_num} Aggregated via FedAvg: Global Acc = {round_acc:.2f}%, Loss = {round_loss:.4f} (Saved to {output_ckpt.name})",
                    job_id=job.id, db_session=db
                )
                
                await user_ws_manager.broadcast("round_completed", {
                    "job_id": job_id,
                    "round": round_num,
                    "accuracy": round_acc,
                    "loss": round_loss,
                    "participating_nodes": [u["node_id"] for u in node_updates],
                    "estimated_remaining_seconds": j.estimated_remaining_seconds
                })
                
                # Check for target accuracy or round completion
                if round_acc >= j.target_accuracy or round_num >= j.max_rounds:
                    j.status = "COMPLETED"
                    j.completed_at = datetime.utcnow()
                    await db.commit()
                    await user_ws_manager.broadcast("job_status_change", {"job_id": job.id, "status": "COMPLETED"})
                    await log_event("INFO", "orchestrator", f"Job {j.job_code} successfully COMPLETED at Round {round_num}!", job_id=job.id, db_session=db)
                    break

orchestrator = TrainingOrchestrator()

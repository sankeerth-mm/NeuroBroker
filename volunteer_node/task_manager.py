import shutil
from pathlib import Path
from typing import Dict, Any
import torch
from volunteer_node.logger import logger
from volunteer_node.node_client import NodeClient
from volunteer_node.model_loader import model_loader
from volunteer_node.dataset_loader import dataset_loader
from volunteer_node.trainer import local_trainer
from volunteer_node.security import sandbox_security

class TaskManager:
    def __init__(self, client: NodeClient, work_dir: Path):
        self.client = client
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def execute_task(self, task_data: Dict[str, Any]):
        """
        Executes a complete federated training task received from broker.
        """
        task_id = task_data["task_id"]
        job_id = task_data["job_id"]
        round_num = task_data["round_number"]
        local_epochs = task_data.get("local_epochs", 2)
        batch_size = task_data.get("batch_size", 32)
        learning_rate = task_data.get("learning_rate", 0.001)
        
        task_dir = self.work_dir / f"job_{job_id}_round_{round_num}_task_{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"==> [TASK START] Job {job_id} | Round {round_num} | Task ID: {task_id}")
        
        try:
            # 1. Download Model Package
            model_pkg_path = task_dir / "model_pkg.zip"
            logger.info("  1. Downloading model package...")
            self.client.download_file(task_data["model_download_url"], model_pkg_path)
            
            # 2. Download Dataset Partition
            partition_path = task_dir / "partition.zip"
            logger.info("  2. Downloading assigned dataset partition...")
            self.client.download_file(task_data["partition_download_url"], partition_path)
            
            # 3. Download Global Model Checkpoint (if available)
            global_sd = None
            if "checkpoint_download_url" in task_data:
                try:
                    ckpt_path = task_dir / "global_model.pth"
                    self.client.download_file(task_data["checkpoint_download_url"], ckpt_path)
                    global_sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)
                    if isinstance(global_sd, dict) and "state_dict" in global_sd:
                        global_sd = global_sd["state_dict"]
                except Exception as e:
                    logger.warning(f"Could not load global checkpoint ({e}), using initialized weights.")
                    
            # 4. Load Model & Dataset
            logger.info("  3. Building model architecture and DataLoader...")
            model = model_loader.load_model_from_package(model_pkg_path)
            dataloader, total_samples = dataset_loader.create_dataloader(partition_path, batch_size=batch_size)
            
            # 5. Execute Local Training
            logger.info(f"  4. Training locally on {total_samples} samples...")
            
            def progress_cb(ep, loss_val, acc_val, pct):
                self.client.report_task_progress(job_id, task_id, ep, loss_val, acc_val, pct)
                
            local_weights_path = task_dir / "local_update.pth"
            updated_sd, final_loss, final_acc, elapsed_sec = local_trainer.train(
                model=model,
                dataloader=dataloader,
                global_state_dict=global_sd,
                local_epochs=local_epochs,
                learning_rate=learning_rate,
                progress_callback=progress_cb,
                save_path=local_weights_path
            )
            
            # 6. Upload Completion Update
            logger.info("  5. Uploading trained weights and metrics to Broker...")
            self.client.upload_task_completion(
                job_id=job_id,
                task_id=task_id,
                loss=final_loss,
                accuracy=final_acc,
                sample_count=total_samples,
                training_time_sec=elapsed_sec,
                weights_path=local_weights_path
            )
            logger.info(f"==> [TASK COMPLETED] Successfully uploaded update for Task {task_id}!")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        finally:
            # Cleanup task directory
            shutil.rmtree(task_dir, ignore_errors=True)

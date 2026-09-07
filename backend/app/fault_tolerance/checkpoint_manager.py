from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import torch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.config import settings
from backend.app.models.model_pkg import ModelVersion
from backend.app.logging.logger import broker_logger

class CheckpointManager:
    @staticmethod
    def get_checkpoint_path(job_id: int, round_number: int) -> Path:
        return settings.CHECKPOINTS_DIR / f"job_{job_id}" / f"global_model_round_{round_number}.pth"

    @staticmethod
    async def load_latest_checkpoint(job_id: int, db: AsyncSession) -> Tuple[Optional[Path], Optional[Dict[str, torch.Tensor]], int]:
        """
        Loads the latest global model state_dict for job_id from DB/disk for crash recovery or next round.
        Returns (checkpoint_path, state_dict, round_number).
        """
        query = (
            select(ModelVersion)
            .where(ModelVersion.job_id == job_id)
            .order_by(desc(ModelVersion.round_number))
        )
        result = await db.execute(query)
        latest_version = result.scalars().first()
        
        if not latest_version:
            return None, None, 0
            
        ckpt_path = Path(latest_version.checkpoint_path)
        if not ckpt_path.exists():
            broker_logger.error(f"Checkpoint file does not exist on disk: {ckpt_path}")
            return None, None, latest_version.round_number
            
        try:
            state_dict = torch.load(ckpt_path, map_location="cpu", weights_only=False)
            if isinstance(state_dict, dict) and "state_dict" in state_dict:
                state_dict = state_dict["state_dict"]
            return ckpt_path, state_dict, latest_version.round_number
        except Exception as e:
            broker_logger.error(f"Failed to load checkpoint {ckpt_path}: {e}")
            return None, None, latest_version.round_number

checkpoint_manager = CheckpointManager()

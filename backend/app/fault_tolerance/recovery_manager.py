from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.config import settings
from backend.app.models.job import TrainingJob
from backend.app.models.task import TrainingTask
from backend.app.models.node import VolunteerNode
from backend.app.scheduler.reliability import reliability_manager
from backend.app.logging.logger import log_event

class RecoveryManager:
    @staticmethod
    async def evaluate_round_faults(
        job: TrainingJob,
        tasks: List[TrainingTask],
        db: AsyncSession
    ) -> Tuple[bool, str, List[TrainingTask]]:
        """
        Evaluates task statuses in a federated round.
        Returns:
            (can_aggregate, action_description, successful_tasks)
        """
        completed = [t for t in tasks if t.status == "COMPLETED"]
        failed = [t for t in tasks if t.status in ("FAILED", "TIMEOUT")]
        
        # Penalize reliability for failed nodes
        for ft in failed:
            query = select(VolunteerNode).where(VolunteerNode.node_id == ft.node_id)
            res = await db.execute(query)
            node = res.scalars().first()
            if node:
                reliability_manager.update_on_task_failure(node, ft.error_message or "Task Failed")
                node.status = "ONLINE"
                node.current_task_id = None
                
        await db.commit()
        
        # Check if minimum volunteer participation threshold is satisfied
        if len(completed) >= job.min_volunteer_nodes:
            action = f"Proceeding with FedAvg aggregation using {len(completed)}/{len(tasks)} completed node updates ({len(failed)} nodes failed/dropped)."
            await log_event(
                level="WARNING" if failed else "INFO",
                component="fault_tolerance",
                message=action,
                job_id=job.id,
                db_session=db
            )
            return True, action, completed
        else:
            action = f"Insufficient completed nodes: {len(completed)} completed < minimum required {job.min_volunteer_nodes}."
            await log_event(
                level="ERROR",
                component="fault_tolerance",
                message=action,
                job_id=job.id,
                db_session=db
            )
            return False, action, completed

recovery_manager = RecoveryManager()

from typing import Tuple
from backend.app.models.node import VolunteerNode

class ReliabilityManager:
    @staticmethod
    def update_on_task_success(node: VolunteerNode, training_time_sec: float, sample_count: int):
        """Increase reliability score upon successful verified update."""
        node.tasks_completed += 1
        node.total_training_time_seconds += training_time_sec
        node.total_samples_processed += sample_count
        node.rounds_participated += 1
        
        # Exponential moving average boost up towards 1.0
        node.reliability_score = min(1.0, node.reliability_score * 0.95 + 0.05 * 1.0)

    @staticmethod
    def update_on_task_failure(node: VolunteerNode, reason: str = "Training Failed"):
        """Penalize reliability score on failure, disconnect, or timeout."""
        node.tasks_failed += 1
        penalty = 0.15
        if "Timeout" in reason:
            penalty = 0.20
        elif "Corrupt" in reason:
            penalty = 0.35
            
        node.reliability_score = max(0.1, node.reliability_score - penalty)

    @staticmethod
    def update_on_disconnect(node: VolunteerNode):
        """Penalize reliability on unexpected drop during task."""
        node.tasks_failed += 1
        node.reliability_score = max(0.1, node.reliability_score - 0.20)

reliability_manager = ReliabilityManager()

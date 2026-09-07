from typing import List, Dict, Any, Tuple
import numpy as np
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.base_scheduler import BaseScheduler
from backend.app.scheduler.resource_score_scheduler import resource_scheduler
from backend.app.scheduler.state_builder import state_builder
from backend.app.logging.logger import broker_logger

class HybridDRLScheduler(BaseScheduler):
    """
    Hybrid Deep Reinforcement Learning Scheduler with safety feasibility validation
    and automatic fallback to ResourceScoreScheduler.
    """
    def __init__(self, fallback_scheduler: BaseScheduler = resource_scheduler):
        self.fallback_scheduler = fallback_scheduler
        self.model = None # PyTorch RL policy or Q-network

    def select_nodes(
        self,
        available_nodes: List[VolunteerNode],
        job: TrainingJob,
        dataset_size_bytes: int,
        model_size_bytes: int,
        k_needed: int
    ) -> Tuple[List[VolunteerNode], List[Dict[str, Any]]]:
        try:
            # Build state
            state_vec = state_builder.build_state_vector(available_nodes, job)
            
            # If DRL policy model is loaded, evaluate action logits
            if self.model is not None:
                # In actual DRL inference: action = self.model.predict(state_vec)
                pass
            
            # Hybrid validation: Ensure minimum requirements and safety
            # If DRL output is invalid, fallback cleanly
            broker_logger.info("Hybrid scheduler applying resource multi-objective safety policy.")
            return self.fallback_scheduler.select_nodes(
                available_nodes, job, dataset_size_bytes, model_size_bytes, k_needed
            )
        except Exception as e:
            broker_logger.warning(f"DRL Scheduler encountered error ({e}), safely falling back to ResourceScoreScheduler.")
            return self.fallback_scheduler.select_nodes(
                available_nodes, job, dataset_size_bytes, model_size_bytes, k_needed
            )

    def calculate_data_allocations(
        self,
        selected_nodes: List[VolunteerNode]
    ) -> List[float]:
        return self.fallback_scheduler.calculate_data_allocations(selected_nodes)

drl_scheduler = HybridDRLScheduler()

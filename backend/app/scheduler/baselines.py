import random
from typing import List, Dict, Any, Tuple
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.base_scheduler import BaseScheduler

class RoundRobinScheduler(BaseScheduler):
    def __init__(self):
        self.current_idx = 0

    def select_nodes(
        self,
        available_nodes: List[VolunteerNode],
        job: TrainingJob,
        dataset_size_bytes: int,
        model_size_bytes: int,
        k_needed: int
    ) -> Tuple[List[VolunteerNode], List[Dict[str, Any]]]:
        if not available_nodes:
            return [], []
        
        N = len(available_nodes)
        selected = []
        for i in range(min(k_needed, N)):
            node = available_nodes[(self.current_idx + i) % N]
            selected.append(node)
        self.current_idx = (self.current_idx + k_needed) % N
        
        decisions = [
            {
                "job_id": job.id,
                "round_number": (job.current_round or 0) + 1,
                "node_id": n.node_id,
                "is_selected": n in selected,
                "overall_score": 0.5,
                "cpu_score": 0.5,
                "ram_score": 0.5,
                "gpu_score": 0.5,
                "network_score": 0.5,
                "reliability_score": float(n.reliability_score or 1.0),
                "fairness_score": 1.0,
                "estimated_transfer_time_sec": 5.0,
                "estimated_training_time_sec": 15.0,
                "rationale": f"[{n.node_id}] Round-robin rotation assignment.",
            }
            for n in available_nodes
        ]
        return selected, decisions

    def calculate_data_allocations(self, selected_nodes: List[VolunteerNode]) -> List[float]:
        # Equal split
        k = len(selected_nodes)
        return [1.0 / k] * k if k > 0 else []


class RandomScheduler(BaseScheduler):
    def select_nodes(
        self,
        available_nodes: List[VolunteerNode],
        job: TrainingJob,
        dataset_size_bytes: int,
        model_size_bytes: int,
        k_needed: int
    ) -> Tuple[List[VolunteerNode], List[Dict[str, Any]]]:
        if not available_nodes:
            return [], []
        
        shuffled = list(available_nodes)
        random.shuffle(shuffled)
        selected = shuffled[:k_needed]
        
        decisions = [
            {
                "job_id": job.id,
                "round_number": (job.current_round or 0) + 1,
                "node_id": n.node_id,
                "is_selected": n in selected,
                "overall_score": 0.5,
                "cpu_score": 0.5,
                "ram_score": 0.5,
                "gpu_score": 0.5,
                "network_score": 0.5,
                "reliability_score": float(n.reliability_score or 1.0),
                "fairness_score": 1.0,
                "estimated_transfer_time_sec": 5.0,
                "estimated_training_time_sec": 15.0,
                "rationale": f"[{n.node_id}] Random assignment.",
            }
            for n in available_nodes
        ]
        return selected, decisions

    def calculate_data_allocations(self, selected_nodes: List[VolunteerNode]) -> List[float]:
        k = len(selected_nodes)
        return [1.0 / k] * k if k > 0 else []

round_robin_scheduler = RoundRobinScheduler()
random_scheduler = RandomScheduler()

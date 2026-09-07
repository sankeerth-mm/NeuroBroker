from typing import List, Dict, Any
import numpy as np
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob

class StateBuilder:
    @staticmethod
    def build_state_vector(
        nodes: List[VolunteerNode],
        job: TrainingJob,
        max_nodes: int = 10
    ) -> np.ndarray:
        """
        Builds a normalized state feature vector for RL agents.
        Each node has 6 features: [cpu_free, ram_free, has_gpu, network_speed, reliability, rounds_participated].
        Job has 3 features: [current_round_ratio, target_accuracy_ratio, min_nodes].
        """
        node_features = []
        for i in range(max_nodes):
            if i < len(nodes):
                n = nodes[i]
                cpu_free = max(0.0, 1.0 - (n.cpu_usage / 100.0))
                ram_free = max(0.0, 1.0 - (n.ram_usage_percent / 100.0))
                has_gpu = 1.0 if (n.cuda_available or (n.gpu_name and "CPU" not in n.gpu_name.upper())) else 0.0
                net_norm = min(1.0, n.network_download_mbps / 1000.0)
                rel = float(n.reliability_score or 1.0)
                rounds = min(1.0, (n.rounds_participated or 0) / 20.0)
                node_features.extend([cpu_free, ram_free, has_gpu, net_norm, rel, rounds])
            else:
                # Padding
                node_features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                
        job_features = [
            min(1.0, job.current_round / max(1, job.max_rounds)),
            min(1.0, job.target_accuracy / 100.0),
            min(1.0, job.min_volunteer_nodes / 10.0)
        ]
        
        return np.array(node_features + job_features, dtype=np.float32)

state_builder = StateBuilder()

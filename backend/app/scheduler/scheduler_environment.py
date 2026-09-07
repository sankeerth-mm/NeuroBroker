from typing import List, Tuple, Dict, Any
import numpy as np
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.state_builder import state_builder
from backend.app.scheduler.reward import reward_calculator

class SchedulerEnvironment:
    """
    Simulation / Gym-like environment interface for RL scheduling agents.
    """
    def __init__(self, nodes: List[VolunteerNode], job: TrainingJob):
        self.nodes = nodes
        self.job = job
        self.current_step = 0
        self.max_steps = job.max_rounds

    def reset(self) -> np.ndarray:
        self.current_step = 0
        return state_builder.build_state_vector(self.nodes, self.job)

    def step(self, action_mask: List[int]) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Takes action (binary selection mask over nodes), simulates one round step, returns (next_state, reward, done, info).
        """
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # Calculate simulated duration and accuracy gain based on selected node capabilities
        selected_nodes = [self.nodes[i] for i in range(min(len(self.nodes), len(action_mask))) if action_mask[i] == 1]
        
        if not selected_nodes:
            return state_builder.build_state_vector(self.nodes, self.job), -10.0, True, {"error": "No nodes selected"}
            
        avg_compute = sum(n.overall_capability_score for n in selected_nodes) / len(selected_nodes)
        sim_duration = max(5.0, 30.0 / (avg_compute + 0.5))
        sim_acc_gain = min(5.0, 2.0 * avg_compute)
        
        reward = reward_calculator.calculate_reward(
            round_duration_sec=sim_duration,
            round_accuracy_gain=sim_acc_gain,
            failed_tasks_count=0,
            fairness_jain_index=0.9
        )
        
        next_state = state_builder.build_state_vector(self.nodes, self.job)
        return next_state, reward, done, {"duration": sim_duration, "acc_gain": sim_acc_gain}

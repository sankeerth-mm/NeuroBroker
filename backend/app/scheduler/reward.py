from typing import List, Dict, Any

class RewardCalculator:
    @staticmethod
    def calculate_reward(
        round_duration_sec: float,
        round_accuracy_gain: float,
        failed_tasks_count: int,
        fairness_jain_index: float
    ) -> float:
        """
        Calculates RL reward:
        Reward = + w_acc * accuracy_gain - w_time * log(duration) - w_fail * failures + w_fair * fairness
        """
        w_acc = 10.0
        w_time = 1.5
        w_fail = 5.0
        w_fair = 2.0
        
        reward = (
            w_acc * max(0.0, round_accuracy_gain)
            - w_time * (round_duration_sec / 10.0)
            - w_fail * failed_tasks_count
            + w_fair * fairness_jain_index
        )
        return float(reward)

reward_calculator = RewardCalculator()

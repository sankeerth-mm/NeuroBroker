from typing import List

class RollingAveragePredictor:
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.ema_round_time: float = 0.0

    def update_round_time(self, round_time_sec: float) -> float:
        if self.ema_round_time <= 0:
            self.ema_round_time = round_time_sec
        else:
            self.ema_round_time = self.alpha * round_time_sec + (1.0 - self.alpha) * self.ema_round_time
        return self.ema_round_time

    def estimate_remaining_time(self, current_round: int, max_rounds: int, current_acc: float, target_acc: float) -> float:
        rounds_left = max(0, max_rounds - current_round)
        if rounds_left == 0 or self.ema_round_time <= 0:
            return 0.0
        return float(rounds_left * self.ema_round_time)

rolling_predictor = RollingAveragePredictor()

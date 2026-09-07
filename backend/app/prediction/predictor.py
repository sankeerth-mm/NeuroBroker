from typing import List, Dict, Any
from backend.app.prediction.rolling_average import rolling_predictor, RollingAveragePredictor
from backend.app.prediction.optional_lstm import lstm_predictor_model

class PerformancePredictor:
    def __init__(self):
        self.rolling = rolling_predictor

    def record_round_completion(self, round_time_sec: float) -> float:
        return self.rolling.update_round_time(round_time_sec)

    def estimate_job_remaining(self, current_round: int, max_rounds: int, current_acc: float, target_acc: float) -> float:
        return self.rolling.estimate_remaining_time(current_round, max_rounds, current_acc, target_acc)

predictor = PerformancePredictor()

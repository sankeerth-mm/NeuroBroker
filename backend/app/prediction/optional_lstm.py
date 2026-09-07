import torch
import torch.nn as nn
from typing import List

class LSTMExecutionTimePredictor(nn.Module):
    """
    Lightweight LSTM network for multi-round training duration time series forecasting.
    """
    def __init__(self, input_dim: int = 4, hidden_dim: int = 16, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]
        prediction = self.fc(last_step)
        return torch.relu(prediction) # Execution time is positive

lstm_predictor_model = LSTMExecutionTimePredictor()

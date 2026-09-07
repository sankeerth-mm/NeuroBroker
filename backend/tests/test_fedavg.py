import pytest
import tempfile
from pathlib import Path
import torch
from backend.app.aggregation.fedavg import fedavg_aggregator
from backend.app.aggregation.update_validator import update_validator

def test_fedavg_mathematical_precision():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 2 synthetic node updates
        # Node 1 trained 100 samples with weights all 1.0
        sd1 = {"layer.weight": torch.ones(2, 2) * 1.0, "layer.bias": torch.ones(2) * 1.0}
        # Node 2 trained 300 samples with weights all 5.0
        sd2 = {"layer.weight": torch.ones(2, 2) * 5.0, "layer.bias": torch.ones(2) * 5.0}
        
        # Expected calculation: (100/400)*1.0 + (300/400)*5.0 = 0.25*1 + 0.75*5 = 0.25 + 3.75 = 4.0
        updates = [
            {"node_id": "NODE-01", "state_dict": sd1, "sample_count": 100, "loss": 1.0, "accuracy": 80.0},
            {"node_id": "NODE-02", "state_dict": sd2, "sample_count": 300, "loss": 0.5, "accuracy": 90.0},
        ]
        
        ckpt_path = Path(tmpdir) / "global_model.pth"
        agg_sd, checksum, loss, acc = fedavg_aggregator.aggregate(
            node_updates=updates,
            base_state_dict=sd1,
            output_checkpoint_path=ckpt_path
        )
        
        assert ckpt_path.exists()
        assert torch.allclose(agg_sd["layer.weight"], torch.ones(2, 2) * 4.0)
        assert torch.allclose(agg_sd["layer.bias"], torch.ones(2) * 4.0)
        assert abs(acc - (0.25 * 80.0 + 0.75 * 90.0)) < 1e-4
        assert abs(loss - (0.25 * 1.0 + 0.75 * 0.5)) < 1e-4

def test_update_validator_nan_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        corrupted_sd = {"layer.weight": torch.tensor([[1.0, float('nan')], [0.0, 1.0]])}
        corrupt_path = Path(tmpdir) / "corrupt.pth"
        torch.save(corrupted_sd, corrupt_path)
        
        base_sd = {"layer.weight": torch.ones(2, 2)}
        is_valid, err, _ = update_validator.validate_update(corrupt_path, None, base_sd, sample_count=50)
        assert is_valid is False
        assert "NaN" in err

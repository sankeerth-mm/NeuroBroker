import copy
from pathlib import Path
from typing import List, Dict, Any, Tuple
import torch
from backend.app.config import settings
from backend.app.security.checksum import compute_sha256
from backend.app.aggregation.update_validator import update_validator
from backend.app.logging.logger import broker_logger

class FedAvgAggregator:
    @staticmethod
    def aggregate(
        node_updates: List[Dict[str, Any]],
        base_state_dict: Dict[str, torch.Tensor],
        output_checkpoint_path: Path
    ) -> Tuple[Dict[str, torch.Tensor], str, float, float]:
        """
        Executes mathematically exact Weighted FedAvg:
            w_i = n_i / total_samples
            Global_Weight = sum(w_i * local_weight_i)
        
        Args:
            node_updates: List of dicts with keys:
                          - 'node_id': str
                          - 'state_dict': Dict[str, torch.Tensor]
                          - 'sample_count': int
                          - 'loss': float
                          - 'accuracy': float
            base_state_dict: Previous global model state dict
            output_checkpoint_path: Destination path for saving .pth checkpoint
            
        Returns:
            Tuple of (aggregated_state_dict, checkpoint_checksum, weighted_global_loss, weighted_global_acc)
        """
        if not node_updates:
            raise ValueError("Cannot perform FedAvg on empty list of node updates.")
            
        total_samples = sum(u["sample_count"] for u in node_updates)
        if total_samples <= 0:
            raise ValueError("Total sample count across node updates must be > 0.")
            
        broker_logger.info(f"Starting FedAvg across {len(node_updates)} nodes with {total_samples} total samples.")
        
        # Initialize new global state dict cloned from structure of base model or first update
        first_sd = node_updates[0]["state_dict"]
        aggregated_state_dict = {}
        for key in first_sd.keys():
            aggregated_state_dict[key] = torch.zeros_like(first_sd[key], dtype=torch.float32)
            
        weighted_loss = 0.0
        weighted_acc = 0.0
        
        # Accumulate weighted tensors
        for update in node_updates:
            n_i = update["sample_count"]
            weight_i = float(n_i) / float(total_samples)
            sd = update["state_dict"]
            
            weighted_loss += weight_i * float(update.get("loss", 0.0))
            weighted_acc += weight_i * float(update.get("accuracy", 0.0))
            
            for key, tensor in sd.items():
                # Cast to float for exact weighted accumulation
                t_float = tensor.to(torch.float32)
                aggregated_state_dict[key] += weight_i * t_float
                
        # Cast back to original dtypes if needed
        for key in aggregated_state_dict.keys():
            orig_dtype = first_sd[key].dtype
            if orig_dtype != torch.float32:
                aggregated_state_dict[key] = aggregated_state_dict[key].to(orig_dtype)
                
        # Save checkpoint to disk
        output_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(aggregated_state_dict, output_checkpoint_path)
        
        checksum = compute_sha256(output_checkpoint_path)
        broker_logger.info(f"FedAvg completed successfully! Checkpoint saved to {output_checkpoint_path} (Acc: {weighted_acc:.2f}%, Loss: {weighted_loss:.4f})")
        
        return aggregated_state_dict, checksum, weighted_loss, weighted_acc

fedavg_aggregator = FedAvgAggregator()

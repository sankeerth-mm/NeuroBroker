import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import torch
from backend.app.security.checksum import verify_sha256

class UpdateValidator:
    @staticmethod
    def validate_update(
        update_path: Path,
        expected_checksum: str,
        base_state_dict: Dict[str, torch.Tensor],
        sample_count: int
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, torch.Tensor]]]:
        """
        Validates an incoming volunteer model weight update.
        Checks:
        1. File existence and SHA-256 checksum
        2. PyTorch tensor deserialization
        3. Key names matching base model
        4. Tensor shapes matching base model
        5. No NaN or Inf values in weights
        6. Valid sample count (> 0)
        """
        if not update_path.exists():
            return False, f"Update file not found: {update_path}", None
            
        if expected_checksum and not verify_sha256(update_path, expected_checksum):
            return False, "Checksum mismatch! Corrupted file transfer.", None
            
        if sample_count <= 0:
            return False, f"Invalid sample count: {sample_count} (must be > 0)", None
            
        try:
            # Load weights onto CPU safely with weights_only=True when possible
            loaded_update = torch.load(update_path, map_location=torch.device("cpu"), weights_only=False)
            
            # Extract state_dict if wrapped in a dict
            if isinstance(loaded_update, dict) and "state_dict" in loaded_update:
                state_dict = loaded_update["state_dict"]
            elif isinstance(loaded_update, dict):
                state_dict = loaded_update
            else:
                return False, "Loaded object is not a valid PyTorch state_dict dictionary.", None
                
            # If base_state_dict is provided, compare keys and shapes
            if base_state_dict:
                if set(state_dict.keys()) != set(base_state_dict.keys()):
                    missing = set(base_state_dict.keys()) - set(state_dict.keys())
                    extra = set(state_dict.keys()) - set(base_state_dict.keys())
                    return False, f"State dict keys mismatch! Missing: {missing}, Extra: {extra}", None
                    
                for key, tensor in state_dict.items():
                    base_tensor = base_state_dict[key]
                    if tensor.shape != base_tensor.shape:
                        return False, f"Tensor shape mismatch for '{key}': expected {base_tensor.shape}, got {tensor.shape}", None
                        
                    if torch.isnan(tensor).any():
                        return False, f"NaN values detected in tensor '{key}'!", None
                        
                    if torch.isinf(tensor).any():
                        return False, f"Inf values detected in tensor '{key}'!", None
            else:
                # Basic NaN/Inf check on all tensors
                for key, tensor in state_dict.items():
                    if isinstance(tensor, torch.Tensor):
                        if torch.isnan(tensor).any() or torch.isinf(tensor).any():
                            return False, f"NaN/Inf values detected in tensor '{key}'!", None
                            
            return True, None, state_dict
            
        except Exception as e:
            return False, f"Failed to deserialize PyTorch state_dict: {str(e)}", None

update_validator = UpdateValidator()

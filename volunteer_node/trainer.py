import time
from pathlib import Path
from typing import Dict, Any, Tuple, Callable, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from volunteer_node.logger import logger

class LocalTrainer:
    @staticmethod
    def train(
        model: nn.Module,
        dataloader: DataLoader,
        global_state_dict: Optional[Dict[str, torch.Tensor]],
        local_epochs: int = 2,
        learning_rate: float = 0.001,
        progress_callback: Optional[Callable[[int, float, float, float], None]] = None,
        save_path: Optional[Path] = None
    ) -> Tuple[Dict[str, torch.Tensor], float, float, float]:
        """
        Executes real local PyTorch training over local dataset partition.
        
        Returns:
            Tuple of (state_dict, final_loss, final_accuracy, elapsed_time_seconds)
        """
        device = torch.device("cuda:0" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu"))
        logger.info(f"Starting local training on device: {device} for {local_epochs} epochs (Batch count: {len(dataloader)})")
        
        # Load global model weights if provided
        if global_state_dict:
            try:
                model.load_state_dict(global_state_dict, strict=False)
            except Exception as e:
                logger.warning(f"Partial state_dict load: {e}")
                
        model.to(device)
        model.train()
        
        optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9)
        criterion = nn.CrossEntropyLoss()
        
        t0 = time.time()
        final_loss = 0.0
        final_acc = 0.0
        
        for epoch in range(1, local_epochs + 1):
            epoch_loss = 0.0
            correct = 0
            total_samples = 0
            
            for batch_idx, (data, target) in enumerate(dataloader):
                data, target = data.to(device), target.to(device)
                optimizer.zero_grad()
                
                output = model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item() * data.size(0)
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total_samples += data.size(0)
                
            avg_loss = epoch_loss / max(1, total_samples)
            acc = (correct / max(1, total_samples)) * 100.0
            final_loss = avg_loss
            final_acc = acc
            
            progress_pct = (epoch / local_epochs) * 100.0
            logger.info(f"  [Epoch {epoch}/{local_epochs}] Loss: {avg_loss:.4f} | Acc: {acc:.2f}% | Progress: {progress_pct:.0f}%")
            
            if progress_callback:
                progress_callback(epoch, avg_loss, acc, progress_pct)
                
        elapsed_sec = time.time() - t0
        logger.info(f"Local training completed in {elapsed_sec:.2f}s! Final Acc: {final_acc:.2f}%, Loss: {final_loss:.4f}")
        
        # Move state dict to CPU before returning or saving
        cpu_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(cpu_state_dict, save_path)
            
        return cpu_state_dict, final_loss, final_acc, elapsed_sec

local_trainer = LocalTrainer()

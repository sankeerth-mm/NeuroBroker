import os
import platform
import socket
import psutil
import torch
from typing import Dict, Any

class ResourceMonitor:
    @staticmethod
    def get_hardware_specs() -> Dict[str, Any]:
        """Collect static and initial hardware specifications."""
        hostname = socket.gethostname()
        cpu_cores = psutil.cpu_count(logical=True) or 1
        ram_total_mb = psutil.virtual_memory().total / (1024 * 1024)
        disk_total_gb = psutil.disk_usage("/").total / (1024 * 1024 * 1024)
        
        # GPU Discovery
        cuda_avail = torch.cuda.is_available()
        gpu_name = "CPU Only"
        gpu_vram_mb = 0.0
        cuda_version = None
        
        if cuda_avail:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            cuda_version = torch.version.cuda
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu_name = "Apple Silicon GPU (MPS)"
            gpu_vram_mb = ram_total_mb * 0.7 # Unified memory
            
        return {
            "hostname": hostname,
            "os_info": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python_version": platform.python_version(),
            "pytorch_version": torch.__version__,
            "cpu_name": platform.processor() or "Generic CPU",
            "cpu_cores": cpu_cores,
            "ram_total_mb": float(ram_total_mb),
            "gpu_name": gpu_name,
            "gpu_memory_total_mb": float(gpu_vram_mb),
            "disk_total_gb": float(disk_total_gb),
            "cuda_available": cuda_avail,
            "cuda_version": cuda_version,
        }

    @staticmethod
    def get_live_telemetry() -> Dict[str, Any]:
        """Collect real-time CPU, RAM, GPU, and disk metrics."""
        cpu_pct = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        ram_usage_pct = vm.percent
        ram_avail_mb = vm.available / (1024 * 1024)
        
        disk_usage = psutil.disk_usage("/")
        disk_avail_gb = disk_usage.free / (1024 * 1024 * 1024)
        
        gpu_usage_pct = 0.0
        gpu_mem_avail_mb = 0.0
        
        if torch.cuda.is_available():
            try:
                # Approximate CUDA memory
                allocated = torch.cuda.memory_allocated(0) / (1024 * 1024)
                total = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                gpu_mem_avail_mb = max(0.0, total - allocated)
                gpu_usage_pct = (allocated / total) * 100.0 if total > 0 else 0.0
            except Exception:
                pass
                
        return {
            "cpu_usage": float(cpu_pct),
            "ram_usage_percent": float(ram_usage_pct),
            "ram_available_mb": float(ram_avail_mb),
            "gpu_usage_percent": float(gpu_usage_pct),
            "gpu_memory_available_mb": float(gpu_mem_avail_mb),
            "disk_available_gb": float(disk_avail_gb),
            "network_upload_mbps": 100.0,
            "network_download_mbps": 100.0,
            "latency_ms": 10.0,
        }

resource_monitor = ResourceMonitor()

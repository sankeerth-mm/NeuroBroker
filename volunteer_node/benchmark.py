import time
import torch
from typing import Dict, Any
from volunteer_node.logger import logger

class VolunteerBenchmark:
    @staticmethod
    def run_micro_benchmark() -> Dict[str, float]:
        """
        Executes a rapid 1-2 second hardware benchmark to normalize performance scores.
        """
        logger.info("Running volunteer node hardware micro-benchmark...")
        
        # 1. CPU Benchmark (Matrix multiplication)
        t0 = time.time()
        a = torch.randn(1000, 1000)
        b = torch.randn(1000, 1000)
        for _ in range(5):
            c = torch.mm(a, b)
        cpu_time = max(0.001, time.time() - t0)
        # Score ~ 1.0 for fast CPU, 0.3 for slow CPU
        compute_score = min(5.0, max(0.1, 0.5 / cpu_time))
        
        # 2. Memory Throughput Benchmark
        t0 = time.time()
        arr = torch.zeros(10_000_000, dtype=torch.float32)
        arr.fill_(1.0)
        mem_time = max(0.001, time.time() - t0)
        memory_score = min(5.0, max(0.1, 0.05 / mem_time))
        
        # 3. GPU Benchmark if CUDA or MPS available
        gpu_score = 0.0
        if torch.cuda.is_available():
            try:
                device = torch.device("cuda:0")
                t0 = time.time()
                ga = torch.randn(2000, 2000, device=device)
                gb = torch.randn(2000, 2000, device=device)
                for _ in range(10):
                    gc = torch.mm(ga, gb)
                torch.cuda.synchronize()
                gpu_time = max(0.001, time.time() - t0)
                gpu_score = min(10.0, max(1.0, 1.0 / gpu_time))
            except Exception:
                gpu_score = 1.0
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu_score = 2.5
            
        network_score = 1.0
        
        overall = float(
            0.30 * compute_score +
            0.20 * memory_score +
            0.40 * (gpu_score if gpu_score > 0 else compute_score * 0.5) +
            0.10 * network_score
        )
        
        scores = {
            "compute_score": round(float(compute_score), 2),
            "memory_score": round(float(memory_score), 2),
            "gpu_score": round(float(gpu_score), 2),
            "network_score": round(float(network_score), 2),
            "overall_capability_score": round(float(overall), 2),
        }
        
        logger.info(f"Benchmark completed: Overall Capability Score = {scores['overall_capability_score']}")
        return scores

volunteer_benchmark = VolunteerBenchmark()

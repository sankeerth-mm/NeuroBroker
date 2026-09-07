import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import time
import random
import json
from typing import Dict, Any, List
import numpy as np

from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.resource_score_scheduler import resource_scheduler
from backend.app.scheduler.baselines import round_robin_scheduler, random_scheduler
from backend.app.scheduler.drl_scheduler import drl_scheduler

def create_synthetic_nodes() -> List[VolunteerNode]:
    """Creates a simulated heterogeneous cluster of 5 nodes."""
    return [
        VolunteerNode(
            node_id="NODE-01", hostname="alpha-4090", cpu_cores=24, cpu_usage=20.0,
            ram_total_mb=65536.0, ram_usage_percent=30.0, ram_available_mb=45000.0,
            gpu_name="NVIDIA RTX 4090", gpu_memory_total_mb=24576.0, gpu_memory_available_mb=20000.0,
            gpu_usage_percent=15.0, network_download_mbps=850.0, latency_ms=8.0,
            cuda_available=True, overall_capability_score=4.8, reliability_score=0.98, rounds_participated=0, status="ONLINE"
        ),
        VolunteerNode(
            node_id="NODE-02", hostname="beta-3060", cpu_cores=16, cpu_usage=35.0,
            ram_total_mb=16384.0, ram_usage_percent=45.0, ram_available_mb=9000.0,
            gpu_name="NVIDIA RTX 3060", gpu_memory_total_mb=12288.0, gpu_memory_available_mb=9000.0,
            gpu_usage_percent=25.0, network_download_mbps=450.0, latency_ms=18.0,
            cuda_available=True, overall_capability_score=3.6, reliability_score=0.95, rounds_participated=0, status="ONLINE"
        ),
        VolunteerNode(
            node_id="NODE-03", hostname="gamma-1650", cpu_cores=12, cpu_usage=55.0,
            ram_total_mb=8192.0, ram_usage_percent=65.0, ram_available_mb=3000.0,
            gpu_name="NVIDIA GTX 1650", gpu_memory_total_mb=4096.0, gpu_memory_available_mb=2500.0,
            gpu_usage_percent=40.0, network_download_mbps=120.0, latency_ms=45.0,
            cuda_available=True, overall_capability_score=2.4, reliability_score=0.88, rounds_participated=0, status="ONLINE"
        ),
        VolunteerNode(
            node_id="NODE-04", hostname="delta-cpu", cpu_cores=8, cpu_usage=68.0,
            ram_total_mb=8192.0, ram_usage_percent=75.0, ram_available_mb=2000.0,
            gpu_name="CPU Only", gpu_memory_total_mb=0.0, gpu_memory_available_mb=0.0,
            gpu_usage_percent=0.0, network_download_mbps=50.0, latency_ms=80.0,
            cuda_available=False, overall_capability_score=1.4, reliability_score=0.82, rounds_participated=0, status="ONLINE"
        ),
        VolunteerNode(
            node_id="NODE-05", hostname="epsilon-2060", cpu_cores=12, cpu_usage=40.0,
            ram_total_mb=16384.0, ram_usage_percent=40.0, ram_available_mb=10000.0,
            gpu_name="NVIDIA RTX 2060", gpu_memory_total_mb=6144.0, gpu_memory_available_mb=4500.0,
            gpu_usage_percent=20.0, network_download_mbps=300.0, latency_ms=25.0,
            cuda_available=True, overall_capability_score=3.1, reliability_score=0.92, rounds_participated=0, status="ONLINE"
        )
    ]

def evaluate_scheduler(scheduler, name: str, num_rounds: int = 5) -> Dict[str, Any]:
    nodes = create_synthetic_nodes()
    job = TrainingJob(
        id=1, job_code="JOB-BENCH", user_id=1, name="Benchmark",
        model_package_id=1, dataset_id=1, current_round=0, max_rounds=num_rounds, local_epochs=2,
        batch_size=32, learning_rate=0.01, target_accuracy=95.0, min_volunteer_nodes=3
    )
    
    dataset_size = 50_000_000 # 50 MB
    model_size = 5_000_000 # 5 MB
    
    round_times = []
    transfer_times = []
    node_participation = {n.node_id: 0 for n in nodes}
    accuracies = []
    
    current_acc = 10.0 # Random guess base
    
    for r in range(num_rounds):
        selected, decisions = scheduler.select_nodes(nodes, job, dataset_size, model_size, k_needed=3)
        allocations = scheduler.calculate_data_allocations(selected)
        
        # Calculate simulated round time (straggler effect: round time is bounded by slowest node)
        node_round_durations = []
        node_transfer_durations = []
        
        for idx, node in enumerate(selected):
            node_participation[node.node_id] += 1
            node.rounds_participated += 1
            
            # Transfer time based on bandwidth
            t_trans = (dataset_size * allocations[idx] * 8) / (node.network_download_mbps * 1e6) + (node.latency_ms / 1000.0)
            node_transfer_durations.append(t_trans)
            
            # Compute time (proportional to allocation / compute capability)
            t_comp = (allocations[idx] * 100.0) / max(0.5, node.overall_capability_score)
            node_round_durations.append(t_trans + t_comp)
            
        round_duration = max(node_round_durations) # Synchronous FedAvg bottlenecked by slowest worker
        round_transfer = max(node_transfer_durations)
        
        round_times.append(round_duration)
        transfer_times.append(round_transfer)
        
        # Accuracy improvement with diminishing returns
        gain = (100.0 - current_acc) * 0.35 * (sum(n.overall_capability_score for n in selected) / (3.0 * 4.0))
        current_acc += gain
        accuracies.append(round(current_acc, 2))
        
    total_time = sum(round_times)
    avg_round_time = total_time / num_rounds
    
    # Calculate Jain's Fairness Index on node participation: J(x) = (sum x)^2 / (n * sum x^2)
    participations = list(node_participation.values())
    sum_p = sum(participations)
    sum_sq_p = sum(p**2 for p in participations)
    jain_index = (sum_p**2) / (len(participations) * sum_sq_p) if sum_sq_p > 0 else 1.0
    
    return {
        "scheduler_name": name,
        "total_job_time_sec": round(total_time, 2),
        "avg_round_time_sec": round(avg_round_time, 2),
        "avg_transfer_time_sec": round(sum(transfer_times) / num_rounds, 2),
        "final_accuracy": round(current_acc, 2),
        "jains_fairness_index": round(jain_index, 3),
        "node_participation": node_participation,
        "round_accuracies": accuracies,
        "round_durations": [round(t, 2) for t in round_times]
    }

def run_all_benchmarks() -> Dict[str, Any]:
    print("=" * 70)
    print("  RUNNING NEUROBROKER EXPERIMENTAL SCHEDULING BENCHMARKS")
    print("=" * 70)
    
    results = {}
    schedulers = [
        ("Random Scheduling", random_scheduler),
        ("Round Robin", round_robin_scheduler),
        ("NeuroBroker Resource-Aware", resource_scheduler),
        ("NeuroBroker Hybrid DRL", drl_scheduler),
    ]
    
    for name, sched in schedulers:
        print(f"Evaluating {name} ...")
        res = evaluate_scheduler(sched, name, num_rounds=5)
        results[name] = res
        print(f"  -> Total Time: {res['total_job_time_sec']}s | Avg Round: {res['avg_round_time_sec']}s | Final Acc: {res['final_accuracy']}% | Fairness: {res['jains_fairness_index']}")
        
    out_file = Path(__file__).resolve().parent / "benchmark_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved benchmark results to {out_file}")
    return results

if __name__ == "__main__":
    run_all_benchmarks()

import pytest
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.resource_score_scheduler import resource_scheduler
from backend.app.scheduler.network_aware import network_estimator
from backend.app.scheduler.fairness import fairness_manager

def test_resource_scheduler_scoring():
    gpu_node = VolunteerNode(
        node_id="GPU-BOX", cpu_cores=16, cpu_usage=10.0,
        ram_total_mb=32768.0, ram_usage_percent=20.0, ram_available_mb=26000.0,
        gpu_name="NVIDIA RTX 4090", gpu_memory_total_mb=24576.0, gpu_memory_available_mb=20000.0,
        gpu_usage_percent=10.0, network_download_mbps=900.0, latency_ms=5.0,
        cuda_available=True, overall_capability_score=4.8, reliability_score=1.0, status="ONLINE",
        rounds_participated=0
    )
    
    cpu_node = VolunteerNode(
        node_id="CPU-BOX", cpu_cores=4, cpu_usage=80.0,
        ram_total_mb=8192.0, ram_usage_percent=85.0, ram_available_mb=1200.0,
        gpu_name="CPU Only", gpu_memory_total_mb=0.0, gpu_memory_available_mb=0.0,
        gpu_usage_percent=0.0, network_download_mbps=40.0, latency_ms=100.0,
        cuda_available=False, overall_capability_score=1.2, reliability_score=0.8, status="ONLINE",
        rounds_participated=0
    )
    
    job = TrainingJob(
        id=1, job_code="JOB-TEST", user_id=1, name="TestJob",
        model_package_id=1, dataset_id=1, current_round=0, max_rounds=5,
        local_epochs=2, batch_size=32, learning_rate=0.01, target_accuracy=95.0, min_volunteer_nodes=1
    )
    
    selected, decisions = resource_scheduler.select_nodes(
        available_nodes=[gpu_node, cpu_node],
        job=job,
        dataset_size_bytes=10_000_000,
        model_size_bytes=2_000_000,
        k_needed=1
    )
    
    assert len(selected) == 1
    assert selected[0].node_id == "GPU-BOX"
    assert len(decisions) == 2
    assert any("SELECTED" in d["rationale"] for d in decisions if d["node_id"] == "GPU-BOX")

def test_network_estimator():
    # 10 MB on 100 Mbps = 80 Mbits / 100 Mbps = 0.8s + latency
    t_sec = network_estimator.estimate_transfer_time(data_size_bytes=10_000_000, bandwidth_mbps=100.0, latency_ms=20.0)
    assert 0.7 < t_sec < 1.0

from typing import List, Dict, Any, Tuple
from backend.app.config import settings
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob
from backend.app.scheduler.base_scheduler import BaseScheduler
from backend.app.scheduler.network_aware import network_estimator
from backend.app.scheduler.fairness import fairness_manager
from backend.app.scheduler.scheduler_explainer import scheduler_explainer

class ResourceScoreScheduler(BaseScheduler):
    def __init__(
        self,
        w_cpu: float = settings.WEIGHT_CPU,
        w_ram: float = settings.WEIGHT_RAM,
        w_gpu: float = settings.WEIGHT_GPU_CAPABILITY,
        w_gpu_mem: float = settings.WEIGHT_GPU_MEMORY,
        w_net: float = settings.WEIGHT_NETWORK,
        w_rel: float = settings.WEIGHT_RELIABILITY,
        w_hist: float = settings.WEIGHT_HISTORICAL_PERF,
        w_load: float = settings.WEIGHT_CURRENT_LOAD,
        w_transfer: float = settings.WEIGHT_TRANSFER_PENALTY,
    ):
        self.w_cpu = w_cpu
        self.w_ram = w_ram
        self.w_gpu = w_gpu
        self.w_gpu_mem = w_gpu_mem
        self.w_net = w_net
        self.w_rel = w_rel
        self.w_hist = w_hist
        self.w_load = w_load
        self.w_transfer = w_transfer

    def score_node(
        self,
        node: VolunteerNode,
        dataset_size_bytes: int,
        model_size_bytes: int,
        all_nodes: List[VolunteerNode]
    ) -> Dict[str, Any]:
        """
        Calculate normalized multi-objective resource score for a single volunteer node.
        """
        # 1. CPU Availability & Cores (0.0 to 1.0)
        cpu_free_fraction = max(0.0, 1.0 - (node.cpu_usage / 100.0))
        cpu_cores_norm = min(1.0, node.cpu_cores / 16.0)
        cpu_score = 0.6 * cpu_free_fraction + 0.4 * cpu_cores_norm
        
        # 2. RAM Availability (0.0 to 1.0)
        ram_free_fraction = max(0.0, 1.0 - (node.ram_usage_percent / 100.0))
        ram_volume_norm = min(1.0, node.ram_total_mb / 32768.0)
        ram_score = 0.6 * ram_free_fraction + 0.4 * ram_volume_norm
        
        # 3. GPU Capability & VRAM
        has_gpu = node.cuda_available or (node.gpu_name and "CPU" not in node.gpu_name.upper())
        if has_gpu:
            gpu_score = max(0.5, min(1.0, node.gpu_score or 0.8))
            gpu_vram_free = max(0.0, 1.0 - (node.gpu_usage_percent / 100.0))
            gpu_mem_score = min(1.0, (node.gpu_memory_available_mb / 16384.0)) * 0.5 + gpu_vram_free * 0.5
        else:
            gpu_score = 0.0
            gpu_mem_score = 0.0
            
        # 4. Network Score & Transfer Time Estimation
        net_score = network_estimator.score_network_speed(
            node.network_download_mbps,
            node.latency_ms
        )
        total_transfer_bytes = dataset_size_bytes + model_size_bytes
        est_transfer_sec = network_estimator.estimate_transfer_time(
            total_transfer_bytes,
            node.network_download_mbps,
            node.latency_ms
        )
        # Normalize transfer penalty (0.0 for 0s, 1.0 for >= 30s)
        transfer_penalty = min(1.0, est_transfer_sec / 30.0)
        
        # 5. Reliability / Trust
        rel_score = max(0.1, min(1.0, node.reliability_score))
        
        # 6. Historical Performance (samples/sec or benchmark score)
        hist_score = min(1.0, node.overall_capability_score / 5.0) if node.overall_capability_score else 0.5
        
        # 7. Current Load Penalty
        current_load = (node.cpu_usage + node.ram_usage_percent + node.gpu_usage_percent) / 300.0
        
        # 8. Fairness Score
        fairness_score = fairness_manager.calculate_fairness_score(node, all_nodes)
        
        # Composite Multi-Objective Formula
        overall_score = (
            self.w_cpu * cpu_score +
            self.w_ram * ram_score +
            self.w_gpu * gpu_score +
            self.w_gpu_mem * gpu_mem_score +
            self.w_net * net_score +
            self.w_rel * rel_score +
            self.w_hist * hist_score +
            0.10 * fairness_score -
            self.w_load * current_load -
            self.w_transfer * transfer_penalty
        )
        
        # Estimate training time based on compute score
        est_training_sec = max(5.0, 60.0 / (hist_score * 2.0 + gpu_score * 3.0 + 0.5))
        
        return {
            "node_id": node.node_id,
            "overall_score": float(overall_score),
            "cpu_score": float(cpu_score),
            "ram_score": float(ram_score),
            "gpu_score": float(gpu_score),
            "gpu_mem_score": float(gpu_mem_score),
            "network_score": float(net_score),
            "reliability_score": float(rel_score),
            "fairness_score": float(fairness_score),
            "current_load": float(current_load),
            "estimated_transfer_time_sec": float(est_transfer_sec),
            "estimated_training_time_sec": float(est_training_sec),
            "gpu_name": node.gpu_name,
            "cpu_cores": node.cpu_cores,
            "cpu_usage": node.cpu_usage,
            "bandwidth_mbps": node.network_download_mbps,
        }

    def select_nodes(
        self,
        available_nodes: List[VolunteerNode],
        job: TrainingJob,
        dataset_size_bytes: int,
        model_size_bytes: int,
        k_needed: int
    ) -> Tuple[List[VolunteerNode], List[Dict[str, Any]]]:
        if not available_nodes:
            return [], []
            
        has_gpu_in_pool = any(n.cuda_available or (n.gpu_name and "CPU" not in n.gpu_name.upper()) for n in available_nodes)
        
        # Score each node
        scored_nodes = []
        for node in available_nodes:
            metrics = self.score_node(node, dataset_size_bytes, model_size_bytes, available_nodes)
            metrics["has_gpu_nodes_in_pool"] = has_gpu_in_pool
            scored_nodes.append((node, metrics))
            
        # Sort descending by overall_score
        scored_nodes.sort(key=lambda x: x[1]["overall_score"], reverse=True)
        
        selected_nodes = []
        decision_records = []
        
        for idx, (node, metrics) in enumerate(scored_nodes):
            is_selected = idx < k_needed and node.status != "UNHEALTHY"
            if is_selected:
                selected_nodes.append(node)
                
            rationale = scheduler_explainer.generate_explanation(metrics, is_selected)
            decision_records.append({
                "job_id": job.id,
                "round_number": (job.current_round or 0) + 1,
                "node_id": node.node_id,
                "is_selected": is_selected,
                "overall_score": metrics["overall_score"],
                "cpu_score": metrics["cpu_score"],
                "ram_score": metrics["ram_score"],
                "gpu_score": metrics["gpu_score"],
                "network_score": metrics["network_score"],
                "reliability_score": metrics["reliability_score"],
                "fairness_score": metrics["fairness_score"],
                "estimated_transfer_time_sec": metrics["estimated_transfer_time_sec"],
                "estimated_training_time_sec": metrics["estimated_training_time_sec"],
                "rationale": rationale,
            })
            
        return selected_nodes, decision_records

    def calculate_data_allocations(
        self,
        selected_nodes: List[VolunteerNode]
    ) -> List[float]:
        """
        Dynamically calculates data volume proportion for each selected node.
        More capable nodes receive proportionally more samples, bounded to avoid starvation.
        """
        if not selected_nodes:
            return []
        if len(selected_nodes) == 1:
            return [1.0]
            
        raw_scores = []
        for n in selected_nodes:
            # Capability base
            cap = (n.overall_capability_score or 1.0) + (1.5 if n.cuda_available else 0.5)
            # Free RAM/CPU multiplier
            cap *= max(0.3, 1.0 - (n.cpu_usage / 200.0))
            raw_scores.append(cap)
            
        total = sum(raw_scores)
        allocations = [s / total for s in raw_scores]
        
        # Smooth allocations to ensure no node gets < 10% or > 60% if multiple nodes exist
        min_bound = 0.10
        max_bound = 0.60
        smoothed = [max(min_bound, min(max_bound, a)) for a in allocations]
        sm_total = sum(smoothed)
        return [s / sm_total for s in smoothed]

resource_scheduler = ResourceScoreScheduler()

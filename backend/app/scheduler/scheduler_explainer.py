from typing import Dict, Any

class SchedulerExplainer:
    @staticmethod
    def generate_explanation(metrics: Dict[str, Any], is_selected: bool) -> str:
        """
        Generate a human-readable explanation for a scheduling decision.
        """
        node_id = metrics.get("node_id", "Node")
        overall_score = metrics.get("overall_score", 0.0)
        cpu_score = metrics.get("cpu_score", 0.0)
        ram_score = metrics.get("ram_score", 0.0)
        gpu_score = metrics.get("gpu_score", 0.0)
        gpu_name = metrics.get("gpu_name", "CPU Only")
        net_score = metrics.get("network_score", 0.0)
        bandwidth_mbps = metrics.get("bandwidth_mbps", 100.0)
        reliability = metrics.get("reliability_score", 1.0)
        fairness = metrics.get("fairness_score", 1.0)
        transfer_sec = metrics.get("estimated_transfer_time_sec", 0.0)
        train_sec = metrics.get("estimated_training_time_sec", 0.0)
        
        status_text = "SELECTED" if is_selected else "REJECTED / UNSELECTED"
        
        reasons = []
        if is_selected:
            if gpu_score > 0.6:
                reasons.append(f"High GPU acceleration capability ({gpu_name})")
            if cpu_score > 0.7:
                reasons.append(f"Low CPU utilization with {metrics.get('cpu_cores', 1)} cores")
            if ram_score > 0.7:
                reasons.append("Ample free RAM available")
            if net_score > 0.7:
                reasons.append(f"High network throughput ({bandwidth_mbps:.0f} Mbps, transfer est: {transfer_sec:.1f}s)")
            if reliability >= 0.90:
                reasons.append(f"High trust & reliability rating ({reliability*100:.0f}%)")
            if fairness > 0.8:
                reasons.append("High fairness participation priority")
                
            rationale = (
                f"[{node_id} {status_text} - Score: {overall_score:.3f}]\n"
                f"Key factors:\n"
                + "\n".join(f"  • {r}" for r in (reasons or ["Balanced resource score across all metrics"]))
                + f"\n  • Total Estimated Completion: {(transfer_sec + train_sec):.1f}s (Train: {train_sec:.1f}s, Transfer: {transfer_sec:.1f}s)"
            )
        else:
            rejections = []
            if gpu_score == 0 and metrics.get("has_gpu_nodes_in_pool", False):
                rejections.append("CPU-only mode deprioritized in favor of GPU-accelerated workers")
            if cpu_score < 0.3:
                rejections.append(f"High CPU utilization ({metrics.get('cpu_usage', 0):.0f}%)")
            if ram_score < 0.3:
                rejections.append("Insufficient available RAM")
            if net_score < 0.4:
                rejections.append(f"Slow network transfer bottleneck ({transfer_sec:.1f}s)")
            if reliability < 0.75:
                rejections.append(f"Reduced reliability score ({reliability*100:.0f}%) from historical timeouts/failures")
            if fairness < 0.4:
                rejections.append("Deprioritized for fairness to prevent compute starvation of other nodes")
                
            rationale = (
                f"[{node_id} {status_text} - Score: {overall_score:.3f}]\n"
                f"Limiting factors:\n"
                + "\n".join(f"  • {r}" for r in (rejections or ["Lower overall composite resource score than selected peers"]))
            )
            
        return rationale

scheduler_explainer = SchedulerExplainer()

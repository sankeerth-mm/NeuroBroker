from typing import Tuple, Optional
from backend.app.config import settings
from backend.app.models.node import VolunteerNode

class AnomalyDetector:
    @staticmethod
    def evaluate_node_health(node: VolunteerNode) -> Tuple[bool, Optional[str]]:
        """
        Evaluate live telemetry for anomalous behavior.
        Returns (is_anomaly, reason_description).
        """
        # Check CPU Spike
        if node.cpu_usage >= settings.ANOMALY_CPU_SPIKE_PERCENT:
            return True, f"CPU utilization spike: {node.cpu_usage:.1f}% (Threshold: {settings.ANOMALY_CPU_SPIKE_PERCENT}%)"
        
        # Check RAM exhaustion
        if node.ram_usage_percent >= settings.ANOMALY_RAM_SPIKE_PERCENT:
            return True, f"RAM exhaustion spike: {node.ram_usage_percent:.1f}% (Threshold: {settings.ANOMALY_RAM_SPIKE_PERCENT}%)"
        
        # Check Network Latency Degradation
        if node.latency_ms >= settings.ANOMALY_LATENCY_MAX_MS:
            return True, f"Severe network latency: {node.latency_ms:.1f}ms (Threshold: {settings.ANOMALY_LATENCY_MAX_MS}ms)"
        
        # Check Failure Rate
        total_tasks = node.tasks_completed + node.tasks_failed
        if total_tasks >= 5 and (node.tasks_failed / total_tasks) > 0.5:
            return True, f"High task failure rate: {node.tasks_failed}/{total_tasks} failed (Reliability: {node.reliability_score:.2f})"
        
        return False, None

anomaly_detector = AnomalyDetector()

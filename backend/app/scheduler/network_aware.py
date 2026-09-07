from typing import Dict, Any

class NetworkAwareEstimator:
    @staticmethod
    def estimate_transfer_time(
        data_size_bytes: int,
        bandwidth_mbps: float,
        latency_ms: float = 10.0
    ) -> float:
        """
        Estimate transfer time in seconds.
        T_transfer = (data_size_bits / bandwidth_bps) + (latency / 1000)
        """
        if bandwidth_mbps <= 0:
            bandwidth_mbps = 1.0 # Minimum 1 Mbps fallback
            
        data_size_bits = data_size_bytes * 8.0
        bandwidth_bps = bandwidth_mbps * 1_000_000.0
        
        transfer_sec = data_size_bits / bandwidth_bps
        latency_sec = max(0.0, latency_ms) / 1000.0
        
        return transfer_sec + latency_sec

    @staticmethod
    def score_network_speed(
        bandwidth_mbps: float,
        latency_ms: float
    ) -> float:
        """
        Normalize network quality to [0.0, 1.0].
        Standard reference: 1000 Mbps = 1.0, 100 Mbps = 0.6, 10 Mbps = 0.2
        Latency reference: < 20ms = high, > 200ms = low.
        """
        # Bandwidth component (log-scale normalized)
        bw_score = min(1.0, max(0.0, (bandwidth_mbps / 500.0)))
        
        # Latency component
        lat_score = max(0.0, 1.0 - (latency_ms / 300.0))
        
        return 0.7 * bw_score + 0.3 * lat_score

network_estimator = NetworkAwareEstimator()

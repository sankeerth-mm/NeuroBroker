import math
from typing import Dict, List, Tuple

class NonIIDDetector:
    @staticmethod
    def calculate_imbalance_ratio(class_distribution: Dict[str, int]) -> float:
        """
        Calculate ratio of maximum class count to minimum class count.
        1.0 means perfectly balanced. > 3.0 indicates significant imbalance.
        """
        counts = [c for c in class_distribution.values() if c > 0]
        if not counts or len(counts) <= 1:
            return 1.0
        return max(counts) / (min(counts) + 1e-6)

    @staticmethod
    def calculate_entropy(class_distribution: Dict[str, int]) -> float:
        """
        Calculate normalized Shannon entropy for class distribution.
        1.0 means perfectly uniform distribution, 0.0 means completely degenerate single class.
        """
        total = sum(class_distribution.values())
        if total == 0:
            return 1.0
        
        num_classes = len(class_distribution)
        if num_classes <= 1:
            return 1.0
            
        entropy = 0.0
        for count in class_distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
                
        max_entropy = math.log2(num_classes)
        return entropy / max_entropy if max_entropy > 0 else 1.0

    @staticmethod
    def is_skewed(class_distribution: Dict[str, int], threshold_entropy: float = 0.75) -> Tuple[bool, str]:
        """
        Determine if the distribution is skewed and generate descriptive warning.
        """
        entropy = NonIIDDetector.calculate_entropy(class_distribution)
        ratio = NonIIDDetector.calculate_imbalance_ratio(class_distribution)
        
        if entropy < threshold_entropy or ratio > 4.0:
            return True, f"Non-IID skew detected! Imbalance ratio: {ratio:.1f}x, Normalized entropy: {entropy:.2f}"
        return False, f"Balanced distribution. Imbalance ratio: {ratio:.1f}x, Normalized entropy: {entropy:.2f}"

non_iid_detector = NonIIDDetector()

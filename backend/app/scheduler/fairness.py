from typing import List
from backend.app.models.node import VolunteerNode

class FairnessManager:
    @staticmethod
    def calculate_fairness_score(
        node: VolunteerNode,
        all_nodes: List[VolunteerNode]
    ) -> float:
        """
        Calculates a fairness contribution score in [0.0, 1.0].
        Nodes with fewer rounds participated relative to peers get higher fairness priority.
        """
        if not all_nodes:
            return 1.0
            
        max_rounds = max((n.rounds_participated for n in all_nodes), default=0)
        min_rounds = min((n.rounds_participated for n in all_nodes), default=0)
        
        if max_rounds == min_rounds:
            return 1.0
            
        # Inverse participation scaling
        disparity = node.rounds_participated - min_rounds
        fairness_score = max(0.1, 1.0 - (disparity / (max_rounds - min_rounds + 1e-5)))
        return float(fairness_score)

fairness_manager = FairnessManager()

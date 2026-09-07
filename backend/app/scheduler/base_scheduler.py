from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from backend.app.models.node import VolunteerNode
from backend.app.models.job import TrainingJob

class BaseScheduler(ABC):
    @abstractmethod
    def select_nodes(
        self,
        available_nodes: List[VolunteerNode],
        job: TrainingJob,
        dataset_size_bytes: int,
        model_size_bytes: int,
        k_needed: int
    ) -> Tuple[List[VolunteerNode], List[Dict[str, Any]]]:
        """
        Select the best k_needed nodes from available_nodes.
        Returns:
            Tuple of:
            - selected_nodes (List[VolunteerNode])
            - decision_records (List[Dict] containing full explanation & score metrics for every node)
        """
        pass

    @abstractmethod
    def calculate_data_allocations(
        self,
        selected_nodes: List[VolunteerNode]
    ) -> List[float]:
        """
        Calculates proportional partition allocation weights for each selected node.
        Returns list of floats summing to 1.0.
        """
        pass

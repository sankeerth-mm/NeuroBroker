from backend.app.scheduler.base_scheduler import BaseScheduler
from backend.app.scheduler.resource_score_scheduler import resource_scheduler, ResourceScoreScheduler
from backend.app.scheduler.drl_scheduler import drl_scheduler, HybridDRLScheduler
from backend.app.scheduler.baselines import round_robin_scheduler, random_scheduler, RoundRobinScheduler, RandomScheduler
from backend.app.scheduler.network_aware import network_estimator, NetworkAwareEstimator
from backend.app.scheduler.fairness import fairness_manager, FairnessManager
from backend.app.scheduler.reliability import reliability_manager, ReliabilityManager
from backend.app.scheduler.scheduler_explainer import scheduler_explainer, SchedulerExplainer
from backend.app.config import settings

def get_scheduler(mode: str = None) -> BaseScheduler:
    selected_mode = mode or settings.SCHEDULER_MODE
    if selected_mode == "hybrid" or selected_mode == "drl":
        return drl_scheduler
    elif selected_mode == "round_robin":
        return round_robin_scheduler
    elif selected_mode == "random":
        return random_scheduler
    return resource_scheduler

__all__ = [
    "BaseScheduler",
    "resource_scheduler",
    "ResourceScoreScheduler",
    "drl_scheduler",
    "HybridDRLScheduler",
    "round_robin_scheduler",
    "random_scheduler",
    "network_estimator",
    "fairness_manager",
    "reliability_manager",
    "scheduler_explainer",
    "get_scheduler",
]

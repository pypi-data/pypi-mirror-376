import abc
from abc import abstractmethod
from evotool.task.base_task import Solution
from evotool.task.base_task.base_task_adapter import BaseTaskAdapter


class PythonTaskAdapter(BaseTaskAdapter):
    """Base Task Adapter"""
    def __init__(self, task_info: dict):
        super().__init__(task_info)

    # Task-wise methods
    @abstractmethod
    def _get_base_task_description(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def make_init_sol_wo_other_info(self) -> Solution:
        """Create initial solution from task info without other_info."""
        raise NotImplementedError()
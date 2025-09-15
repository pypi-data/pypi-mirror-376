import abc
from abc import abstractmethod
from .base_evaluator import Solution


class BaseAdapter(abc.ABC):
    """Base Adapter"""
    def __init__(self, task_info: dict):
        self.task_info = task_info

    @abstractmethod
    def make_init_sol(self) -> Solution:
        """Create initial solution from task info."""
        raise NotImplementedError()

    @abstractmethod
    def parse_response(self, response_str: str) -> Solution:
        raise NotImplementedError()
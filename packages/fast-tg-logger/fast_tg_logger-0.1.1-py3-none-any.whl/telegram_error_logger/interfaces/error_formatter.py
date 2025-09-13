from abc import ABC, abstractmethod
from ..entities.error_message import ErrorMessage
class ErrorFormatter(ABC):

    @abstractmethod
    def format_message(self, message: ErrorMessage) -> str:
        pass
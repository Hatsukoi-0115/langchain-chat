from abc import ABC, abstractmethod

class AbstractUI(ABC):
    @abstractmethod
    def display_message(self, message: str) -> None:
        pass

    @abstractmethod
    def get_user_input(self, prompt: str) -> str:
        pass
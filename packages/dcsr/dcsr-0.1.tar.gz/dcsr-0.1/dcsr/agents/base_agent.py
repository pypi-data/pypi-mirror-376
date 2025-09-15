import abc

class BaseAgent(abc.ABC):
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    def process(self, data: dict) -> dict:
        pass

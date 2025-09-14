from abc import ABC, abstractmethod

class FactoryInterface(ABC):
    @abstractmethod
    def create(self, **kwargs):
        raise NotImplementedError

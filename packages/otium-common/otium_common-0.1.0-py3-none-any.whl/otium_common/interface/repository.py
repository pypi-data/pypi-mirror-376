from abc import ABC, abstractmethod

class RepositoryInterface(ABC):
    @abstractmethod
    def get(self, entity_id: int):
        raise NotImplementedError
    
    @abstractmethod
    def save(self, instance):
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, instance):
        raise NotImplementedError
    

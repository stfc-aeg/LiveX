from abc import ABC, abstractmethod

class BaseError(Exception):
    pass

class BaseController(ABC):

    @abstractmethod
    def __init__(self, options):
        pass

    @abstractmethod
    def initialize(self, adapters) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def get(self, path: str, with_metadata: bool = False):
        pass

    @abstractmethod
    def set(self, path: str, data) -> None:
        pass

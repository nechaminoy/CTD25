from abc import ABC, abstractmethod
from EventType import EventType
class Subscriber(ABC):
    @abstractmethod
    def handle_event(self, event_type: EventType, data: dict):
        raise NotImplementedError("Subclasses must implement handle_event method")
# TODO :adding inheritance class Subscriber each subscribers must implement handle_event method

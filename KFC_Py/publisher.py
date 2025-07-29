from bus import EventBus
from event import EventType, Event

class PublisherMixin:
    def __init__(self, bus: EventBus):
        self._bus = bus

    def publish_event(self, et: EventType, timestamp, **payload):
        evt = Event(type=et, payload=payload, timestamp=timestamp)
        self._bus.publish(evt)

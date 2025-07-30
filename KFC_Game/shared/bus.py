from collections import defaultdict
from typing import Callable, Dict, List
from .event import Event, EventType

ObserverFn = Callable[[Event], None]

class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[ObserverFn]] = defaultdict(list)

    def subscribe(self, et: EventType, fn: ObserverFn) -> None:
        self._subscribers[et].append(fn)

    def unsubscribe(self, et: EventType, fn: ObserverFn) -> None:
        self._subscribers[et].remove(fn)

    def publish(self, event: Event) -> None:
        for fn in list(self._subscribers.get(event.type, [])):
            fn(event)

event_bus = EventBus()

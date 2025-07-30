import asyncio
from ..shared.event import Event
from ..shared.bus import EventBus

class EventBridge:
    """Listen to WS events and publish them into the local EventBus."""
    def __init__(self, ws_client, local_bus: EventBus):
        self._ws = ws_client
        self._bus = local_bus
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _run(self):
        async for evt in self._ws.events():   
            self._bus.publish(evt)

from typing import AsyncIterator, Protocol
from Command import Command
from event import Event

class TransportClient(Protocol):
    async def send_command(self, cmd: Command) -> None: ...
    async def events(self) -> AsyncIterator[Event]: ...

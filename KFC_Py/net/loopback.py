import asyncio
from typing import AsyncIterator, Callable, Dict, List
from Command import Command
from event import Event, EventType
from bus import EventBus
from .transport import TransportClient


class LoopbackServer:
    """
    In‑memory transport that simulates a WS hub:
    - clients call client.send_command(cmd)
    - server forwards cmd into game's user_input_queue
    - server broadcasts any Event published on EventBus to all clients
    """
    def __init__(self, *, bus: EventBus, put_into_game_queue: Callable[[Command], None]):
        self._bus = bus
        self._put_cmd = put_into_game_queue
        self._incoming_cmds: "asyncio.Queue[Command]" = asyncio.Queue()
        self._client_streams: List["asyncio.Queue[Event]"] = []
        self._tasks: List[asyncio.Task] = []
        self._started = False

    # ----- server lifecycle -----
    def start(self):
        if self._started:
            return
        # 1) forward commands from clients -> game queue
        self._tasks.append(asyncio.create_task(self._drain_commands()))
        # 2) subscribe to all EventTypes and fan‑out to clients
        for et in EventType:
            self._bus.subscribe(et, self._on_event)  # publish→queues
        self._started = True

    async def _drain_commands(self):
        while True:
            cmd = await self._incoming_cmds.get()
            self._put_cmd(cmd)

    def _on_event(self, evt: Event):
        for q in self._client_streams:
            # put_nowait to avoid blocking game loop on slow clients
            try:
                q.put_nowait(evt)
            except asyncio.QueueFull:
                pass

    # ----- client API -----
    class Client(TransportClient):
        def __init__(self, send_impl: Callable[[Command], None], ev_q: "asyncio.Queue[Event]"):
            self._send_impl = send_impl
            self._ev_q = ev_q

        async def send_command(self, cmd: Command) -> None:
            # unified Transport API
            await self._send_impl(cmd)

        async def events(self) -> AsyncIterator[Event]:
            # unified async generator of events
            while True:
                yield await self._ev_q.get()

        def __aiter__(self) -> AsyncIterator[Event]:
            return self.events()

    def connect_client(self) -> TransportClient:
        ev_q: "asyncio.Queue[Event]" = asyncio.Queue(maxsize=1000)
        self._client_streams.append(ev_q)
        async def _send(cmd: Command):
            await self._incoming_cmds.put(cmd)
        return LoopbackServer.Client(_send, ev_q)

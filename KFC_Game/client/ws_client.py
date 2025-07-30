import asyncio, websockets
import json
import uuid
from ..network.transport import TransportClient
from ..network.protocol import command_to_json, event_from_json
from ..shared.command import Command
from ..shared.event import Event


class WSClient(TransportClient):
    def __init__(self, uri: str,  *, ping_interval: float = 10.0, ping_timeout: float = 5.0):
        self._uri = uri
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._player: str = "W"
        self._hb_task: asyncio.Task | None = None
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._lock = asyncio.Lock()

    async def connect(self, player="W"):
        self._player = player
        async with self._lock:
            self._ws = await websockets.connect(self._uri)
            await self._ws.send(json.dumps({"kind": "join", "player": self._player}))
            await self._request_snapshot()
            if self._hb_task is None or self._hb_task.done():
                self._hb_task = asyncio.create_task(self._heartbeat())
        return self

    async def _reconnect(self):
        async with self._lock:
            if self._ws is not None:
                try:
                    waiter = await self._ws.ping()
                    await asyncio.wait_for(waiter, timeout=self._ping_timeout)
                    return
                except Exception:
                    try:
                        await self._ws.close()
                    except Exception:
                        pass
                    self._ws = None

            backoff = 0.5
            while True:
                try:
                    self._ws = await websockets.connect(self._uri)
                    await self._ws.send(json.dumps({"kind": "join", "player": self._player}))
                    await self._request_snapshot()
                    return
                except Exception:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2.0, 5.0)

    async def _heartbeat(self):
        while True:
            await asyncio.sleep(self._ping_interval)
            ws = self._ws
            if ws is None:
                continue
            try:
                waiter = await ws.ping()
                await asyncio.wait_for(waiter, timeout=self._ping_timeout)
            except Exception:
                try:
                    await ws.close()
                except Exception:
                    pass
                self._ws = None
                await self._reconnect()

    async def send_command(self, cmd: Command) -> None:
        if getattr(cmd, "cmd_id", None) is None:
            cmd.cmd_id = uuid.uuid4().hex

        payload = command_to_json(cmd)

        if self._ws is None:
            await self._reconnect()

        for attempt in (1, 2):
            try:
                await self._ws.send(payload)
                return
            except Exception:
                if attempt == 2:
                    raise
                self._ws = None
                await self._reconnect()

    async def events(self):
        while True:
            if self._ws is None:
                await self._reconnect()
            try:
                msg = await self._ws.recv()
                yield event_from_json(msg)
            except Exception:
                self._ws = None
                await self._reconnect()
                await asyncio.sleep(0)

    async def _request_snapshot(self):
        try:
            await self._ws.send(json.dumps({"kind": "get_snapshot"}))
        except Exception:
            pass
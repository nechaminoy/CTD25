import asyncio, websockets
import json
import logging

from websockets.server import WebSocketServerProtocol
from typing import Set
from net.protocol import command_from_json, event_to_json
from event import EventType, Event
from bus import EventBus

from Command import Command


class WSHub:
    def __init__(self, bus: EventBus, put_cmd, loop: asyncio.AbstractEventLoop, game):
        self._bus = bus
        self._clients: Set[WebSocketServerProtocol] = set()
        self._put_cmd = put_cmd
        self._loop = loop
        self._game = game
        self._players = {}  # ws -> "W"/"B"
        for et in EventType:
            self._bus.subscribe(et, self._on_event)

    def _on_event(self, evt):
        data = event_to_json(evt)
        for ws in list(self._clients):
            fut = asyncio.run_coroutine_threadsafe(ws.send(data), self._loop)
            fut.add_done_callback(lambda f: f.exception())
        important_types = {EventType.PIECE_MOVED, EventType.CAPTURE}
        if hasattr(EventType, "PROMOTION"):
            important_types.add(EventType.PROMOTION)
        if hasattr(EventType, "STATE_SNAPSHOT") and evt.type in important_types:
            snap_evt = Event(EventType.STATE_SNAPSHOT, self._snapshot(), self._game.game_time_ms())
            snap = event_to_json(snap_evt)
            for ws in list(self._clients):
                fut = asyncio.run_coroutine_threadsafe(ws.send(snap), self._loop)
                fut.add_done_callback(lambda f: f.exception())

    async def handler(self, ws):
        self._clients.add(ws)
        try:
            # Handshake: join + snapshot
            try:
                first = await ws.recv()
                jo = json.loads(first)
                if jo.get("kind") == "join":
                    self._players[ws] = jo.get("player", "W")
                    t = self._game.game_time_ms()
                    if hasattr(EventType, "ASSIGN_PLAYER"):
                        await ws.send(event_to_json(Event(EventType.ASSIGN_PLAYER, {"player": self._players[ws]}, t)))
                    if hasattr(EventType, "STATE_SNAPSHOT"):
                        await ws.send(event_to_json(Event(EventType.STATE_SNAPSHOT, self._snapshot(), t)))
            except Exception:
                logging.exception("join/snapshot failed; continuing without welcome events")

            async for msg in ws:
                try:
                    d = json.loads(msg)
                    if isinstance(d, dict) and d.get("kind") == "get_snapshot":
                        t = self._game.game_time_ms()
                        await ws.send(event_to_json(Event(EventType.STATE_SNAPSHOT, self._snapshot(), t)))
                        continue
                except Exception:
                    pass
                try:
                    cmd = command_from_json(msg)  # params כבר tuples
                    ok = True
                    reason = None

                    try:
                        player_color = self._players.get(ws)
                        if player_color:
                            piece_color = "W" if "W" in cmd.piece_id else "B"
                            if player_color != piece_color:
                                ok = False
                                reason = "wrong player"
                    except Exception:
                        ok = False
                        reason = "invalid command"

                    t = self._game.game_time_ms()
                    if ok:
                        if hasattr(EventType, "COMMAND_RESULT"):
                            ack = Event(EventType.COMMAND_RESULT,
                                        {"cmd_id": getattr(cmd, "cmd_id", None), "status": "accepted"}, t)
                            await ws.send(event_to_json(ack))
                        self._put_cmd(cmd)
                    else:
                        if hasattr(EventType, "COMMAND_RESULT"):
                            nack = Event(
                                EventType.COMMAND_RESULT,
                                {"cmd_id": getattr(cmd, "cmd_id", None), "status": "rejected",
                                 "reason": reason or "invalid"},
                                t,
                            )
                            await ws.send(event_to_json(nack))

                except Exception:
                    logging.exception("failed to process client message")
        finally:
            self._clients.discard(ws)
            self._players.pop(ws, None)

    def _snapshot(self) -> dict:
        return self._game.snapshot()


async def serve(game, host="127.0.0.1", port=8765):
    loop = asyncio.get_running_loop()
    hub = WSHub(game.bus, game.user_input_queue.put, loop, game)
    async with websockets.serve(hub.handler, host, port):
        await asyncio.Future()

import asyncio, websockets, json, logging, contextlib

from websockets.server import WebSocketServerProtocol
from typing import Set
from ..network.protocol import command_from_json, event_to_json
from ..shared.event import EventType, Event
from ..shared.bus import EventBus
from ..shared.command import Command


class WSHub:
    def __init__(self, bus: EventBus, put_cmd, loop: asyncio.AbstractEventLoop, game):
        self._bus = bus
        self._clients: Set[WebSocketServerProtocol] = set()
        self._put_cmd = put_cmd
        self._loop = loop
        self._game = game
        self._players = {}  # ws -> "W"/"B"
        self._player_cursors = {}  # player -> (row, col)
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

                    # Handle cursor update commands specially
                    if cmd.type == "cursor_update":
                        player_num = cmd.params[0]
                        cursor_pos = cmd.params[1]
                        player_color = self._players.get(ws)
                        if player_color:
                            self._player_cursors[player_color] = cursor_pos
                            logging.debug(f"Updated cursor for player {player_color} to {cursor_pos}")
                        continue

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
        # Get the base snapshot from the game
        snapshot = self._game.snapshot()
        
        # Add client cursors to the snapshot
        cursors = []
        for player_color, cursor_pos in self._player_cursors.items():
            player_num = 1 if player_color == "W" else 2
            cursors.append({"player": player_num, "cell": cursor_pos})
        
        # If there are client cursors, use them, otherwise fall back to game's local cursors
        if cursors:
            snapshot["cursors"] = cursors
        
        return snapshot


async def serve(game, host="127.0.0.1", port=8765):
    loop = asyncio.get_running_loop()
    hub = WSHub(game.bus, game.user_input_queue.put, loop, game)
    async with websockets.serve(hub.handler, host, port):
        await asyncio.Future()

async def _game_ticker(game, hz: float = 60.0):
    """Run the game loop on the server side without graphics."""
    dt = 1.0 / hz
    while True:
        try:
            game._run_game_loop(num_iterations=1, is_with_graphics=False)
        except Exception:
            logging.exception("game tick failed")
        await asyncio.sleep(dt)

async def serve_and_tick(game, host="127.0.0.1", port=8765, *, hz: float = 60.0):
    """
    Start WS hub and run the game loop ticker concurrently.
    """
    loop = asyncio.get_running_loop()
    hub = WSHub(game.bus, game.user_input_queue.put, loop, game)
    sleep_dt = 0.0 if not hz or hz <= 0 else 1.0 / hz
    async def _ticker():
        try:
            while True:
                game._run_game_loop(num_iterations=1, is_with_graphics=False)
                if sleep_dt > 0:
                    await asyncio.sleep(sleep_dt)
                else:
                    await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass

    async with websockets.serve(hub.handler, host, port):
        ticker_task = asyncio.create_task(_ticker())
        try:
            await asyncio.Future()
        finally:
            ticker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ticker_task

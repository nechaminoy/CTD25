# KFC_Game/tests/test_ws_server_ticker.py
import asyncio
import pathlib
import pytest

from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..client.ws_client import WSClient
from ..server.ws_server import serve_and_tick  # make sure this function exists
from ..shared.event import EventType

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"


async def next_of_type(client: WSClient, typ: EventType, timeout: float = 2.0):
    """Wait for the next event of a given type from the client's event stream."""
    agen = client.events()
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise asyncio.TimeoutError(f"no {typ} within {timeout}s")
        evt = await asyncio.wait_for(agen.__anext__(), timeout=remaining)
        if evt.type == typ:
            return evt


async def wait_snapshot_gt(client: WSClient, base_v: int, timeout: float = 2.0):
    """
    Wait for a STATE_SNAPSHOT whose version is > base_v.
    This avoids latching onto initial snapshots (version=0) sent during handshake/startup.
    """
    agen = client.events()
    deadline = asyncio.get_event_loop().time() + timeout
    last = None
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            last_v = getattr(getattr(last, "payload", {}), "get", lambda *_: "n/a")("version")
            raise AssertionError(
                f"No STATE_SNAPSHOT with version>{base_v} in {timeout}s (last={last_v})"
            )
        evt = await asyncio.wait_for(agen.__anext__(), timeout=remaining)
        if evt.type == EventType.STATE_SNAPSHOT:
            last = evt
            v = evt.payload.get("version", 0)
            if v > base_v:
                return evt


@pytest.mark.asyncio
async def test_server_runs_game_loop_and_broadcasts_snapshot():
    # Build a headless game
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000  # speed up logical time if your engine uses it

    # Start WS server + game loop ticker
    srv = asyncio.create_task(serve_and_tick(game, host="127.0.0.1", port=8798, hz=120.0))
    await asyncio.sleep(0.05)
    try:
        # Two clients: White and Black
        cW = await WSClient("ws://127.0.0.1:8798").connect(player="W")
        cB = await WSClient("ws://127.0.0.1:8798").connect(player="B")

        # Consume initial snapshot(s) and take the highest version seen before the move
        snapW0 = await next_of_type(cW, EventType.STATE_SNAPSHOT)
        v0 = snapW0.payload.get("version", 0)
        # There might be another initial snapshot (from handshake/startup); try to catch it briefly
        try:
            while True:
                s = await asyncio.wait_for(next_of_type(cW, EventType.STATE_SNAPSHOT), timeout=0.05)
                v0 = max(v0, s.payload.get("version", 0))
        except asyncio.TimeoutError:
            pass

        # Issue a legal White move: pawn from (6,0) to (4,0)
        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])
        await cW.send_command(cmd)

        # (Optional but recommended) Wait for ACK
        ack = await asyncio.wait_for(next_of_type(cW, EventType.COMMAND_RESULT), timeout=0.5)
        assert ack.payload.get("status") == "accepted"

        # Now wait for a snapshot with a strictly higher version on both clients
        snapW1 = await wait_snapshot_gt(cW, v0, timeout=2.0)
        snapB1 = await wait_snapshot_gt(cB, v0, timeout=2.0)

        v1 = snapW1.payload["version"]
        assert v1 == v0 + 1
        assert v1 == snapB1.payload["version"]
    finally:
        srv.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv

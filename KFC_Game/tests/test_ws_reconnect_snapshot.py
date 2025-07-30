# KFC_Game/tests/test_ws_reconnect_snapshot.py
import asyncio
import pathlib
import pytest

from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..client.ws_client import WSClient
from ..server.ws_server import serve
from ..shared.event import EventType

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"


async def next_of_type(client: WSClient, typ: EventType, timeout: float = 2.0):
    agen = client.events()
    end = asyncio.get_event_loop().time() + timeout
    while True:
        left = end - asyncio.get_event_loop().time()
        if left <= 0:
            raise asyncio.TimeoutError(f"no {typ} within {timeout}s")
        evt = await asyncio.wait_for(agen.__anext__(), timeout=left)
        if evt.type == typ:
            return evt

@pytest.mark.asyncio
async def test_ws_reconnect_snapshot():
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv = asyncio.create_task(serve(game, host="127.0.0.1", port=8793))
    await asyncio.sleep(0.05)

    try:
        c1 = await WSClient("ws://127.0.0.1:8793").connect(player="W")
        c2 = await WSClient("ws://127.0.0.1:8793").connect(player="B")

        snap0 = await next_of_type(c1, EventType.STATE_SNAPSHOT)
        v0 = snap0.payload.get("version", 0)

        await c1._ws.close()
        await asyncio.sleep(0.01)

        pb = game.pos[(1, 0)][0]
        cmd_b = Command(game.game_time_ms(), pb.id, "move", [(1, 0), (3, 0)])
        await c2.send_command(cmd_b)
        await asyncio.sleep(0.02)
        game._run_game_loop(num_iterations=180, is_with_graphics=False)

        await c1._reconnect()

        snap1 = await next_of_type(c1, EventType.STATE_SNAPSHOT, timeout=2.0)
        v1 = snap1.payload["version"]
        assert v1 == v0 + 1, f"expected snapshot version to increase: {v0} -> {v1}"

    finally:
        srv.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv

import asyncio, pathlib, pytest
from GameFactory import create_game
from GraphicsFactory import MockImgFactory
from Command import Command
from client.ws_client import WSClient
from server.ws_server import serve
from event import EventType

from Tests.test_ws_server_ticker import wait_snapshot_gt

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

async def next_of_type(client, typ, timeout=2.0):
    agen = client.events()
    end = asyncio.get_event_loop().time() + timeout
    while True:
        left = end - asyncio.get_event_loop().time()
        if left <= 0: raise asyncio.TimeoutError()
        evt = await asyncio.wait_for(agen.__anext__(), timeout=left)
        if evt.type == typ:
            return evt

@pytest.mark.asyncio
async def test_snapshot_version_increments_on_move():
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv = asyncio.create_task(serve(game, host="127.0.0.1", port=8791))
    await asyncio.sleep(0.05)

    try:
        c = await WSClient("ws://127.0.0.1:8791").connect(player="W")

        snap0 = await next_of_type(c, EventType.STATE_SNAPSHOT)
        v0 = snap0.payload.get("version", 0)

        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])
        await c.send_command(cmd)
        await asyncio.sleep(0.02)

        game._run_game_loop(num_iterations=160, is_with_graphics=False)

        snap1 = await wait_snapshot_gt(c, v0, timeout=2.0)
        v1 = snap1.payload["version"]
        assert v1 == v0 + 1
    finally:
        srv.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv

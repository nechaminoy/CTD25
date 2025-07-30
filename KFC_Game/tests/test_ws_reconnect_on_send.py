import asyncio, pathlib, pytest
from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..client.ws_client import WSClient
from ..server.ws_server import serve
from ..shared.event import EventType

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
async def test_ws_reconnect_on_send():
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv = asyncio.create_task(serve(game, host="127.0.0.1", port=8792))
    await asyncio.sleep(0.05)
    try:
        c = await WSClient("ws://127.0.0.1:8792").connect(player="W")
        await next_of_type(c, EventType.STATE_SNAPSHOT)

        await c._ws.close()
        await asyncio.sleep(0.01)
        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])
        await c.send_command(cmd)

        await asyncio.sleep(0.02)
        game._run_game_loop(num_iterations=160, is_with_graphics=False)

        evt = await next_of_type(c, EventType.SOUND_PLAY)
        assert evt.type == EventType.SOUND_PLAY
    finally:
        srv.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv

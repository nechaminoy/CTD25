import asyncio
import pathlib
import pytest

from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..network.protocol import event_to_json
from ..network.loopback import LoopbackServer
from ..client.ws_client import WSClient
from ..server.ws_server import serve

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

async def next_event_of_types(client, types=("piece_moved", "sound_play"), timeout=3.0):
    agen = client.events()
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise asyncio.TimeoutError("no matching event")
        evt = await asyncio.wait_for(agen.__anext__(), timeout=remaining)
        if evt.type.value in types:
            return evt


async def scenario_send_and_get(game, client_factory, server_setup=None, server_teardown=None):
    if server_setup:
        await server_setup()

    try:
        c1 = await client_factory("W")
        c2 = await client_factory("B")

        game._update_cell2piece_map()
        game._time_factor = 1_000_000_000
        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])

        await c1.send_command(cmd)
        await asyncio.sleep(0.02)

        game._run_game_loop(num_iterations=160, is_with_graphics=False)

        evt1 = await next_event_of_types(c1)
        evt2 = await next_event_of_types(c2)

        return event_to_json(evt1), event_to_json(evt2)
    finally:
        if server_teardown:
            await server_teardown()

@pytest.mark.asyncio
async def test_transport_loopback_and_ws_have_same_semantics():
    # --- Loopback ---
    game1 = create_game(PIECES_DIR, MockImgFactory())
    lb = LoopbackServer(bus=game1.bus, put_into_game_queue=game1.user_input_queue.put)
    lb.start()
    async def lb_factory(_player="W"):
        return lb.connect_client()
    json1_a, json1_b = await scenario_send_and_get(game1, lb_factory)
    assert json1_a == json1_b

    # --- WS ---
    game2 = create_game(PIECES_DIR, MockImgFactory())

    async def ws_setup():
        test_ctx.task = asyncio.create_task(serve(game2, host="127.0.0.1", port=8766))
        await asyncio.sleep(0.05)

    async def ws_teardown():
        test_ctx.task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await test_ctx.task
    class test_ctx: pass

    async def ws_factory(player="W"):
        return await WSClient("ws://127.0.0.1:8766").connect(player=player)

    json2_a, json2_b = await scenario_send_and_get(game2, ws_factory, ws_setup, ws_teardown)

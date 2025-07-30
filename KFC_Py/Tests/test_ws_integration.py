import asyncio
import pathlib
import pytest

from GameFactory import create_game
from GraphicsFactory import MockImgFactory
from Command import Command
from event import Event

from server.ws_server import serve
from client.ws_client import WSClient
from net.protocol import event_to_json

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


@pytest.mark.asyncio
async def test_ws_two_clients_receive_same_event():
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv_task = asyncio.create_task(serve(game, host="127.0.0.1", port=8765))
    await asyncio.sleep(0.05)

    try:
        import socket
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        srv_task = asyncio.create_task(serve(game, host="127.0.0.1", port=free_port))
        c1 = await WSClient(f"ws://127.0.0.1:{free_port}").connect(player="W")
        c2 = await WSClient(f"ws://127.0.0.1:{free_port}").connect(player="B")
        await asyncio.sleep(0.02)

        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])

        await c1.send_command(cmd)
        await asyncio.sleep(0.02)

        game._run_game_loop(num_iterations=120, is_with_graphics=False)

        async def next_event(client, timeout=2.0) -> Event:
            agen = client.events()
            return await asyncio.wait_for(agen.__anext__(), timeout=timeout)

        evt1 = await next_event_of_types(c1)
        evt2 = await next_event_of_types(c2)
        assert event_to_json(evt1) == event_to_json(evt2)

        await c1._ws.close()
        await c2._ws.close()

    finally:
        srv_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv_task

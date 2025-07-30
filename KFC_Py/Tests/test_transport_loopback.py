import asyncio
import pathlib
import pytest

from GameFactory import create_game
from GraphicsFactory import MockImgFactory
from Command import Command
from event import Event

from net.loopback import LoopbackServer
from net.protocol import event_to_json

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

@pytest.mark.asyncio
async def test_loopback_two_clients_receive_same_event():
    # Build game (headless)
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv = LoopbackServer(bus=game.bus, put_into_game_queue=game.user_input_queue.put)
    srv.start()

    c1 = srv.connect_client()
    c2 = srv.connect_client()

    # White pawn at (6,0) -> (4,0)
    pw = game.pos[(6, 0)][0]
    cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])

    await c1.send_command(cmd)
    await asyncio.sleep(0)

    game._run_game_loop(num_iterations=100, is_with_graphics=False)

    async def next_event(client, timeout=2.0) -> Event:
        agen = client.events()
        return await asyncio.wait_for(agen.__anext__(), timeout=timeout)

    evt1 = await next_event(c1)
    evt2 = await next_event(c2)

    assert event_to_json(evt1) == event_to_json(evt2)

import asyncio
import pytest
import pathlib

from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..network.loopback import LoopbackServer
from ..shared.event import EventType

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

@pytest.mark.asyncio
async def test_loopback_two_clients_receive_piece_moved():
    game = create_game(PIECES_DIR, MockImgFactory())  # returns a ready Game with bus
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000
    bus = game.bus  # Game stores the bus on .bus

    srv = LoopbackServer(bus=bus, put_into_game_queue=game.user_input_queue.put)
    srv.start()

    c1 = srv.connect_client()
    c2 = srv.connect_client()

    pw = game.pos[(6, 0)][0]
    cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])

    await c1.send_command(cmd)
    await asyncio.sleep(0)

    game._run_game_loop(num_iterations=100, is_with_graphics=False)

    evt1 = await asyncio.wait_for(c1._ev_q.get(), timeout=1.0)
    evt2 = await asyncio.wait_for(c2._ev_q.get(), timeout=1.0)
    assert evt1.type == EventType.PIECE_MOVED and evt2.type == EventType.PIECE_MOVED

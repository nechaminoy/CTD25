import asyncio
import pathlib
import pytest

from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..shared.command import Command
from ..client.ws_client import WSClient
from ..server.ws_server import serve
from ..shared.bus import EventBus
from ..client.event_bridge import EventBridge
from ..client.ui_state_sync import subscribe_state_sync

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

class FakeBoardUI:
    def __init__(self):
        self.calls = []

    def replace_all(self, pieces):
        self.calls.append(pieces)

@pytest.mark.asyncio
async def test_ws_client_state_sync_integration():
    # Headless server‑side game
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    game._time_factor = 1_000_000_000

    srv = asyncio.create_task(serve(game, host="127.0.0.1", port=8796))
    await asyncio.sleep(0.05)
    try:
        # Client connects and bridges WS events into a local EventBus
        c = await WSClient("ws://127.0.0.1:8796").connect(player="W")
        local_bus = EventBus()
        EventBridge(c, local_bus).start()

        ui = FakeBoardUI()
        subscribe_state_sync(local_bus, ui)

        # Wait for the initial snapshot (sent on join)
        end = asyncio.get_event_loop().time() + 2
        while not ui.calls and asyncio.get_event_loop().time() < end:
            await asyncio.sleep(0.01)
        assert ui.calls, "expected initial snapshot to reach UI"

        # Make a legal move on the server
        pw = game.pos[(6, 0)][0]
        cmd = Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)])
        await c.send_command(cmd)
        await asyncio.sleep(0.02)
        game._run_game_loop(num_iterations=140, is_with_graphics=False)

        # Expect a second snapshot to arrive via the bus → UI
        prev = len(ui.calls)
        end = asyncio.get_event_loop().time() + 2
        while len(ui.calls) <= prev and asyncio.get_event_loop().time() < end:
            await asyncio.sleep(0.01)
        assert len(ui.calls) > prev, "expected a subsequent snapshot after move"

        # Verify pawn's new cell is (4,0) in the latest snapshot's 'pieces'
        latest = ui.calls[-1]
        moved = [p for p in latest if p["id"] == pw.id][0]
        assert tuple(moved["cell"]) == (4, 0)
    finally:
        srv.cancel()
        with pytest.raises(asyncio.CancelledError):
            await srv

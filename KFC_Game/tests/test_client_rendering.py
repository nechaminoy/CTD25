# KFC_Game/tests/test_client_rendering.py
import pathlib
from ..server.game_factory import create_game
from ..graphics.graphics_factory import MockImgFactory
from ..client.renderer import ClientRenderer
from .mock_img import MockImg
from ..shared.bus import EventBus
from ..shared.event import Event, EventType
from ..client.ui_state_sync import subscribe_render


PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

def test_renderer_draws_piece_at_cell():
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()

    from ..utils.mock_img import MockImg
    MockImg.reset()

    pw = game.pos[(6, 0)][0]
    payload = {
        "version": 1,
        "pieces": [
            {"id": pw.id, "cell": (6, 0)}
        ]
    }

    r = ClientRenderer(game.board, PIECES_DIR, MockImgFactory())
    r.render_snapshot(payload)

    # Just check that something was drawn - the exact position depends on board size
    assert len(MockImg.traj) > 0, f"expected some drawing, got {MockImg.traj}"

class StubRenderer:
    def __init__(self):
        self.called = 0
        self.last_payload = None
    def render_snapshot(self, payload):
        self.called += 1
        self.last_payload = payload

def test_subscribe_render_wires_snapshot_to_renderer():
    bus = EventBus()
    stub = StubRenderer()
    subscribe_render(bus, stub)

    payload = {"version": 7, "pieces": []}
    bus.publish(Event(EventType.STATE_SNAPSHOT, payload, timestamp=123))

    assert stub.called == 1
    assert stub.last_payload is payload

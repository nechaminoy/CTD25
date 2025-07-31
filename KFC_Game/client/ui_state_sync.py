from ..shared.event import EventType

class BoardMirror:
    """
    Minimal UI adapter that just remembers the latest 'pieces' list from a snapshot.
    Real UI code can read 'pieces' and render accordingly.
    """
    def __init__(self):
        self.pieces: list[dict] = []

    def replace_all(self, pieces: list[dict]) -> None:
        self.pieces = list(pieces)  # shallow copy

def subscribe_state_sync(bus, board_ui):
    def on_snapshot(evt):
        # evt.payload = {"version": int, "pieces": [{id, cell, color, state}, ...]}
        board_ui.replace_all(evt.payload["pieces"])
    bus.subscribe(EventType.STATE_SNAPSHOT, on_snapshot)

def subscribe_render(bus, renderer):
    def on_snapshot(evt):
        renderer.render_snapshot(evt.payload)
    bus.subscribe(EventType.STATE_SNAPSHOT, on_snapshot)
    
    # Subscribe to player assignment events to know which cursor to show
    def on_assign_player(evt):
        if hasattr(renderer, 'handle_assign_player'):
            renderer.handle_assign_player(evt.payload)
    bus.subscribe(EventType.ASSIGN_PLAYER, on_assign_player)
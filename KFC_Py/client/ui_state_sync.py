from event import EventType

def subscribe_state_sync(bus, board_ui):
    def on_snapshot(evt):
        # TODO add replace_all to Board
        board_ui.replace_all(evt.payload["pieces"])
    bus.subscribe(EventType.STATE_SNAPSHOT, on_snapshot)

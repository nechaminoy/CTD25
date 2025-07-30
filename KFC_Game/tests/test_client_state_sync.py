import asyncio
import pathlib
import pytest

from ..shared.bus import EventBus
from ..shared.event import Event, EventType
from ..client.ui_state_sync import subscribe_state_sync

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

class FakeBoardUI:
    def __init__(self):
        self.calls = []

    def replace_all(self, pieces):
        self.calls.append(pieces)

def test_local_bus_snapshot_calls_replace_all():
    bus = EventBus()
    ui = FakeBoardUI()
    subscribe_state_sync(bus, ui)

    payload = {
        "version": 0,
        "pieces": [{"id": "PW_(6,0)", "cell": [6, 0], "color": "W", "state": "idle"}],
    }
    bus.publish(Event(EventType.STATE_SNAPSHOT, payload, 0))
    assert ui.calls and ui.calls[-1] == payload["pieces"]

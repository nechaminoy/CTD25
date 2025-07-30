import asyncio
import pytest
from ..client.render_loop import ClientRenderLoop
from ..shared.bus import EventBus
from ..shared.event import Event, EventType
from ..client.ui_state_sync import subscribe_render

class FakeRenderer:
    def __init__(self):
        self.calls = 0
    def frame(self):
        self.calls += 1
        return None

@pytest.mark.asyncio
async def test_render_loop_ticks_and_calls_frame():
    r = FakeRenderer()
    loop = ClientRenderLoop(r, hz=100.0)
    loop.start()

    await asyncio.sleep(0.05)
    await loop.stop()

    assert loop.frames >= 3, f"expected >=3 frames, got {loop.frames}"
    assert r.calls == loop.frames


class FakeRenderer2:
    def __init__(self):
        self.snapshots = []
        self.frames = 0
    def render_snapshot(self, payload):
        self.snapshots.append(payload)
    def frame(self):
        self.frames += 1
        return None

@pytest.mark.asyncio
async def test_subscribe_render_with_render_loop():
    bus = EventBus()
    renderer = FakeRenderer2()
    subscribe_render(bus, renderer)

    loop = ClientRenderLoop(renderer, hz=120.0)
    loop.start()

    payload = {"version": 42, "pieces": []}
    bus.publish(Event(EventType.STATE_SNAPSHOT, payload, timestamp=0))

    await asyncio.sleep(0.03)
    await loop.stop()

    assert renderer.snapshots and renderer.snapshots[-1]["version"] == 42
    assert renderer.frames >= 2

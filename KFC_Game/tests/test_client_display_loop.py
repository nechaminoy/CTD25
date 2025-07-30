import asyncio
import pytest
from ..client.render_loop import ClientRenderLoop

from ..shared.bus import EventBus
from ..client.ui_state_sync import subscribe_render
from ..shared.event import Event, EventType


class FakeRenderer:
    def __init__(self):
        self.calls = 0
        self.frame_obj = object()
    def frame(self):
        self.calls += 1
        return self.frame_obj

class FakeDisplay:
    def __init__(self):
        self.present_calls = 0
        self.last = None
    def present(self, img):
        self.present_calls += 1
        self.last = img
    def close(self): pass

@pytest.mark.asyncio
async def test_render_loop_calls_display_present():
    r = FakeRenderer()
    d = FakeDisplay()
    loop = ClientRenderLoop(r, hz=120.0, display=d)
    loop.start()
    await asyncio.sleep(0.05)
    await loop.stop()

    assert loop.frames >= 3
    assert r.calls == loop.frames
    assert d.present_calls == loop.frames
    assert d.last is r.frame_obj

class FakeRenderer2:
    def __init__(self):
        self.snapshots = []
        self.frames = 0
        self.frame_img = object()
    def render_snapshot(self, payload):
        self.snapshots.append(payload)
    def frame(self):
        self.frames += 1
        return self.frame_img

class FakeDisplay2:
    def __init__(self):
        self.presented = []
    def present(self, img):
        self.presented.append(img)
    def close(self): pass

@pytest.mark.asyncio
async def test_snapshot_triggers_renderer_and_display():
    bus = EventBus()
    renderer = FakeRenderer2()
    subscribe_render(bus, renderer)

    disp = FakeDisplay2()
    loop = ClientRenderLoop(renderer, hz=100.0, display=disp)
    loop.start()

    payload = {"version": 5, "pieces": []}
    bus.publish(Event(EventType.STATE_SNAPSHOT, payload, timestamp=0))

    await asyncio.sleep(0.04)
    await loop.stop()
    disp.close()

    assert renderer.snapshots and renderer.snapshots[-1]["version"] == 5
    assert len(disp.presented) >= 2
    assert disp.presented[-1] is renderer.frame_img

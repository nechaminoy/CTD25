# test_overlay.py
import numpy as np
import cv2
import pytest

# Adjust this import if your module name isn't "overlay.py"
from ..graphics import overlay_manager as ol
from ..shared.event import Event, EventType


# ──────────────────────────────────────────────────────────────────────────────
# Test helpers & fixtures
# ──────────────────────────────────────────────────────────────────────────────

class FakeBus:
    """Minimal event bus used to verify subscribe/publish integration."""
    def __init__(self):
        self._subs = {}

    def subscribe(self, et, cb):
        self._subs.setdefault(et, []).append(cb)

    def publish(self, evt: Event):
        for cb in self._subs.get(evt.type, []):
            cb(evt)


class BoardWrapper:
    """Wrap a numpy array under `.img` to match the API expected by render_overlay."""
    def __init__(self, img: np.ndarray):
        self.img = img


def make_canvas(w=512, h=512, ch=3, fill=0):
    arr = np.full((h, w, ch), fill, dtype=np.uint8)
    return BoardWrapper(arr)


@pytest.fixture(autouse=True)
def clean_state():
    """Reset overlay state before each test to keep tests independent."""
    ol.reset_overlay()
    yield
    ol.reset_overlay()


# ──────────────────────────────────────────────────────────────────────────────
# Basic state & internal API
# ──────────────────────────────────────────────────────────────────────────────

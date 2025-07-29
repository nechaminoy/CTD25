# test_overlay.py
import numpy as np
import cv2
import pytest

# Adjust this import if your module name isn't "overlay.py"
import overlay_manager as ol
from event import Event, EventType


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

def test_reset_overlay_clears_state():
    # Prime state
    now = 1000
    ol._set_message("hello", now_ms=now, duration_ms=500)
    st = ol.overlay_state()
    assert st["msg"] == "hello"
    assert st["start_ms"] == now
    assert st["until_ms"] == now + 500

    # Reset
    ol.reset_overlay()
    st = ol.overlay_state()
    assert st["msg"] is None
    assert st["start_ms"] == 0
    assert st["until_ms"] == 0


def test_compute_layout_is_centered_and_within_bounds():
    img_shape = (200, 300, 3)
    layout = ol._compute_layout("Test", img_shape)
    assert layout is not None
    x, y, w, h = layout["box"]
    H, W = img_shape[:2]
    # Box is within the image
    assert 0 <= x <= W - 1
    assert 0 <= y <= H - 1
    assert x + w <= W
    assert y + h <= H
    # Centered horizontally (integer center with padding)
    # Can't assert exact equality due to font metrics, but should be "near" center.
    cx_img = W // 2
    cx_box = x + w // 2
    assert abs(cx_img - cx_box) <= 2  # tolerance of a couple of pixels


def test_draw_filled_box_with_alpha_modifies_only_roi():
    dst = np.zeros((100, 120, 3), dtype=np.uint8)
    before = dst.copy()
    x, y, w, h = 10, 20, 50, 30
    ol._draw_filled_box_with_alpha(dst, x, y, w, h, (32, 32, 32), alpha=0.5)

    # Changes happened
    assert np.count_nonzero(dst - before) > 0

    # Outside ROI unchanged
    outside = dst.copy()
    outside[y:y+h, x:x+w] = before[y:y+h, x:x+w]
    assert np.array_equal(outside, before)  # i.e., only ROI changed


# ──────────────────────────────────────────────────────────────────────────────
# Event callbacks & subscribe
# ──────────────────────────────────────────────────────────────────────────────

def test_on_game_started_sets_message_and_window():
    ts = 1_000
    evt = Event(EventType.GAME_STARTED, payload={}, timestamp=ts)
    ol.on_game_started(evt)
    st = ol.overlay_state()
    assert st["msg"] == "Game Start!"
    assert st["start_ms"] == ts
    assert st["until_ms"] == ts + ol._START_DUR_MS


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"winner": "white", "reason": "checkmate"}, "White wins! – checkmate"),
        ({"winner": "black"}, "Black wins!"),
        ({"message": "Draw by stalemate"}, "Draw by stalemate"),
        ({}, "Game Over"),
    ],
)
def test_on_game_ended_message_formatting(payload, expected):
    ts = 2_000
    evt = Event(EventType.GAME_ENDED, payload=payload, timestamp=ts)
    ol.on_game_ended(evt)
    st = ol.overlay_state()
    assert st["msg"] == expected
    assert st["start_ms"] == ts
    assert st["until_ms"] == ts + ol._END_DUR_MS


def test_on_announcement_show_default_and_custom_duration():
    ts = 3_000
    # default 2000ms
    evt = Event(EventType.ANNOUNCEMENT_SHOW, payload={"message": "Hi"}, timestamp=ts)
    ol.on_announcement_show(evt)
    st = ol.overlay_state()
    assert st["msg"] == "Hi"
    assert st["until_ms"] == ts + 2000

    # custom duration
    ts2 = 3_500
    evt2 = Event(EventType.ANNOUNCEMENT_SHOW, payload={"message": "Yo", "duration_ms": 750}, timestamp=ts2)
    ol.on_announcement_show(evt2)
    st = ol.overlay_state()
    assert st["msg"] == "Yo"
    assert st["until_ms"] == ts2 + 750


def test_on_announcement_hide_resets():
    ts = 4_000
    ol._set_message("hide-me", ts, 5000)
    ol.on_announcement_hide(Event(EventType.ANNOUNCEMENT_HIDE, payload={}, timestamp=ts + 10))
    st = ol.overlay_state()
    assert st["msg"] is None
    assert st["until_ms"] == 0


def test_subscribe_to_events_overlay_and_publish_flow_renders():
    bus = FakeBus()
    ol.subscribe_to_events_overlay(bus)

    # Publish a start event to prime the overlay
    ts = 5_000
    bus.publish(Event(EventType.GAME_STARTED, payload={"message": "Start!"}, timestamp=ts))

    # Prepare canvas and render
    base = make_canvas(512, 512, 3, fill=0)
    canvas_before = base.img.copy()

    roi = ol.render_overlay(now_ms=ts + 100, board=base)
    assert roi is not None
    x, y, w, h = roi

    # Verify that some pixels changed, and that changes are confined to ROI
    diff_full = cv2.absdiff(base.img, canvas_before)
    assert np.count_nonzero(diff_full) > 0

    masked = diff_full.copy()
    masked[y:y+h, x:x+w] = 0  # zero-out ROI changes
    assert np.count_nonzero(masked) == 0  # nothing changed outside ROI


# ──────────────────────────────────────────────────────────────────────────────
# render_overlay edge cases
# ──────────────────────────────────────────────────────────────────────────────

def test_render_overlay_none_when_no_message_or_after_expiry():
    # No message yet
    b = make_canvas()
    assert ol.render_overlay(now_ms=0, board=b) is None

    # After expiry
    ts = 10_000
    ol._set_message("temp", now_ms=ts, duration_ms=100)
    assert ol.render_overlay(now_ms=ts + 200, board=b) is None


def test_render_overlay_returns_none_for_invalid_board():
    ts = 11_000
    ol._set_message("msg", now_ms=ts, duration_ms=1000)

    class NoImg: pass
    assert ol.render_overlay(now_ms=ts + 10, board=None) is None
    assert ol.render_overlay(now_ms=ts + 10, board=NoImg()) is None
    obj = NoImg(); obj.img = None
    assert ol.render_overlay(now_ms=ts + 10, board=obj) is None

    # wrong shape (e.g., grayscale)
    b_gray = BoardWrapper(np.zeros((100, 100), dtype=np.uint8))
    assert ol.render_overlay(now_ms=ts + 10, board=b_gray) is None


@pytest.mark.xfail(reason=(
    "BGRA path likely fails: code does `img[:] = cv2.cvtColor(img, BGRA2BGR)`, "
    "which assigns a 3-channel array into a 4-channel buffer. "
    "Fix by replacing the array (e.g., `board.img = cv2.cvtColor(board.img, BGRA2BGR)`) "
    "or allocating a new 3-channel canvas before drawing."
))
def test_bgra_canvas_converted_and_drawn():
    ts = 12_000
    ol._set_message("rgba", now_ms=ts, duration_ms=1000)

    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    b = BoardWrapper(rgba)
    roi = ol.render_overlay(now_ms=ts + 1, board=b)
    assert roi is not None
    # Expectation after fix: board.img should become 3-channel BGR
    assert b.img.ndim == 3 and b.img.shape[2] == 3

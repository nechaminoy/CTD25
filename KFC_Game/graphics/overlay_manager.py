from __future__ import annotations
from typing import Optional, Tuple
import cv2
import numpy as np

from ..shared.event import Event, EventType
from .canvas import board_img  # Img wrapper with .img (np.ndarray)

# ───────────────────────────────────────────────────────────────────────────────
# Module state
_msg: Optional[str] = None
_show_until_ms: int = 0
_show_start_ms: int = 0
_last_now_ms: int = 0  # for optional fade calc

# Default durations (ms)
_START_DUR_MS: int = 3000
_END_DUR_MS:   int = 5000

# Styling
_FONT            = cv2.FONT_HERSHEY_DUPLEX
_FONT_SCALE      = 1.2
_TEXT_THICKNESS  = 2
_TEXT_COLOR      = (255, 255, 255)  # BGR
_TEXT_OUTLINE    = (0, 0, 0)
_BG_COLOR        = (32, 32, 32)     # box fill color (BGR)
_BG_ALPHA        = 0.55             # 0..1
_PADDING_X       = 28
_PADDING_Y       = 18
_ROUND_RADIUS    = 12               # visual only; we approximate with filled rectangles

# ───────────────────────────────────────────────────────────────────────────────
def reset_overlay():
    """Clear any pending overlay message."""
    global _msg, _show_until_ms, _show_start_ms
    _msg = None
    _show_until_ms = 0
    _show_start_ms = 0


def _set_message(msg: str, now_ms: int, duration_ms: int):
    """Internal: set current overlay message window."""
    global _msg, _show_until_ms, _show_start_ms
    _msg = msg
    _show_start_ms = now_ms
    _show_until_ms = now_ms + max(0, int(duration_ms))


# ─────────────────────── Event callbacks (SUB side) ────────────────────────────
def on_game_started(evt: Event):
    """
    Show a 'Game Start!' announcement for a short time.
    Optional: payload['message'] to override the default.
    """
    msg = evt.payload.get('message', 'Game Start!')
    _set_message(msg, now_ms=evt.timestamp, duration_ms=_START_DUR_MS)


def on_game_ended(evt: Event):
    """
    Show end-of-game announcement, e.g. 'White wins (checkmate)'.
    Expected payload (flexible): winner ('white'|'black'|str), reason (str, optional), message (optional).
    """
    winner = evt.payload.get('winner')  # 'white'|'black'|None/str
    reason = evt.payload.get('reason')
    if 'message' in evt.payload:
        msg = evt.payload['message']
    else:
        if winner:
            base = f"{str(winner).capitalize()} wins!"
        else:
            base = "Game Over"
        msg = f"{base} – {reason}" if reason else base

    _set_message(msg, now_ms=evt.timestamp, duration_ms=_END_DUR_MS)


def on_announcement_show(evt: Event):
    """
    Optional helper: show arbitrary message for payload['duration_ms'] (default 2000).
    """
    msg = evt.payload.get('message', '')
    dur = int(evt.payload.get('duration_ms', 2000))
    _set_message(msg, now_ms=evt.timestamp, duration_ms=dur)


def on_announcement_hide(evt: Event):
    """Optional helper: hide current announcement immediately."""
    reset_overlay()


def subscribe_to_events_overlay(bus):
    """Register all relevant overlay subscriptions on the given EventBus."""
    bus.subscribe(EventType.GAME_STARTED, on_game_started)
    bus.subscribe(EventType.GAME_ENDED,   on_game_ended)
    # Optional helpers if you plan to use them:
    bus.subscribe(EventType.ANNOUNCEMENT_SHOW, on_announcement_show)
    bus.subscribe(EventType.ANNOUNCEMENT_HIDE, on_announcement_hide)


# ───────────────────────── Rendering (to be called per frame) ──────────────────
def render_overlay(now_ms: int, board=board_img) -> Optional[Tuple[int,int,int,int]]:
    """
    Draw the overlay (centered translucent box + text) if an announcement is active.
    Call this once per frame in your render step.
    """
    global _last_now_ms
    _last_now_ms = now_ms

    if _msg is None or now_ms >= _show_until_ms:
        return  None # nothing to draw

    # Ensure we have a valid canvas
    if board is None or not hasattr(board, 'img') or board.img is None:
        return None

    img = board.img  # np.ndarray
    if img.ndim == 3 and img.shape[2] == 4:
        # Replace 4‑channel canvas with a 3‑channel BGR copy
        board.img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        img = board.img
    if img.ndim != 3 or img.shape[2] != 3:
        return None

    layout = _compute_layout(_msg, img.shape)
    if not layout:
        return None

    remain = max(0, _show_until_ms - now_ms)
    alpha = max(0.15, _BG_ALPHA * (remain / 300.0)) if remain < 300 else _BG_ALPHA

    x, y, w, h = layout["box"]
    _draw_filled_box_with_alpha(img, x, y, w, h, _BG_COLOR, alpha)
    cv2.putText(img, layout["text"], layout["text_pos"], _FONT, _FONT_SCALE, _TEXT_OUTLINE, _TEXT_THICKNESS + 2,
                lineType=cv2.LINE_AA)
    cv2.putText(img, layout["text"], layout["text_pos"], _FONT, _FONT_SCALE, _TEXT_COLOR, _TEXT_THICKNESS,
                lineType=cv2.LINE_AA)
    return (x, y, w, h)

# ──────────────────────────────── Utils ────────────────────────────────────────
def _draw_filled_box_with_alpha(dst: np.ndarray, x: int, y: int, w: int, h: int,
                                color: Tuple[int, int, int], alpha: float):
    """
    Draw a filled rectangle with alpha blending onto dst (BGR).
    """
    x2, y2 = x + w, y + h
    x, y   = max(0, x), max(0, y)
    x2     = min(dst.shape[1], x2)
    y2     = min(dst.shape[0], y2)
    if x >= x2 or y >= y2:
        return

    roi = dst[y:y2, x:x2].copy()
    overlay = roi.copy()
    cv2.rectangle(overlay, (0, 0), (x2 - x - 1, y2 - y - 1), color, thickness=-1)
    cv2.addWeighted(overlay, alpha, roi, 1.0 - alpha, 0.0, dst[y:y2, x:x2])

def _compute_layout(msg: str, img_shape) -> Optional[dict]:
    if not msg:
        return None
    h, w = img_shape[:2]
    (tw, th), baseline = cv2.getTextSize(msg, _FONT, _FONT_SCALE, _TEXT_THICKNESS)
    box_w = tw + 2 * _PADDING_X
    box_h = th + baseline + 2 * _PADDING_Y
    x = max(0, (w - box_w) // 2)
    y = max(0, (h - box_h) // 2)
    return {
        "text": msg, "tw": tw, "th": th, "baseline": baseline,
        "box": (x, y, box_w, box_h),
        "text_pos": (x + _PADDING_X, y + _PADDING_Y + th),
    }

def overlay_state():
    return {
        "msg": _msg,
        "start_ms": _show_start_ms,
        "until_ms": _show_until_ms,
    }

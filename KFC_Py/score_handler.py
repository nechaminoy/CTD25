# engine/score_panel_handler.py
from typing import Dict
import cv2
from pathlib import Path

from event import Event, EventType
from img import Img
from canvas import board_img

# Panel template for drawing scores (e.g. a 200×60 blank panel)
IMG_PATH = Path(__file__).resolve().parent.parent / "blank_panel_score.png"
if not IMG_PATH.exists():
    raise FileNotFoundError(f"Cannot load score-panel image: {IMG_PATH}")

score_panel_template = None

# Piece values for scoring
_piece_values: Dict[str, int] = {
    'p': 1,
    'n': 3,   # Knight
    'b': 3,
    'r': 5,
    'q': 9,
}
_name_to_letter = {
    'pawn': 'p',
    'knight': 'n',
    'bishop': 'b',
    'rook': 'r',
    'queen': 'q',
}

# Running score counters
black_score: int = 0
white_score: int = 0

def reset_scores():
    global black_score, white_score
    black_score = 0
    white_score = 0

def get_score(player: str) -> int:
    return black_score if player.lower() == 'black' else white_score

def add_capture_score(player: str, piece: str):
    global black_score, white_score
    p = (piece or "").strip().lower()
    # allow full names like "bishop", fallback to first letter
    key = _name_to_letter.get(p, (p[:1] if p else ''))
    value = _piece_values.get(key, 0)

    if player.lower() == 'black':
        black_score += value
    else:
        white_score += value



def on_capture(event: Event):
    """
    EventBus callback for CAPTURE events:
    - Updates the appropriate player's score
    - Redraws both score panels on the board
    """
    # global black_score, white_score

    payload = event.payload
    player  = payload.get('player', 'white')
    piece   = payload.get('piece', '')
    add_capture_score(player, piece)
    # value   = _piece_values.get(piece, 0)

    # if player == 'black':
    #     black_score += value
    # else:
    #     white_score += value

    update_score_panels()


def update_score_panels(board=board_img, template=score_panel_template):
    """
    Draw a fresh score panel for each player:
    - Black's panel at bottom-center
    - White's panel at top-center
    Designed to work with real Img() and with MagicMock in tests.
    """
    if board is None:
        from canvas import board_img as _board_img  # local import
        board = _board_img
    global score_panel_template

    # Load a real template only when none was provided
    if template is None:
        if score_panel_template is None and IMG_PATH.exists():
            try:
                score_panel_template = Img().read(str(IMG_PATH), size=(200, 60), keep_aspect=False)
            except Exception:
                return
        template = score_panel_template
        if template is None:
            return

    # Create two panels (works for MagicMock via .clone())
    panel_black = _panel_from(template)
    panel_white = _panel_from(template)

    font      = cv2.FONT_HERSHEY_SIMPLEX
    scale     = 1.0
    thickness = 2

    # Safe centering helper (falls back to fixed coords if .img/shape missing)
    def _safe_center_xy(panel, text):
        try:
            (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
            img = getattr(panel, 'img', None)
            if img is not None and hasattr(img, 'shape'):
                return img.shape[1] // 2 - tw // 2, img.shape[0] // 2 + th // 2
        except Exception:
            pass
        return 10, 30  # safe fallback for mocks

    # Text
    text_b = str(black_score)
    text_w = str(white_score)

    xb, yb = _safe_center_xy(panel_black, text_b)
    xw, yw = _safe_center_xy(panel_white, text_w)

    # These calls are MagicMock-friendly in tests
    panel_black.put_text(text_b, x=xb, y=yb, font_size=scale, thickness=thickness)
    panel_white.put_text(text_w, x=xw, y=yw, font_size=scale, thickness=thickness)

    # Board size (board is a MagicMock with img.shape in tests)
    h, w = board.img.shape[:2]

    # Determine panel size if available; otherwise use defaults matching template size
    def _panel_wh(panel):
        img = getattr(panel, 'img', None)
        if img is not None and hasattr(img, 'shape'):
            return img.shape[1], img.shape[0]
        return 200, 60  # default fallback

    panel_w, panel_h = _panel_wh(panel_black)

    # Place panels
    px_b = w // 2 - panel_w // 2
    py_b = h - panel_h - 10
    panel_black.draw_on(board, x=px_b, y=py_b)

    px_w = w // 2 - panel_w // 2
    py_w = 10
    panel_white.draw_on(board, x=px_w, y=py_w)

def _copy_img(src: Img) -> Img:
    """Return a shallow Img wrapper whose .img is a numpy copy of src.img."""
    dst = Img()
    dst.img = src.img.copy()
    return dst

def _panel_from(template):
    """Return a drawable panel from the provided template.

    Uses template.clone() when available (works with MagicMock in tests),
    otherwise falls back to copying an Img.
    """
    try:
        return template.clone()
    except Exception:
        return _copy_img(template)


# Subscribe to CAPTURE events
def subscribe_to_events_capture(bus):
    bus.subscribe(EventType.CAPTURE, on_capture)
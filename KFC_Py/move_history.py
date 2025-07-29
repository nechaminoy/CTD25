import logging
from typing import List, Tuple, Dict
from pathlib import Path
import cv2

from event import Event, EventType
from img import Img
from canvas import board_img

logger = logging.getLogger(__name__)
# 1) Move histories storing (time_str, move_str) tuples
black_move_history: List[Tuple[str, str]] = []
white_move_history: List[Tuple[str, str]] = []

# 2) Templates for the history panels
IMG_PATH = Path(__file__).resolve().parent.parent / "blank_panel_history.png"
if not IMG_PATH.exists():
    raise FileNotFoundError(f"Cannot load history-panel image: {IMG_PATH}")

black_history_template = Img().read(str(IMG_PATH), size=(200, 400), keep_aspect=False)
white_history_template = Img().read(str(IMG_PATH), size=(200, 400), keep_aspect=False)

def format_time(ms: int) -> str:
    """Convert milliseconds to MM:SS.mmm format."""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"

def coords_to_algebraic(coord: Tuple[int, int]) -> str:
    """
    Convert (row,col) to algebraic file+rank.
    Assumes row 0 is rank 8 and col 0 is file 'a'.
    """
    files = 'abcdefgh'
    row, col = coord
    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise IndexError(f"Invalid board coordinates: {coord}")
    rank = 8 - coord[0]
    file = files[coord[1]]
    return f"{file}{rank}"

def to_algebraic_notation(mv: Dict) -> str:
    """
    Simplified algebraic notation:
    - Pawn: 'e4' or 'exd5'
    - Pieces: N, B, R, Q, K + destination (with 'x' if capture)
    - Castling: O-O or O-O-O
    - Promotion: '=Q'
    - Check '+', Checkmate '#'
    Disambiguation and full rules can be added as needed.
    """
    symbol_map = {
        'queen':'Q','rook':'R','bishop':'B','knight':'N',
        'q':'Q','r':'R','b':'B','n':'N',
        'Q':'Q','R':'R','B':'B','N':'N'
    }
    castling = mv.get('castling')

    if castling in ('O-O', 'O-O-O'):
        move = castling
    else:

        piece = mv.get('piece','')
        symbol = symbol_map.get(piece, '')
        from_sq = coords_to_algebraic(mv['from'])
        to_sq = coords_to_algebraic(mv['to'])
        capture = mv.get('capture', False)
        promotion = mv.get('promotion')
        check = mv.get('check', False)
        checkmate = mv.get('checkmate', False)

        if castling in ('O-O','O-O-O'):
            move = castling
        else:
            if symbol == '':  # pawn
                if capture:
                    move = f"{from_sq[0]}x{to_sq}"
                else:
                    move = f"{to_sq}"
            else:
                move = symbol
                if capture:
                    move += f"x{to_sq}"
                else:
                    move += f"{to_sq}"
            if promotion:
                move += f"={symbol_map.get(promotion, promotion)}"
        if checkmate:
            move += '#'
        elif check:
            move += '+'
    logger.info(move)
    return move

def add_move_to_history(player: str, time_str: str, move_str: str):
    entry = (time_str, move_str)
    if player.lower() == 'black':
        black_move_history.append(entry)
    else:
        white_move_history.append(entry)

def on_piece_moved(event: Event):
    """EventBus callback: record time + move, then redraw panels."""
    mv = event.payload  # expects keys: 'piece','from','to','player','timestamp_ms', etc.
    ts_ms = event.payload.get('timestamp_ms', event.timestamp)
    time_str = format_time(ts_ms)
    move_str = to_algebraic_notation(mv)
    entry = (time_str, move_str)

    player = mv.get('player', 'white').lower()
    add_move_to_history(player, time_str, move_str)

    update_history_panels()

def update_history_panels(board=board_img, 
                          black_template=black_history_template, 
                          white_template=white_history_template,
                          black_history=None,
                          white_history=None):
    """Redraw both players' history panels and blit onto main board image."""
    # Use clone() for tests (MagicMock.clone.return_value = mock_template),
    # fallback to copy() or the object itself in runtime.
    def _clone(tpl):
        if hasattr(tpl, "clone") and callable(getattr(tpl, "clone")):
            return tpl.clone()
        if hasattr(tpl, "copy") and callable(getattr(tpl, "copy")):
            return tpl.copy()
        return tpl

    black_panel = _clone(black_template)
    white_panel = _clone(white_template)

    font      = cv2.FONT_HERSHEY_SIMPLEX
    scale     = 0.5
    thickness = 1
    margin    = 10

    black_history = black_history if black_history is not None else black_move_history
    white_history = white_history if white_history is not None else white_move_history

    # Wrapper: prefer panel.put_text fallback ל‑cv2.putText
    def _put(panel, text, x, y):
        fn = getattr(panel, "put_text", None)
        if callable(fn):
            # (text, x=.., y=.., font_size=.., thickness=..)
            fn(text, x=x, y=y, font_size=scale, thickness=thickness)
        else:
            target = panel.img if hasattr(panel, "img") else panel
            cv2.putText(target, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    # Draw up to last 20 moves: two columns (time @ x=5, move @ x=5 + time_width + margin)
    def _draw(panel, history):
        y0 = 20
        dy = 20
        x_time = 5
        for idx, (t, m) in enumerate(history[-20:]):
            y = y0 + idx * dy
            (text_w, _), _ = cv2.getTextSize(t, font, scale, thickness)
            x_move = x_time + text_w + margin
            _put(panel, t, x_time, y)
            _put(panel, m, x_move, y)

    _draw(black_panel, black_history)
    _draw(white_panel, white_history)

    # Blit panels onto main board
    bp_draw = getattr(black_panel, "draw_on", None)
    if callable(bp_draw):
        bp_draw(board, x=10, y=10)

    wp_draw = getattr(white_panel, "draw_on", None)
    if callable(wp_draw):
        w = white_panel.img.shape[1] if hasattr(white_panel, "img") else 0
        b_w = board.img.shape[1] if hasattr(board, "img") else 0
        wp_draw(board, x=b_w - w - 10, y=10)

def get_move_history(player: str) -> List[Tuple[str, str]]:
    return black_move_history if player.lower() == 'black' else white_move_history

def clear_move_histories():
    black_move_history.clear()
    white_move_history.clear()


# Subscribe the callback
def subscribe_to_events(bus):
    bus.subscribe(EventType.PIECE_MOVED, on_piece_moved)


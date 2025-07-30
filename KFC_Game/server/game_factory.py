import pathlib
import logging
from ..shared.board import Board
from ..graphics.overlay_manager import subscribe_to_events_overlay
from ..audio.sound_handler import subscribe_to_events_sound_play, init_mixer
from ..shared.score_handler import subscribe_to_events_capture
from ..shared.move_history import subscribe_to_events
from ..shared.bus import EventBus
from ..shared.piece_factory import PieceFactory
from .game import Game
from ..graphics.graphics_factory import GraphicsFactory

CELL_PX = 64


def create_game(pieces_root: str | pathlib.Path, img_factory) -> Game:
    """Build a *Game* from the on-disk asset hierarchy rooted at *pieces_root*.

    This reads *board.csv* located inside *pieces_root*, creates a blank board
    (or loads board.png if present), instantiates every piece via PieceFactory
    and returns a ready-to-run *Game* instance.
    """
    root = pathlib.Path(pieces_root)
    if not root.is_absolute():
        root = (pathlib.Path(__file__).resolve().parent / root).resolve()
    board_csv = root / "board.csv"
    if not board_csv.exists():
        raise FileNotFoundError(board_csv)

    # Board image: use board.png beside this file if present, else blank RGBA
    board_png = root / "board.png"
    if not board_png.exists():
        raise FileNotFoundError(board_png)

    loader = img_factory

    # Calculate board dimensions
    board_w = CELL_PX * 8
    board_h = CELL_PX * 8
    logging.debug(f"Creating board with dimensions: {board_w}x{board_h}")
    board_img = loader(board_png, (board_w, board_h), keep_aspect=False)

    board = Board(CELL_PX, CELL_PX, 8, 8, board_img)

    gfx_factory = GraphicsFactory(img_factory)
    pf = PieceFactory(board, pieces_root, graphics_factory=gfx_factory)

    pieces = []
    with board_csv.open() as f:
        for r, line in enumerate(f):
            for c, code in enumerate(line.strip().split(",")):
                if code:
                    pieces.append(pf.create_piece(code, (r, c)))

    event_bus = EventBus()
    subscribe_to_events(event_bus)
    subscribe_to_events_capture(event_bus)
    subscribe_to_events_sound_play(event_bus)
    init_mixer()
    subscribe_to_events_overlay(event_bus)
    return Game(pieces, board, event_bus)
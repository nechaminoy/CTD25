import pathlib, queue
import numpy as np

from ..shared.board import Board
from ..shared.command import Command
from ..server.game import Game, InvalidBoard
from ..shared.piece import Piece
from ..shared.state import State
from ..shared.physics import IdlePhysics, MovePhysics, JumpPhysics
from ..graphics.graphics import Graphics
from ..graphics.graphics_factory import MockImgFactory
from ..shared.img import Img
from ..shared.moves import Moves
from ..shared.bus import EventBus


ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
PIECES_DIR = ROOT_DIR / "pieces"
MOVES_FILE = PIECES_DIR / "QW" / "states" / "idle" / "moves.txt"

def _blank_img(w: int = 8, h: int = 8):
    img_path = ROOT_DIR / "pieces/board.png"
    return Img().read(img_path, (w, h), keep_aspect=False)


def _board(cells: int = 8):
    cell_px = 32
    return Board(cell_px, cell_px, cells, cells, _blank_img(cells * cell_px, cells * cell_px))


def _graphics():
    sprites_dir = pathlib.Path(__file__).parent.parent.parent / "pieces" / "BB" / "states" / "idle" / "sprites"
    return Graphics(sprites_folder=sprites_dir, cell_size=(32, 32),
                    loop=False, fps=1.0,
                    img_loader=MockImgFactory())


def _make_piece(piece_id: str, cell: tuple[int, int], board: Board) -> Piece:
    """Create a test piece with idle, move and jump states."""
    idle_phys = IdlePhysics(board)
    move_phys = MovePhysics(board, param=1.0)  # 1 cell/sec
    jump_phys = JumpPhysics(board, param=0.1)  # 100ms jump

    gfx = _graphics()

    idle = State(moves=Moves(MOVES_FILE, (8,8)), graphics=gfx, physics=idle_phys)
    move = State(moves=None, graphics=gfx, physics=move_phys)
    jump = State(moves=None, graphics=gfx, physics=jump_phys)

    idle.name = "idle"
    move.name = "move"
    jump.name = "jump"

    # Set up transitions
    idle.set_transition("move", move)
    idle.set_transition("jump", jump)
    move.set_transition("done", idle)
    jump.set_transition("done", idle)

    # Create piece and initialize
    piece = Piece(piece_id, idle)
    idle.reset(Command(0, piece_id, "idle", [cell]))
    
    return piece


def test_simple_piece_creation():
    """Test that we can create a piece with multiple states."""
    board = _board()
    piece = _make_piece("test_piece", (3, 3), board)
    
    assert piece.id == "test_piece"
    assert piece.state.name == "idle"
    assert piece.current_cell() == (3, 3)

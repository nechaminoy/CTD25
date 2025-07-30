import pathlib
import numpy as np

from ..shared.board import Board
from ..shared.command import Command
from ..shared.img import Img
from ..shared.physics import IdlePhysics, MovePhysics, JumpPhysics, RestPhysics
from ..shared.state import State
from ..shared.piece import Piece
# Adapt graphics builder to utilise mock image loader
from ..graphics.graphics import Graphics
from ..graphics.graphics_factory import MockImgFactory

PIECES_ROOT = pathlib.Path(__file__).parent.parent.parent / "pieces"
SPRITES_DIR = PIECES_ROOT / "BB" / "states" / "idle" / "sprites"

# ---------------------------------------------------------------------------
#                           HELPER BUILDERS
# ---------------------------------------------------------------------------


def _blank_img(w: int = 8, h: int = 8):
    img_path = PIECES_ROOT / "BB" / "states" / "idle" / "sprites" / "1.png"
    return Img().read(img_path, (w, h), keep_aspect=False)


def _board(cells: int = 8):
    cell_px = 1  # keep images tiny – we only test logic
    return Board(cell_px, cell_px, cells, cells, _blank_img(cells, cells))


def _graphics():
    gfx = Graphics(sprites_folder=SPRITES_DIR, cell_size=(1, 1), loop=False, fps=1.0, img_loader=MockImgFactory())
    # substitute minimal frame list
    from .mock_img import MockImg
    gfx.frames = [MockImg()]
    return gfx


# ---------------------------------------------------------------------------
#                              PHYSICS TESTS
# ---------------------------------------------------------------------------


def test_idle_physics_properties():
    board = _board()
    phys = IdlePhysics(board)
    cmd = Command(0, "P", "idle", [(2, 3)])
    phys.reset(cmd)

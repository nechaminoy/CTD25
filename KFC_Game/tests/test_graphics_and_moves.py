import pathlib, tempfile
from types import SimpleNamespace

from ..shared.board import Board
from ..shared.command import Command
from ..graphics.graphics import Graphics
from ..graphics.graphics_factory import MockImgFactory
from ..shared.moves import Moves
from .mock_img import MockImg


PIECES_ROOT = pathlib.Path(__file__).parent.parent.parent / "pieces"
SPRITES_DIR = PIECES_ROOT / "BB" / "states" / "idle" / "sprites"


def test_graphics_animation_timing():
    gfx = Graphics(
        sprites_folder=SPRITES_DIR,
        cell_size=(32, 32),
        loop=True,
        fps=10.0,
        img_loader=MockImgFactory(),
    )
    gfx.reset(Command(0, "test", "idle", []))

    num_frames = len(gfx.frames)
    frame_ms   = 1000 / gfx.fps
    for i in range(num_frames):
        gfx.update(i * frame_ms + frame_ms / 2)
        assert gfx.cur_frame == i

    gfx.update(num_frames * frame_ms + frame_ms / 2)
    assert gfx.cur_frame == 0


def test_graphics_non_looping():
    gfx = Graphics(
        sprites_folder=SPRITES_DIR,
        cell_size=(32, 32),
        loop=False,
        fps=10.0,
        img_loader=MockImgFactory(),
    )
    gfx.frames = [MockImg() for _ in range(3)]
    gfx.reset(Command(0, "test", "idle", []))

    gfx.update(1000)                # well past the end
    assert gfx.cur_frame == 2       # stuck on last frame


def test_graphics_empty_frames():
    gfx = Graphics(
        sprites_folder=SPRITES_DIR,
        cell_size=(32, 32),
        loop=True,
        fps=10.0,
        img_loader=MockImgFactory(),
    )
    gfx.frames = []                 # no frames loaded

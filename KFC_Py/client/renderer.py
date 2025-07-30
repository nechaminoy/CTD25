# KFC_Py/client/renderer.py
from __future__ import annotations
from typing import Dict, Any, Tuple
from pathlib import Path

from Board import Board
from GraphicsFactory import GraphicsFactory, ImgFactory
from Graphics import Graphics

class ClientRenderer:
    """
    Render snapshot payloads onto the board image.
    Caches per‑piece‑type sprites (idle) at board cell size.
    """
    def __init__(self, board: Board, pieces_root: Path, img_factory=None):
        self._board = board
        self._pieces_root = Path(pieces_root)
        self._gfx_factory = GraphicsFactory(img_factory or ImgFactory())
        self._cache: Dict[str, Graphics] = {}  # key: "PW"/"KB"/...

    @staticmethod
    def _type_name(piece_id: str) -> str:
        # IDs look like "PW_1", "KB_3", ...
        return piece_id.split("_", 1)[0]

    def _sprite(self, type_name: str) -> Graphics:
        g = self._cache.get(type_name)
        if g is None:
            sprites = self._pieces_root / type_name / "states" / "idle" / "sprites"
            g = self._gfx_factory.load(
                sprites_dir=sprites,
                cfg={},  # idle
                cell_size=(self._board.cell_W_pix, self._board.cell_H_pix),
            )
            self._cache[type_name] = g
        return g

    def render_snapshot(self, payload: Dict[str, Any]) -> None:
        canvas = self._board.img.copy()
        pieces = payload.get("pieces", [])

        for p in pieces:
            pid = p["id"]
            cell = tuple(p["cell"]) if isinstance(p.get("cell"), (list, tuple)) else p.get("cell")
            if cell is None:
                continue
            x_m, y_m = self._board.cell_to_m(cell)
            x_px, y_px = self._board.m_to_pix((x_m, y_m))

            sprite = self._sprite(self._type_name(pid)).get_img()
            sprite.draw_on(canvas, x_px, y_px)

        self._board.img = canvas

    def frame(self):
        return self._board.img

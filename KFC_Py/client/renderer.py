# KFC_Py/client/renderer.py
from __future__ import annotations
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from canvas import board_img  
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
        
        # Ensure board image is loaded
        if self._board.img is None:
            logging.info("Loading initial board image")
            board_img = self._gfx_factory._img_factory(
                str(self._pieces_root / "board.png"),
                (self._board.W_cells * self._board.cell_W_pix,
                 self._board.H_cells * self._board.cell_H_pix),
                keep_aspect=False
            )
            self._board = board_img

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
        if self._board.img is None:
            # Try to reload both background and board images
            logging.warning("Board image is None, attempting to reload")
            
            # Load background first
            bg_path = str(Path(__file__).resolve().parent.parent.parent / "table_bg_13in.png")
            if Path(bg_path).exists():
                self._board.img = self._gfx_factory._img_factory(bg_path, (1920, 1080))
            else:
                logging.error(f"Background image not found at {bg_path}")
                return
            
        if self._board.img is None:
            logging.error("Failed to load board image")
            return
            
        canvas = self._board.img.copy()
        pieces = payload.get("pieces", [])
        # logging.debug(f"Rendering snapshot with {len(pieces)} pieces")

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
        bg = board_img.copy()
        x0 = (bg.W - canvas.W) // 2
        y0 = (bg.H - canvas.H) // 2
        canvas.draw_on(bg, x0, y0)

        self._frame = bg.img

    def frame(self):
        if self._board.img is None:
            # logging.error("Board image is None in frame()")
            return None
        # logging.debug(f"Returning board image with shape {self._board.img.img.shape}")
        # return getattr(self._board.img, "img", self._board.img)
        return getattr(self, "_frame", self._board.img.img)

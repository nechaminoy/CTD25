# KFC_Game/client/renderer.py
from __future__ import annotations
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from ..shared.board import Board
from ..graphics.graphics_factory import GraphicsFactory, ImgFactory
from ..graphics.graphics import Graphics

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
            # Try to reload both background and board images
            logging.warning("Board image is None, attempting to reload")
            
            # Load background first
            bg_path = str(Path(__file__).resolve().parent.parent.parent / "table_bg_13in.png")
            if Path(bg_path).exists():
                self._board.img = self._gfx_factory._img_factory(bg_path, (1920, 1080))
            else:
                logging.error(f"Background image not found at {bg_path}")
                return

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
            logging.error("Failed to load board image")
            return
            
        # Start with a fresh copy of the background
        bg_path = str(Path(__file__).resolve().parent.parent.parent / "table_bg_13in.png")
        if Path(bg_path).exists():
            canvas = self._gfx_factory._img_factory(bg_path, (1920, 1080))
        else:
            canvas = self._board.img.copy()
        
        # Draw the chess board on top of the background
        board_path = str(Path(__file__).resolve().parent.parent.parent / "pieces" / "board.png")
        if Path(board_path).exists():
            board_img = self._gfx_factory._img_factory(board_path, (512, 512))
            # Center the board on the background
            board_x = (canvas.img.shape[1] - 512) // 2  # Center horizontally
            board_y = (canvas.img.shape[0] - 512) // 2  # Center vertically
            board_img.draw_on(canvas, board_x, board_y)
            # logging.debug(f"Drew chess board at position ({board_x}, {board_y})")
            
        pieces = payload.get("pieces", [])
        # logging.debug(f"Rendering snapshot with {len(pieces)} pieces")

        for p in pieces:
            pid = p["id"]
            cell = tuple(p["cell"]) if isinstance(p.get("cell"), (list, tuple)) else p.get("cell")
            if cell is None:
                continue
            
            # Fix coordinate mapping: chess notation (row, col) to screen coordinates
            # cell[0] is row (0-7), cell[1] is column (0-7)
            row, col = cell[0], cell[1]
            
            # Calculate position on the board (centered on background)
            board_x_offset = (canvas.img.shape[1] - 512) // 2
            board_y_offset = (canvas.img.shape[0] - 512) // 2
            
            # Calculate cell position within the board
            cell_x = col * 64 + 32  # column * cell_width + center_offset
            cell_y = row * 64 + 32  # row * cell_height + center_offset
            
            # Final position on canvas
            sprite_x = board_x_offset + cell_x - 32  # center the sprite
            sprite_y = board_y_offset + cell_y - 32
            
            # Center the sprite on the cell
            sprite = self._sprite(self._type_name(pid)).get_img()
            
            logging.debug(f"Drawing piece {pid} at cell ({row}, {col}) -> pixel ({sprite_x}, {sprite_y})")
            sprite.draw_on(canvas, sprite_x, sprite_y)

        # Draw player cursors (selection indicators)
        cursors = payload.get("cursors", [])
        for cursor in cursors:
            player = cursor.get("player")
            cursor_cell = cursor.get("cell")
            if cursor_cell is None:
                continue
                
            row, col = cursor_cell[0], cursor_cell[1]
            
            # Calculate cursor position
            board_x_offset = (canvas.img.shape[1] - 512) // 2
            board_y_offset = (canvas.img.shape[0] - 512) // 2
            
            # Calculate cell boundaries for cursor rectangle
            x1 = board_x_offset + col * 64
            y1 = board_y_offset + row * 64
            x2 = x1 + 64 - 1
            y2 = y1 + 64 - 1
            
            # Player 1 = Green, Player 2 = Red (BGR format)
            color = (0, 255, 0) if player == 1 else (0, 0, 255)
            
            # Draw cursor rectangle using OpenCV directly on the numpy array
            import cv2
            cv2.rectangle(canvas.img, (x1, y1), (x2, y2), color, 3)
            logging.debug(f"Drawing cursor for player {player} at cell ({row}, {col}) -> rect ({x1}, {y1}) to ({x2}, {y2})")

        self._board.img = canvas

    def frame(self):
        if self._board.img is None:
            logging.error("Board image is None in frame()")
            return None
        # logging.debug(f"Returning board image with shape {self._board.img.img.shape}")
        return self._board.img.img  # Return the actual numpy array, not the wrapper

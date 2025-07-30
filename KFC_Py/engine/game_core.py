from typing import Optional
from Game import Game
from Command import Command
from Board import Board
from bus import EventBus
from Piece import Piece

class GameCore:
    """A thin seam around Game – no behaviour change."""
    def __init__(self, pieces: list[Piece], board: Board, bus: Optional[EventBus] = None):
        self._impl = Game(pieces, board, bus)

    def enqueue(self, cmd: Command) -> None:
        self._impl.user_input_queue.put(cmd)  # delegate

    def tick(self, num_iterations: int | None = None, with_graphics: bool = False):
        return self._impl._run_game_loop(num_iterations=num_iterations, is_with_graphics=with_graphics)

    @property
    def game(self) -> Game:
        return self._impl

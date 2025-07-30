import pathlib, time, sys
import logging
import pytest

from ..graphics.graphics_factory import MockImgFactory
from ..server.game import Game
from ..shared.command import Command
from ..server.game_factory import create_game

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_cannot_capture_same_color():
    """Test that pieces cannot capture pieces of their own color."""
    pieces_dir = pathlib.Path(__file__).parent.parent.parent / "pieces"
    game = create_game(pieces_dir, MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Get two white pieces - a pawn and a knight
    white_pawn = game.pos[(6, 0)][0]  # White pawn on a2
    white_knight = game.pos[(7, 1)][0]  # White knight on b1
    
    print(f"White pawn at {white_pawn.current_cell()}, id: {white_pawn.id}")
    print(f"White knight at {white_knight.current_cell()}, id: {white_knight.id}")
    
    # Move the pawn forward to create a target
    game.user_input_queue.put(Command(game.game_time_ms(), white_pawn.id, "move", [(6, 0), (4, 0)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Pawn moved to {white_pawn.current_cell()}")
    assert white_pawn.current_cell() == (4, 0)
    
    # Try to move knight to capture the white pawn (should fail)
    initial_position = white_knight.current_cell()
    game.user_input_queue.put(Command(game.game_time_ms(), white_knight.id, "move", [(7, 1), (4, 0)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    
    # Knight should not have moved because it cannot capture its own pawn
    print(f"Knight position after attempted capture: {white_knight.current_cell()}")
    assert white_knight.current_cell() == initial_position, "Knight should not be able to capture same color piece"
    
    # Both pieces should still exist
    assert white_pawn in game.pieces, "White pawn should not be captured by same color"
    assert white_knight in game.pieces, "White knight should still exist"

def test_pawn_cannot_capture_same_color():
    """Test that pawns cannot capture pieces of their own color."""
    pieces_dir = pathlib.Path(__file__).parent.parent.parent / "pieces"
    game = create_game(pieces_dir, MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Get two white pawns
    pawn1 = game.pos[(6, 0)][0]  # White pawn on a2
    pawn2 = game.pos[(6, 1)][0]  # White pawn on b2
    
    print(f"Pawn1 at {pawn1.current_cell()}, id: {pawn1.id}")
    print(f"Pawn2 at {pawn2.current_cell()}, id: {pawn2.id}")
    
    # Move pawn2 to a position where pawn1 could "capture" it diagonally
    game.user_input_queue.put(Command(game.game_time_ms(), pawn2.id, "move", [(6, 1), (5, 1)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Pawn2 moved to {pawn2.current_cell()}")
    
    # Try to move pawn1 diagonally to "capture" pawn2 (should fail)
    initial_position = pawn1.current_cell()
    game.user_input_queue.put(Command(game.game_time_ms(), pawn1.id, "move", [(6, 0), (5, 1)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    
    # Pawn1 should not have moved because it cannot capture its own color
    print(f"Pawn1 position after attempted capture: {pawn1.current_cell()}")
    assert pawn1.current_cell() == initial_position, "Pawn should not be able to capture same color piece"
    
    # Both pawns should still exist
    assert pawn1 in game.pieces, "Pawn1 should still exist"
    assert pawn2 in game.pieces, "Pawn2 should not be captured by same color"

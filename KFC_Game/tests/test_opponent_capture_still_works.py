import pathlib, time, sys
import logging

from ..graphics.graphics_factory import MockImgFactory
from ..server.game import Game
from ..shared.command import Command
from ..server.game_factory import create_game

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_can_capture_opponent_color():
    """Test that pieces CAN capture pieces of the opponent's color."""
    pieces_dir = pathlib.Path(__file__).parent.parent.parent / "pieces"
    game = create_game(pieces_dir, MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Get a white pawn and move it forward
    white_pawn = game.pos[(6, 0)][0]  # White pawn on a2
    print(f"White pawn at {white_pawn.current_cell()}, id: {white_pawn.id}")
    
    # Move white pawn forward two squares
    game.user_input_queue.put(Command(game.game_time_ms(), white_pawn.id, "move", [(6, 0), (4, 0)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"White pawn moved to {white_pawn.current_cell()}")
    
    # Get a black pawn and move it to be captured
    black_pawn = game.pos[(1, 1)][0]  # Black pawn on b7
    print(f"Black pawn at {black_pawn.current_cell()}, id: {black_pawn.id}")
    
    # Move black pawn down to be in range for white pawn capture
    game.user_input_queue.put(Command(game.game_time_ms(), black_pawn.id, "move", [(1, 1), (3, 1)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Black pawn moved to {black_pawn.current_cell()}")
    
    # Now move white pawn diagonally to capture black pawn (should succeed)
    initial_pieces_count = len(game.pieces)
    game.user_input_queue.put(Command(game.game_time_ms(), white_pawn.id, "move", [(4, 0), (3, 1)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    
    # Verify that capture occurred
    assert len(game.pieces) < initial_pieces_count, "Piece count should decrease after capture"
    assert white_pawn.current_cell() == (3, 1), "White pawn should be at capture position"
    assert black_pawn not in game.pieces, "Black pawn should be removed from game"
    
    print("✓ Opponent capture test passed!")

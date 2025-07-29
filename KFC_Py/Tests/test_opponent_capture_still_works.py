import pathlib, time, sys
import logging

# Add parent directory to path for imports
sys.path.append('..')

from GraphicsFactory import MockImgFactory
from Game import Game
from Command import Command
from GameFactory import create_game

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_can_capture_opponent_color():
    """Test that pieces CAN capture pieces of the opponent's color."""
    game = create_game("../pieces", MockImgFactory())
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
    game._run_game_loop(num_iterations=150, is_with_graphics=False)
    
    print(f"White pawn final position: {white_pawn.current_cell()}")
    print(f"Black pawn still in game: {black_pawn in game.pieces}")
    print(f"Pieces count before: {initial_pieces_count}, after: {len(game.pieces)}")
    
    # White pawn should have moved to capture position
    assert white_pawn.current_cell() == (3, 1), f"White pawn should be at (3,1) but is at {white_pawn.current_cell()}"
    
    # Black pawn should be captured (removed from game)
    assert all(p.id != black_pawn.id for p in game.pieces), "Black pawn should be captured"

    # Total pieces should be reduced by 1
    assert len(game.pieces) == initial_pieces_count - 1, "One piece should be captured"

if __name__ == "__main__":
    test_can_capture_opponent_color()
    print("Test passed! Opponent capture still works correctly.")

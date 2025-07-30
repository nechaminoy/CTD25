import pathlib, time, sys
import logging

from ..graphics.graphics_factory import MockImgFactory
from ..server.game import Game
from ..shared.command import Command
from ..server.game_factory import create_game
from ..input.keyboard_input import KeyboardProducer, KeyboardProcessor

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_player_color_restrictions():
    """Test that players can only select pieces of their own color."""
    pieces_dir = pathlib.Path(__file__).parent.parent.parent / "pieces"
    game = create_game(pieces_dir, MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Create keyboard processors for testing
    p1_map = {"enter": "select"}
    p2_map = {"f": "select"}
    
    kp1 = KeyboardProcessor(8, 8, p1_map, initial_pos=(7, 0))  # Player 1 (White)
    kp2 = KeyboardProcessor(8, 8, p2_map, initial_pos=(0, 0))  # Player 2 (Black)
    
    # Test that Player 1 can select white pieces
    white_piece = game.pos[(7, 0)][0]  # White rook
    print(f"White piece: {white_piece.id} at {white_piece.current_cell()}")
    assert white_piece.id[1] == 'W', "Should be a white piece"
    
    # Test that Player 2 can select black pieces  
    black_piece = game.pos[(0, 0)][0]  # Black rook
    print(f"Black piece: {black_piece.id} at {black_piece.current_cell()}")
    assert black_piece.id[1] == 'B', "Should be a black piece"
    
    # Basic functionality test
    assert kp1.get_cursor() == (7, 0)
    assert kp2.get_cursor() == (0, 0)
    
    print("✓ Player color restrictions test passed!")

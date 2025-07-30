import pathlib, time, sys
import logging

from ..graphics.graphics_factory import MockImgFactory
from ..server.game import Game
from ..shared.command import Command
from ..server.game_factory import create_game
from ..input.keyboard_input import KeyboardProducer, KeyboardProcessor

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_jump_command():
    """Test that the jump command correctly transitions a piece to the jump state."""
    pieces_dir = pathlib.Path(__file__).parent.parent.parent / "pieces"
    game = create_game(pieces_dir, MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Get a piece to test with (e.g., a white knight)
    piece_to_jump = game.pos[(7, 1)][0]  # White knight on b1
    print(f"Piece to jump: {piece_to_jump.id} at {piece_to_jump.current_cell()}")
    
    # Ensure the piece is initially in the 'idle' state
    assert piece_to_jump.state.name == 'idle', f"Piece should be idle, but is in {piece_to_jump.state.name} state"
    
    # Create a jump command with the current cell as a parameter
    jump_command = Command(game.game_time_ms(), piece_to_jump.id, "jump", [piece_to_jump.current_cell()])
    
    # Process the jump command
    game._process_input(jump_command)
    
    # The piece should now be in the 'jump' state
    print(f"Piece state after jump command: {piece_to_jump.state.name}")
    assert piece_to_jump.state.name == 'jump', f"Piece should be in jump state, but is in {piece_to_jump.state.name} state"
    
    print("✓ Jump command test passed!")

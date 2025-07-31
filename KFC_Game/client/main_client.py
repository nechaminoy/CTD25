"""
Client main entry point for KFC Game.
"""
import asyncio
import logging
from pathlib import Path

# Import shared components
from ..server.game_factory import create_game
from ..graphics.graphics_factory import ImgFactory
from ..config.settings import PIECES_DIR, WS_HOST, WS_PORT

logger = logging.getLogger(__name__)

DEFAULT_HOST = WS_HOST or "localhost"
DEFAULT_PORT = WS_PORT or 8765

async def run_client(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, player: str = "W"):
    """
    Run the game client.
    
    Args:
        host: Server host address
        port: Server port number
        player: Player color ("W" or "B")
    """
    logger.info(f"Starting KFC client, connecting to {host}:{port} as player {player}")
    
    try:
        # Create game instance for client - this will properly subscribe to all events including move_history
        game = create_game(PIECES_DIR, ImgFactory())
        
        # Import client-specific modules
        from .ws_client import WSClient
        from .event_bridge import EventBridge
        from .renderer import ClientRenderer
        from .display import Cv2Display
        from .render_loop import ClientRenderLoop
        from .ui_state_sync import BoardMirror, subscribe_state_sync, subscribe_render
        from .input_handler import setup_input_handling
        
        # Setup WebSocket connection
        ws_uri = f"ws://{host}:{port}"
        ws_client = WSClient(ws_uri)
        await ws_client.connect(player=player)
        
        # Setup event bridge
        event_bridge = EventBridge(ws_client, game.bus)
        event_bridge.start()
        
        # Setup UI state synchronization
        board_mirror = BoardMirror()
        subscribe_state_sync(game.bus, board_mirror)
        
        # Setup renderer and display
        player_num = 1 if player == "W" else 2
        renderer = ClientRenderer(game.board, PIECES_DIR, ImgFactory(), player_num=player_num)
        subscribe_render(game.bus, renderer)
        
        display = Cv2Display("Kung Fu Chess")
        render_loop = ClientRenderLoop(renderer, hz=60.0, display=display)
        render_loop.start()
        
        # Setup input handling
        input_handler = setup_input_handling(game, ws_client, player, board_mirror)
        input_handler.start()
        
        # Main client loop
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            await render_loop.stop()
            display.close()
            
    except Exception as e:
        logger.error(f"Client error: {e}")
        raise

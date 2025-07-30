"""
Client main entry point for KFC Game.
"""
import asyncio
import logging
from pathlib import Path

# Import shared components
from shared.game_factory import GameFactory
from shared.graphics_factory import ImgFactory
from shared.config import PIECES_DIR, DEFAULT_HOST, DEFAULT_PORT

logger = logging.getLogger(__name__)


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
        # Create game instance for client
        game_factory = GameFactory(PIECES_DIR, ImgFactory())
        game = game_factory.create_client_game()
        
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
        renderer = ClientRenderer(game.board, PIECES_DIR, ImgFactory())
        subscribe_render(game.bus, renderer)
        
        display = Cv2Display("Kung Fu Chess")
        render_loop = ClientRenderLoop(renderer, hz=60.0, display=display)
        render_loop.start()
        
        # Setup input handling
        input_handler = setup_input_handling(game, ws_client, player)
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

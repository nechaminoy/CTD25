"""
Server main entry point for KFC Game.
"""
import asyncio
import logging
from pathlib import Path

# Import components
from .game_factory import create_game
from ..graphics.graphics_factory import ImgFactory
from ..config.settings import PIECES_DIR, WS_HOST, WS_PORT

logger = logging.getLogger(__name__)

DEFAULT_HOST = WS_HOST or "localhost"
DEFAULT_PORT = WS_PORT or 8765


async def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Run the game server.
    
    Args:
        host: Server host address
        port: Server port number
    """
    logger.info(f"Starting KFC server on {host}:{port}")
    
    try:
        # Create game instance for server - this will properly subscribe to all events including move_history
        game = create_game(PIECES_DIR, ImgFactory())
        
        # Import server-specific modules
        from .ws_server import serve_and_tick
        
        # Start server with game loop
        await serve_and_tick(game, host=host, port=port)
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

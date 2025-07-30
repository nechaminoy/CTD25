"""
Server main entry point for KFC Game.
"""
import asyncio
import logging
from pathlib import Path

# Import shared components
from shared.game_factory import GameFactory
from shared.graphics_factory import ImgFactory
from shared.config import PIECES_DIR, DEFAULT_HOST, DEFAULT_PORT

logger = logging.getLogger(__name__)


async def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Run the game server.
    
    Args:
        host: Server host address
        port: Server port number
    """
    logger.info(f"Starting KFC server on {host}:{port}")
    
    try:
        # Create game instance for server
        game_factory = GameFactory(PIECES_DIR, ImgFactory())
        game = game_factory.create_server_game()
        
        # Import server-specific modules
        from .ws_server import serve_and_tick
        
        # Start server with game loop
        await serve_and_tick(game, host=host, port=port)
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

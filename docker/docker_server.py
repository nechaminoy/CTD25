#!/usr/bin/env python3
"""
Docker entry point for KFC Game Server
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the server"""
    try:
        # Import after setting up the path
        from KFC_Game.main import run_server
        
        # Get host and port from environment variables
        host = os.getenv("KFC_HOST", "0.0.0.0")  # Listen on all interfaces in Docker
        port = int(os.getenv("KFC_PORT", "8765"))
        
        logger.info(f"Starting KFC Game Server in Docker container on {host}:{port}")
        await run_server(host=host, port=port)
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure PYTHONPATH includes the project root")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

import os
from pathlib import Path

PIECES_DIR = str(Path(__file__).parent.parent.parent / "pieces")

# Server configuration with environment variable support
WS_HOST = os.getenv("KFC_HOST", "127.0.0.1")
WS_PORT = int(os.getenv("KFC_PORT", "8765"))
WS_URI = f"ws://{WS_HOST}:{WS_PORT}"

"""
Shared configuration for KFC Game.
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
PIECES_DIR = ASSETS_DIR / "pieces"
SOUNDS_DIR = ASSETS_DIR / "sounds"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"

# Network settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
WS_PING_INTERVAL = 10.0
WS_PING_TIMEOUT = 5.0

# Game settings
CELL_SIZE = 64  # pixels
BOARD_SIZE = (8, 8)  # cells
BOARD_PIXEL_SIZE = (CELL_SIZE * BOARD_SIZE[0], CELL_SIZE * BOARD_SIZE[1])

# Display settings
WINDOW_SIZE = (1920, 1080)
FPS = 60

# Audio settings
MASTER_VOLUME = 0.7
SOUND_ENABLED = True

# Input settings
KEYBOARD_REPEAT_DELAY = 0.2  # seconds
KEYBOARD_REPEAT_RATE = 0.05  # seconds

# Debug settings
DEBUG_GRAPHICS = False
DEBUG_NETWORK = False
DEBUG_PHYSICS = False

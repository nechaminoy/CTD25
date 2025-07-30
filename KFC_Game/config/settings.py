from pathlib import Path
PIECES_DIR = str(Path(__file__).parent.parent.parent / "pieces")
WS_HOST = "127.0.0.1"
WS_PORT = 8765
WS_URI  = f"ws://{WS_HOST}:{WS_PORT}"

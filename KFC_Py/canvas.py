from img import Img
from pathlib import Path

IMG_PATH = Path(__file__).resolve().parent.parent / "table_bg_13in.png"
if not IMG_PATH.exists():
    raise FileNotFoundError(f"Cannot load image: {IMG_PATH}")
board_img = Img().read(str(IMG_PATH), size=(1920, 1080))

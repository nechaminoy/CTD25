# mock_img.py
import pathlib, cv2
import numpy as np
from ..shared.img import Img


class MockImg(Img):
    """Headless Img that just records calls."""
    traj: list[tuple[int, int]] = []  # every draw_on() position
    txt_traj: list[tuple[tuple[int, int], str]] = []

    def __init__(self):  # override, no cv2 needed

        self.img = None
        self.W = 0
        self.H = 0

    # keep the method names identical to Img -------------------------
    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA):
        if size is None:
            w, h = 64, 64
        else:
            w, h = size

        self.img = np.zeros((h, w, 3), dtype=np.uint8)

        self.W, self.H = w, h
        return self  # chain-call compatible

    def copy(self):
        m = MockImg()
        m.W, m.H = self.W, self.H
        m.img = None if self.img is None else self.img.copy()
        return m

    def draw_on(self, other, x, y):
        MockImg.traj.append((x, y))

    def put_text(self, txt, x, y, font_size, *_, **__):
        MockImg.txt_traj.append(((x, y), txt))

    def show(self):
        pass  # do nothing

    # helper for tests
    @classmethod
    def reset(cls):
        cls.traj.clear()
        cls.txt_traj.clear()


mock_graphics_image_loader = (
    lambda path, size, keep_aspect=False: MockImg().read(path, size, keep_aspect)
)

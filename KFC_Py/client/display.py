# KFC_Py/client/display.py
from __future__ import annotations
from typing import Optional

class NullDisplay:
    def present(self, img):  # img: numpy array (H,W,3|4)
        pass
    def close(self):
        pass

class Cv2Display:
    def __init__(self, window_name: str = "Kung Fu Chess"):
        import cv2
        self.cv2 = cv2
        self.window_name = window_name
        self.cv2.namedWindow(self.window_name, self.cv2.WINDOW_AUTOSIZE)

    def present(self, img):
        if img is None:
            return
        if img.ndim == 3 and img.shape[2] == 4:
            bgr = self.cv2.cvtColor(img, self.cv2.COLOR_BGRA2BGR)
            self.cv2.imshow(self.window_name, bgr)
        else:
            self.cv2.imshow(self.window_name, img)
        self.cv2.waitKey(1)

    def close(self):
        try:
            self.cv2.destroyWindow(self.window_name)
        except Exception:
            pass

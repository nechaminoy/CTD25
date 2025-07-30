# KFC_Py/client/render_loop.py
from __future__ import annotations
import logging
import asyncio
import contextlib

class ClientRenderLoop:
    """
    Simple client-side render ticker.
    Calls renderer.frame() at a fixed rate (hz). You can later extend it to:
    - interpolate positions between snapshots
    - present frames to a window
    """
    def __init__(self, renderer, hz: float = 60.0, display=None):
        self.renderer = renderer
        self.hz = hz
        self.display = display
        self._task = None
        self._running = False
        self.frames = 0

    async def _run(self):
        period = 1.0 / self.hz if self.hz and self.hz > 0 else 0.0
        try:
            while self._running:
                # pull the current frame from the renderer (side effects update the board image)
                frame = self.renderer.frame()
                self.frames += 1
                
                # if frame is None:
                #     logging.error("Renderer returned None frame")
                # else:
                #     logging.debug(f"Got frame from renderer: shape={frame if hasattr(frame, 'shape') else 'no shape'}")
                
                if self.display is not None:
                    self.display.present(frame)
                # yield control at a steady cadence
                await asyncio.sleep(period)
        except asyncio.CancelledError:
            pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

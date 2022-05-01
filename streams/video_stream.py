from typing import Tuple

import numpy as np
from ffutils import VideoReader

from .base import IVisualStream


class VideoStream(IVisualStream):
    def __init__(self, vpath):
        super().__init__()
        self._reader = VideoReader(vpath, "rgb")
        got, im = self._reader.read()
        assert got
        self._extend = (im.shape[1], im.shape[0])
        self._reader.seek_msec(0.0)

    @property
    def duration(self) -> float:
        return self._reader.duration

    @property
    def extend(self) -> Tuple[int, int]:
        return self._extend

    def seek_msec(self, msec: float):
        self._reader.seek_msec(msec)

    def _read(self) -> Tuple[bool, np.ndarray]:
        return self._reader.read()

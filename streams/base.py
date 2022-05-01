from typing import Tuple

import numpy as np
from imgui.utils.image_texture import ImageTexture


class IVisualStream(object):
    def __init__(self):
        self._tex = ImageTexture()

    @property
    def duration(self) -> float:
        raise NotImplementedError()

    @property
    def extend(self) -> Tuple[int, int]:
        raise NotImplementedError()

    def seek_msec(self, msec: float):
        raise NotImplementedError()

    def _read(self) -> Tuple[bool, np.ndarray]:
        raise NotImplementedError()

    def update(self):
        got, im = self._read()
        if got:
            self._tex.update(im)

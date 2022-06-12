from typing import Tuple

import numpy as np
from imgui.utils.image_texture import ImageTexture


class IVisualStream(object):
    def __init__(self):
        self._textures = [ImageTexture(), ImageTexture()]
        self._cur_tidx = len(self._textures) - 1

    @property
    def texture(self):
        return self._textures[self._cur_tidx]

    def update(self):
        got, im = self._read()
        if got:
            self._cur_tidx = (self._cur_tidx + 1) % len(self._textures)
            self.texture.update(im)

    @property
    def duration(self) -> float:
        raise NotImplementedError()

    @property
    def extend(self) -> Tuple[int, int]:
        raise NotImplementedError()

    @property
    def curr_msec(self) -> float:
        raise NotImplementedError()

    def seek_msec(self, msec: float):
        raise NotImplementedError()

    def _read(self) -> Tuple[bool, np.ndarray]:
        raise NotImplementedError()

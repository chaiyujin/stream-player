import argparse
import time
from typing import List

import glfw
import imgui
import numpy as np
from OpenGL import GL as gl

from streams import AudioPlayer, IVisualStream, VideoStream
from utils import format_time, timeit


class ImGuiStreamPlayer(object):
    def __init__(self):
        # playing state
        self._playing = False
        self._seeking = False
        # cur timestamp in milliseconds
        self._ts = np.asarray([0.0], dtype=np.float32)
        # video reader
        self._visual_streams: List[IVisualStream] = []
        # optional audio
        self._ap = AudioPlayer()
        # clock for non-audio case
        self._prv_time = time.time()
        self._cur_time = time.time()

    def set_audio(self, apath):
        try:
            self._ap.open(apath)
        except Exception as e:
            self._ap.close()
            print("Failed to open audio: {}".format(e))

    def open(self, vpath):
        st = VideoStream(vpath)
        print("Video Stream: {}".format(st.extend))
        # TODO: multiple streams
        self._visual_streams = [st]

    def close_all(self):
        self._ap.close()

    @property
    def duration(self) -> float:
        dur = float("inf") if not self._ap.is_open() else self._ap.duration
        for st in self._visual_streams:
            dur = min(dur, st.duration)
        return dur

    def sync_streams(self):
        # main clock: time | audio player
        if not self._ap.is_open():
            self._cur_time = time.time()
            if self._playing and not self._seeking:
                delta = self._cur_time - self._prv_time
                self._ts[0] += delta * 1000.0
            self._prv_time = self._cur_time
        else:
            if self._seeking:
                self._ap.pause()
                self._ap.seek(self._ts[0])
            else:
                self._ap.toggle(self._playing)
                self._ts[0] = self._ap.curr_msec

        # seek visual streams
        for st in self._visual_streams:
            st.seek_msec(self._ts[0])
            st.update()

    def imgui_draw(self):
        # imgui video player
        io = imgui.get_io()
        style = imgui.get_style()
        imgui.set_next_window_pos((0, 0))
        imgui.set_next_window_size(io.display_size)
        # fmt: off
        imgui.begin("Video", None, imgui.ImGuiWindowFlags.NoTitleBar
                                 | imgui.ImGuiWindowFlags.NoResize
                                 | imgui.ImGuiWindowFlags.NoScrollbar)
        # fmt: on

        ctrl_h = imgui.get_frame_height_with_spacing()
        win_size = imgui.get_window_size()
        win_pads = style.window_padding
        win_brdr = style.window_border_size

        # top bar
        # - app running fps
        app_fps_info = "{:3.0f} FPS".format(io.framerate)
        app_fps_info_size = imgui.calc_text_size(app_fps_info)
        imgui.set_cursor_pos_x(win_size.x - win_pads.x - win_brdr - app_fps_info_size.x)
        imgui.text(app_fps_info)

        # compute area for image
        max_w = win_size.x - (win_pads.x + win_brdr) * 2
        max_h = win_size.y - (win_pads.y + win_brdr) - imgui.get_cursor_pos_y() - ctrl_h
        # image
        st = self._visual_streams[0]  # TODO: multiple streams
        if not st._tex.empty():
            w, h = st._tex.extend
            # proper position
            if max_w * h > w * max_h:
                w = w / h * max_h
                h = max_h
            else:
                h = h / w * max_w
                w = max_w
            x = (max_w - w) // 2
            y = (max_h - h) // 2
            imgui.set_cursor_pos_x(x + imgui.get_cursor_pos_x())
            imgui.set_cursor_pos_y(y + imgui.get_cursor_pos_y())
            imgui.image(st._tex.id, (w, h))
            imgui.set_cursor_pos_y(y + imgui.get_cursor_pos_y())
        else:
            imgui.set_cursor_pos_y(max_h + imgui.get_cursor_pos_y())

        # control
        # - time info string, get size here
        time_info_str = format_time(self._ts[0])
        time_info_size = imgui.calc_text_size(format_time(self._ts[0]))
        # - play/stop button
        if imgui.button("stop" if self._playing else "play"):
            self._playing = not self._playing
        imgui.same_line()
        # - seeker slider
        seeker_w = imgui.get_window_width() - imgui.get_cursor_pos_x()
        seeker_w -= style.window_padding.x + style.window_border_size  # right padding and border
        seeker_w -= style.item_spacing.x + time_info_size.x
        imgui.push_item_width(seeker_w)
        if imgui.slider_float("##video_player-seeker", self._ts, 0.0, self.duration, ""):
            self._seeking = True
        else:
            self._seeking = self._seeking and imgui.is_mouse_down(imgui.ImGuiMouseButton.Left)
        imgui.pop_item_width()
        imgui.same_line()
        # - time info text
        imgui.push_item_width(time_info_size.x)
        imgui.text(time_info_str)
        imgui.pop_item_width()
        imgui.end()


def imgui_main(window, filepath):
    # imgui context and init implementation
    imgui_ctx = imgui.create_context()
    imgui.set_current_context(imgui_ctx)
    imgui.style_colors_dark()
    imgui.impl_init(window)

    # data
    player = ImGuiStreamPlayer()
    player.set_audio(filepath)
    player.open(filepath)

    def _frame_begin():
        glfw.poll_events()
        imgui.impl_new_frame()
        imgui.new_frame()

    def _frame_end():
        imgui.render()
        w, h = glfw.get_framebuffer_size(window)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.2, 0.2, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        imgui.impl_render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    while not glfw.window_should_close(window):
        # data
        player.sync_streams()

        # ui
        _frame_begin()
        player.imgui_draw()
        _frame_end()

    # cleanup
    imgui.impl_shutdown()
    imgui.destroy_context(imgui_ctx)


def key_callback(window, key, scancode, action, mods):
    # print(f"press key {key}")
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main(filepath):
    if not glfw.init():
        return

    window = glfw.create_window(640, 480, "Stream Player", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.make_context_current(window)
    glfw.swap_interval(-1)

    glfw.set_key_callback(window, key_callback)

    imgui_main(window, filepath)

    glfw.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", type=str)
    args = parser.parse_args()

    main(args.filepath)

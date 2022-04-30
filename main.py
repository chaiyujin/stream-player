import os
import time

import glfw
import imgui
import numpy as np
from ffutils import VideoReader
from imgui.utils.image_texture import ImageTexture
from OpenGL import GL as gl

from utils import timeit
from audio_player import AudioPlayer

test_vpath = os.path.expanduser("~/Videos/30fps.mp4")
test_vpath = os.path.expanduser("~/Videos/love_poem.mp4")

ap = None
ap = AudioPlayer()
ap.open(test_vpath)


def format_time(msec):
    sec = msec / 1000.0
    h = int(sec / 3600)
    sec -= h * 3600
    m = int(sec / 60)
    sec -= m * 60
    s = int(sec)
    ms = sec - s
    return f"{h:02d}:{m:02d}:{s:02d}" + f"{ms:.3f}"[1:]


def test_imgui(window):

    imgui_ctx = imgui.create_context()
    imgui.set_current_context(imgui_ctx)
    imgui.style_colors_dark()
    imgui.impl_init(window)

    img_tex = ImageTexture()
    reader = VideoReader(test_vpath)
    reader.seek_msec(0.0)
    duration = reader.duration
    # fps = reader.fps  # todo

    # init timestamp
    msec = np.asarray([0.0], dtype=np.float32)

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

    lst_time = 0
    cur_time = time.time()
    playing = False
    seeking = False
    while not glfw.window_should_close(window):
        _frame_begin()

        # update time / audio player
        if ap is None:
            if seeking:
                lst_time = msec[0] / 1000.0
            else:
                now_time = time.time()
                if playing:
                    lst_time += now_time - cur_time
                    msec[0] = lst_time * 1000.0
                cur_time = now_time
        else:
            if seeking:
                ap.pause()
                ap.seek(msec[0])
            else:
                ap.toggle(playing)
                msec[0] = ap.curr_msec

        # seek video
        # print(msec[0])
        reader.seek_msec(msec[0])
        got, im = reader.read()
        if got:
            img_tex.update(im, is_bgr=True)

        # imgui video player
        io = imgui.get_io()
        style = imgui.get_style()
        imgui.begin("Video", np.asarray([1], dtype=np.uint8))
        # info area
        imgui.text(
            "Msec: {:.0f}ms, Frame: {:.0f}, Player FPS: {:.1f}".format(
                msec[0],
                msec[0] * 30.0 / 1000.0,
                io.framerate
            )
        )
        # Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / io.Framerate, io.Framerate);
        # compute area for image
        ctrl_h = imgui.get_frame_height_with_spacing()
        max_w = imgui.get_window_width() - (style.window_padding.x + style.window_border_size) * 2
        max_h = imgui.get_window_height() - style.window_padding.y - style.window_border_size - imgui.get_cursor_pos_y() - ctrl_h
        # image
        if not img_tex.empty():
            w, h = img_tex.extend
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
            imgui.image(img_tex.id, (w, h))
            imgui.set_cursor_pos_y(y + imgui.get_cursor_pos_y())
        # control
        # - play/stop
        if imgui.button('stop' if playing else 'play'):
            playing = not playing
        imgui.same_line()
        # - time info
        imgui.text(format_time(msec[0]))
        imgui.same_line()
        # - seeker
        imgui.push_item_width(-1)
        if imgui.slider_float("##video_player-seeker", msec, 0.0, duration, ""):
            seeking = True
        else:
            seeking = seeking and imgui.is_mouse_down(imgui.ImGuiMouseButton.Left)
        imgui.pop_item_width()
        imgui.end()

        _frame_end()

    imgui.impl_shutdown()
    imgui.destroy_context(imgui_ctx)


def key_callback(window, key, scancode, action, mods):
    # print(f"press key {key}")
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main():

    if not glfw.init():
        return

    window = glfw.create_window(1280, 720, "Opengl GLFW Window", None, None)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.set_key_callback(window, key_callback)

    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)  # enable vsync

    test_imgui(window)

    glfw.terminate()


if __name__ == "__main__":
    main()

import os

import glfw
import imgui
import numpy as np
from ffutils import VideoReader
from imgui.utils.image_texture import ImageTexture
from OpenGL import GL as gl


def test_imgui(window):

    imgui_ctx = imgui.create_context()
    imgui.set_current_context(imgui_ctx)
    imgui.style_colors_dark()
    imgui.impl_init(window)

    img_tex = ImageTexture()
    reader = VideoReader(os.path.expanduser("~/Videos/30fps.mp4"))
    reader.seek_msec(0.0)
    got, im = reader.read()
    if got:
        img_tex.update(im, is_bgr=True)
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

    while not glfw.window_should_close(window):
        _frame_begin()

        # seek
        reader.seek_msec(msec[0])
        got, im = reader.read()
        if got:
            img_tex.update(im, is_bgr=True)

        # draw
        imgui.begin("Video", np.asarray([1], dtype=np.uint8))
        imgui.text("Msec: {:.0f}ms, Frame: {:.0f}".format(msec[0], msec[0] * 30.0 / 1000.0))
        if not img_tex.empty():
            imgui.image(img_tex.id, img_tex.extend)
        imgui.slider_float("Value", msec, 0.0, 10000.0, "%.0fms")
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

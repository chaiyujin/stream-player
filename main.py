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

    io = imgui.get_io()
    io.ini_filename = "imgui_new.ini"

    is_open = np.asarray([True], dtype=np.uint8)
    v_float = np.asarray([0.0], dtype=np.float32)
    v_float2 = np.asarray([0.0, 1.0], dtype=np.float32)

    img_tex = ImageTexture()
    reader = VideoReader(os.path.expanduser("~/Videos/30fps.mp4"))

    count = 0
    while not glfw.window_should_close(window):
        glfw.poll_events()

        got, im = reader.read()
        if got:
            img_tex.update(im, is_bgr=True)

        imgui.impl_new_frame()
        imgui.new_frame()

        imgui.demo(is_open)
        imgui.begin("haha", np.asarray([1], dtype=np.uint8))
        imgui.text("Hello World!")
        imgui.slider_float("Value", v_float, -10.0, 10.0)
        imgui.slider_float2("Value2", v_float2, -10.0, 10.0)
        imgui.checkbox("open", is_open)
        imgui.image(img_tex.id, img_tex.extend)
        imgui.end()

        imgui.begin("test", is_open)
        if imgui.button("Click {}".format(count)):
            count += 1
        imgui.end()

        imgui.render()
        w, h = glfw.get_framebuffer_size(window)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.2, 0.2, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        imgui.impl_render(imgui.get_draw_data())

        glfw.swap_buffers(window)

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

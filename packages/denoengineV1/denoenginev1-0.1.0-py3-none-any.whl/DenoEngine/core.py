import glfw
from OpenGL.GL import *

class Game:
    def __init__(self, width=800, height=600, title="My DenoEngine Game"):
        if not glfw.init():
            raise Exception("GLFW başlatılamadı!")
        self.window = glfw.create_window(width, height, title, None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("Pencere oluşturulamadı!")
        glfw.make_context_current(self.window)

    def run(self, update_fn=None):
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            if update_fn:
                update_fn()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        glfw.terminate()

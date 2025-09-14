import glfw
import sys
from OpenGL.GL import *
from OpenGL.GLU import *

glutInit(sys.args)

class Game:
    def __init__(self, width=800, height=600, camera_mode="FPS"):
        if not glfw.init():
            raise Exception("GLFW başlatılamadı")
        self.width = width
        self.height = height
        self.camera_mode = camera_mode
        self.window = glfw.create_window(width, height, "DenoEngine", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("Pencere oluşturulamadı")
        glfw.make_context_current(self.window)
        self.objects = []
        self.overlay_fn = None

    def add_object(self, obj):
        self.objects.append(obj)

    def set_overlay(self, fn):
        self.overlay_fn = fn

    def run(self, update_fn=None, overlay_fn=None):
        self.set_overlay(overlay_fn)
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            if self.camera_mode=="FPS":
                gluLookAt(0,1,5, 0,0,0, 0,1,0)
            else:
                gluLookAt(5,5,5, 0,0,0, 0,1,0)

            if update_fn:
                update_fn()
            for obj in self.objects:
                obj.draw()

            if self.overlay_fn:
                glMatrixMode(GL_PROJECTION)
                glPushMatrix()
                glLoadIdentity()
                glOrtho(0, self.width, 0, self.height, -1,1)
                glMatrixMode(GL_MODELVIEW)
                glPushMatrix()
                glLoadIdentity()
                self.overlay_fn()
                glPopMatrix()
                glMatrixMode(GL_PROJECTION)
                glPopMatrix()
                glMatrixMode(GL_MODELVIEW)

            glfw.swap_buffers(self.window)
            glfw.poll_events()
        glfw.terminate()

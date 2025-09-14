
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class Camera:
    def __init__(self, mode="FPS", target=None):
        self.mode = mode
        self.position = np.array([0.0, 1.0, 5.0])
        self.rotation = np.array([0.0,0.0])
        self.target = target
        self.mouse_sensitivity = 0.1

    def apply(self):
        glLoadIdentity()
        if self.mode=="FPS":
            glRotatef(-self.rotation[0],1,0,0)
            glRotatef(-self.rotation[1],0,1,0)
            glTranslatef(-self.position[0],-self.position[1],-self.position[2])
        elif self.mode=="TPS" and self.target:
            cam_offset = np.array([0,2,5])
            cam_pos = self.target.position + cam_offset
            gluLookAt(cam_pos[0], cam_pos[1], cam_pos[2],
                      self.target.position[0], self.target.position[1], self.target.position[2],
                      0,1,0)

class Game:
    def __init__(self,width=800,height=600,title="DenoEngine",camera_mode="FPS"):
        if not glfw.init(): raise Exception("GLFW başlatılamadı!")
        self.width,self.height=width,height
        self.window=glfw.create_window(width,height,title,None,None)
        if not self.window: glfw.terminate(); raise Exception("Pencere oluşturulamadı!")
        glfw.make_context_current(self.window)
        glfw.set_input_mode(self.window,glfw.CURSOR,glfw.CURSOR_DISABLED)
        glEnable(GL_DEPTH_TEST)
        self.camera=Camera(mode=camera_mode)
        self.update_fn=None
        self.overlay_fn=None
        self._last_mouse=None
        self.keys=set()
        self.objects=[]
        self._setup_callbacks()
        self.gravity=-0.01

    def _setup_callbacks(self):
        glfw.set_key_callback(self.window,self._key_callback)

    def _key_callback(self,win,key,scancode,action,mods):
        if action==glfw.PRESS: self.keys.add(key)
        elif action==glfw.RELEASE: self.keys.discard(key)

    def handle_input(self):
        speed=0.1
        if glfw.KEY_W in self.keys: self.camera.position[2]-=speed
        if glfw.KEY_S in self.keys: self.camera.position[2]+=speed
        if glfw.KEY_A in self.keys: self.camera.position[0]-=speed
        if glfw.KEY_D in self.keys: self.camera.position[0]+=speed
        x,y=glfw.get_cursor_pos(self.window)
        if self._last_mouse is None: self._last_mouse=(x,y)
        dx,dy=x-self._last_mouse[0],y-self._last_mouse[1]
        self.camera.rotation[1]+=dx*self.camera.mouse_sensitivity
        self.camera.rotation[0]+=dy*self.camera.mouse_sensitivity
        self.camera.rotation[0]=max(-90,min(90,self.camera.rotation[0]))
        self._last_mouse=(x,y)

    def draw_2d_overlay(self):
        if not self.overlay_fn: return
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0,self.width,0,self.height,-1,1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        self.overlay_fn()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def run(self,update_fn=None,overlay_fn=None):
        self.update_fn=update_fn
        self.overlay_fn=overlay_fn
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(70,self.width/self.height,0.1,100)
            glMatrixMode(GL_MODELVIEW)
            self.handle_input()
            self.camera.apply()
            if self.update_fn: self.update_fn()
            if self.overlay_fn: self.draw_2d_overlay()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        glfw.terminate()

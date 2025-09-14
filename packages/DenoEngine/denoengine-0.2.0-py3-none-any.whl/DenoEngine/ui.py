from OpenGL.GL import *
from OpenGL.GLUT import *

class HUDText:
    def __init__(self,text,x,y,color=(1,1,1)):
        self.text=text
        self.x,self.y=x,y
        self.color=color
    def draw(self):
        glColor3f(*self.color)
        glWindowPos2f(self.x,self.y)
        for c in self.text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

class HUDButton:
    def __init__(self, x, y, w, h, text, color=(0,1,0), hover_color=(0,0.8,0)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.clicked = False

    def draw(self, mouse_pos=None):
        mx, my = mouse_pos if mouse_pos else (-1,-1)
        if self.x <= mx <= self.x+self.w and self.y <= my <= self.y+self.h:
            glColor3f(*self.hover_color)
        else:
            glColor3f(*self.color)
        # Buton dikdörtgeni
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x+self.w, self.y)
        glVertex2f(self.x+self.w, self.y+self.h)
        glVertex2f(self.x, self.y+self.h)
        glEnd()
        # Buton yazısı
        HUDText(self.text, self.x+10, self.y+10, color=(0,0,0)).draw()

    def check_click(self, mouse_pos):
        mx, my = mouse_pos
        if self.x <= mx <= self.x+self.w and self.y <= my <= self.y+self.h:
            self.clicked = True
            return True
        return False

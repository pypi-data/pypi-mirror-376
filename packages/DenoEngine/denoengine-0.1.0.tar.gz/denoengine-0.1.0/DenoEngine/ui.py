
from OpenGL.GL import *
from OpenGL.GLUT import *

class HUDText:
    def __init__(self,text,x,y,color=(1,1,1)):
        self.text=text
        self.x,self.y=x,y
        self.color=color

    def draw(self):
        glColor3f(*self.color)
        glRasterPos2f(self.x,self.y)
        for c in self.text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

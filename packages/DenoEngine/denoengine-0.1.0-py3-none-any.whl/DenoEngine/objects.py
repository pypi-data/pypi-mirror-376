
from OpenGL.GL import *
import numpy as np

class Cube:
    def __init__(self,pos=[0,0,0],size=1,color=(1,0,0)):
        self.position=np.array(pos)
        self.size=size
        self.color=color

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glColor3f(*self.color)
        s=self.size/2
        glBegin(GL_QUADS)
        glVertex3f(-s,-s,s)
        glVertex3f(s,-s,s)
        glVertex3f(s,s,s)
        glVertex3f(-s,s,s)
        glEnd()
        glPopMatrix()

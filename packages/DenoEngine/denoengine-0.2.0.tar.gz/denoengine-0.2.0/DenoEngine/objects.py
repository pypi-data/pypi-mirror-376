from OpenGL.GL import *
from OpenGL.GLU import *
import math

# 3D Obje
class Cube:
    def __init__(self, pos=[0,0,0], size=1, color=(1,1,1)):
        self.pos = pos
        self.size = size
        self.color = color
    def draw(self):
        x,y,z = self.pos
        s = self.size/2
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        # Ön
        glVertex3f(x-s,y-s,z+s)
        glVertex3f(x+s,y-s,z+s)
        glVertex3f(x+s,y+s,z+s)
        glVertex3f(x-s,y+s,z+s)
        # Ark
        glVertex3f(x-s,y-s,z-s)
        glVertex3f(x+s,y-s,z-s)
        glVertex3f(x+s,y+s,z-s)
        glVertex3f(x-s,y+s,z-s)
        # Yanlar
        glVertex3f(x-s,y-s,z-s)
        glVertex3f(x-s,y-s,z+s)
        glVertex3f(x-s,y+s,z+s)
        glVertex3f(x-s,y+s,z-s)

        glVertex3f(x+s,y-s,z-s)
        glVertex3f(x+s,y-s,z+s)
        glVertex3f(x+s,y+s,z+s)
        glVertex3f(x+s,y+s,z-s)

        glVertex3f(x-s,y-s,z-s)
        glVertex3f(x+s,y-s,z-s)
        glVertex3f(x+s,y-s,z+s)
        glVertex3f(x-s,y-s,z+s)

        glVertex3f(x-s,y+s,z-s)
        glVertex3f(x+s,y+s,z-s)
        glVertex3f(x+s,y+s,z+s)
        glVertex3f(x-s,y+s,z+s)
        glEnd()

class Triangle3D:
    def __init__(self, vertices=[[-1,0,0],[1,0,0],[0,1,0]], color=(1,1,1)):
        self.vertices = vertices
        self.color = color
    def draw(self):
        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        for v in self.vertices:
            glVertex3f(*v)
        glEnd()

class Sphere:
    def __init__(self, pos=[0,0,0], radius=1, color=(1,1,1), slices=16, stacks=16):
        self.pos = pos
        self.radius = radius
        self.color = color
        self.slices = slices
        self.stacks = stacks
    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(*self.pos)
        quad = gluNewQuadric()
        gluSphere(quad, self.radius, self.slices, self.stacks)
        glPopMatrix()

# 2D Obje
class Cube2D:
    def __init__(self, x,y,w,h,color=(1,1,1)):
        self.x,self.y,self.w,self.h=x,y,w,h
        self.color=color
    def draw(self):
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        glVertex2f(self.x,self.y)
        glVertex2f(self.x+self.w,self.y)
        glVertex2f(self.x+self.w,self.y+self.h)
        glVertex2f(self.x,self.y+self.h)
        glEnd()

class Triangle2D:
    def __init__(self, vertices=[[0,0],[1,0],[0.5,1]], color=(1,1,1)):
        self.vertices = vertices
        self.color=color
    def draw(self):
        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        for v in self.vertices:
            glVertex2f(*v)
        glEnd()

class Circle2D:
    def __init__(self, x,y,r,color=(1,1,1),segments=32):
        self.x,self.y,self.r=x,y,r
        self.color=color
        self.segments=segments
    def draw(self):
        glColor3f(*self.color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(self.x,self.y)
        for i in range(self.segments+1):
            theta=2*3.14159*i/self.segments
            glVertex2f(self.x+self.r*math.cos(theta), self.y+self.r*math.sin(theta))
        glEnd()

from OpenGL.GL import *

class Cube:
    def __init__(self, size=1.0):
        self.size = size

    def draw(self):
        glBegin(GL_QUADS)
        glColor3f(1, 0, 0)  # kırmızı
        # sadece tek yüzü çizelim örnek olsun
        glVertex3f(-self.size, -self.size, -self.size)
        glVertex3f(-self.size, self.size, -self.size)
        glVertex3f(self.size, self.size, -self.size)
        glVertex3f(self.size, -self.size, -self.size)
        glEnd()

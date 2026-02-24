import OpenGL.GL as GL
import glfw
import sys
import os
from itertools import cycle

# Add parent directory to path to import libs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.transform import Trackball
from sphere.sphere import SphereSubdiv


class Viewer:
    """GLFW viewer windows, with classic initialization & graphics loop."""
    def __init__(self, width=800, height=800):
        self.fill_modes = cycle([GL.GL_FILL, GL.GL_LINE, GL.GL_POINT])
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)
        glfw.window_hint(glfw.DEPTH_BITS, 16)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        glfw.make_context_current(self.win)

        self.trackball = Trackball()
        self.mouse = (0, 0)

        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)

        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        GL.glClearColor(0.1, 0.1, 0.12, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LESS)

        self.drawables = []

    def run(self):
        """Main render loop for this OpenGL windows."""
        while not glfw.window_should_close(self.win):
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            win_size = glfw.get_window_size(self.win)
            view = self.trackball.view_matrix()
            projection = self.trackball.projection_matrix(win_size)

            for drawable in self.drawables:
                drawable.draw(projection, view, None)

            glfw.swap_buffers(self.win)
            glfw.poll_events()

    def add(self, *drawables):
        """add objects to draw in this windows"""
        self.drawables.extend(drawables)

    def on_key(self, _win, key, _scancode, action, _mods):
        """'Q' or 'Escape' quits"""
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            if key == glfw.KEY_W:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))

            for drawable in self.drawables:
                if hasattr(drawable, 'key_handler'):
                    drawable.key_handler(key)

    def on_mouse_move(self, win, xpos, ypos):
        """Rotate on left-click & drag, pan on right-click & drag."""
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.trackball.drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.trackball.pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        """Scroll controls the camera distance to trackball center."""
        self.trackball.zoom(deltay, glfw.get_window_size(win)[1])


def main():
    viewer = Viewer()

    shader_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    model = SphereSubdiv(
        os.path.join(shader_dir, "flat.vert"),
        os.path.join(shader_dir, "flat.frag"),
        subdiv=5,
        radius=0.8,
    ).setup()

    viewer.add(model)
    viewer.run()


if __name__ == '__main__':
    glfw.init()
    main()
    glfw.terminate()

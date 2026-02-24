# Sample/portal/viewer.py
import OpenGL.GL as GL
import glfw
import os
import sys

# Add parent directory to path to import libs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from portal import NeonPortal


class Viewer:
    def __init__(self, width=900, height=600):
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)

        self.win = glfw.create_window(width, height, "Neon Portal", None, None)
        glfw.make_context_current(self.win)
        glfw.set_key_callback(self.win, self.on_key)

        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode(),
              '| GLSL', GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode(),
              '| Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        GL.glClearColor(0.02, 0.02, 0.03, 1.0)

        # Additive blending cho glow “đã”
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)

        self.drawables = []

    def add(self, *drawables):
        self.drawables.extend(drawables)

    def on_key(self, _win, key, _scancode, action, _mods):
        if action in (glfw.PRESS, glfw.REPEAT):
            if key in (glfw.KEY_ESCAPE, glfw.KEY_Q):
                glfw.set_window_should_close(self.win, True)

    def run(self):
        while not glfw.window_should_close(self.win):
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

            t = glfw.get_time()
            for d in self.drawables:
                d.draw(t)

            glfw.swap_buffers(self.win)
            glfw.poll_events()


def main():
    viewer = Viewer(900, 600)

    # Get the directory where the current script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct absolute paths to shader files
    vert_path = os.path.join(script_dir, "portal.vert")
    frag_path = os.path.join(script_dir, "portal.frag")
    
    # Print paths for debugging
    print(f"Vertex shader path: {vert_path}")
    print(f"Fragment shader path: {frag_path}")
    
    # Check if shader files exist
    if not os.path.exists(vert_path):
        print(f"Error: Vertex shader not found at {vert_path}")
        return
    if not os.path.exists(frag_path):
        print(f"Error: Fragment shader not found at {frag_path}")
        return
    
    portal = NeonPortal(vert_path, frag_path).setup()
    viewer.add(portal)
    viewer.run()


if __name__ == "__main__":
    glfw.init()
    main()
    glfw.terminate()

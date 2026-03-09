import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean windows system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
from itertools import cycle   # cyclic iterator to easily toggle polygon rendering modes
import sys
import os

# Add parent directory to path to import libs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs import transform as T
from libs.transform import Trackball
from cylinder.cylinder import Cylinder

class MultiCameraViewer:
    def __init__(self, width=1600, height=800):
        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])

        # version hints: create GL windows with >= OpenGL 3.3 and core profile
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)
        glfw.window_hint(glfw.DEPTH_BITS, 16)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        # make win's OpenGL context current; no OpenGL calls can happen before
        glfw.make_context_current(self.win)

        # initialize trackball
        self.trackball = Trackball()
        self.mouse = (0, 0)

        # register event handlers
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)
        
        # useful message to check OpenGL renderer characteristics
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        # initialize GL by setting viewport and default render characteristics
        GL.glClearColor(0, 0, 0, 1.0)
        #GL.glEnable(GL.GL_CULL_FACE)   # enable backface culling (Exercise 1)
        #GL.glFrontFace(GL.GL_CCW) # GL_CCW: default

        GL.glEnable(GL.GL_DEPTH_TEST)  # enable depth test (Exercise 1)
        GL.glDepthFunc(GL.GL_LESS)   # GL_LESS: default
        GL.glLineWidth(1.0) # duong ke

        # initially empty list of object to draw
        self.drawables = []


    def render_scene(self, projection, view, cam2_pos=None):
        """Vẽ toàn bộ vật thể trong cảnh"""
        self.model.draw(projection, view, T.identity())
        
        if cam2_pos is not None:
            model_proxy = T.translate(*cam2_pos)
            self.cam_proxy.draw(projection, view, model_proxy)

    def on_key(self, _win, key, _scancode, action, _mods):
        if action == glfw.PRESS:
            # 1. Thoát chương trình
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            
            # 2. Sửa lỗi W: Chuyển đổi chế độ Wireframe (Sử dụng next() an toàn với cycle)
            if key == glfw.KEY_W:
                new_mode = next(self.fill_modes)
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, new_mode)

            # 3. Vá lỗi thiếu phím M (Chia màn hình)
            if key == glfw.KEY_M:
                self.show_split = not self.show_split

            # 4. Vá lỗi thiếu phím SPACE (Đổi camera)
            if key == glfw.KEY_SPACE and not self.show_split:
                self.active_cam = 2 if self.active_cam == 1 else 1

            # 5. Gọi key_handler của các vật thể (nếu có)
            for drawable in self.drawables:
                if hasattr(drawable, 'key_handler'):
                    drawable.key_handler(key)

    def on_mouse_move(self, win, xpos, ypos):
        """ Rotate on left-click & drag, pan on right-click & drag """
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.trackball.drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.trackball.pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        """ Scroll controls the camera distance to trackball center """
        self.trackball.zoom(deltay, glfw.get_window_size(win)[1])
                
    def run(self):
        """ Main render loop for this OpenGL windows """
        while not glfw.window_should_close(self.win):
            # clear draw buffer
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            w,h = glfw.get_window_size(self.win)

            t = glfw.get_time()

            c2_pos = np.array([5.0 * np.cos(t*2), 2.0, 5.0 * np.sin(t*2)])
            view2 = T.lookat(c2_pos, np.array([0, 0, 0]), np.array([0, 1, 0]))

            c1_pos = np.array([5.0, 3.0, 5.0]) 
            view1 = T.lookat(c1_pos, np.array([0, 0, 0]), np.array([0, 1, 0]))

            half_w = w // 2
            gap = 1
            
            proj = T.perspective(45, (half_w - gap)/h, 0.1, 100.0)

            # Bật Scissor để clear màu nền riêng cho từng viewport
            GL.glEnable(GL.GL_SCISSOR_TEST)

            # cam 1
            GL.glViewport(0, 0, half_w - gap, h)
            GL.glScissor(0, 0, half_w - gap, h)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            self.render_scene(proj, view1, cam2_pos=c2_pos)

            # cam 2
            GL.glViewport(half_w + gap, 0, half_w - gap, h)
            GL.glScissor(half_w + gap, 0, half_w - gap, h)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            self.render_scene(proj, view2, cam2_pos=None)
            
            GL.glDisable(GL.GL_SCISSOR_TEST)

            glfw.swap_buffers(self.win)
            glfw.poll_events()

def main():
    
    """ create windows, add shaders & scene objects, then run rendering loop """
    viewer = MultiCameraViewer()
    # place instances of our basic objects

    shader_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    
    viewer.model = Cylinder(
        os.path.join(shader_dir, "color_interp.vert"),
        os.path.join(shader_dir, "color_interp.frag"),
        segments=64).setup()
    viewer.cam_proxy = Cylinder(
        os.path.join(shader_dir, "color_interp.vert"),
        os.path.join(shader_dir, "color_interp.frag"),
        segments=16, radius=0.5, height=1.0).setup()

    viewer.drawables = [viewer.model, viewer.cam_proxy]

    # viewer.add(viewer.model, viewer.cam_proxy)
    viewer.run()

    

if __name__ == '__main__':
    glfw.init()                # initialize windows system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts
# Sample/portal/portal.py
import OpenGL.GL as GL
import numpy as np
import ctypes
import os
import sys

# Add parent directory to path to import libs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shader import Shader
from libs.buffer import VAO, UManager


class NeonPortal:
    """
    Fullscreen quad (2 triangles), interleaved attributes:
    [pos.x, pos.y, uv.x, uv.y]
    """
    def __init__(self, vert_shader, frag_shader):
        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)
        self.vao = VAO()

        # 2 triangles covering the screen in clip space
        # (pos)          (uv)
        data = np.array([
            [-1.0, -1.0,   0.0, 0.0],
            [ 1.0, -1.0,   1.0, 0.0],
            [ 1.0,  1.0,   1.0, 1.0],

            [-1.0, -1.0,   0.0, 0.0],
            [ 1.0,  1.0,   1.0, 1.0],
            [-1.0,  1.0,   0.0, 1.0],
        ], dtype=np.float32)

        self.data = data

    def setup(self):
        stride = 4 * 4  # 4 floats per vertex * 4 bytes
        offset_pos = ctypes.c_void_p(0)
        offset_uv = ctypes.c_void_p(2 * 4)

        self.vao.add_vbo(0, self.data, ncomponents=2, dtype=GL.GL_FLOAT,
                         normalized=False, stride=stride, offset=offset_pos)
        self.vao.add_vbo(1, self.data, ncomponents=2, dtype=GL.GL_FLOAT,
                         normalized=False, stride=stride, offset=offset_uv)

        # default uniforms
        self.uma.upload_uniform_scalar1f(0.0, "uTime")
        return self

    def draw(self, t):
        self.vao.activate()
        GL.glUseProgram(self.shader.render_idx)

        # animate
        self.uma.upload_uniform_scalar1f(float(t), "uTime")

        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        self.vao.deactivate()

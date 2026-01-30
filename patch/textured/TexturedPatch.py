import sys
import os

# Add parent directory to path to import libs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.lighting import LightingManager
import ctypes
import cv2
import glfw
import numpy as np
import tempfile

class TexturedPatch(object):
    def __init__(self, vert_shader, frag_shader):
        """
        self.vertex_attrib:
        each row: v.x, v.y, v.z, c.r, c.g, c.b, t.x, t.y, n.x, n.y, n.z
        =>  (a) stride = nbytes(v0.x -> v1.x) = 9*4 = 36
            (b) offset(vertex) = ctypes.c_void_p(0); can use "None"
                offset(color) = ctypes.c_void_p(3*4)
                offset(normal) = ctypes.c_void_p(6*4)
        """
        vertex_color = np.array([
         #  v.x  v.y v.z  c.r  c.g  c.b   t.x  t.y
            [0,  0,  0,   0.0, 0.0, 0.0,  0.0, 1.0],  # A
            [0,  1,  0,   1.0, 0.0, 0.0,  0.0, 0.0],  # B
            [1,  0,  0,   0.0, 1.0, 0.0,  0.5, 1.0],  # C
            [1,  1,  0,   0.0, 0.0, 1.0,  0.5, 0.0],  # D
            [2,  0,  0,   1.0, 0.0, 0.0,  1.0, 1.0],  # E
            [2,  1,  0,   1.0, 1.0, 1.0,  1.0, 0.0]   # F
        ], dtype=np.float32)

        # random normals (facing +z)
        normals = np.random.normal(0, 5, (vertex_color.shape[0], 3)).astype(np.float32)
        normals[:, 2] = np.abs(normals[:, 2])  # (facing +z)
        normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
        self.vertex_attrib = np.concatenate([vertex_color, normals], axis=1)

        # indices
        self.indices = np.arange(self.vertex_attrib.shape[0]).astype(np.int32)

        self.vao = VAO()

        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)
        self.lighting = LightingManager(self.uma)

        self.selected_texture = 1


    def setup(self):
        stride = 11*4
        offset_v = ctypes.c_void_p(0)  # None
        offset_c = ctypes.c_void_p(3*4)
        offset_t = ctypes.c_void_p(6*4)
        offset_n = ctypes.c_void_p(8*4)
        self.vao.add_vbo(0, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_v)
        self.vao.add_vbo(1, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_c)
        self.vao.add_vbo(2, self.vertex_attrib, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_n)
        self.vao.add_vbo(3, self.vertex_attrib, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=stride, offset=offset_t)

        self.vao.add_ebo(self.indices)

        # Get the absolute path to the original texture files
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        original_texture1 = os.path.join(base_dir, 'patch', 'textured', 'image', 'texture1.jpeg')
        original_texture2 = os.path.join(base_dir, 'patch', 'textured', 'image', 'texture2.jpeg')
        
        # Create a temporary directory with ASCII-only path
        temp_dir = os.path.join(tempfile.gettempdir(), 'opengl_textures')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Define paths in the temporary directory
        temp_texture1 = os.path.join(temp_dir, 'texture1.jpeg')
        temp_texture2 = os.path.join(temp_dir, 'texture2.jpeg')
        
        # Copy texture files to temporary location if they don't exist or are outdated
        def copy_if_needed(src, dst):
            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                import shutil
                shutil.copy2(src, dst)
        
        try:
            copy_if_needed(original_texture1, temp_texture1)
            copy_if_needed(original_texture2, temp_texture2)
            
            if not os.path.exists(temp_texture1):
                raise FileNotFoundError(f"Failed to copy texture file to: {temp_texture1}")
            if not os.path.exists(temp_texture2):
                raise FileNotFoundError(f"Failed to copy texture file to: {temp_texture2}")
                
            # Load textures from the temporary location
            self.uma.setup_texture("texture1", temp_texture1)
            self.uma.setup_texture("texture2", temp_texture2)
            
        except Exception as e:
            raise RuntimeError(f"Error setting up textures: {str(e)}")

        projection = T.ortho(-0.5, 2.5, -0.5, 1.5, -1, 1)
        modelview = np.identity(4, 'f')

        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)

        # Setup Phong lighting using LightingManager
        self.lighting.setup_phong(mode=1)
        
        # Upload phong_factor for texture blending
        phong_factor = 0.2
        self.uma.upload_uniform_scalar1f(phong_factor, 'phong_factor')

        return self

    def draw(self, projection, view, model):
        self.vao.activate()

        self.uma.upload_uniform_scalar1i(self.selected_texture, 'selected_texture')

        GL.glUseProgram(self.shader.render_idx)
        self.uma.upload_uniform_scalar1i(1, 'face')
        GL.glDrawElements(GL.GL_TRIANGLE_STRIP, 4, GL.GL_UNSIGNED_INT, None)

        GL.glUseProgram(self.shader.render_idx)
        self.uma.upload_uniform_scalar1i(2, 'face')
        offset = ctypes.c_void_p(2*4)  # None
        GL.glDrawElements(GL.GL_TRIANGLE_STRIP, 4, GL.GL_UNSIGNED_INT, offset)
        self.vao.deactivate()

    def key_handler(self, key):

        if key == glfw.KEY_1:
            self.selected_texture = 1
        if key == glfw.KEY_2:
            self.selected_texture = 2

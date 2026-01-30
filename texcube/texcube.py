import sys
import os
import tempfile

# Add parent directory to path to import libs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.lighting import LightingManager
import ctypes
import glfw
import numpy as np
import OpenGL.GL as GL


"""
TOP (y =+1): EFGH
                                |
   G (-1, +1, -1)   ......................... H: (+1, +1, -1) 
   color: (0,1,1)   |           |           |    WHITE: (1, 1, 1)
                    |           |           |
                    |           |           |
            --------------------------------------->X
                    |           |           |
                    |           |           |
                    |           |           |
   F: (-1, +1, +1)  ......................... E: (+1, +1, +1)
   BLUE: (0, 0, 1)              |              color: (1,0,1)
                                V 
                                Z

BOTTOM (y=-1): ABCD
                                |
    C: (-1, -1, -1) ......................... D: (+1, -1, -1)
    GREEN: (0,1,0)  |           |           |  color: (1,1,0)
                    |           |           |
                    |           |           |
            --------------------------------------->X
                    |           |           |
                    |           |           |
                    |           |           |
    B: (-1, -1, +1) ......................... A: (+1, -1, +1)
    BLACK: (0,0,0)              |               RED: (1,0,0)
                                V 
                                Z

Texture (2D image: 3x4, see: shape/texcube/image/texture.jpeg
        0             1/4             2/4             3/4             1.0  
   0    ...............................F...............E.......................>X
        |              |               |               |               |
        |              |               |               |               |
        |              |               |               |               |
   1/3  E..............F...............G...............H...............E
        |              |               |               |               |
        |              |               |               |               |
        |              |               |               |               |
   2/3  A..............B...............C...............D...............A
        |              |               |               |               |
        |              |               |               |               |
        |              |               |               |               |
   1.0  ...............................B...............A................
        |
        V 
        Y
"""


class TexCube(object):
    def __init__(self, vert_shader, frag_shader):
        self.vert_shader = vert_shader
        self.frag_shader = frag_shader
        # 24 vertices (4 per face) so each face has its own normal/UVs
        self.vertices = np.array(
            [
                # +X (right)
                [1, -1, -1], [1, -1,  1], [1,  1,  1], [1,  1, -1],
                # -X (left)
                [-1, -1,  1], [-1, -1, -1], [-1,  1, -1], [-1,  1,  1],
                # +Y (top)
                [-1, 1, -1], [1, 1, -1], [1, 1,  1], [-1, 1,  1],
                # -Y (bottom)
                [-1, -1,  1], [1, -1,  1], [1, -1, -1], [-1, -1, -1],
                # +Z (front)
                [-1, -1, 1], [-1,  1, 1], [1,  1, 1], [1, -1, 1],
                # -Z (back)
                [1, -1, -1], [1,  1, -1], [-1,  1, -1], [-1, -1, -1],
            ],
            dtype=np.float32
        )

        # 12 triangles (6 faces)
        self.indices = np.array(
            [
                0, 1, 2,  0, 2, 3,      # +X
                4, 5, 6,  4, 6, 7,      # -X
                8, 9, 10, 8, 10, 11,    # +Y
                12, 13, 14, 12, 14, 15, # -Y
                16, 17, 18, 16, 18, 19, # +Z
                20, 21, 22, 20, 22, 23  # -Z
            ],
            dtype=np.int32
        )

        self.normals = np.array(
            [
                # +X
                [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0],
                # -X
                [-1, 0, 0], [-1, 0, 0], [-1, 0, 0], [-1, 0, 0],
                # +Y
                [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0],
                # -Y
                [0, -1, 0], [0, -1, 0], [0, -1, 0], [0, -1, 0],
                # +Z
                [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1],
                # -Z
                [0, 0, -1], [0, 0, -1], [0, 0, -1], [0, 0, -1],
            ],
            dtype=np.float32
        )

        # texture atlas: 4 columns x 3 rows (see comment in file)
        # tiles with images are at: (row, col) = (0,2), (1,0..3), (2,2)
        def tile_uv(col, row):
            tw = 1.0 / 4.0
            th = 1.0 / 3.0
            u0 = col * tw
            u1 = (col + 1) * tw
            # OpenCV loads with top-left origin; flip v for OpenGL
            v1 = 1.0 - row * th
            v0 = 1.0 - (row + 1) * th
            return [
                [u0, v0], [u1, v0], [u1, v1], [u0, v1],  # bl, br, tr, tl
            ]

        # Map faces to tiles in the atlas (centered cross at col=2)
        uv_top = tile_uv(2, 0)     # +Y
        uv_bottom = tile_uv(2, 2)  # -Y
        uv_back = tile_uv(0, 1)    # -Z
        uv_left = tile_uv(1, 1)    # -X
        uv_front = tile_uv(2, 1)   # +Z
        uv_right = tile_uv(3, 1)   # +X

        self.texcoords = np.array(
            [
                # +X (right)
                *uv_right,
                # -X (left)
                *uv_left,
                # +Y (top)
                *uv_top,
                # -Y (bottom)
                *uv_bottom,
                # +Z (front)
                *uv_front,
                # -Z (back)
                *uv_back,
            ],
            dtype=np.float32
        )

        self.colors = np.array(
            [
                # +X (red)
                [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0],
                # -X (green)
                [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0],
                # +Y (blue)
                [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1],
                # -Y (yellow)
                [1, 1, 0], [1, 1, 0], [1, 1, 0], [1, 1, 0],
                # +Z (magenta)
                [1, 0, 1], [1, 0, 1], [1, 0, 1], [1, 0, 1],
                # -Z (cyan)
                [0, 1, 1], [0, 1, 1], [0, 1, 1], [0, 1, 1],
            ],
            dtype=np.float32
        )

        self.vao = VAO()

        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)
        self.lighting = LightingManager(self.uma)

    """
    Create object -> call setup -> call draw
    """
    def setup(self):
        # setup VAO for drawing cylinder's side
        self.vao.add_vbo(0, self.vertices, ncomponents=3, stride=0, offset=None)
        self.vao.add_vbo(1, self.normals, ncomponents=3, stride=0, offset=None)
        self.vao.add_vbo(2, self.texcoords, ncomponents=2, stride=0, offset=None)
        self.vao.add_vbo(3, self.colors, ncomponents=3, stride=0, offset=None)

        # setup EBO for drawing cylinder's side, bottom and top
        self.vao.add_ebo(self.indices)

        # setup textures (only for phong_texture shader)
        if 'phong_texture' in self.frag_shader.lower():
            # Use the temporary texture path with ASCII-only characters
            temp_dir = os.path.join(tempfile.gettempdir(), 'texcube_textures')
            image_path = os.path.join(temp_dir, 'texture.jpeg')
            
            # If the file doesn't exist in temp, try to copy it from the original location
            if not os.path.exists(image_path):
                original_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "texture.jpeg")
                os.makedirs(temp_dir, exist_ok=True)
                import shutil
                shutil.copy2(original_path, image_path)
                
            self.uma.setup_texture("texture", image_path)
            phong_factor = 0.0  # blending factor for phong shading and texture
            self.uma.upload_uniform_scalar1f(phong_factor, 'phong_factor')

        # Setup lighting if using Gouraud or Phong shader
        if 'gouraud' in self.vert_shader.lower():
            self.lighting.setup_gouraud()
        elif 'phong' in self.vert_shader.lower() and 'texture' not in self.frag_shader.lower():
            self.lighting.setup_phong(mode=1)
        elif 'phong_texture' in self.frag_shader.lower():
            self.lighting.setup_phong(mode=1)
        return self

    def draw(self, projection, view, model):
        GL.glUseProgram(self.shader.render_idx)
        modelview = view

        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)
        
        # Setup lighting if using Gouraud or Phong shader (not phong_texture, already setup in setup())
        if 'gouraud' in self.vert_shader.lower():
            self.lighting.setup_gouraud()
        elif 'phong' in self.vert_shader.lower() and 'texture' not in self.frag_shader.lower():
            self.lighting.setup_phong(mode=1)

        self.vao.activate()
        GL.glDrawElements(GL.GL_TRIANGLES, self.indices.shape[0], GL.GL_UNSIGNED_INT, None)


    def key_handler(self, key):

        if key == glfw.KEY_1:
            self.selected_texture = 1
        if key == glfw.KEY_2:
            self.selected_texture = 2

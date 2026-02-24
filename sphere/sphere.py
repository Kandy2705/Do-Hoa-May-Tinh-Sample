import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import OpenGL.GL as GL
import glfw

from libs.shader import Shader
from libs.buffer import VAO, UManager
from libs import transform as T

V = np.array([
    [0.0, 0.0, 1.0],
    [0.0, 0.942809, -0.33333],
    [-0.816497, -0.471405, -0.33333],
    [0.816497, -0.471405, -0.33333],
], dtype=np.float32)

def normalize(v): #chuan hoa
    v = np.array(v, dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n

def subdivide_triangle(a, b, c, n, out_verts):
    if n <= 0:
        out_verts.append(a)
        out_verts.append(b)
        out_verts.append(c)
        return
    m = normalize((a + b) * 0.5)
    p = normalize((a + c) * 0.5)
    o = normalize((b + c) * 0.5)
    subdivide_triangle(a, m, p, n - 1, out_verts)
    subdivide_triangle(b, m, o, n - 1, out_verts)
    subdivide_triangle(c, p, o, n - 1, out_verts)
    subdivide_triangle(m, p, o, n - 1, out_verts)


def build_sphere(subdiv = 4, radius=0.8):
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (0, 3, 1),
        (1, 3, 2),
    ]

    out = []

    for i0, i1, i2 in faces:
        a = normalize(V[i0])
        b = normalize(V[i1])
        c = normalize(V[i2])
        subdivide_triangle(a, b, c, subdiv, out)

    verts = np.array(out, dtype=np.float32) * radius
    return verts

class SphereSubdiv:
    def __init__(self, vert_shader, frag_shader, subdiv=4, radius=0.8):
        self.vert_shader = vert_shader
        self.frag_shader = frag_shader

        vertex_colors = np.array([
            [0.0, 1.0, 1.0], #blue
            [0.0, 1.0, 0.0], #green
            [1.0, 0.0, 0.0], #red
            [1.0, 0.0, 1.0]  #red
        ], dtype=np.float32)

        self.vertices = []
        self.colors = []
        
        def subdivide_with_colors(a, b, c, color_a, color_b, color_c, n, out_verts, out_colors):
            if n <= 0:
                out_verts.extend([a, b, c])
                out_colors.extend([color_a, color_b, color_c])
                return
                
            m = normalize((a + b) * 0.5)
            p = normalize((a + c) * 0.5)
            o = normalize((b + c) * 0.5)
            
            color_m = (color_a + color_b) * 0.5
            color_p = (color_a + color_c) * 0.5
            color_o = (color_b + color_c) * 0.5
            
            subdivide_with_colors(a, m, p, color_a, color_m, color_p, n - 1, out_verts, out_colors)
            subdivide_with_colors(b, m, o, color_b, color_m, color_o, n - 1, out_verts, out_colors)
            subdivide_with_colors(c, p, o, color_c, color_p, color_o, n - 1, out_verts, out_colors)
            subdivide_with_colors(m, p, o, color_m, color_p, color_o, n - 1, out_verts, out_colors)

        out_verts = []
        out_colors = []
        
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]
        
        for i0, i1, i2 in faces: #chay tung mat phang cua tu dien
            a = normalize(V[i0])
            b = normalize(V[i1])
            c = normalize(V[i2]) 
            
            color_a = vertex_colors[i0]
            color_b = vertex_colors[i1]
            color_c = vertex_colors[i2]
            
            subdivide_with_colors(a, b, c, color_a, color_b, color_c, subdiv, out_verts, out_colors)
        
        self.vertices = np.array(out_verts, dtype=np.float32) * radius
        self.colors = np.array(out_colors, dtype=np.float32)

        self.vao = VAO()
        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)

        self.angle_x = 0.0
        self.angle_y = 0.0

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, stride=0, offset=None)
        return self


    def draw(self, projection, view, _model_unused):
        GL.glUseProgram(self.shader.render_idx) 

        modelview = view 

        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)

        self.vao.activate()
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertices.shape[0])
        self.vao.deactivate()

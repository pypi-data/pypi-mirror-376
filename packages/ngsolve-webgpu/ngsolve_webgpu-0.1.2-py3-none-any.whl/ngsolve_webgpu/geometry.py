import numpy as np
import webgpu
from webgpu.clipping import Clipping
from webgpu.renderer import MultipleRenderer, Renderer, RenderOptions
from webgpu.utils import (
    buffer_from_array,
    create_bind_group,
    read_buffer,
    read_shader_file,
    uniform_from_array,
)
from webgpu.webgpu_api import *


class Binding:
    VERTICES = 90
    NORMALS = 91
    INDICES = 92
    COLORS = 93


class BaseGeometryRenderer(Renderer):
    clipping: Clipping | None = None
    select_entry_point: str = "fragmentQueryIndex"
    vis_data: dict

    def __init__(self, clipping, *args, **kwargs):
        self.clipping = clipping
        super().__init__(*args, **kwargs)


class GeometryFaceRenderer(BaseGeometryRenderer):
    n_vertices: int = 3

    def __init__(self, geo, clipping):
        super().__init__(clipping, label="GeometryFaces")
        self.geo = geo
        self.colors = None
        self.active = True
        self._buffers = {}

    def get_bounding_box(self):
        return self.bounding_box

    def set_colors(self, colors):
        """colors is numpy float32 array with 4 times number indices entries"""
        self.colors = colors
        if "colors" in self._buffers:
            self.device.queue.writeBuffer(self._buffers["colors"], 0, self.colors.tobytes())

    def update(self, options):
        vis_data = self.vis_data
        self.bounding_box = (vis_data["min"], vis_data["max"])
        verts = vis_data["vertices"]
        self.n_instances = len(verts) // 9
        normals = vis_data["normals"]
        indices = vis_data["indices"]
        if self.colors is None:
            self.colors = vis_data["face_colors"]
        self._buffers = {}
        for key, data in zip(
            ("vertices", "normals", "indices", "colors"),
            (verts, normals, indices, self.colors),
        ):
            self._buffers[key] = buffer_from_array(data)

    def get_bindings(self):
        return [
            *self.clipping.get_bindings(),
            webgpu.BufferBinding(Binding.VERTICES, self._buffers["vertices"]),
            webgpu.BufferBinding(Binding.NORMALS, self._buffers["normals"]),
            webgpu.BufferBinding(Binding.INDICES, self._buffers["indices"]),
            webgpu.BufferBinding(Binding.COLORS, self._buffers["colors"]),
        ]

    def get_shader_code(self):
        return read_shader_file("ngsolve/geo_face.wgsl")


class GeometryEdgeRenderer(BaseGeometryRenderer):
    n_vertices: int = 4
    topology: PrimitiveTopology = PrimitiveTopology.triangle_strip

    # make sure that edges are rendered on top of faces
    depthBias: int = -5
    depthBiasSlopeScale: int = -5

    def __init__(self, geo, clipping):
        self.geo = geo
        super().__init__(clipping, label="GeometryEdges")
        self.active = True
        self.thickness = 0.005
        self._buffers = {}

    def set_colors(self, colors):
        """colors is numpy float32 array with 4 times number indices entries"""
        self.colors = colors
        if "colors" in self._buffers:
            self.device.queue.writeBuffer(self._buffers["colors"], 0, self.colors.tobytes())

    def update(self, options):
        vis_data = self.vis_data
        verts = vis_data["edges"]
        self.colors = vis_data["edge_colors"]
        self.n_instances = len(verts) // 6
        self.thickness_uniform = uniform_from_array(np.array([self.thickness], dtype=np.float32))
        self._buffers = {}
        self._buffers["vertices"] = buffer_from_array(verts)
        self._buffers["colors"] = buffer_from_array(self.colors)
        self._buffers["index"] = buffer_from_array(vis_data["edge_indices"])

    def get_shader_code(self):
        return read_shader_file("ngsolve/geo_edge.wgsl")

    def get_bindings(self):
        return [
            *self.clipping.get_bindings(),
            webgpu.BufferBinding(90, self._buffers["vertices"]),
            webgpu.BufferBinding(91, self._buffers["colors"]),
            webgpu.UniformBinding(92, self.thickness_uniform),
            webgpu.BufferBinding(93, self._buffers["index"]),
        ]


class GeometryVertexRenderer(BaseGeometryRenderer):
    n_vertices: int = 4
    topology: PrimitiveTopology = PrimitiveTopology.triangle_strip

    def __init__(self, geo, clipping):
        self.geo = geo
        super().__init__(clipping, label="GeometryVertices")
        self.active = True
        self.thickness = 0.05
        self._buffers = {}

    def set_colors(self, colors):
        """colors is numpy float32 array with 4 times number indices entries"""
        self.colors = colors
        if "colors" in self._buffers:
            self.device.queue.writeBuffer(self._buffers["colors"], 0, self.colors.tobytes())

    def get_shader_code(self):
        return read_shader_file("ngsolve/geo_vertex.wgsl")

    def update(self, options):
        verts = set(self.geo.shape.vertices)
        self.colors = np.array(
            [v.col if v.col is not None else [0.3, 0.3, 0.3, 1.0] for v in verts],
            dtype=np.float32,
        ).flatten()
        self.n_instances = len(verts)
        vert_values = np.array([[pi for pi in v.p] for v in verts], dtype=np.float32).flatten()
        self._buffers = {}
        self._buffers["vertices"] = buffer_from_array(vert_values)
        self._buffers["colors"] = buffer_from_array(self.colors)
        self.thickness_uniform = uniform_from_array(np.array([self.thickness], dtype=np.float32))

    def get_bindings(self):
        return [
            *self.clipping.get_bindings(),
            webgpu.BufferBinding(90, self._buffers["vertices"]),
            webgpu.BufferBinding(91, self._buffers["colors"]),
            webgpu.UniformBinding(92, self.thickness_uniform),
        ]


class GeometryRenderer(MultipleRenderer):
    def __init__(self, geo, label="Geometry", clipping=None):
        self.geo = geo
        self.clipping = clipping or Clipping()
        self.faces = GeometryFaceRenderer(geo, self.clipping)
        self.edges = GeometryEdgeRenderer(geo, self.clipping)
        self.vertices = GeometryVertexRenderer(geo, self.clipping)
        self.faces.clipping = self.clipping
        self.edges.clipping = self.clipping
        self.vertices.clipping = self.clipping
        self.vertices.active = False
        super().__init__([self.vertices, self.edges, self.faces])

    def update(self, options: RenderOptions):
        vis_data = self.geo._visualizationData()
        self.clipping.update(options)
        for ro in self.render_objects:
            ro.vis_data = vis_data
            ro.update(options)

        self.canvas = options.canvas

    def get_bounding_box(self):
        pmin, pmax = self.geo.shape.bounding_box
        return ([pmin[0], pmin[1], pmin[2]], [pmax[0], pmax[1], pmax[2]])

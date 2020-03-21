import imp
import inspect
import logging
import os
import sys
from datetime import datetime
from math import floor
from pprint import pformat

import numpy as np

import bpy
from mathutils import Matrix, Vector

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)
try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    imp.reload(__import__('common'))  # dumb hacks because of blender's pycache settings
    from common import (Z_AXIS_3D, ENDLTAB, format_matrix, format_vector, TRI_VERTS, ATOL,
                        X_AXIS_2D, setup_logger, mode_set, serialise_matrix, export_json,
                        get_selected_polygons)
finally:
    sys.path = PATH

LOG_FILE = os.path.splitext(os.path.basename(THIS_FILE))[0] + '.log'
Z_OFFSET = -0.01
COLLECTION_NAME = 'LEDs'
# LED_SPACING = 1.0/16
LED_SPACING = 0.050
IGNORE_LAMPS = True


def orientation(*vec):
    assert len(vec) == 3
    return (vec[1].y - vec[0].y)*(vec[2].x - vec[1].x) - (vec[2].y - vec[1].y)*(vec[1].x - vec[0].x)


def plane_flattener(center, normal):
    """
    Form a matrix which will transform all points on the plane onto the X-Y plane.
    """

    cross_z = normal.cross(Z_AXIS_3D)
    logging.debug(f"Normal cross Z-Axis: {ENDLTAB + format_vector(cross_z)}")
    angle_z = normal.angle(Z_AXIS_3D)
    logging.debug(f"Normal angle with Z-axis: {angle_z}")
    rotation = Matrix.Rotation(angle_z, 3, cross_z).to_4x4()
    # logging.debug(f"Rotation Matrix:" + ENDLTAB + format_matrix(rotation))
    translation = Matrix.Translation(-center)
    # logging.debug(f"Translation Matrix:" + ENDLTAB + format_matrix(translation))
    flattener = rotation @ translation
    logging.debug(f"Flattener Matrix:" + ENDLTAB + format_matrix(flattener))
    return flattener


def orient_flat_triangle(flattened):
    lengths = [
        (flattened[i] - flattened[(i+1) % TRI_VERTS]).magnitude
        for i in range(TRI_VERTS)
    ]
    logging.debug(f"Lengths: \n{pformat(lengths)}")
    ratios = [
        lengths[i]/lengths[(i+1) % TRI_VERTS]
        for i in range(TRI_VERTS)
    ]
    logging.debug(f"Ratios: \n{pformat(ratios)}")
    equalities = [
        np.isclose(ratio, 1, atol=ATOL)
        for ratio in ratios
    ]
    logging.debug(f"Equalities: {equalities}")
    tri_type = {3: 'EQU', 1: 'ISO'}.get(len(list(filter(None, equalities))), 'OTH')
    logging.debug(f"Type: {tri_type}")
    equal_index = equalities.index(True) if tri_type == 'ISO' else 0
    logging.debug(f"Equal Index: {equal_index}")
    ori = orientation(*flattened)
    logging.debug(f"Orientation: {ori}")
    oriented = flattened[equal_index:] + flattened[:equal_index]
    if ori > 0:
        oriented[0], oriented[2] = oriented[2], oriented[0]
    logging.debug(f"Oriented: {ENDLTAB + ENDLTAB.join(map(format_vector, oriented))}")
    return oriented, tri_type


def get_normaliser(oriented):
    """
    Form a matrix based on the oriented points which transforms points on the X-Y plane so that
    oriented[2] is at the origin, and oriented[0] is at the X-axis
    """
    translation = Matrix.Translation(-oriented[2]).to_4x4()
    angle_x = (oriented[0]-oriented[2]).to_2d().angle_signed(X_AXIS_2D)
    logging.debug(f"Angle X: {angle_x}")
    rotation = Matrix.Rotation(-angle_x, 4, 'Z')
    normaliser = rotation @ translation
    logging.debug(f"Normaliser Matrix:" + ENDLTAB + format_matrix(normaliser))
    return normaliser


def generate_lights_for_triangle(tri_width, tri_height, tri_apex, spacing, z_height):
    """
    Create a set of points
    """
    tri_gradient_left = tri_height / tri_apex
    # tri_gradient_right =
    logging.debug(f"Triangle Gradients: {tri_gradient_left}")
    logging.debug(f"Spacing: {spacing}")
    vertical_lines = floor(tri_height / spacing) - 1
    padding = tri_height - (spacing * vertical_lines)
    lights = []
    for vertical_idx in range(vertical_lines):
        pixel_y = padding + (vertical_idx * spacing)
        row_start = (pixel_y / tri_gradient_left) + (padding / 2)
        half_horizontal_lines = floor((tri_apex - row_start) / spacing) - 1
        for horizontal_idx in range(-half_horizontal_lines, half_horizontal_lines + 1):
            pixel_x = tri_apex + horizontal_idx * spacing
            lights.append(Vector((pixel_x, pixel_y, z_height)))
    logging.debug(f"Lights (Norm):" + ENDLTAB + ENDLTAB.join(map(format_vector, lights)))
    return lights


def normalise_triangle(center, normal, vertices):
    """
    Transform a triangular polygon defined by center, normal and vertices such that:
    - it is on the X-Y plane
    - point 2 at the origin
    - point 0 is on the X-axis

    and form a matrix which will translate points on the normalised triangle onto the polygon.
    """

    assert len(vertices) == TRI_VERTS

    # Bring all points on the triangle down to the X-Y plane

    flattener = plane_flattener(center, normal)
    flattened = [flattener @ vertex for vertex in vertices]
    logging.debug(f"Flattened: {ENDLTAB + ENDLTAB.join(map(format_vector, flattened))}")
    zs = [vertex.z for vertex in flattened]
    assert all([np.isclose(z_, 0, atol=ATOL) for z_ in zs]), f"all zs should be 0: {zs}"

    # Normalise points to simplify geometry
    oriented, tri_type = orient_flat_triangle(flattened)
    normaliser = get_normaliser(oriented)
    normalised = [normaliser @ point for point in oriented]
    logging.debug(f"Normalised: {ENDLTAB + ENDLTAB.join(map(format_vector, normalised))}")

    # Sanity check results

    tri_width = normalised[0].x
    logging.debug(f"Triangle Width: {tri_width}")
    assert tri_width > 0
    tri_height = normalised[1].y
    logging.debug(f"Triangle Height: {tri_height}")
    assert tri_height > 0
    tri_apex = normalised[1].x
    logging.debug(f"Triangle Midpoint: {tri_apex}")
    if tri_type in ['EQU', 'ISO']:
        assert np.isclose(tri_apex * 2, tri_width, 1e-4), \
            f"Local midpoint {tri_apex} should be half of Local width {tri_width} for {tri_type}"

    return flattener.inverted() @ normaliser.inverted(), normalised


def main():
    setup_logger(LOG_FILE)
    logging.info(f"*** Starting Light Layout {datetime.now().isoformat()} ***")
    obj = bpy.context.object
    logging.info(f"Selected object: {obj}")
    logging.debug(f"Object World Matrix:" + ENDLTAB + format_matrix(obj.matrix_world))
    if not IGNORE_LAMPS:
        with mode_set('OBJECT'):
            bpy.ops.object.delete({"selected_objects": bpy.data.collections['LEDs'].all_objects})
        coll = bpy.data.collections[COLLECTION_NAME]

    panels = []

    for poly_idx, polygon in enumerate(get_selected_polygons(obj)):

        panel = {}

        logging.debug(f"Center (local):" + ENDLTAB + format_vector(polygon.center))
        center = polygon.center
        logging.debug(f"Normal (local):" + ENDLTAB + format_vector(polygon.normal))
        normal = polygon.normal
        logging.debug(f"Vertex IDs:" + ENDLTAB + pformat(list(polygon.vertices)))
        vertices = [obj.data.vertices[vertex_id].co for vertex_id in polygon.vertices]
        logging.debug(f"Vertices (local):" + ENDLTAB + ENDLTAB.join(map(format_vector, vertices)))

        panel_matrix, panel_triangle = normalise_triangle(
            obj.matrix_world @ center,
            obj.matrix_world @ normal,
            [obj.matrix_world @ vertex for vertex in vertices]
        )
        panel['matrix'] = serialise_matrix(panel_matrix)
        panel['triangle'] = serialise_matrix(panel_triangle)

        pixels = generate_lights_for_triangle(
            panel_triangle[0].x,
            panel_triangle[1].y,
            panel_triangle[1].x,
            LED_SPACING,
            Z_OFFSET
        )

        panel['pixels'] = serialise_matrix(pixels)

        panels.append(panel)

        if IGNORE_LAMPS:
            continue

        logging.info(f"adding {len(pixels)} lights to scene")

        for light_idx, position in enumerate(pixels):
            name = f"LED {poly_idx:4d} {light_idx:4d}"
            lamp_data = bpy.data.lights.new(name=f"{name} data", type='POINT')
            lamp_data.energy = 1.0
            lamp_object = bpy.data.objects.new(name=f"{name} object", object_data=lamp_data)
            lamp_object.location = panel_matrix @ position
            coll.objects.link(lamp_object)

    logging.info(f"exporting {len(panels)} panels")
    export_json(obj, {'panels': panels}, 'LEDs')

    logging.info(f"*** Completed Light Layout {datetime.now().isoformat()} ***")


if __name__ == '__main__':
    main()

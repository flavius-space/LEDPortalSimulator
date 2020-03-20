import logging
import os
from contextlib import contextmanager
from datetime import datetime
from math import floor, nan
from pprint import pformat, pprint
from functools import reduce, partial

import coloredlogs
import numpy as np

import bpy
from mathutils import Matrix, Vector

Z_OFFSET = 0.01
COLLECTION_NAME = 'LEDs'

Z_AXIS_3D = Vector((0, 0, 1))
X_AXIS_2D = Vector((1, 0))
TRI_VERTS = 3
ENDLTAB = "\n\t"
ATOL = 1e-4
# LED_SPACING = 1.0/16
LED_SPACING = 0.050
DEBUG = False
LOG_FILE = os.path.splitext(os.path.basename(__file__))[0] + '.log'
LOG_STREAM_FMT = "%(asctime)s %(levelname)s %(message)s"


@contextmanager
def mode_set(mode):
    prev_mode = bpy.context.object.mode
    try:
        bpy.ops.object.mode_set(mode=mode)
        yield
    finally:
        bpy.ops.object.mode_set(mode=prev_mode)


def orientation(*vec):
    assert len(vec) == 3
    return (vec[1].y - vec[0].y)*(vec[2].x - vec[1].x) - (vec[2].y - vec[1].y)*(vec[1].x - vec[0].x)


def format_vector(vec):
    mag = vec.magnitude
    if len(vec) == 3:
        theta = vec.to_2d().angle_signed(X_AXIS_2D) if mag > 0 else nan
        phi = vec.angle(Z_AXIS_3D) if mag > 0 else nan
        return f"C({vec.x: 2.3f}, {vec.y: 2.3f}, {vec.z: 2.3f}) " \
            f"P({mag: 2.3f}, {theta: 2.3f}, {phi: 2.3f})"
    elif len(vec) == 2:
        theta = vec.angle_signed(X_AXIS_2D) if mag > 0 else nan
        return f"C({vec.x: 2.3f}, {vec.y: 2.3f}) " \
            f"P({mag: 2.3f}, {theta: 2.3f})"


def get_scale_factor(matrix):
    factors = matrix.to_scale()
    assert all(map(partial(np.isclose, factors[0], atol=ATOL), factors[1:]))
    return sum(factors)/len(factors)


def polygon_flattener(polygon):
    # Generate a matrix which will move all points on the polygon onto the X-Y plane.
    cross_z = polygon.normal.cross(Z_AXIS_3D)
    logging.debug(f"Normal cross Z-Axis: {ENDLTAB + format_vector(cross_z)}")
    angle_z = polygon.normal.angle(Z_AXIS_3D)
    logging.debug(f"Normal angle with Z-axis: {angle_z}")
    rotation = Matrix.Rotation(angle_z, 3, cross_z).to_4x4()
    logging.debug(f"Rotation Matrix: \n{rotation}")
    translation = Matrix.Translation(-polygon.center)
    logging.debug(f"Translation Matrix: \n{translation}")
    flattener = rotation @ translation
    logging.debug(f"Flattener Matrix: \n{flattener}")
    return flattener


def get_leds(obj, polygon):
    logging.debug(f"Center (local): {ENDLTAB + format_vector(polygon.center)}")
    logging.debug(f"Normal (local): {ENDLTAB + format_vector(polygon.normal)}")
    scale_factor = get_scale_factor(obj.matrix_world)
    logging.debug(f"Scale factor: {scale_factor}")
    logging.debug(f"Vertex IDs: \n{pformat(list(polygon.vertices))}")
    assert len(polygon.vertices) == TRI_VERTS
    vertices = [
        obj.data.vertices[vertex_id].co
        for vertex_id in polygon.vertices
    ]
    logging.debug(f"Vertices (local): {ENDLTAB + ENDLTAB.join(map(format_vector, vertices))}")

    # Bring all points on the triangle down to the X-Y plane

    flattener = polygon_flattener(polygon)
    flattened = [flattener @ vertex for vertex in vertices]
    logging.debug(f"Flattened: {ENDLTAB + ENDLTAB.join(map(format_vector, flattened))}")
    z_zero = [
        np.isclose(vertex.z, 0, atol=ATOL) for vertex in flattened
    ]
    assert all(z_zero), f"all should be true: {[vertex.z for vertex in flattened]}"

    # Convert points to 2D to simplify geometry

    flattened = [
        vertex.to_2d() for vertex in flattened
    ]
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
    flattened = flattened[equal_index:] + flattened[:equal_index]
    orientation_ = orientation(*flattened)
    logging.debug(f"Orientation: {orientation_}")
    if orientation_ > 0:
        flattened[0], flattened[2] = flattened[2], flattened[0]
    logging.debug(f"Flattened: {ENDLTAB + ENDLTAB.join(map(format_vector, flattened))}")
    normalised = [
        point - flattened[2]
        for point in flattened
    ]
    logging.debug(f"Normalised: {ENDLTAB + ENDLTAB.join(map(format_vector, normalised))}")
    angle_x = normalised[0].angle_signed(X_AXIS_2D)
    logging.debug(f"Angle X: {angle_x}")
    rotation_2d = Matrix.Rotation(-1 * angle_x, 2)
    normalised = [
        rotation_2d @ point
        for point in normalised
    ]
    logging.debug(f"Normalised: {ENDLTAB + ENDLTAB.join(map(format_vector, normalised))}")

    # Use Normalised points to generate lights on triangle

    tri_width = normalised[0].x
    assert tri_width > 0
    logging.debug(f"Triangle Width: {tri_width} ({scale_factor * tri_width} u)")
    tri_height = normalised[1].y
    assert tri_height > 0
    logging.debug(f"Triangle Height: {tri_height} ({scale_factor * tri_height} u)")
    tri_midpoint = normalised[1].x
    if tri_type in ['EQU', 'ISO']:
        assert np.isclose(tri_midpoint * 2, tri_width, 1e-4), \
            f"tri_midpoint {tri_midpoint} should be half of tri_width {tri_width}"
    tri_gradient = tri_height / tri_midpoint
    logging.debug(f"Triangle Gradient: {tri_gradient}")

    local_spacing = LED_SPACING / scale_factor
    logging.debug(f"Local Spacing: {local_spacing} ({LED_SPACING} u)")
    vertical_lines = floor(tri_height / local_spacing) - 1
    padding = tri_height - (local_spacing * vertical_lines)
    lights_2d = []
    for vertical_idx in range(vertical_lines):
        pixel_y = padding + (vertical_idx * local_spacing)
        row_start = (pixel_y / tri_gradient) + (padding / 2)
        half_horizontal_lines = floor((tri_midpoint - row_start) / local_spacing) - 1
        for horizontal_idx in range(-half_horizontal_lines, half_horizontal_lines + 1):
            pixel_x = tri_midpoint + horizontal_idx * local_spacing
            lights_2d.append(Vector((pixel_x, pixel_y)))

    logging.debug(f"Lights 2D: {ENDLTAB + ENDLTAB.join(map(format_vector, lights_2d))}")
    lights_2d = [
        rotation_2d.inverted() @ point + flattened[2]
        for point in lights_2d
    ]
    logging.debug(f"Lights 2D: {ENDLTAB + ENDLTAB.join(map(format_vector, lights_2d))}")
    offset = Vector((0, 0, Z_OFFSET))
    lights_3d = [
        flattener.inverted() @ (point.to_3d() + offset)
        for point in lights_2d
    ]
    logging.debug(
        f"Lights 3D ({len(lights_3d)}): " + ENDLTAB + ENDLTAB.join(map(format_vector, lights_3d)))
    return lights_3d


def setup_logger():
    logger = logging.getLogger()
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(LOG_FILE, 'w')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    if os.name != 'nt':
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(coloredlogs.ColoredFormatter(LOG_STREAM_FMT))
        logger.addHandler(stream_handler)


def main():
    setup_logger()
    logging.info(f"*** Starting Light Layout {datetime.now().isoformat()} ***")
    obj = bpy.context.object
    pprint(obj)
    logging.debug(f"Object World Matrix: \n{pformat(obj.matrix_world)}")
    logging.debug(f"Object Local Matrix: \n{pformat(obj.matrix_local)}")
    selections = [
        (polygon, polygon.select)
        for polygon in obj.data.polygons
    ]
    logging.info(f"Polygon Selections: \n{pformat(selections)}")
    with mode_set('OBJECT'):
        bpy.ops.object.delete({"selected_objects": bpy.data.collections['LEDs'].all_objects})
    coll = bpy.data.collections[COLLECTION_NAME]
    for poly_idx, polygon in enumerate(obj.data.polygons):
        if not polygon.select:
            continue

        lights_3d = get_leds(obj, polygon)

        for light_idx, position in enumerate(lights_3d):
            name = f"LED {poly_idx:4d} {light_idx:4d}"
            lamp_data = bpy.data.lights.new(name=f"{name} data", type='POINT')
            lamp_data.energy = 1.0
            lamp_object = bpy.data.objects.new(name=f"{name} object", object_data=lamp_data)
            lamp_object.location = obj.matrix_world @ position
            coll.objects.link(lamp_object)

    logging.info(f"*** Completed Light Layout {datetime.now().isoformat()} ***")


if __name__ == '__main__':
    main()

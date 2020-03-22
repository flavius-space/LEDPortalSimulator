import imp
import inspect
import logging
import os
import sys
from datetime import datetime
from math import floor
from pprint import pformat
from itertools import starmap

import numpy as np

import bpy
from mathutils import Matrix, Vector

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)
try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    imp.reload(__import__('common'))  # dumb hacks because of blender's pycache settings
    from common import (Z_AXIS_3D, ENDLTAB, format_matrix, format_vector, TRI_VERTS, ATOL, ORIGIN_3D,
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


# def plot_vecs_2d(vecs):
#     # DELET THIS
#     return
#     vecs = [vec.to_2d() for vec in vecs]
#     logging.info(f"plotting:" + ENDLTAB + ENDLTAB.join(map(format_vector, vecs)))
#     import matplotlib.pyplot as plt
#     plt.plot(*zip(*vecs + [(0, 0)]), 'o-')
#     plt.show()


def orientation(*vecs):
    """
    How this works:
    ---
    Take the first 3 points p0, p1, p2 and treat them like a triangle.

    determine the relative vectors r0 and r1
    - r0 = p1 - p0
    - r1 = p2 - p1

    find the cross-product of these two vectors. if it is in the same direction as
    """
    # logging.debug("Orientation Vectors:" + ENDLTAB + ENDLTAB.join(map(format_vector, vecs[:TRI_VERTS])))
    # lengths = [(vecs[i] - vecs[(i+1) % TRI_VERTS]).magnitude for i in range(TRI_VERTS)]
    # logging.debug(f"Lengths: \n{pformat(lengths)}")
    # ratios = [lengths[i]/lengths[(i+1) % TRI_VERTS] for i in range(TRI_VERTS)]
    # logging.debug(f"Ratios: \n{pformat(ratios)}")
    # equalities = [np.isclose(ratio, 1, atol=ATOL) for ratio in ratios]
    # logging.debug(f"Equalities: {equalities}")
    # tri_type = {3: 'EQU', 1: 'ISO'}.get(len(list(filter(None, equalities))), 'OTH')
    # logging.debug(f"Type: {tri_type}")
    # equal_index = equalities.index(True) if tri_type == 'ISO' else 0
    # logging.debug(f"Equal Index: {equal_index}")
    # logging.info("DIAGNOSIS: " + [
    #     f"p1 {vecs[1]} is apex, move p2 {vecs[2]} to origin, move p0 {vecs[0]} to +ve x-axis",
    #     f"you're good",
    #     f"p0 {vecs[0]} is apex, move p1 {vecs[1]} to origin, move p2 {vecs[2]} to +ve x-axis"
    # ][equal_index])

    rotation = Matrix.Rotation(-(vecs[1]-vecs[0]).to_2d().angle_signed(X_AXIS_2D), 4, 'Z')
    relative = [rotation @ (vec - vecs[0]) for vec in vecs[1:]]
    logging.debug("Relative:" + ENDLTAB + ENDLTAB.join(map(format_vector, relative)))
    # plot_vecs_2d(relative)

    cross = relative[0].cross(relative[1])
    logging.debug("Cross:" + ENDLTAB + format_vector(cross))
    orientation = cross.dot(Z_AXIS_3D)
    logging.debug(f"Orientation: {orientation}")
    return orientation


def plane_flattener(center, normal):
    """
    Form a matrix which will transform all points on the plane onto the X-Y plane.
    """

    cross_z = normal.cross(Z_AXIS_3D)
    logging.debug(f"Normal cross Z-Axis: {ENDLTAB + format_vector(cross_z)}")
    angle_z = normal.angle(Z_AXIS_3D)
    logging.debug(f"Normal angle with Z-axis: {angle_z}")
    rotation = Matrix.Rotation(angle_z, 3, cross_z).to_4x4()
    logging.debug(f"Rotation Matrix:" + ENDLTAB + format_matrix(rotation))
    translation = Matrix.Translation(-center)
    logging.debug(f"Translation Matrix:" + ENDLTAB + format_matrix(translation))
    flattener = rotation @ translation
    logging.debug(f"Flattener Matrix:" + ENDLTAB + format_matrix(flattener))
    return flattener


def do_flattening(center, normal, vertices):
    """
    Bring all coplanar points on the plane defined by center and normal down to the X-Y plane.
    """
    flattener = plane_flattener(center, normal)
    flattened = [flattener @ vertex for vertex in vertices]
    logging.debug(f"Flattened: {ENDLTAB + ENDLTAB.join(map(format_vector, flattened))}")
    zs = [vertex.z for vertex in flattened]
    assert all([np.isclose(z_, 0, atol=ATOL) for z_ in zs]), f"all zs should be 0: {zs}"
    return flattener, flattened


def rotate_seq(seq, times):
    """
    Causes the operation
        [s0, s1, ...] -> [s1, ..., p0]
    to happen a specified amount of times
    """
    times = (len(seq) + times) % len(seq)
    return seq[times:] + seq[:times]


def orient_flattened_points(flattened):
    """
    How this works:
    ---
    Take the first 3 points p0, p1, p2 and treat them like a triangle.

    1. if they are anticlockwise oriented (-ve orientation) then reverse the points.

    2. determine the side lenghts between them:
    - L0 = |p0 - p1|
    - L1 = |p1 - p2|
    - L2 = |p2 - p1|

    3. Determine ratios between the side lengths:
    - r0 = L0 : L1
    - r1 = L1 : L2
    - r2 = L2 : L3

    4. Determine which kind of triange this makes
    - if only one is close to 1, then it is isosceles and needs extra orientation.
    - if all three or none are close to 1, then skip the next skip

    5. Different actions need to be performed on the points depending on the unitary r value:
    - r0 ~ 1 : p1 is apex, move p2 to origin, move p0 to +ve x-axis
    - r1 ~ 1 : p2 is apex, move p0 to origin, move p1 to +ve x-axis
    - r2 ~ 1 : p0 is apex, move p1 to origin, move p2 to +ve x-axis

    6. if we were to rotate the points by equal_index, then means that the operation
        [p0, p1, p2] -> [p1, p2, p0]
    happens equal_index times, so the actions factor down to:
        move p2 to origin, move p0 to +ve x-axis
    which is a further 2 rotations.
    """
    if orientation(*flattened) < 0:
        flattened = list(reversed(flattened))
        assert orientation(*flattened) >= 0, "Flattened orientation can't be -ve after reversing"
    lengths = [(flattened[i] - flattened[(i+1) % TRI_VERTS]).magnitude for i in range(TRI_VERTS)]
    logging.debug(f"Lengths: \n{pformat(lengths)}")
    ratios = [lengths[i]/lengths[(i+1) % TRI_VERTS] for i in range(TRI_VERTS)]
    logging.debug(f"Ratios: \n{pformat(ratios)}")
    equalities = [np.isclose(ratio, 1, atol=ATOL) for ratio in ratios]
    logging.debug(f"Equalities: {equalities}")
    tri_type = {3: 'EQU', 1: 'ISO'}.get(len(list(filter(None, equalities))), 'OTH')
    logging.debug(f"Type: {tri_type}")
    equal_index = equalities.index(True) if tri_type == 'ISO' else 0
    # logging.debug(f"Equal Index: {equal_index}")
    # logging.info([
    #     f"p1 {flattened[0]} is apex, move p2 {flattened[2]} to origin, move p0 {flattened[0]} to +ve x-axis",
    #     f"p2 {flattened[1]} is apex, move p0 {flattened[0]} to origin, move p1 {flattened[1]} to +ve x-axis",
    #     f"p0 {flattened[2]} is apex, move p1 {flattened[1]} to origin, move p2 {flattened[2]} to +ve x-axis"
    # ][equal_index])
    oriented = rotate_seq(flattened, equal_index + 2)
    logging.debug(f"Oriented: {ENDLTAB + ENDLTAB.join(map(format_vector, oriented))}")
    orientation(*oriented)
    # logging.info(f"rotating once")
    # orientation(*rotate_seq(oriented, 1))
    # logging.info(f"rotating twice")
    # orientation(*rotate_seq(oriented, 2))
    return oriented, tri_type


def get_normaliser(oriented):
    """
    Form a matrix based on the oriented points which transforms points on the X-Y plane so that
    oriented[0] is at the origin, and oriented[1] is at the X-axis
    """
    translation = Matrix.Translation(-oriented[0]).to_4x4()
    # logging.info(f"Translation Matrix:" + ENDLTAB + format_matrix(translation))
    angle_x = (oriented[1]-oriented[0]).to_2d().angle_signed(X_AXIS_2D)
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


def normalise_plane(center, normal, vertices):
    """
    Normalise a set of coplanar points d defined by center, normal and vertices such that:
    - it is on the X-Y plane
    - point 0 at the origin
    - point 1 is on the X-axis
    - point 2 is above the X-axis

    and form a matrix which will translate points on the normalised plane onto the polygon.

    Ideally, the x and y axes of the normalised plane should form the basis of the desired grid
    """

    assert len(vertices) >= TRI_VERTS

    flattener, flattened = do_flattening(center, normal, vertices)

    # Normalise points to simplify geometry
    oriented, tri_type = orient_flattened_points(flattened)
    normaliser = get_normaliser(oriented)
    normalised = [normaliser @ point for point in oriented]
    logging.debug(f"Normalised: {ENDLTAB + ENDLTAB.join(map(format_vector, normalised))}")
    # plot_vecs_2d(normalised[:3])
    # Sanity check results

    assert \
        np.isclose(normalised[0].x, 0, atol=ATOL) and np.isclose(normalised[0].y, 0, atol=ATOL), \
        f"point 0 {format_vector(normalised[0])} should be on the origin x-axis"
    tri_width = normalised[1].x
    logging.debug(f"Triangle Width: {tri_width}")
    assert \
        tri_width > 0 and np.isclose(normalised[1].y, 0, atol=ATOL), \
        f"point 1 {format_vector(normalised[1])} should be on positive x-axis"
    tri_height = normalised[2].y
    logging.debug(f"Triangle Height: {tri_height}")
    assert \
        tri_height > 0, \
        f"point 2 {format_vector(normalised[2])} should be above x-axis"
    tri_apex = normalised[2].x
    logging.debug(f"Triangle Midpoint: {tri_apex}")
    if len(vertices) == TRI_VERTS and tri_type in ['EQU', 'ISO']:
        assert np.isclose(tri_apex * 2, tri_width, 1e-4), \
            f"apex {tri_apex} should be half of Local width {tri_width} for {tri_type}"

    return flattener.inverted() @ normaliser.inverted(), normalised


def format_vecs(*vecs):
    return " / ".join(map(format_vector, vecs))


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

        world_center = obj.matrix_world @ polygon.center
        logging.debug(
            f"Center (local / world):" + ENDLTAB + format_vecs(polygon.center, world_center))
        world_normal = (obj.matrix_world @ polygon.normal) - (obj.matrix_world @ ORIGIN_3D)
        logging.debug(
            f"Normal (local / world):" + ENDLTAB + format_vecs(polygon.normal, world_normal))
        logging.debug(f"Vertex IDs:" + ENDLTAB + pformat(list(polygon.vertices)))
        vertices = [obj.data.vertices[vertex_id].co for vertex_id in polygon.vertices]
        world_vertices = [obj.matrix_world @ vertex for vertex in vertices]
        logging.debug(
            f"Vertices (local / world):" + ENDLTAB
            + ENDLTAB.join(starmap(format_vecs, zip(vertices, world_vertices))))

        panel_matrix, panel_vertices = normalise_plane(
            world_center, world_normal, world_vertices
        )

        panel['matrix'] = serialise_matrix(panel_matrix)
        panel['vertices'] = serialise_matrix(panel_vertices)

        pixels = generate_lights_for_triangle(
            panel_vertices[1].x,
            panel_vertices[2].y,
            panel_vertices[2].x,
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

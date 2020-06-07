"""
Script which uses the Blender API to generate a set of lights for all selected polygons in the
currently selected mesh group. Optionally places lights in the blender scene for preview.

Light placement works on any coplanar tri / quad polygon, and is highly configurable.

TODO:
- make the following configurable in object properties:
    - LED_SPACING
    - controller info (channel number, IP)
"""


import imp
import inspect
import logging
import os
import sys
from datetime import datetime
from itertools import starmap
from math import atan, ceil, copysign, cos, floor, inf, isinf, nan, sin, sqrt
from pprint import pformat

import bpy
import numpy as np
from mathutils import Matrix, Vector

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)
try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    import common
    imp.reload(common)  # dumb hacks because of blender's pycache settings
    from common import (Z_AXIS_3D, ENDLTAB, format_matrix, format_vector, TRI_VERTS, ATOL,
                        ORIGIN_3D, X_AXIS_2D, setup_logger, mode_set, serialise_matrix, export_json,
                        get_selected_polygons)
finally:
    sys.path = PATH

LOG_FILE = os.path.splitext(os.path.basename(THIS_FILE))[0] + '.log'
Z_OFFSET = -0.01
COLLECTION_NAME = 'LEDs'
# LED_SPACING = 1.0/16
# LED_SPACING = 0.2
LED_SPACING = 0.06
SERPENTINE = True
GRID_GRADIENT = sqrt(3)
IGNORE_LAMPS = False


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

    rotation = Matrix.Rotation(-(vecs[1]-vecs[0]).to_2d().angle_signed(X_AXIS_2D), 4, 'Z')
    relative = [rotation @ (vec - vecs[0]) for vec in vecs[1:]]
    logging.debug("Relative:" + ENDLTAB + ENDLTAB.join(map(format_vector, relative)))

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
    oriented = rotate_seq(flattened, equal_index + 2)
    logging.debug(f"Oriented: {ENDLTAB + ENDLTAB.join(map(format_vector, oriented))}")
    orientation(*oriented)
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


def nan_divide(quotient, dividend):
    if np.isclose(dividend, 0, atol=ATOL):
        return nan
    if dividend is nan:
        return 0
    return quotient / dividend


def inf_divide(quotient, dividend):
    sign = 1 if (quotient >= 0) else -1
    sign *= 1 if (dividend >= 0) else -1
    if np.isclose(dividend, 0, atol=ATOL):
        return copysign(inf, sign)
    if isinf(dividend):
        return copysign(0, sign)
    return quotient / dividend


def gradient_rise(gradient):
    """
    get the length of the opposite side of a right triangle, angle=θ, hypotenuse=1

       /|
    1 / |
     /  | <- rise
    /θ__| <- 90

    gradient = rise / run = tan(theta)
    => theta = atan(gradient)
    sin(theta) = rise / 1
    => rise = sin(atan(gradient))
    """
    return sin(atan(gradient))


def gradient_run(gradient):
    """
    get the length of the adjacent side of a right triangle, angle=θ, hypotenuse=1
       /|
    1 / |
     /  |
    /θ__| <- 90
    |<->| <- run

    gradient = rise / run = tan(theta)
    => theta = atan(gradient)
    cos(theta) = run / 1
    => rise = cos(atan(gradient))
    """
    return cos(atan(gradient))


def float_floor(number):
    closest_int = round(number)
    if np.isclose(number, closest_int, atol=ATOL):
        return closest_int
    return floor(number)


def float_ceil(number):
    closest_int = round(number)
    if np.isclose(number, closest_int, atol=ATOL):
        return closest_int
    return ceil(number)


def float_abs_floor(number):
    closest_int = round(number)
    if np.isclose(number, closest_int, atol=ATOL):
        return closest_int
    return int(copysign(floor(abs(number)), number))


def float_abs_ceil(number):
    closest_int = round(number)
    if np.isclose(number, closest_int, atol=ATOL):
        return closest_int
    return int(copysign(ceil(abs(number)), number))


def axis_centered_lines(axis_length, spacing, margin_left, margin_right=None, axis_name=None):
    """
    Divide an axis into lines `spacing` units apart, centered on the space inside `axis_length`
    after removing `margin_left` and `margin_right`. If `margin_right` is not provided, it is
    assumed to be the same as `margin_left`

    |--------------------|----X---------X----------X----|------------------|
    ^- origin            |    ^- lines -^         -^    |                  |
    |<- axis_length ------------------------------------------------------>|
    |<- margin_left ---->|    |         |          |    |<- margin_right ->|
    |          usable -> |<---------------------------->|                  |
    |         padding -> |<-->|         |          |<-->|                  |
    |              spacing -> |<------->|<-------->|    |                  |
    """

    if margin_right is None:
        margin_right = margin_left

    usable = axis_length - margin_left - margin_right
    lines = float_floor(usable / spacing) + 1
    usage = spacing * (lines - 1)
    assert \
        usage < usable \
        or np.isclose(usable - usage, 0, atol=ATOL), \
        f"{axis_name + ' ' if axis_name else ''}axis usage {usage} >= usable {usable}"
    padding = (usable - (spacing * (lines - 1))) / 2
    start = margin_left + padding

    return start, lines, padding


def generate_lights_for_convex_polygon(
        base_width: float,
        quad_right_x: float,
        quad_right_height: float,
        quad_left_x: float,
        quad_left_height: float,
        spacing: float,
        z_height: float = 0.0,
        margin: float = 0.0,
        serpentine: bool = True,
        grid_gradient: float = inf,
):
    """
    Geometric Assumptions:
        all points are coplanar
        polygon has already been flattened and normalised (see normalise_plane)
        points 0, 1, 2 and -1 are convex
        points form a triangle or quadrangle
        point 0 is at origin (0, 0)
        point 1 is on y axis, right of base line (base_width, 0)
        point 2 is top right of quad (quad_right_x, quad_right_height)
        point -1 is top left of quad (quad_left_x, quad_left_height)


                          mL                            <- left gradient
                         ╱         mR                   <- right gradient
                        ╱           ╲      mG           <- grid gradient
                       ╱             ╲    /
               │<- horizontal start width -->│
               │     ╱                 ╲     |             P-1: (quad left x, quad left height)
               |    o(P-1)__________(P2)o    |          <- P2: (quad right x, quad right height)
               │   ╱ ╱ ╱__│(Mv)______/ ╲ ╲   │          <- Mv: vertical margin
               │  ╱ ╱ ╱___│(pv)_____/_╲_╲_╲__│__
               │ ╱ ╱ ╱* * * * * * */* *╲_╲_╲_│__|(sv)   <- sv: vertical spacing
               │╱ ╱ ╱* * * * * * */* * *╲ ╲ ╲|             PS: (horizontal_start, vertical_start);
               o_/_o(PS)*_*_*_*_*/*_*(PE)o_╲_o          <- PE: (horizontal_end, vertical_start)
              ╱_╱_╱_______│(pv)___|_|_____╲_╲_╲         <- Pv: vertical padding
         (P0)o_╱_╱________│(Mv)___|_|______╲_╲_o(P1)    <- P0: (0,0); P1: (base_width, 0)
             │ │ │                |-|(s)   │ │ │        <- s: spacing
             │ │ │                         │ │ │           Ml: left margin
         (Ml)│-│ │                         │ │-│(Mr)    <- Mr: right margin
           (ph)│-│                         │-│(ph)      <- ph: horizontal padding


    Args:
        base_width (float): distance between (0)->(1)
        quad_right_x (float):
        quad_right_height (float):
        quad_left_x (float):
        quad_left_height (float):
        spacing (float):
        z_height (float):
        margin (float): minimum spacing between polygon edges and pixels, default: 0.0
        serpentine (bool): pixels alternate direction between each row, default: True
        grid_gradient (bool): determines how much each line of pixels is offset from the last

    TODO:
    - handle other polygon types
    """
    height = max([quad_left_height, quad_right_height])
    gradient_left = inf_divide(quad_left_height, quad_left_x)
    gradient_right = inf_divide(quad_right_height, quad_right_x - base_width)
    spacing_vertical = abs(gradient_rise(grid_gradient) * spacing)
    spacing_shear = abs(gradient_run(grid_gradient) * spacing)

    vertical_start, vertical_lines, vertical_padding = axis_centered_lines(
        height, spacing_vertical, margin, axis_name="Vertical")

    # Width of the horizontal line at `vertical_start` height
    horizontal_start_width = base_width \
        - inf_divide(vertical_start, gradient_left) \
        + inf_divide(vertical_start, gradient_right)
    # Width of the margin projected onto the horizontal axis at a right angle from each gradient
    margin_left = abs(margin/gradient_rise(gradient_left))
    margin_right = abs(margin/gradient_rise(gradient_right))

    horizontal_start, horizontal_lines, horizontal_padding = axis_centered_lines(
        horizontal_start_width, spacing, margin_left, margin_right, axis_name="Horizontal")
    horizontal_usage = spacing * (horizontal_lines - 1)

    translation = Matrix.Translation(Vector((
        horizontal_start, vertical_start, z_height
    )))
    scale = Matrix([
        [spacing, spacing_shear, 0, 0],
        [0, spacing_vertical, 0, 0],
        [0, 0, spacing, 0],
        [0, 0, 0, 1],
    ])
    transformation = translation @ scale

    lights = []
    for vertical_idx in range(vertical_lines):
        pixel_y_relative = (vertical_idx * spacing_vertical)
        row_grid_origin_x = inf_divide(pixel_y_relative, grid_gradient)
        row_start_relative = inf_divide(pixel_y_relative, gradient_left)
        row_grid_start = float_abs_ceil(
            (row_start_relative - row_grid_origin_x)/spacing)

        row_end_relative = horizontal_usage + inf_divide(pixel_y_relative, gradient_right)
        row_grid_end = float_abs_floor(
            (row_end_relative - row_grid_origin_x)/spacing)
        row_capacity = abs(row_end_relative - row_start_relative)
        row_usage = max(row_grid_end - row_grid_start - 1, 0) * spacing
        assert \
            row_usage < row_capacity \
            or np.isclose(row_capacity - row_usage, 0, atol=ATOL), \
            f"Row usage {row_usage} >= capacity {row_capacity}"
        row = []
        if row_grid_end >= row_grid_start:
            for horizontal_idx in range(row_grid_start, row_grid_end + 1):
                row.append((horizontal_idx, vertical_idx))
        if serpentine and vertical_idx % 2:
            row = list(reversed(row))
        lights.extend(row)

    return transformation, lights


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
    base_width = normalised[1].x
    logging.debug(f"First Triangle Width: {base_width}")
    assert \
        base_width > 0 and np.isclose(normalised[1].y, 0, atol=ATOL), \
        f"point 1 {format_vector(normalised[1])} should be on positive x-axis"
    apex_height = normalised[2].y
    logging.debug(f"First Triangle Height: {apex_height}")
    assert \
        apex_height > 0, \
        f"point 2 {format_vector(normalised[2])} should be above x-axis"
    apex_x = normalised[2].x
    logging.debug(f"First Triangle Midpoint: {apex_x}")
    if len(vertices) == TRI_VERTS and tri_type in ['EQU', 'ISO']:
        assert np.isclose(apex_x * 2, base_width, 1e-4), \
            f"apex {apex_x} should be half of Local width {base_width} for {tri_type}"

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

        # TODO: Make this configurable in object properties
        vertex_rotation = 1
        world_vertices = rotate_seq(world_vertices, vertex_rotation)

        panel_matrix, panel_vertices = normalise_plane(
            world_center, world_normal, world_vertices
        )

        panel['vertices'] = serialise_matrix(panel_vertices)

        pixel_matrix, pixels = generate_lights_for_convex_polygon(
            panel_vertices[1].x,
            panel_vertices[2].x,
            panel_vertices[2].y,
            panel_vertices[-1].x,
            panel_vertices[-1].y,
            LED_SPACING,
            Z_OFFSET,
            margin=LED_SPACING / 2,
            serpentine=SERPENTINE,
            grid_gradient=GRID_GRADIENT
        )

        panel['matrix'] = serialise_matrix(panel_matrix @ pixel_matrix)
        panel['pixels'] = serialise_matrix(pixels)

        panels.append(panel)

        if IGNORE_LAMPS:
            continue

        logging.info(f"adding {len(pixels)} lights to scene")

        logging.debug("Lights (Norm):")

        for light_idx, position in enumerate(pixels):
            name = f"LED {poly_idx:4d} {light_idx:4d}"
            lamp_data = bpy.data.lights.new(name=f"{name} data", type='POINT')
            lamp_data.energy = 1.0
            lamp_object = bpy.data.objects.new(name=f"{name} object", object_data=lamp_data)
            norm_position = pixel_matrix @ Vector((position[0], position[1], 0))
            logging.debug('\t' + format_vector(norm_position))
            lamp_object.location = panel_matrix @ norm_position
            coll.objects.link(lamp_object)

    logging.info(f"exporting {len(panels)} panels")
    export_json(obj, {'panels': panels}, 'LEDs')

    logging.info(f"*** Completed Light Layout {datetime.now().isoformat()} ***")


if __name__ == '__main__':
    main()

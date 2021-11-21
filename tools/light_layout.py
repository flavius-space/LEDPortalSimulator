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
from functools import reduce
from itertools import starmap
from math import acos, asin, ceil, copysign, floor, inf, isinf, nan, pi, sin, sqrt, cos, atan2, degrees
from pprint import pformat
import traceback
import shutil

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
    from common import (
        X_AXIS_3D, Y_AXIS_3D, Z_AXIS_3D, ENDLTAB, format_matrix,
        format_vector, TRI_VERTS, ATOL, ORIGIN_3D, X_AXIS_2D,
        setup_logger, mode_set, serialise_matrix, export_json,
        get_selected_polygons_suffix, sanitise_names, matrix_isclose,
        format_matrix_components, serialise_vector, format_quaternion,
        format_euler, format_vecs, format_angle, get_out_path
    )
    from trig import gradient_cos, gradient_sin
finally:
    sys.path = PATH

# Defaults

LOG_FILE = os.path.splitext(os.path.basename(THIS_FILE))[0] + '.log'
LED_COLLECTION_NAME = 'LEDs'
DEBUG_COLLECTION_NAME = 'DEBUG'
# TODO: Make this configurable in object properties
VERTEX_ROTATION = 1
VERTEX_ROTATION_OVERRIDE = {}
LED_SPACING = 1.0
LED_MARGIN_VERTICAL_TOP = None
LED_MARGIN_LEFT = None
LED_MARGIN_RIGHT = None
LED_SPACING_VERTICAL = None
EXPORT_TYPE = 'P'
IGNORE_LAMPS = False

# Makex axes in blender match LX
# COORDINATE_TRANSFORM = Matrix([
#     [1, 0, 0, 0],
#     [0, 1, 0, 0],
#     [0, 0, 1, 0],
#     [0, 0, 0, 1],
# ])

# Use processing axes
COORDINATE_TRANSFORM = Matrix([
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 1]
])

# LED_CONFIG = 'LedPortal'
LED_CONFIG = 'TeleCortex'

if LED_CONFIG == 'LedPortal':
    LED_SPACING = 1.22 * 2 / (sqrt(3) * 26)  # = 0.054182102
    WIRING_SERPENTINE = True
    GRID_GRADIENT = sqrt(3)
    LED_MARGIN = abs(gradient_sin(GRID_GRADIENT) * LED_SPACING)
    WIRING_REVERSE = False
    # LED_SPACING_VERTICAL = 1.22 / 26  # = 0.046923077
    # Z_OFFSET = -0.1
    Z_OFFSET = 0
elif LED_CONFIG == 'TeleCortex':
    LED_SPACING = 1.0 / 16
    WIRING_SERPENTINE = True
    LED_SPACING_VERTICAL = 1.0 / 16
    # LED_SPACING_VERTICAL = None
    GRID_GRADIENT = inf
    LED_MARGIN = 0.03
    LED_MARGIN_VERTICAL_TOP = 0.00
    LED_MARGIN_LEFT = 0.03
    LED_MARGIN_RIGHT = 0.03
    WIRING_REVERSE = True
    Z_OFFSET = -0.02


# Telecortex Pixel positions

TELE_POINTS_BIG = [[13, 23], [13, 22], [12, 21], [13, 21], [14, 21], [14, 20], [13, 20], [12, 20], [11, 19], [12, 19], [13, 19], [14, 19], [15, 19], [15, 18], [14, 18], [13, 18], [12, 18], [11, 18], [10, 17], [11, 17], [12, 17], [13, 17], [14, 17], [15, 17], [16, 17], [16, 16], [15, 16], [14, 16], [13, 16], [12, 16], [11, 16], [10, 16], [9, 15], [10, 15], [11, 15], [12, 15], [13, 15], [14, 15], [15, 15], [16, 15], [17, 15], [18, 14], [17, 14], [16, 14], [15, 14], [14, 14], [13, 14], [12, 14], [11, 14], [10, 14], [9, 14], [8, 14], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13], [13, 13], [14, 13], [15, 13], [16, 13], [17, 13], [18, 13], [19, 12], [18, 12], [17, 12], [16, 12], [15, 12], [14, 12], [13, 12], [12, 12], [11, 12], [10, 12], [9, 12], [8, 12], [7, 12], [7, 11], [8, 11], [9, 11], [10, 11], [11, 11], [12, 11], [13, 11], [14, 11], [15, 11], [16, 11], [17, 11], [18, 11], [19, 11], [20, 10], [19, 10], [18, 10], [17, 10], [16, 10], [15, 10], [14, 10], [13, 10], [12, 10], [11, 10], [10, 10], [9, 10], [8, 10], [7, 10], [6, 10], [6, 9], [7, 9], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9], [20, 9], [21, 8], [20, 8], [19, 8], [18, 8], [17, 8], [16, 8], [15, 8], [14, 8], [13, 8], [12, 8], [11, 8], [10, 8], [9, 8], [8, 8], [7, 8], [6, 8], [5, 8], [4, 7], [5, 7], [6, 7], [7, 7], [8, 7], [9, 7], [10, 7], [11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [17, 7], [18, 7], [19, 7], [20, 7], [21, 7], [22, 7], [22, 6], [21, 6], [20, 6], [19, 6], [18, 6], [17, 6], [16, 6], [15, 6], [14, 6], [13, 6], [12, 6], [11, 6], [10, 6], [9, 6], [8, 6], [7, 6], [6, 6], [5, 6], [4, 6], [3, 5], [4, 5], [5, 5], [6, 5], [7, 5], [8, 5], [9, 5], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5], [18, 5], [19, 5], [20, 5], [21, 5], [22, 5], [23, 5], [23, 4], [22, 4], [21, 4], [20, 4], [19, 4], [18, 4], [17, 4], [16, 4], [15, 4], [14, 4], [13, 4], [12, 4], [11, 4], [10, 4], [9, 4], [8, 4], [7, 4], [6, 4], [5, 4], [4, 4], [3, 4], [2, 3], [3, 3], [4, 3], [5, 3], [6, 3], [7, 3], [8, 3], [9, 3], [10, 3], [11, 3], [12, 3], [13, 3], [14, 3], [15, 3], [16, 3], [17, 3], [18, 3], [19, 3], [20, 3], [21, 3], [22, 3], [23, 3], [24, 3], [25, 2], [24, 2], [23, 2], [22, 2], [21, 2], [20, 2], [19, 2], [18, 2], [17, 2], [16, 2], [15, 2], [14, 2], [13, 2], [12, 2], [11, 2], [10, 2], [9, 2], [8, 2], [7, 2], [6, 2], [5, 2], [4, 2], [3, 2], [2, 2], [1, 2], [1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 1], [13, 1], [14, 1], [15, 1], [16, 1], [17, 1], [18, 1], [19, 1], [20, 1], [21, 1], [22, 1], [23, 1], [24, 1], [25, 1], [26, 0], [25, 0], [24, 0], [23, 0], [22, 0], [21, 0], [20, 0], [19, 0], [18, 0], [17, 0], [16, 0], [15, 0], [14, 0], [13, 0], [12, 0], [11, 0], [10, 0], [9, 0], [8, 0], [7, 0], [6, 0], [5, 0], [4, 0], [3, 0], [2, 0], [1, 0], [0, 0]]  # noqa
TELE_POINTS_SMALL = [[13, 19], [13, 18], [12, 17], [13, 17], [14, 17], [14, 16], [13, 16], [12, 16], [11, 15], [12, 15], [13, 15], [14, 15], [15, 15], [16, 14], [15, 14], [14, 14], [13, 14], [12, 14], [11, 14], [10, 14], [9, 13], [10, 13], [11, 13], [12, 13], [13, 13], [14, 13], [15, 13], [16, 13], [17, 13], [17, 12], [16, 12], [15, 12], [14, 12], [13, 12], [12, 12], [11, 12], [10, 12], [9, 12], [8, 11], [9, 11], [10, 11], [11, 11], [12, 11], [13, 11], [14, 11], [15, 11], [16, 11], [17, 11], [18, 11], [19, 10], [18, 10], [17, 10], [16, 10], [15, 10], [14, 10], [13, 10], [12, 10], [11, 10], [10, 10], [9, 10], [8, 10], [7, 10], [7, 9], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9], [20, 8], [19, 8], [18, 8], [17, 8], [16, 8], [15, 8], [14, 8], [13, 8], [12, 8], [11, 8], [10, 8], [9, 8], [8, 8], [7, 8], [6, 8], [5, 7], [6, 7], [7, 7], [8, 7], [9, 7], [10, 7], [11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [17, 7], [18, 7], [19, 7], [20, 7], [21, 7], [21, 6], [20, 6], [19, 6], [18, 6], [17, 6], [16, 6], [15, 6], [14, 6], [13, 6], [12, 6], [11, 6], [10, 6], [9, 6], [8, 6], [7, 6], [6, 6], [5, 6], [4, 5], [5, 5], [6, 5], [7, 5], [8, 5], [9, 5], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5], [18, 5], [19, 5], [20, 5], [21, 5], [22, 5], [23, 4], [22, 4], [21, 4], [20, 4], [19, 4], [18, 4], [17, 4], [16, 4], [15, 4], [14, 4], [13, 4], [12, 4], [11, 4], [10, 4], [9, 4], [8, 4], [7, 4], [6, 4], [5, 4], [4, 4], [3, 4], [3, 3], [4, 3], [5, 3], [6, 3], [7, 3], [8, 3], [9, 3], [10, 3], [11, 3], [12, 3], [13, 3], [14, 3], [15, 3], [16, 3], [17, 3], [18, 3], [19, 3], [20, 3], [21, 3], [22, 3], [23, 3], [24, 2], [23, 2], [22, 2], [21, 2], [20, 2], [19, 2], [18, 2], [17, 2], [16, 2], [15, 2], [14, 2], [13, 2], [12, 2], [11, 2], [10, 2], [9, 2], [8, 2], [7, 2], [6, 2], [5, 2], [4, 2], [3, 2], [2, 2], [1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 1], [13, 1], [14, 1], [15, 1], [16, 1], [17, 1], [18, 1], [19, 1], [20, 1], [21, 1], [22, 1], [23, 1], [24, 1], [25, 1], [26, 0], [25, 0], [24, 0], [23, 0], [22, 0], [21, 0], [20, 0], [19, 0], [18, 0], [17, 0], [16, 0], [15, 0], [14, 0], [13, 0], [12, 0], [11, 0], [10, 0], [9, 0], [8, 0], [7, 0], [6, 0], [5, 0], [4, 0], [3, 0], [2, 0], [1, 0], [0, 0]]  # noqa

OVERRIDES = {
    "fixture": {
        "port": 42069,
        "protocol": 3
    }
}

##########################
# TELECORTEX BACK LAYOUT #
##########################

# This layout consists of 10 small panels and 2 large panels.
# The small panels are arranged in 2 pentagons, bridged by the big panels.
#
# We hand craft the transformations to stitch these panels together in the
# smallest possible quantization grid that attempts to avoid two pixels being mapped to the
# same point.
#
# When creating these transformations, it's important to avoid non-right angle
# rotations and non-integer scale / skews wherever possible.

# Panel Naming:
#          /\``````/\
# .----```/  \ BU /  \```----.
# |`\.SLU/SLIU\  /SRIU\SRU./ |
# |SLO`\/      \/      \/ SRO|
# |   ./\``````/\``````/\.   |
# |./`SLD\SLID/  \SRID/SRD`\.|
# `----___\  / BD \  /___----`
#          \/______\/
#
# Codes:
# - S|B = small / big
# - L|R = left or right pentagon
# - I = inner (close to center of mapping)
# - U|D = up or down
# -> labels, controller info and rotations


def get_back_overrides():
    POLY_OVERRIDES = {
        1: {'fixture': {
            'label': 'SRU 1',
            'host': 'quiet-hill',
            'opcChannel': 1},
            'pixels': TELE_POINTS_SMALL},
        2: {'fixture': {
            'label': 'SLIU 2',
            'host': 'lingering-brook',
            'opcChannel': 1},
            'pixels': TELE_POINTS_SMALL},
        10: {'fixture': {
            'label': 'SLU 10',
            'host': 'still-brook',
            'opcChannel': 0},
            'pixels': TELE_POINTS_SMALL},
        12: {'fixture': {
            'label': 'BU 12',
            'host': 'lingering-brook',
            'opcChannel': 1},
            'pixels': TELE_POINTS_BIG, 'vertex_rotation': 3},
        13: {'fixture': {
            'label': 'SRIU 13',
            'host': 'quiet-hill',
            'opcChannel': 0},
            'pixels': TELE_POINTS_SMALL},
        25: {'fixture': {
            'label': 'SLO 25',
            'host': 'still-brook',
            'opcChannel': 1},
            'pixels': TELE_POINTS_SMALL},
        26: {'fixture': {
            'label': 'SLID 26',
            'host': 'still-brook',
            'opcChannel': 3},
            'pixels': TELE_POINTS_SMALL},
        27: {'fixture': {
            'label': 'BD 27',
            'host': 'lingering-brook',
            'opcChannel': 2},
            'pixels': TELE_POINTS_BIG},
        28: {'fixture': {
            'label': 'SRID 28',
            'host': 'lingering-brook',
            'opcChannel': 3},
            'pixels': TELE_POINTS_SMALL},
        29: {'fixture': {
            'label': 'SRO 29'},
            'pixels': TELE_POINTS_SMALL},
        # TODO: what controller is this?
        36: {'fixture': {
            'label': 'SLD 36',
            'host': 'still-brook',
            'opcChannel': 2},
            'pixels': TELE_POINTS_SMALL},
        37: {'fixture': {
            'label': 'SRD 37',
            'host': 'quiet-hill',
            'opcChannel': 3},
            'pixels': TELE_POINTS_SMALL},
    }

    # -> GEOMETRY

    PIX_WIDTH = 26
    PIX_MID = PIX_WIDTH // 2
    BIG_HEIGHT = 23
    BIG_HYP = sqrt((BIG_HEIGHT * BIG_HEIGHT) + (PIX_MID * PIX_MID))
    BIG_ANGLE = atan2(BIG_HEIGHT, PIX_MID)
    BIG_SIN = sin(BIG_ANGLE)
    BIG_COS = cos(BIG_ANGLE)
    SMALL_HEIGHT = 19
    SMALL_HYP = sqrt((BIG_HEIGHT * BIG_HEIGHT) + (PIX_MID * PIX_MID))
    SMALL_ANGLE = atan2(SMALL_HEIGHT, PIX_MID)
    SMALL_SIN = sin(SMALL_ANGLE)
    SMALL_COS = cos(SMALL_ANGLE)
    # The midpoint height of a unit pentagon (all vertices unit from origin)
    UNIT_PENT_MID_HEIGHT = acos(2 * pi / 10)
    # The side length of a unit pentagon
    UNIT_PENT_SIDE = 2 * asin(2 * pi / 10)
    # The midpoint height of a pentagon with side length = PIX_WIDTH

    # side length of inner small panel in global pixel coords
    INNERSIDE = 22
    # INNERSIDE = 0

    # -> BIG PANELS (BU and BD)
    # these panels' normals are the most orthogonal to the internal grid camera, and
    # so their mapping is a simple scale up by 2. This means that there are extra
    # rows for pixels from other panels that have more squished transforms to use.

    BIG_SCALE = 2

    # --> BU
    POLY_OVERRIDES[12].update({
        "grid_origin": [
            int(PIX_MID * BIG_SCALE),
            int((BIG_HEIGHT * BIG_SCALE) + 1)
        ],
        "grid_matrix": [[-BIG_SCALE, 0], [0, -BIG_SCALE]],
    })
    # --> BD
    POLY_OVERRIDES[27].update({
        "grid_origin": [
            int(-PIX_MID * BIG_SCALE),
            int(-(BIG_HEIGHT * BIG_SCALE) - 1)
        ],
        "grid_matrix": [[BIG_SCALE, 0], [0, BIG_SCALE]],
    })

    logging.debug("-> SMALL PENTAGON VERTICALS (SLU, SLD, SRU, SRD)")
    # to get from an upright small panel to SLD, we can fix the right bottom
    # corner with BD, and skew the other verticies into position.
    # in order to avoid a rotation by a messy skewed-pentagon angle, we instead
    # skew the outer side of the triangle vertically towards the center, and then
    # the vertex at the center of the pentagon is skewed horizontally into place
    # so that it lines up with the outer triangles

    # --> The gradient of the slope of the edges of the pentagon
    PENT_VERT_GRAD = ((BIG_HEIGHT - PIX_MID + 1) / PIX_WIDTH)
    PENT_VERT_SCALE_X = 2
    # the desired height of a midpoint cross-section
    PENT_VERT_MID_HEIGHT = (BIG_SCALE * (BIG_HEIGHT - (PIX_MID * PENT_VERT_GRAD + 1)))
    # the Y scale factor required to scale the top verex to Y = 0
    PENT_VERT_SCALE_Y = (PENT_VERT_MID_HEIGHT / SMALL_HEIGHT)
    logging.debug(f"-> PENT_VERT_SCALE: ({PENT_VERT_SCALE_X}, {PENT_VERT_SCALE_Y})")

    # since the x-component of base of the small outers is dependent on the
    # x-component of base of the pentagon verticals, and the x-component
    # of the top of the pentagon verticals is dependent on the
    # x-component of the top of the small outers, we have to skip ahead a little
    PENT_OUTER_SCALE_Y = 2
    # The distance between the outer edge and the center of a pentagon with side
    # length PIX_WIDTH * PENT_OUTER_SCALE_Y
    PENT_OUTER_MID_DIST = (UNIT_PENT_MID_HEIGHT / UNIT_PENT_SIDE) * PENT_OUTER_SCALE_Y * PIX_WIDTH
    logging.debug(f"-> PENT_OUTER_MID_DIST: {PENT_OUTER_MID_DIST}")
    PENT_OUTER_SCALE_X = PENT_OUTER_MID_DIST / SMALL_HEIGHT
    logging.debug(f"-> PENT_OUTER_SCALE_X: {PENT_OUTER_SCALE_X}")

    # back to pentagon verticals, the x-position of the top vertex needs
    # to be sheard horizontally from `PENT_VERT_SCALE_X * PIX_MID` to
    # `PENT_OUTER_MID_DIST` at a distance of PENT_VERT_MID_HEIGHT
    PENT_VERT_SHEAR_Y = (PENT_OUTER_MID_DIST - (PENT_VERT_SCALE_X * PIX_MID)) / PENT_VERT_MID_HEIGHT
    PENT_VERT_SCALE = Matrix([[PENT_VERT_SCALE_X, 0], [0, PENT_VERT_SCALE_Y]])

    # --> SLD
    POLY_OVERRIDES[36].update({
        "grid_origin": [
            int(POLY_OVERRIDES[27]['grid_origin'][0] - BIG_SCALE - PENT_VERT_SCALE_X * (PIX_WIDTH + 1)),
            int(-PENT_VERT_SCALE_X * (PIX_MID + 1))
        ],
        # "grid_matrix": Matrix([[1, PENT_VERT_SHEAR_Y], [-PENT_VERT_GRAD, 1]]) @ PENT_VERT_SCALE,
        "grid_matrix": Matrix([
            [PENT_VERT_SCALE_X, PENT_VERT_SHEAR_Y * PENT_VERT_SCALE_X],
            [-PENT_VERT_GRAD * PENT_VERT_SCALE_Y, PENT_VERT_SCALE_Y]
        ]),
    })
    # --> SLU
    POLY_OVERRIDES[10].update({
        "grid_origin": [
            int(POLY_OVERRIDES[27]['grid_origin'][0] - BIG_SCALE - PENT_VERT_SCALE_X),
            int(POLY_OVERRIDES[12]['grid_origin'][1])
        ],
        "grid_matrix": Matrix([
            [-PENT_VERT_SCALE_X, PENT_VERT_SHEAR_Y * PENT_VERT_SCALE_X],
            [-PENT_VERT_GRAD * PENT_VERT_SCALE_Y, -PENT_VERT_SCALE_Y]
        ]),
    })
    # --> SRD
    POLY_OVERRIDES[37].update({
        "grid_origin": [
            int(-POLY_OVERRIDES[10]['grid_origin'][0]),
            int(-POLY_OVERRIDES[10]['grid_origin'][1])
        ],
        # "grid_matrix": Matrix([[1, PENT_VERT_SHEAR_Y], [-PENT_VERT_GRAD, 1]]) @ PENT_VERT_SCALE,
        "grid_matrix": Matrix([
            [PENT_VERT_SCALE_X, -PENT_VERT_SHEAR_Y * PENT_VERT_SCALE_X],
            [PENT_VERT_GRAD * PENT_VERT_SCALE_Y, PENT_VERT_SCALE_Y]
        ]),
    })
    # --> SRU
    POLY_OVERRIDES[1].update({
        "grid_origin": [
            int(-POLY_OVERRIDES[10]['grid_origin'][0]),
            int(POLY_OVERRIDES[10]['grid_origin'][1])
        ],
        # "grid_matrix": Matrix([[1, PENT_VERT_SHEAR_Y], [-PENT_VERT_GRAD, 1]]) @ PENT_VERT_SCALE,
        "grid_matrix": Matrix([
            [PENT_VERT_SCALE_X, -PENT_VERT_SHEAR_Y * PENT_VERT_SCALE_X],
            [-PENT_VERT_GRAD * PENT_VERT_SCALE_Y, -PENT_VERT_SCALE_Y]
        ]),
    })


    logging.debug("-> SMALL OUTERS (SLO, SRO)")
    # we rotate by 90 degrees, scale vertically by 2, and horizontally by 1

    # --> SLO
    POLY_OVERRIDES[25].update({
        "grid_origin": [
            POLY_OVERRIDES[36]['grid_origin'][0] - 1,
            (PIX_MID * PENT_OUTER_SCALE_Y)
        ],
        "grid_matrix": [[0, PENT_OUTER_SCALE_X], [-PENT_OUTER_SCALE_Y, 0]],
    })
    # --> SRO
    POLY_OVERRIDES[29].update({
        "grid_origin": [
            -POLY_OVERRIDES[25]['grid_origin'][0],
            -(PIX_MID * PENT_OUTER_SCALE_Y)
        ],
        "grid_matrix": [[0, -PENT_OUTER_SCALE_X], [PENT_OUTER_SCALE_Y, 0]],
    })

    logging.debug("-> SMALL INNERS (SLIU, SLID, SRIU, SRID)")

    # first we scale the triangle to the right size, then we rotate
    # here.

    # we want to scale the height to be PENT_OUTER_MID_DIST
    INNER_SCALE_VERT = (PENT_OUTER_MID_DIST + 1) / SMALL_HEIGHT
    # we want to scale the width of the base to be just less than the side length
    # of a big panel.
    INNER_SCALE_BASE = BIG_SCALE * BIG_HYP / SMALL_HYP
    # a factor factor to shear the top vertex clockwise / counter clockwise
    INNER_NUDGE = 0.2
    INNER_SCALE_MATRIX_CW = Matrix([[INNER_SCALE_BASE, INNER_NUDGE], [0, INNER_SCALE_VERT]])
    INNER_SCALE_MATRIX_CCW = Matrix([[INNER_SCALE_BASE, -INNER_NUDGE], [0, INNER_SCALE_VERT]])

    # --> SLID
    POLY_OVERRIDES[26].update({
        "grid_origin": [
            int(POLY_OVERRIDES[27]['grid_origin'][0] - BIG_SCALE),
            int(POLY_OVERRIDES[27]['grid_origin'][1])
        ],
        "grid_matrix": Matrix.Rotation(BIG_ANGLE, 2, 'Z') @ INNER_SCALE_MATRIX_CW,
    })
    # --> SLIU
    POLY_OVERRIDES[2].update({
        "grid_origin": [
            int(-BIG_SCALE),
            int(1)
        ],
        "grid_matrix": Matrix.Rotation(pi - BIG_ANGLE, 2, 'Z') @ INNER_SCALE_MATRIX_CCW,
    })
    # --> SRID
    POLY_OVERRIDES[28].update({
        "grid_origin": [
            int(-POLY_OVERRIDES[2]['grid_origin'][0]),
            int(-POLY_OVERRIDES[2]['grid_origin'][1])
        ],
        "grid_matrix": Matrix.Rotation( - BIG_ANGLE, 2, 'Z') @ (INNER_SCALE_MATRIX_CCW),
    })
    # --> SRIU
    POLY_OVERRIDES[13].update({
        "grid_origin": [
            int(-POLY_OVERRIDES[26]['grid_origin'][0]),
            int(-POLY_OVERRIDES[26]['grid_origin'][1])
        ],
        "grid_matrix": Matrix.Rotation(-pi + BIG_ANGLE, 2, 'Z') @ (INNER_SCALE_MATRIX_CW),
    })



    return POLY_OVERRIDES

# DELETEME
# EXPORT_TYPE = 'PMIN'
# LED_SPACING = 1.0 / 4
# LED_SPACING_VERTICAL = None
# LED_MARGIN = 0.05
# LED_MARGIN_LEFT = None
# LED_MARGIN_RIGHT = None
# LED_MARGIN_VERTICAL_TOP = None


# def plot_vecs_2d(vecs):
#     logging.info(f"plotting: " + str(vecs))
#     # vecs = [vec.to_2d() for vec in vecs]
#     # logging.info(f"plotting:" + ENDLTAB + ENDLTAB.join(map(format_vector, vecs)))
#     import matplotlib.pyplot as plt
#     plt.plot(*zip(*(vecs + [(0, 0)])), 'o-')
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

    rotation = Matrix.Rotation(-(vecs[1] - vecs[0]).to_2d().angle_signed(X_AXIS_2D), 4, 'Z')
    relative = [rotation @ (vec - vecs[0]) for vec in vecs[1:]]
    logging.debug("Relative:" + ENDLTAB + ENDLTAB.join(map(format_vector, relative)))

    cross = relative[0].cross(relative[1])
    logging.debug("Cross:" + ENDLTAB + format_vector(cross))
    orientation = cross.dot(Z_AXIS_3D)
    logging.debug(f"Orientation: {orientation}")
    return orientation


def compose_matrix_components(components):
    logging.debug(
        f"Matrix Components:" + ENDLTAB + format_matrix_components(components))

    composition = reduce(lambda m, n: m @ n, [
        component_type(*component_args)
        for component_type, component_args in components
    ])
    inv_composition = reduce(lambda m, n: n @ m, [
        component_type(*component_args).inverted()
        for component_type, component_args in components
    ])

    logging.debug(f"Composition / Inverse / Identity Matrix:" + ENDLTAB + ENDLTAB.join([
        format_matrix(matrix) for matrix in [
            composition, inv_composition, composition @ inv_composition]
    ]))

    assert matrix_isclose(composition @ inv_composition, Matrix.Identity(4), atol=ATOL)

    return composition, inv_composition


def plane_flattener(center, normal):
    """
    Form a matrix which will transform all points on the plane defined by `center` and `normal`
    onto the X-Y plane.
    """

    cross_z = normal.cross(Z_AXIS_3D)
    logging.debug(f"Normal cross Z-Axis: {ENDLTAB + format_vector(cross_z)}")
    zenith = normal.angle(Z_AXIS_3D)
    logging.debug(f"Normal angle with Z-axis (Zenith): {zenith}")
    zenith_rotation = Matrix.Rotation(zenith, 3, cross_z).to_4x4()
    logging.debug(f"Zenith Rotation Matrix:" + ENDLTAB + format_matrix(zenith_rotation))
    translation = Matrix.Translation(-center)
    logging.debug(f"Translation Matrix:" + ENDLTAB + format_matrix(translation))
    flattener = zenith_rotation @ translation
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
    lengths = [(flattened[i] - flattened[(i + 1) % TRI_VERTS]).magnitude for i in range(TRI_VERTS)]
    logging.debug(f"Lengths: \n{pformat(lengths)}")
    ratios = [lengths[i] / lengths[(i + 1) % TRI_VERTS] for i in range(TRI_VERTS)]
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
    angle_x = (oriented[1] - oriented[0]).to_2d().angle_signed(X_AXIS_2D)
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

    axis_full_name = f"{axis_name if axis_name else ''} axis"

    usable = axis_length - margin_left - margin_right
    lines = float_floor(usable / spacing) + 1
    usage = spacing * (lines - 1)

    logging.debug(
        f"{axis_full_name} Usable / Lines / Usage: {usable: 7.3f} / {lines} / {usage: 7.3f}")

    assert \
        usage < usable \
        or np.isclose(usable - usage, 0, atol=ATOL), \
        f"{axis_full_name} usage {usage} >= usable {usable}"
    padding = (usable - (spacing * (lines - 1))) / 2

    logging.debug(f"{axis_full_name} Padding: {padding: 7.3f}")

    return lines, padding


def intersect_lines(m1, c1, m2, c2):
    """
    line 1 = m1 * x + c1, (c1 is x-intercept in case of inf gradient)
    line 2 = m2 * x + c2, (c2 is x-intercept in case of inf gradient)
    """
    if isinf(m1) and isinf(m2):
        return None, None
    if isinf(m1):
        return c1, m2 * c1 + c2
    elif isinf(m2):
        return c2, m1 * c2 + c1
    elif np.isclose(m1, m2, atol=ATOL):
        return None, None
    intersect_x = (c2 - c1) / (m1 - m2)
    intersect_y = m1 * intersect_x + c1
    return intersect_x, intersect_y


def margin_intersect_offset(gradient_left, gradient_right, base_width, margin):
    r"""
             mL       <- gradient left
        mR  /         <- gradient right
         \ /\/        <- margin
          x-/----     <- regular intersect
         / \    |     <- intersect offset
        / x-\----     <- margin intersect
       / / \ \
      / /   \ \
     /_/_____\_\_____
    o_/_______\_o___| <- margin
    |<--------->|     <- base width

    OR

                         mL  <- gradient left
                    mR  /    <- gradient right
                    | /
                    x----    <- regular intersect
                  / |   |    <- intersect offset
                / x-|----    <- margin intersect
              / / | |
            / /   | |
          /_/_____|_|___
        o_/_______|_o___|    <- margin
        |<--------->|        <- base width
    """

    logging.debug(
        f"Gradient Left / Right: "
        f"{gradient_left: 7.3f} / {gradient_right: 7.3f}")

    if isinf(gradient_left) and isinf(gradient_right):
        return None

    if np.isclose(gradient_left, gradient_right, atol=ATOL):
        return None

    regular_axis_intercept_left = 0
    regular_axis_intercept_right = base_width if isinf(gradient_right) else \
        - base_width * gradient_right

    logging.debug(
        f"Regular Axis Intercept Left / Right: "
        f"{regular_axis_intercept_left: 7.3f} / {regular_axis_intercept_right:7.3f}")

    regular_intersect_x, regular_intersect_y = intersect_lines(
        gradient_left, regular_axis_intercept_left, gradient_right, regular_axis_intercept_right
    )

    if regular_intersect_x is None or regular_intersect_y is None:
        return None

    logging.debug(
        f"Regular Intersect X / Y: "
        f"{regular_intersect_x: 7.3f} / {regular_intersect_y:7.3f}")

    margin_axis_intercept_left = margin if isinf(gradient_left) else \
        - abs(margin / gradient_cos(gradient_left))
    margin_axis_intercept_right = base_width - margin if isinf(gradient_right) else \
        regular_axis_intercept_right - abs(margin / gradient_cos(gradient_right))

    logging.debug(
        f"Margin Axis Intercept Left / Right: "
        f"{margin_axis_intercept_left: 7.3f} / {margin_axis_intercept_right:7.3f}")

    margin_intersect_x, margin_intersect_y = intersect_lines(
        gradient_left, margin_axis_intercept_left, gradient_right, margin_axis_intercept_right
    )

    logging.debug(
        f"Margin Intersect X / Y: "
        f"{margin_intersect_x: 7.3f} / {margin_intersect_y:7.3f}")

    return regular_intersect_y - margin_intersect_y


def generate_lights_for_convex_polygon(
        base_width: float,
        quad_right_x: float,
        quad_right_height: float,
        quad_left_x: float,
        quad_left_height: float,
        spacing: float,
        spacing_vertical: float = None,
        grid_gradient: float = inf,
        margin: float = 0.0,
        margin_vertical_top: float = None,
        margin_left: float = None,
        margin_right: float = None,
        z_offset: float = 0.0,
        wiring_serpentine: bool = True,
        wiring_reverse: bool = None
):
    r"""
    Geometric Assumptions:
        all points are in the same coordinate system
        all points are coplanar
        polygon has already been flattened and normalised (see normalise_plane)
        points 0, 1, 2 and -1 are convex
        points form a triangle or quadrangle
        point 0 is at origin (0, 0)
        point 1 is on y axis, right of base line (base_width, 0)
        point 2 is top right of quad (quad_right_x, quad_right_height)
        point -1 is top left of quad (quad_left_x, quad_left_height)


                          mL                            <- left gradient
                         /         mR                   <- right gradient
                        /           \      mG           <- grid gradient
                       /             \    /
               |<- horizontal start width -->|
               |     /                 \     |             P-1: (quad left x, quad left height)
               |    o(P-1)__________(P2)o    |          <- P2: (quad right x, quad right height)
               |   / / /__|(Mv)______/ \ \   |          <- Mv: vertical margin
               |  / / /___|(pv)_____/_\_\_\__|__
               | / / /* * * * * * */* *\_\_\_|__|(sv)   <- sv: vertical spacing
               |/ / /* * * * * * */* * *\ \ \|
               o_/_o(PS)*_*_*_*_*/*_*_*_*\_\_o          <- PS: (horizontal_start, vertical_start);
              /_/_/_______|(pv)___|_|_____\_\_\         <- Pv: vertical padding
         (P0)o_/_/________|(Mv)___|_|______\_\_o(P1)    <- P0: (0,0); P1: (base_width, 0)
             | | |                |-|(s)   | | |        <- s: spacing
             | | |                         | | |           Ml: left margin
         (Ml)|-| |                         | |-|(Mr)    <- Mr: right margin
           (ph)|-|                         |-|(ph)      <- ph: horizontal padding

    Args:
        base_width (float): distance between (0)->(1)
        quad_right_x (float):
        quad_right_height (float):
        quad_left_x (float):
        quad_left_height (float):
        spacing (float):
        z_offset (float):
        margin (float): minimum spacing between polygon edges and pixels, default: 0.0
        wiring_serpentine (bool): pixels alternate direction between each row, default: True
        grid_gradient (bool): determines how much each line of pixels is offset from the last. Inf
            graadient means grid axes are 90 degrees

    TODO:
    - handle other polygon types
    """
    logging.debug(
        f"Spacing: {spacing: 7.3f}\n"
        f"Z Height: {z_offset: 7.3f}\n"
        f"Margin: {margin: 7.3f}\n"
        f"Grid Gradient: {grid_gradient: 7.3f}"
    )
    height = max([quad_left_height, quad_right_height])
    logging.debug(f"Width (Base) / Height: {base_width: 7.3f} / {height: 7.3f}")
    logging.debug(
        f"Quad Left / Right (x, height): "
        f"({quad_left_x: 7.3f}, {quad_left_height: 7.3f})"
        f"({quad_right_x: 7.3f}, {quad_right_height: 7.3f})")
    gradient_left = inf_divide(quad_left_height, quad_left_x)
    gradient_right = inf_divide(quad_right_height, quad_right_x - base_width)
    logging.debug(
        f"Left / Right / Grid Gradients: "
        f"{gradient_left: 7.3f} / {gradient_right: 7.3f} / {grid_gradient: 7.3f}")
    if spacing_vertical is None:
        spacing_vertical = abs(gradient_sin(grid_gradient) * spacing)
    spacing_shear = abs(gradient_cos(grid_gradient) * spacing)
    logging.debug(
        f"Horizontal / Vertical / Shear Spacing: "
        f"{spacing: 7.3f} / {spacing_vertical: 7.3f} / {spacing_shear: 7.3f}")

    if margin_vertical_top is None:
        margin_vertical_top = margin_intersect_offset(
            gradient_left, gradient_right, base_width, margin) or margin

    logging.debug(f"Vertical / Top Margin: {margin: 7.3f} / {margin_vertical_top: 7.3f}")

    vertical_lines, vertical_padding = axis_centered_lines(
        height, spacing_vertical, margin, margin_vertical_top, axis_name="Vertical")
    vertical_start = margin + vertical_padding

    if margin_left is None:
        margin_left = abs(margin / gradient_sin(gradient_left))
    if margin_right is None:
        margin_right = abs(margin / gradient_sin(gradient_right))
    logging.debug(f"Left / Right Margin: {margin_left: 7.3f} / {margin_right: 7.3f}")

    horizontal_start_width = base_width \
        - inf_divide(vertical_start, gradient_left) \
        + inf_divide(vertical_start, gradient_right)

    horizontal_lines, horizontal_padding = axis_centered_lines(
        horizontal_start_width, spacing, margin_left, margin_right, axis_name="Horizontal")
    horizontal_usage = spacing * (horizontal_lines - 1)
    horizontal_start = margin_left + inf_divide(vertical_start, gradient_left) + horizontal_padding

    lights = []
    for vertical_idx in range(vertical_lines):
        logging.debug(f"Vertical Index: {vertical_idx}")
        # relative to pixel origin: (horizontal_start, vertical_start)
        pixel_y_relative = (vertical_idx * spacing_vertical)
        pixel_y_absolute = pixel_y_relative + vertical_start
        logging.debug(
            f"Pixel Y Relative / Absolute: {pixel_y_relative: 7.3f} {pixel_y_absolute: 7.3f}")
        # x coordinate where row intesects with grid y-axis
        row_grid_origin_x = inf_divide(pixel_y_relative, grid_gradient)
        logging.debug(f"Row Grid Origin X: {row_grid_origin_x: 7.3f}")

        row_start_relative = inf_divide(pixel_y_relative, gradient_left)
        row_grid_start = float_abs_ceil((row_start_relative - row_grid_origin_x) / spacing)

        row_end_relative = horizontal_usage + inf_divide(pixel_y_relative, gradient_right)
        row_grid_end = float_abs_floor((row_end_relative - row_grid_origin_x) / spacing)

        logging.debug(
            f"Row Start / End Relative: {row_start_relative: 7.3f} / {row_end_relative: 7.3f}")
        logging.debug(f"Row Grid Start / End: {row_grid_start} / {row_grid_end}")

        # Sanity check:
        row_capacity = abs(row_end_relative - row_start_relative)
        row_usage = max(row_grid_end - row_grid_start - 1, 0) * spacing
        logging.debug(f"Row Capacity / Usage: {row_capacity: 7.3f} / {row_usage: 7.3f}")
        assert \
            row_usage < row_capacity \
            or np.isclose(row_capacity - row_usage, 0, atol=ATOL), \
            f"Row usage {row_usage} >= capacity {row_capacity}"

        row = []
        if row_grid_end >= row_grid_start:
            for horizontal_idx in range(row_grid_start, row_grid_end + 1):
                row.append((horizontal_idx, vertical_idx))

        if wiring_serpentine and vertical_idx % 2:
            row = list(reversed(row))
        logging.debug(f"Row ({len(row)}): {row}")

        lights.extend(row)
    if wiring_reverse:
        lights = list(reversed(lights))
    logging.debug(f"Lights (Norm):" + ENDLTAB + ENDLTAB.join(map(repr, lights)))

    # Calculate transformation matrix and inverse

    geometry_info = {
        'translation': Vector([horizontal_start, vertical_start, z_offset]),
        'spacing': [spacing, spacing_vertical, spacing_shear],
    }

    geometry_info['transformation_components'] = [
        (Matrix.Translation, [geometry_info['translation']]),
        (Matrix.Scale, [gradient_sin(grid_gradient), 4, Y_AXIS_3D]),
        (Matrix.Shear, ['XZ', 4, (gradient_cos(grid_gradient), 0)]),
        (Matrix.Scale, [spacing, 4]),
    ]

    geometry_info['transformation'], geometry_info['inv_transformation'] = \
        compose_matrix_components(geometry_info['transformation_components'])

    return geometry_info, lights


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
        assert np.isclose(apex_x, base_width / 2, atol=ATOL), \
            f"Apex X {apex_x} should be half of Local Width {base_width} for tri-type {tri_type}"

    return flattener.inverted() @ normaliser.inverted(), normalised


def lx_decompose(matrix, basis_transform=None, debug_coll=None):
    """
    Given `matrix` and `basis_transform`, decompose `matrix` into its translation and Trait-Bryan
    (roll, pitch, yaw) angles.

    `matrix`:
    - is a transformation from X-Y-Z Basis to X-Y-Z Prime
    - could contain a translation component
    - could contain a rotation component
    - could contain a shear in the Y Axis along the X axis

    and `basis transform`:
    - is a transformation from X-Y-Z to X-Y-Z Basis
    - Has no scale / shear

    @return
    - `matrix` 's translation component
    - `matrix` 's Tait–Bryan Yaw: A rotation of Psi about the Z axis in degrees
    - `matrix` 's Tait–Bryan Pitch: A rotation of Theta about the Y axis in degrees
    - `matrix` 's Tait–Bryan Roll: A rotation of Phi about the X axis in degrees

    See https://upload.wikimedia.org/wikipedia/commons/5/53/Taitbrianzyx.svg
    """

    if basis_transform is None:
        basis_transform = Matrix.Identity(4)

    matrix = matrix @ basis_transform
    logging.debug(f"matrix: {format_matrix(matrix)}")
    euler = matrix.to_euler()
    logging.debug(f"euler: {format_euler(euler)}")
    quaternion = matrix.to_quaternion()
    logging.debug(f"quaternion: {format_quaternion(quaternion)}")

    orig = matrix @ ORIGIN_3D
    logging.debug(f"orig: {format_vector(orig)}")

    x_prime = matrix @ X_AXIS_3D - orig
    logging.debug(f"x_prime: {format_vector(x_prime)}")
    y_prime = matrix @ Y_AXIS_3D - orig
    logging.debug(f"y_prime: {format_vector(y_prime)}")
    z_prime = matrix @ Z_AXIS_3D - orig
    logging.debug(f"z_prime: {format_vector(z_prime)}")

    x_basis = basis_transform @ X_AXIS_3D
    logging.debug(f"x_basis: {format_vector(x_basis)}")
    y_basis = basis_transform @ Y_AXIS_3D
    logging.debug(f"y_basis: {format_vector(y_basis)}")
    z_basis = basis_transform @ Z_AXIS_3D
    logging.debug(f"z_basis: {format_vector(z_basis)}")

    # Calculate Tait–Bryan angles which are:
    # - Used to create a transformation from X-Y-Z Basis to X-Y-Z Prime composed of:
    #   - Yaw: A rotation about the Z axis by Psi
    #   - Pitch: A rotation about the Y axis by Theta
    #   - Roll: A rotation about the X axis by Phi

    # Calculate X Projected, which is:
    # - X Prime projected onto the X-Y Basis plane.
    # - The X axis after the first Yaw rotation about the Z-axis
    # - Nodes Perpendicular on the diagram
    x_proj = Vector((
        x_prime.dot(x_basis) / x_basis.magnitude,
        x_prime.dot(y_basis) / y_basis.magnitude,
        0
    ))
    logging.debug(f"x_proj: {format_vector(x_proj)}")

    # Calculate Psi / Yaw, which is:
    # - The rotation about the Z axis.
    # - The angle between X Projected and X Basis
    # - atan2(y, x) where:
    #   - y is the component of X prime in the X basis,
    #   - x is the component of X prime in the Y basis,
    yaw = atan2(
        x_prime.dot(y_basis) / y_basis.magnitude,
        x_prime.dot(x_basis) / x_basis.magnitude
    )
    logging.debug(f"yaw: {format_angle(yaw)}")
    yaw_quat = x_basis.rotation_difference(x_proj)
    logging.debug(f"yaw_quat: {format_quaternion(yaw_quat)}")

    # Calculate the First Intermediate positions, which are:
    # - The position of the X-Y-Z Axies after the first Yaw translation
    x_inter_1 = yaw_quat @ x_basis
    logging.debug(f"x_inter_1: {format_vector(x_inter_1)}")
    y_inter_1 = yaw_quat @ y_basis
    logging.debug(f"y_inter_1: {format_vector(y_inter_1)}")
    z_inter_1 = yaw_quat @ z_basis
    logging.debug(f"z_inter_1: {format_vector(z_inter_1)}")

    # Calculate Theta / Pitch, which is:
    # - The angle between X Prime and X Projected
    # - atan2(y, x) where:
    #   - y is the component of X prime in the Z basis
    #   - x is the component of X prime in the X-Y basis plane (X Projected),
    pitch = atan2(
        - x_prime.dot(z_basis) / z_basis.magnitude,
        x_proj.magnitude
    )
    logging.debug(f"pitch: {format_angle(pitch)}")
    pitch_quat = x_proj.rotation_difference(x_prime)
    logging.debug(f"pitch_quat: {format_quaternion(pitch_quat)}")

    # Calculate the Second Intermediate positions, which are:
    # - The position of the X-Y-Z Axies after the Yaw and Pitch translation
    x_inter_2 = pitch_quat @ x_inter_1
    logging.debug(f"x_inter_2: {format_vector(x_inter_2)}")
    y_inter_2 = pitch_quat @ y_inter_1
    logging.debug(f"y_inter_2: {format_vector(y_inter_2)}")
    z_inter_2 = pitch_quat @ z_inter_1
    logging.debug(f"z_inter_2: {format_vector(z_inter_2)}")

    # Calculate Z Intermediate, which is:
    # - The position of the Z Axis after the Yaw and Pitch translations
    # - Not affected by yaw
    z_inter = pitch_quat @ z_basis
    logging.debug(f"z_inter: {format_vector(z_inter)}")

    # Calculate Phi / Roll, which is:
    # - The angle between Z Prime and Z Intermediate
    # - The angle between (-X Prime x Z Prime) and Y Intermediate

    roll_quat = z_inter.rotation_difference(z_prime)
    roll = roll_quat.angle
    if roll_quat.axis.dot(x_prime) < 0:
        roll = -roll
    logging.debug(f"roll: {format_angle(roll)}")
    logging.debug(f"roll_quat: {format_quaternion(roll_quat)}")

    roll_quat_y = (y_inter_1).rotation_difference(-x_prime.cross(z_prime))
    roll_y = roll_quat_y.angle
    if roll_quat_y.axis.dot(x_prime) > 0:
        roll_y = -roll_y
    logging.debug(f"roll_y: {format_angle(roll_y)}")
    logging.debug(f"roll_quat_y: {format_quaternion(roll_quat)}")

    # Calculate the Second Intermediate positions, which are:
    # - The position of the X-Y-Z Axies after the Yaw and Pitch translation
    x_inter_3 = roll_quat @ x_inter_2
    logging.debug(f"x_inter_3: {format_vector(x_inter_3)}")
    y_inter_3 = roll_quat @ y_inter_2
    logging.debug(f"y_inter_3: {format_vector(y_inter_3)}")
    z_inter_3 = roll_quat @ z_inter_2
    logging.debug(f"z_inter_3: {format_vector(z_inter_3)}")

    # Sanity check:

    rotation_components = [
        (Matrix.Rotation, [yaw, 4, 'Z']),
        (Matrix.Rotation, [pitch, 4, 'Y']),
        (Matrix.Rotation, [roll, 4, 'X']),
    ]

    rotation, _ = compose_matrix_components(rotation_components)

    orig_sanity = rotation @ ORIGIN_3D
    logging.debug(f"orig_sanity: {format_vector(orig_sanity)}")
    x_prime_sanity = rotation @ X_AXIS_3D - orig_sanity
    logging.debug(f"x_prime_sanity: {format_vector(x_prime_sanity)}")
    y_prime_sanity = rotation @ Y_AXIS_3D - orig_sanity
    logging.debug(f"y_prime_sanity: {format_vector(y_prime_sanity)}")
    z_prime_sanity = rotation @ Z_AXIS_3D - orig_sanity
    logging.debug(f"z_prime_sanity: {format_vector(z_prime_sanity)}")

    if debug_coll:
        with mode_set('OBJECT'):
            for name, point in [
                ("x_basis", x_basis.normalized()),
                ("y_basis", y_basis.normalized()),
                ("z_basis", z_basis.normalized()),
                ("x_prime", x_prime.normalized()),
                ("y_prime", y_prime.normalized()),
                ("z_prime", z_prime.normalized()),
                ("x_proj", x_proj.normalized()),
                ("x_inter_1", x_inter_1.normalized()),
                ("y_inter_1", y_inter_1.normalized()),
                ("z_inter_1", z_inter_1.normalized()),
                ("x_inter_2", x_inter_2.normalized()),
                ("y_inter_2", y_inter_2.normalized()),
                ("z_inter_2", z_inter_2.normalized()),
                ("x_inter_3", x_inter_3.normalized()),
                ("y_inter_3", y_inter_3.normalized()),
                ("z_inter_3", z_inter_3.normalized()),
                ("z_inter", z_inter.normalized()),
                ("yaw_quat", yaw_quat.axis),
                ("pitch_quat", pitch_quat.axis),
                ("roll_quat", roll_quat.axis),
                ("x_prime_sanity", x_prime_sanity.normalized()),
                ("y_prime_sanity", y_prime_sanity.normalized()),
                ("z_prime_sanity", z_prime_sanity.normalized()),
            ]:
                debug_verts = [
                    orig,
                    point + orig
                ]
                debug_edges = [
                    (0, 1)
                ]
                debug_mesh = bpy.data.meshes.new(f"mesh_{name}")
                debug_mesh.from_pydata(debug_verts, debug_edges, [])
                debug_obj = bpy.data.objects.new(name, debug_mesh)
                debug_coll.objects.link(debug_obj)

    assert np.isclose(cos(yaw), cos(yaw_quat.angle), atol=ATOL)
    assert np.isclose(cos(pitch), cos(pitch_quat.angle), atol=ATOL)
    assert np.isclose(cos(roll), cos(roll_quat.angle), atol=ATOL)

    try:
        assert all(np.isclose(x_inter_3.normalized(), x_prime_sanity.normalized(), atol=ATOL))
        assert all(np.isclose(y_inter_3.normalized(), y_prime_sanity.normalized(), atol=ATOL))
        assert all(np.isclose(z_inter_3.normalized(), z_prime_sanity.normalized(), atol=ATOL))
    except AssertionError:
        traceback.print_exc()

    assert all(np.isclose(x_prime.normalized(), x_prime_sanity.normalized(), atol=ATOL))
    # The following is not true if shear is applied
    # assert all(np.isclose(y_prime.normalized(), y_prime_sanity.normalized(), atol=ATOL))
    assert all(np.isclose(z_prime.normalized(), z_prime_sanity.normalized(), atol=ATOL))

    angles = list(map(degrees, [yaw, pitch, roll]))
    logging.debug(f"angles (degrees) yaw / pitch / roll: {angles}")

    return (orig, *angles)


def transform_grid_pixels(pixels, grid_origin, grid_matrix):
    mat = Matrix(serialise_matrix(grid_matrix))
    orig = Vector(grid_origin)
    return [
        map(int, orig + (mat @ Vector(pixel)))
        for pixel in pixels
    ]


def debug_grid_info(grid_info):
    import matplotlib.pyplot as plt
    plt, ax = plt.subplots()
    for label, info in grid_info.items():
        grid_pixels = transform_grid_pixels(
            info.get('pixels', [[0, 0]]),
            info.get('grid_origin', [0, 0]),
            info.get("grid_matrix", [[1, 0], [0, 1]])
        )
        ax.plot(*zip(*grid_pixels), 'o-', label=label, markersize=1, linewidth=0.5)

    handles, labels = ax.get_legend_handles_labels()
    logging.info(labels)

    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5))
    # plt.show()
    ax.axis('scaled')
    plt.savefig("/tmp/mapping.png", dpi=1000)
    shutil.move('/tmp/mapping.png', 'mapping.png')


def main():
    setup_logger(LOG_FILE)

    logging.info(f"*** Starting Light Layout ***")
    obj = bpy.context.object
    logging.info(f"Selected object: {obj.name}")
    logging.debug(f"Object World Matrix:" + ENDLTAB + format_matrix(obj.matrix_world))
    inv_coordinate_transform = COORDINATE_TRANSFORM.inverted()
    world_matrix = COORDINATE_TRANSFORM @ obj.matrix_world
    logging.debug(f"Transformed World Matrix:" + ENDLTAB + format_matrix(world_matrix))
    with mode_set('OBJECT'):
        if not IGNORE_LAMPS:
            bpy.ops.object.delete({
                "selected_objects": bpy.data.collections[LED_COLLECTION_NAME].all_objects})
        if DEBUG_COLLECTION_NAME in bpy.data.collections:
            bpy.ops.object.delete({
                "selected_objects": bpy.data.collections[DEBUG_COLLECTION_NAME].all_objects})
        led_coll = bpy.data.collections[LED_COLLECTION_NAME]
        # debug_coll = bpy.data.collections[DEBUG_COLLECTION_NAME]
        debug_coll = None

    panels = []
    fixtures = []

    selected_polygon_enum, suffix = get_selected_polygons_suffix(obj, EXPORT_TYPE)

    # ALL_GRID_PIXELS = []
    grid_info = {}

    POLY_OVERRIDES = get_back_overrides()

    for poly_idx, polygon in selected_polygon_enum:

        poly_overrides = {**OVERRIDES, **POLY_OVERRIDES.get(poly_idx, {})}
        poly_fix_overrides = {
            **OVERRIDES.get('fixture'),
            **POLY_OVERRIDES.get(poly_idx, {}).get('fixture', {})
        }

        name = f"{sanitise_names(obj.name)}.{EXPORT_TYPE}[{poly_idx}]"
        logging.info(f"polygon name: {name}")

        panel = {
            'name': name
        }

        fixture = {
            "id": poly_idx + 1,
            "class": "flavius.ledportal.structure.LPPanelFixture",
            "parameters": {
                "label": name,
            },
        }

        world_center = world_matrix @ polygon.center
        logging.debug(
            f"Center (local / world):" + ENDLTAB + format_vecs(polygon.center, world_center))
        world_normal = (world_matrix @ polygon.normal) - (world_matrix @ ORIGIN_3D)
        logging.debug(
            f"Normal (local / world):" + ENDLTAB + format_vecs(polygon.normal, world_normal))
        logging.debug(f"Vertex IDs:" + ENDLTAB + pformat(list(polygon.vertices)))
        vertices = [obj.data.vertices[vertex_id].co for vertex_id in polygon.vertices]
        world_vertices = [world_matrix @ vertex for vertex in vertices]
        logging.debug(
            f"Vertices (local / world):" + ENDLTAB + ENDLTAB.join(
                starmap(format_vecs, zip(vertices, world_vertices))))

        vertex_rotation = VERTEX_ROTATION
        if 'vertex_rotation' in poly_overrides:
            logging.debug(f"overriding vertex_rotation ({vertex_rotation})")
            vertex_rotation = poly_overrides['vertex_rotation']

        world_vertices = rotate_seq(world_vertices, vertex_rotation)

        panel_matrix, panel_vertices = normalise_plane(
            world_center, world_normal, world_vertices
        )

        info, pixels = generate_lights_for_convex_polygon(
            panel_vertices[1].x,
            panel_vertices[2].x,
            panel_vertices[2].y,
            panel_vertices[-1].x,
            panel_vertices[-1].y,
            spacing=LED_SPACING,
            spacing_vertical=LED_SPACING_VERTICAL,
            grid_gradient=GRID_GRADIENT,
            margin=LED_MARGIN,
            margin_vertical_top=LED_MARGIN_VERTICAL_TOP,
            margin_left=LED_MARGIN_LEFT,
            margin_right=LED_MARGIN_RIGHT,
            wiring_serpentine=WIRING_SERPENTINE,
            wiring_reverse=WIRING_REVERSE,
            z_offset=Z_OFFSET,
        )

        if 'pixels' in poly_overrides:
            logging.debug(f"overriding pixels ({pixels})")
            pixels = poly_overrides['pixels']

        grid_origin = [0, 0]
        if 'grid_origin' in poly_overrides:
            logging.debug(f"overriding grid_origin ({grid_origin})")
            grid_origin = poly_overrides['grid_origin']

        grid_matrix = [[1, 0], [0, 1]]
        if 'grid_matrix' in poly_overrides:
            logging.debug(f"overriding grid_matrix ({grid_matrix})")
            grid_matrix = poly_overrides['grid_matrix']

        panel['spacing'] = info['spacing']
        fixture['parameters']['rowSpacing'] = info['spacing'][0]
        fixture['parameters']['columnSpacing'] = info['spacing'][1]
        fixture['parameters']['rowShear'] = info['spacing'][2]

        panel_pixel_matrix = panel_matrix @ info['transformation']

        panel_loc, panel_yaw, panel_pitch, panel_roll = \
            lx_decompose(panel_pixel_matrix, debug_coll=debug_coll)
        panel['location'] = serialise_vector(panel_loc)
        fixture['parameters']['x'] = panel_loc.x
        fixture['parameters']['y'] = panel_loc.y
        fixture['parameters']['z'] = panel_loc.z
        panel['pitch'] = panel_pitch
        fixture['parameters']['pitch'] = panel_pitch
        panel['yaw'] = panel_yaw
        fixture['parameters']['yaw'] = panel_yaw
        panel['roll'] = panel_roll
        fixture['parameters']['roll'] = panel_roll

        panel['matrix'] = serialise_matrix(panel_pixel_matrix)
        panel['pixels'] = serialise_matrix(pixels)
        fixture['parameters']['pointIndicesJSON'] = repr(serialise_matrix(pixels)).replace(' ', '')
        fixture['parameters']['globalGridMatrix'] = repr(
            serialise_matrix(grid_matrix)).replace(' ', '')
        fixture['parameters']['globalGridOriginX'] = grid_origin[0]
        fixture['parameters']['globalGridOriginY'] = grid_origin[1]

        panel_pixel_vertices = [
            info['inv_transformation'] @ vertex for vertex in panel_vertices
        ]
        panel['vertices'] = serialise_matrix(panel_pixel_vertices)

        panels.append(panel)

        fixture['parameters'].update(poly_fix_overrides)
        fixtures.append(fixture)

        grid_info[fixture['parameters']['label']] = {
            'pixels': pixels,
            'grid_origin': grid_origin,
            'grid_matrix': grid_matrix
        }

        if IGNORE_LAMPS:
            continue

        logging.info(f"adding {len(pixels)} lights to scene")

        logging.debug("Lights (Norm):")

        for light_idx, position in enumerate(pixels):
            name = f"LED {poly_idx:4d} {light_idx:4d}"
            lamp_data = bpy.data.lights.new(name=f"{name} data", type='POINT')
            lamp_data.energy = 1.0
            lamp_object = bpy.data.objects.new(name=f"{name} object", object_data=lamp_data)
            norm_position = info['transformation'] @ Vector((position[0], position[1], 0))
            logging.debug('\t' + format_vector(norm_position))
            lamp_object.location = inv_coordinate_transform @ panel_matrix @ norm_position
            led_coll.objects.link(lamp_object)

    logging.info(f"exporting {len(panels)} {EXPORT_TYPE.lower()}")
    export_json(get_out_path(obj, suffix), {EXPORT_TYPE.lower(): panels})
    export_json(get_out_path(obj, suffix, 'lxm'), {'fixtures': fixtures})

    logging.info(f"*** Completed Light Layout ***")

    debug_grid_info(grid_info)


if __name__ == '__main__':
    main()

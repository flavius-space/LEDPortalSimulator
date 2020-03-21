from contextlib import contextmanager
import bpy
from math import nan
from mathutils import Vector
import coloredlogs
import json
import re
from pprint import pformat
import logging
import os

Z_AXIS_3D = Vector((0, 0, 1))
X_AXIS_2D = Vector((1, 0))
TRI_VERTS = 3
ENDLTAB = "\n\t"
ATOL = 1e-4
LOG_STREAM_FMT = "%(asctime)s %(levelname)s %(message)s"
DATA_PATH = 'LEDPortalSimulator/data'


@contextmanager
def mode_set(mode):
    prev_mode = bpy.context.object.mode
    try:
        bpy.ops.object.mode_set(mode=mode)
        yield
    finally:
        bpy.ops.object.mode_set(mode=prev_mode)


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


def format_matrix(mat, name="Matrix", indent=1):
    loc, rot, scale = mat.decompose()
    out = '\n'.join([
        f"{name} Full:" + ENDLTAB + pformat(mat).replace('\n', '\n\t'),
        f"{name} Location:" + ENDLTAB + pformat(loc).replace('\n', '\n\t'),
        f"{name} Rotation:" + ENDLTAB + pformat(rot).replace('\n', '\n\t'),
        f"{name} Scale:" + ENDLTAB + pformat(scale).replace('\n', '\n\t'),
    ])
    return out.replace('\n', ('\n' + (indent * '\t')))


def setup_logger(log_file):
    logger = logging.getLogger()
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_file, 'w')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    if os.name != 'nt':
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(coloredlogs.ColoredFormatter(LOG_STREAM_FMT))
        logger.addHandler(stream_handler)


def serialise_vector(vec):
    return vec[:]


def serialise_matrix(mat):
    return [serialise_vector(vec) for vec in mat]


def export_json(obj, panels):
    model_name, _ = os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))
    obj_name = obj.name
    sanitised, _ = re.subn(r"\W+", "_", f"{model_name}_{obj_name}")
    sanitised = os.path.join(DATA_PATH, f"{sanitised}.json")
    logging.info(f"exporting to {sanitised}")
    with open(sanitised, 'w') as stream:
        json.dump({'panels': panels}, stream, indent=4)

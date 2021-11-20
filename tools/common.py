import itertools
import json
import logging
import os
import re
from contextlib import contextmanager
from math import degrees, nan
from pprint import pformat

import bpy
import coloredlogs
import numpy as np
from mathutils import Vector

ORIGIN_3D = Vector((0, 0, 0))
X_AXIS_3D = Vector((1, 0, 0))
Y_AXIS_3D = Vector((0, 1, 0))
Z_AXIS_3D = Vector((0, 0, 1))
X_AXIS_2D = Vector((1, 0))
TRI_VERTS = 3
QUAD_VERTS = 4
ENDLTAB = "\n\t"
ATOL = 1e-3
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


def matrix_isclose(a, b, *args, **kwargs):
    return all(np.isclose(
        list(itertools.chain(*a)),
        list(itertools.chain(*b)),
        *args,
        **kwargs
    ))


def format_vector(vec):
    """
    C => Cartesian (x, y, z)
    S => Spherical (r, θ, ɸ)
    P => Polar (r, θ)
    """
    mag = vec.magnitude
    if len(vec) == 3:
        theta = vec.to_2d().angle_signed(X_AXIS_2D) if vec.to_2d().magnitude > 0 else nan
        phi = vec.angle(Z_AXIS_3D) if mag > 0 else nan
        return f"C({vec.x: 7.3f}, {vec.y: 7.3f}, {vec.z: 7.3f}) " \
            f"Sr: {mag: 7.3f}, Sθ: {format_angle(theta)}, Sɸ: {format_angle(phi)})"
    elif len(vec) == 2:
        theta = vec.angle_signed(X_AXIS_2D) if mag > 0 else nan
        return f"C({vec.x: 7.3f}, {vec.y: 7.3f}) " \
            f"Pr: {mag: 7.3f}, Pθ: {format_angle(theta)})"


def format_vecs(*vecs):
    return " / ".join(map(format_vector, vecs))


def format_direction(vec):
    """
    S => Spherical (r, θ, ɸ)
    P => Polar (r, θ)
    """
    mag = vec.magnitude
    if len(vec) == 3:
        theta = vec.to_2d().angle_signed(X_AXIS_2D) if vec.to_2d().magnitude > 0 else nan
        phi = vec.angle(Z_AXIS_3D) if mag > 0 else nan
        return f"Sθ: {format_angle(theta)}, Sɸ: {format_angle(phi)})"
    elif len(vec) == 2:
        theta = vec.angle_signed(X_AXIS_2D) if mag > 0 else nan
        return f"Pθ: {format_angle(theta)})"


def format_matrix(mat, name="Matrix", indent=1):
    """
    F => Full
    L => Location
    R => Rotation
    S => Scale
    """
    loc, rot, scale = mat.decompose()
    out = '\n'.join([
        f"{name} Full:" + ENDLTAB + pformat(mat).replace('\n', '\n\t'),
        f"{name} Loc:" + ENDLTAB + format_vector(loc),
        f"{name} Rot:" + ENDLTAB + format_quaternion(rot),
        f"{name} Scale:" + ENDLTAB + format_vector(scale),
    ])
    return out.replace('\n', ('\n' + (indent * '\t')))


def format_quaternion(quat):
    """
    Qθ = Angle
    QA = Axis
    """
    return f"Qθ: {format_angle(quat.angle)}, QA: {format_direction(quat.axis)}"


def format_euler(euler):
    """
    ER = Roll
    EP = Pitch
    EY = Yaw
    """
    return f"ER: {format_angle(euler.x)}, EP: {format_angle(euler.y)}, EY: {format_angle(euler.z)}"


def format_angle(rad):
    # {rad/pi: 5.3f}πᴿ
    return f"{degrees(rad): 7.3f}°"


def format_matrix_components(components):
    return ENDLTAB.join([
        ENDLTAB.join([
            f"{component_type.__name__}(*{component_args})",
            format_matrix(component_type(*component_args))
        ])
        for component_type, component_args in components
    ])


def setup_logger(log_file=None, stream_log_level=None, file_log_level=None):
    if stream_log_level is None:
        stream_log_level = logging.INFO
    if file_log_level is None:
        file_log_level = logging.DEBUG
    logger = logging.getLogger()
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])
    logger.setLevel(file_log_level)
    if log_file is not None:
        file_handler = logging.FileHandler(log_file, 'w')
        file_handler.setLevel(file_log_level)
        logger.addHandler(file_handler)
    if os.name != 'nt':
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(stream_log_level)
        stream_handler.setFormatter(coloredlogs.ColoredFormatter(LOG_STREAM_FMT))
        logger.addHandler(stream_handler)


def serialise_vector(vec):
    return list(vec[:])


def serialise_matrix(mat):
    return [serialise_vector(vec) for vec in mat]


def sanitise_names(*names):
    return re.subn(r"\W+", "_", "_".join(names))[0]


def get_sanitised_modelname():
    model_name, _ = os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))
    return sanitise_names(model_name)


def get_out_path(obj, suffix, extension="json"):
    model_name, _ = os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))
    sanitised = sanitise_names(model_name, obj.name, suffix)
    return os.path.join(DATA_PATH, f"{sanitised}.{extension}")


def export_json(out_path, serialised):
    logging.info(f"exporting to {out_path}")
    with open(out_path, 'w') as stream:
        json.dump(serialised, stream, indent=4)


def apply_to_selected_objects(fun, *args, **kwargs):
    sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    logging.info(f"objects: {pformat(sel_objs)}")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in sel_objs:
        bpy.context.view_layer.objects.active = obj
        yield fun(obj, *args, **kwargs)


def get_selected_polygons_suffix(obj, type_plural='polygons'):
    """
    if not all polygons are selected, then a suffix can be added to the export file to
    differentiate exports of different selections.
    """

    suffix = f"ALL {type_plural.upper()}"
    if bpy.context.object.mode == 'EDIT':
        selectable = [
            (polygon, polygon.select)
            for polygon in obj.data.polygons
        ]
        logging.info(f"Selectable Polygons: \n{pformat(selectable)}")

        polygon_enum = [
            (index, polygon) for index, polygon in enumerate(obj.data.polygons)
            if polygon.select
        ]
        selected_indices = [
            index for index, polygon in polygon_enum
        ]
        suffix = f"{type_plural.upper()} " + ' '.join(map(str, selected_indices))
        return polygon_enum, suffix
    logging.info(f"collection: {obj.users_collection}")
    logging.info(f"Selected Polygons: \n{pformat(obj.data.polygons)}")
    return enumerate(obj.data.polygons), suffix

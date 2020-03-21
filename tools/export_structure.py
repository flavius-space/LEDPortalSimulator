import imp
import inspect
import logging
import os
import sys
from datetime import datetime
from pprint import pformat

import bpy

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)
try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    imp.reload(__import__('common'))  # dumb hacks because of blender's pycache settings
    from common import (ENDLTAB, format_matrix, setup_logger, serialise_matrix, export_json,
                        get_selected_polygons, apply_to_selected_objects)
finally:
    sys.path = PATH
LOG_FILE = os.path.splitext(os.path.basename(THIS_FILE))[0] + '.log'

# EXPORT_TYPE = 'FACES'
EXPORT_TYPE = 'EDGES'


def serialise_object(obj, method):
    logging.info(f"Serialising object: {obj}")
    logging.info(f"Object World Matrix:" + ENDLTAB + format_matrix(obj.matrix_world))

    vertices = serialise_matrix([ver.co for ver in obj.data.vertices])
    edges = set()
    polygons = []

    for poly_idx, polygon in enumerate(get_selected_polygons(obj)):

        logging.debug(f"Vertex IDs:" + ENDLTAB + pformat(list(polygon.vertices)))

        if EXPORT_TYPE == 'EDGES':
            verts = len(polygon.vertices)
            for i in range(verts):
                edge = tuple(sorted([polygon.vertices[i], polygon.vertices[(i+1) % verts]]))
                edges.add(edge)
        elif EXPORT_TYPE == 'FACES':
            polygons.append(list(polygon.vertices))

    serialised = {
        'type': EXPORT_TYPE,
        'name': obj.name,
        'vertices': vertices,
        'matrix': serialise_matrix(obj.matrix_world)
    }

    if EXPORT_TYPE == 'EDGES':
        logging.info(f"exporting {len(edges)} edges")
        serialised['edges'] = list(edges)
    elif EXPORT_TYPE == 'FACES':
        logging.info(f"exporting {len(polygons)} faces")
        serialised['faces'] = polygons

    return serialised


def main():
    setup_logger(LOG_FILE)
    logging.info(f"*** Starting Structure Export {datetime.now().isoformat()} ***")

    structures = list(apply_to_selected_objects(serialise_object, EXPORT_TYPE))

    export_json(bpy.context.object, {'structures': structures}, EXPORT_TYPE)

    logging.info(f"*** Completed Structure Export {datetime.now().isoformat()} ***")


if __name__ == '__main__':
    main()

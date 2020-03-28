import os
import imp
import inspect
import sys
import unittest
import logging
from mathutils import Vector, Matrix

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)

try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    import __init__
    imp.reload(__init__)
    from __init__ import TOOLS_DIR, debugTestRunner
    sys.path.insert(0, TOOLS_DIR)
    import light_layout
    imp.reload(light_layout)
    from light_layout import generate_lights_for_convex_polygon, float_floor, float_ceil, float_abs_floor, float_abs_ceil
    import common
    imp.reload(common)
    from common import ATOL, matrix_isclose, setup_logger
finally:
    sys.path = PATH


class TestLightLayout(unittest.TestCase):
    def test_generate_lights_for_convex_polygon_right_triangle(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.5
        z_height = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((0, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.025],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_height],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (0, 0, 0),
            (1, 0, 0),
            (1, 1, 0),
            (0, 1, 0),
            (0, 2, 0),
            (0, 3, 0),
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            z_height
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(matrix, expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_right_triangle_flip(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.5
        z_height = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.075],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_height],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (1, 0, 0),
            (2, 0, 0),
            (2, 1, 0),
            (1, 1, 0),
            (2, 2, 0),
            (2, 3, 0),
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            z_height
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(matrix, expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_right_triangle_flip_margin(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.2
        z_height = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.185864],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_height],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (1, 0, 0),
            (2, 0, 0),
            (3, 0, 0),
            (4, 0, 0),
            (4, 1, 0),
            (3, 1, 0),
            (2, 1, 0),
            (1, 1, 0),
            (2, 2, 0),
            (3, 2, 0),
            (4, 2, 0),
            (4, 3, 0),
            (3, 3, 0),
            (2, 3, 0),
            (3, 4, 0),
            (4, 4, 0),
            (4, 5, 0),
            (3, 5, 0),
            (4, 6, 0),
            (4, 7, 0),
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            z_height,
            spacing/2
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(matrix, expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_iso_triangle(self):
        # Given
        width = 3.3
        height = 2.2
        spacing = 0.5
        z_height = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width/2, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.15],
            [0, spacing, 0, 0.10],
            [0, 0, spacing, z_height],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            Vector((1, 0, 0)),
            Vector((2, 0, 0)),
            Vector((3, 0, 0)),
            Vector((4, 0, 0)),
            Vector((5, 0, 0)),
            Vector((5, 1, 0)),
            Vector((4, 1, 0)),
            Vector((3, 1, 0)),
            Vector((2, 1, 0)),
            Vector((1, 1, 0)),
            Vector((2, 2, 0)),
            Vector((3, 2, 0)),
            Vector((4, 2, 0)),
            Vector((3, 3, 0)),
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            z_height
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(matrix, expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_rectangle(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.5
        z_height = 0.15
        vertices = [
            Vector((0, 0)),
            Vector((width, 0)),
            Vector((width, height)),
            Vector((0, height))
        ]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.05],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, 0.15],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            Vector((0, 0, 0)),
            Vector((1, 0, 0)),
            Vector((2, 0, 0)),
            Vector((2, 1, 0)),
            Vector((1, 1, 0)),
            Vector((0, 1, 0)),
            Vector((0, 2, 0)),
            Vector((1, 2, 0)),
            Vector((2, 2, 0)),
            Vector((2, 3, 0)),
            Vector((1, 3, 0)),
            Vector((0, 3, 0)),
            Vector((0, 4, 0)),
            Vector((1, 4, 0)),
            Vector((2, 4, 0)),
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            z_height
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(matrix, expected_matrix, atol=ATOL)


class TestFloatOps(unittest.TestCase):
    def test_float_floor(self):
        assert float_floor(0.0000000000001) == 0
        assert float_floor(-0.0000000000001) == 0
        assert float_floor(0.5) == 0
        assert float_floor(-0.5) == -1
        assert float_floor(1+.0000000000001) == 1
        assert float_floor(1-0.0000000000001) == 1
        assert float_floor(-1+.0000000000001) == -1
        assert float_floor(-1-0.0000000000001) == -1

    def test_float_ceil(self):
        assert float_ceil(0.0000000000001) == 0
        assert float_ceil(-0.0000000000001) == 0
        assert float_ceil(0.5) == 1
        assert float_ceil(-0.5) == 0
        assert float_ceil(1+.0000000000001) == 1
        assert float_ceil(1-0.0000000000001) == 1
        assert float_ceil(-1+.0000000000001) == -1
        assert float_ceil(-1-0.0000000000001) == -1

    def test_float_abs_floor(self):
        assert float_abs_floor(0.0000000000001) == 0
        assert float_abs_floor(-0.0000000000001) == 0
        assert float_abs_floor(0.5) == 0
        assert float_abs_floor(-0.5) == 0
        assert float_abs_floor(1+.0000000000001) == 1
        assert float_abs_floor(1-0.0000000000001) == 1
        assert float_abs_floor(-1+.0000000000001) == -1
        assert float_abs_floor(-1-0.0000000000001) == -1

    def test_float_abs_ceil(self):
        assert float_abs_ceil(0.0000000000001) == 0
        assert float_abs_ceil(-0.0000000000001) == 0
        assert float_abs_ceil(0.5) == 1
        assert float_abs_ceil(-0.5) == -1
        assert float_abs_ceil(1+.0000000000001) == 1
        assert float_abs_ceil(1-0.0000000000001) == 1
        assert float_abs_ceil(-1+.0000000000001) == -1
        assert float_abs_ceil(-1-0.0000000000001) == -1


if __name__ == "__main__":
    setup_logger(stream_log_level=logging.DEBUG)
    for suite in [
        unittest.TestLoader().loadTestsFromTestCase(TestLightLayout),
        unittest.TestLoader().loadTestsFromTestCase(TestFloatOps),
    ]:
        debugTestRunner(verbosity=10).run(suite)

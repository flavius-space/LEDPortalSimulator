import imp
import inspect
import logging
import os
import sys
import unittest
from math import inf, nan, pi, sqrt, tan

import numpy as np
from mathutils import Matrix, Vector

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
    from light_layout import (
        generate_lights_for_convex_polygon, float_floor, float_ceil, float_abs_floor,
        float_abs_ceil, nan_divide, inf_divide, gradient_rise, gradient_run)
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
            (0, 0),
            (1, 0),
            (2, 0),
            (1, 1),
            (0, 1),
            (0, 2),
            (1, 2),
            (0, 3),
            (0, 4)
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
        expected_lights = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (2, 4)]

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
            [spacing, 0, 0, 0.180901],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_height],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (4, 1),
            (3, 1),
            (2, 1),
            (1, 1),
            (1, 2),
            (2, 2),
            (3, 2),
            (4, 2),
            (4, 3),
            (3, 3),
            (2, 3),
            (2, 4),
            (3, 4),
            (4, 4),
            (4, 5),
            (3, 5),
            (3, 6),
            (4, 6),
            (4, 7),
            (4, 8)
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
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (5, 1),
            (4, 1),
            (3, 1),
            (2, 1),
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 2),
            (3, 3),
            (3, 4)
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

    def test_generate_lights_for_convex_polygon_iso_shear(self):
        # Given
        width = 2
        height = sqrt(3)
        gradient = sqrt(3)
        spacing = 1
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width/2, height))]
        expected_matrix = Matrix([
            [spacing, 1/2, 0, 0],
            [0, sqrt(3)/2, 0, 0],
            [0, 0, spacing, 0],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (0, 0),
            (1, 0),
            (2, 0),
            (1, 1),
            (0, 1),
            (0, 2)
        ]

        # When
        matrix, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            grid_gradient=gradient
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
            (0, 0),
            (1, 0),
            (2, 0),
            (2, 1),
            (1, 1),
            (0, 1),
            (0, 2),
            (1, 2),
            (2, 2),
            (2, 3),
            (1, 3),
            (0, 3),
            (0, 4),
            (1, 4),
            (2, 4),
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

    def test_axis_centered_lines(self):
        """
        |m-|p|-s--|-s--|p|m-|
        """
        # Given
        axis_length = 20.0
        spacing = 5.0
        margin = 3.0
        expected_padding = 2.0
        expected_lines = 3
        expected_start = 5.0

        # When
        start, lines, padding = axis_centered_lines(axis_length, spacing, margin)

        # Then
        assert np.isclose(start, expected_start)
        assert np.isclose(lines, expected_lines)
        assert np.isclose(padding, expected_padding)


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

    def test_nan_divide(self):
        assert nan_divide(1, 0.0000000000001) is nan
        assert nan_divide(1, nan) == 0

    def test_inf_divide(self):
        assert inf_divide(inf, 0) == inf
        assert inf_divide(10, 0) == inf
        assert inf_divide(-inf, 0) == -inf
        assert inf_divide(-10, 0) == -inf

        assert inf_divide(inf, inf) == 0
        assert inf_divide(0, inf) == 0
        assert inf_divide(-inf, inf) == -0
        assert inf_divide(-0, inf) == -0

        assert inf_divide(inf, 0.0000000000001) == inf
        assert inf_divide(inf, -0.0000000000001) == -inf
        assert inf_divide(10, 0.0000000000001) == inf
        assert inf_divide(10, -0.0000000000001) == -inf
        assert inf_divide(-inf, 0.0000000000001) == -inf
        assert inf_divide(-inf, -0.0000000000001) == inf
        assert inf_divide(-10, 0.0000000000001) == -inf
        assert inf_divide(-10, -0.0000000000001) == inf

    def test_gradient_rise(self):
        assert np.isclose(gradient_rise(tan(0*pi/6)), 0)
        assert np.isclose(gradient_rise(tan(1*pi/6)), 1/2)
        assert np.isclose(gradient_rise(tan(2*pi/6)), sqrt(3)/2)
        assert np.isclose(gradient_rise(tan(3*pi/6)), 1)
        assert np.isclose(gradient_rise(tan(4*pi/6)), -sqrt(3)/2)
        assert np.isclose(gradient_rise(tan(5*pi/6)), -1/2)

    def test_gradient_run(self):
        assert np.isclose(gradient_run(tan(0*pi/6)), 1)
        assert np.isclose(gradient_run(tan(1*pi/6)), sqrt(3)/2)
        assert np.isclose(gradient_run(tan(2*pi/6)), 1/2)
        assert np.isclose(gradient_run(tan(3*pi/6)), 0)
        assert np.isclose(gradient_run(tan(4*pi/6)), 1/2)
        assert np.isclose(gradient_run(tan(5*pi/6)), sqrt(3)/2)


if __name__ == "__main__":
    setup_logger(stream_log_level=logging.DEBUG)
    for suite in [
        unittest.TestLoader().loadTestsFromTestCase(TestLightLayout),
        unittest.TestLoader().loadTestsFromTestCase(TestFloatOps),
    ]:
        debugTestRunner(verbosity=10).run(suite)

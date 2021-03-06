import imp
import inspect
import logging
import os
import sys
import unittest
from math import inf, nan, sqrt

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
        float_abs_ceil, nan_divide, inf_divide, axis_centered_lines,
        margin_intersect_offset, intersect_lines, lx_decompose)
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
        z_offset = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((0, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.025],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_offset],
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
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing=spacing,
            z_offset=z_offset
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_right_triangle_flip(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.5
        z_offset = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.075],
            [0, spacing, 0, 0.1],
            [0, 0, spacing, z_offset],
            [0, 0, 0, 1]
        ])
        expected_lights = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (2, 4)]

        # When
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing=spacing,
            z_offset=z_offset
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_right_triangle_flip_margin(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.2
        z_offset = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.190],
            [0, spacing, 0, 0.138],
            [0, 0, spacing, z_offset],
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
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing=spacing,
            z_offset=z_offset,
            margin=spacing/2
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_iso_triangle(self):
        # Given
        width = 3.3
        height = 2.2
        spacing = 0.5
        z_offset = 0.15
        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width/2, height))]
        expected_matrix = Matrix([
            [spacing, 0, 0, 0.15],
            [0, spacing, 0, 0.10],
            [0, 0, spacing, z_offset],
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
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing=spacing,
            z_offset=z_offset
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_equ_shear(self):
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
        info, lights = generate_lights_for_convex_polygon(
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
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_equ_shear_margin(self):
        r"""
            /.\
           //*\\
          //* *\\
         //*_*_*\\
        -----------
        """
        # Given
        width = 5
        height = 2.5 * sqrt(3)
        grid_gradient = sqrt(3)
        spacing = 1
        margin = sqrt(3)/2

        vertices = [Vector((0, 0)), Vector((width, 0)), Vector((width/2, height))]
        expected_matrix = Matrix([
            [spacing, 1/2, 0, 1.5],
            [0, sqrt(3)/2, 0, sqrt(3)/2],
            [0, 0, spacing, 0],
            [0, 0, 0, 1]
        ])
        expected_lights = [
            (0, 0),
            (1, 0),
            (2, 0),
            (1, 1),
            (0, 1),
            (0, 2),
        ]

        # When
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing,
            margin=margin,
            grid_gradient=grid_gradient
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

    def test_generate_lights_for_convex_polygon_rectangle(self):
        # Given
        width = 1.1
        height = 2.2
        spacing = 0.5
        z_offset = 0.15
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
        info, lights = generate_lights_for_convex_polygon(
            vertices[1].x,
            vertices[2].x,
            vertices[2].y,
            vertices[-1].x,
            vertices[-1].y,
            spacing=spacing,
            z_offset=z_offset
        )

        # Then
        assert matrix_isclose(lights, expected_lights, atol=ATOL)
        assert matrix_isclose(info['transformation'], expected_matrix, atol=ATOL)

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

        # When
        lines, padding = axis_centered_lines(axis_length, spacing, margin)

        # Then
        assert np.isclose(lines, expected_lines)
        assert np.isclose(padding, expected_padding)

    def test_margin_itersect_offset_equ(self):
        # Given
        gradient_left = sqrt(3)
        gradient_right = -sqrt(3)
        base_width = 1875
        margin = 650/2
        expected = 650

        # When
        intersect = margin_intersect_offset(gradient_left, gradient_right, base_width, margin)

        # Then
        assert np.isclose(expected, intersect, atol=1)

    def test_margin_itersect_offset_parallellogram(self):
        # Given
        gradient_left = sqrt(3)
        gradient_right = -sqrt(3)
        base_width = 1875
        margin = 650/2
        expected = 650

        # When
        intersect = margin_intersect_offset(gradient_left, gradient_right, base_width, margin)

        # Then
        assert np.isclose(expected, intersect, atol=1)

    def test_margin_itersect_offset_square(self):
        # Given
        gradient_left = inf
        gradient_right = inf
        base_width = 1875
        margin = 650/2
        expected = None

        # When
        intersect = margin_intersect_offset(gradient_left, gradient_right, base_width, margin)

        # Then
        assert expected == intersect

    def test_margin_itersect_offset_right(self):
        # Given
        gradient_left = inf
        gradient_right = -1
        base_width = 6
        margin = 1
        expected = 2.41

        # When
        intersect = margin_intersect_offset(gradient_left, gradient_right, base_width, margin)

        # Then
        assert np.isclose(expected, intersect, atol=0.01)

    def test_margin_itersect_offset_right_flip(self):
        # Given
        gradient_left = 1
        gradient_right = inf
        base_width = 6
        margin = 1
        expected = 2.41

        # When
        intersect = margin_intersect_offset(gradient_left, gradient_right, base_width, margin)

        # Then
        assert np.isclose(expected, intersect, atol=0.01)

    def test_intersect_lines(self):
        assert np.isclose(intersect_lines(inf, 0, -1, 1), (0, 1)).all()
        assert np.isclose(intersect_lines(inf, 1, 1, -1), (1, 0)).all()
        assert np.isclose(intersect_lines(1, 0, inf, 1), (1, 1)).all()
        assert np.isclose(intersect_lines(inf, 1, -1, 4.586), (1, 3.586)).all()

    def test_lx_decompose(self):
        # Given
        matrix = Matrix((
            (0.03184741735458374, 0.05174137279391289, -0.014522486366331577, -1.383671760559082),
            (-0.04383426159620285, 0.004105888307094574, -0.01055119652301073, -0.235106959939003),
            (-4.844257439629018e-09, 0.015545825473964214, 0.05112211033701897, 2.79781174659729),
            (0.0, 0.0, 0.0, 1.0)
        ))
        expected_translation = Vector((-1.384,  -0.235,   2.798))
        expected_angles = (
            -54,
            0,
            19.348
        )

        # When
        (translation, *angles) = lx_decompose(matrix)

        # Then
        assert np.isclose(expected_translation, translation, atol=ATOL).all()
        assert np.isclose(expected_angles, angles, atol=ATOL).all()

    def test_lx_decompose_spicy(self):
        # Given
        matrix = Matrix((
            (-0.014242800883948803, 0.03184732794761658, -0.026610037311911583, -1.621147871017456),
            (-0.04383419454097748, -0.04383432865142822, -0.01933331787586212, -0.4076759517192840),
            (-0.028485195711255074, -1.0244548320770264e-07, 0.04305611550807953, 2.62304186820983),
            (0.0, 0.0, 0.0, 1.0)
        ))
        expected_translation = Vector((-1.621,  -0.408,   2.623))
        expected_angles = (
            -108.000,
            31.718,
            20.905
        )

        # When
        (translation, *angles) = lx_decompose(matrix)

        # Then
        assert np.isclose(expected_translation, translation, atol=ATOL).all()
        assert np.isclose(expected_angles, angles, atol=ATOL).all()


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


if __name__ == "__main__":
    setup_logger(stream_log_level=logging.DEBUG)
    for suite in [
        unittest.TestLoader().loadTestsFromTestCase(TestLightLayout),
        unittest.TestLoader().loadTestsFromTestCase(TestFloatOps),
    ]:
        debugTestRunner(verbosity=10).run(suite)

import imp
import inspect
import os
import sys
import unittest
import logging
from math import sqrt, tan, pi

import numpy as np

THIS_FILE = inspect.stack()[-2].filename
THIS_DIR = os.path.dirname(THIS_FILE)

try:
    PATH = sys.path[:]
    sys.path.insert(0, THIS_DIR)
    import __init__
    imp.reload(__init__)
    from __init__ import TOOLS_DIR, debugTestRunner
    sys.path.insert(0, TOOLS_DIR)
    import trig
    imp.reload(trig)
    from trig import (gradient_sin, gradient_cos)
    import common
    imp.reload(common)
    from common import setup_logger
finally:
    sys.path = PATH


class TestTrig(unittest.TestCase):
    def test_gradient_sin(self):
        assert np.isclose(gradient_sin(tan(0*pi/6)), 0)
        assert np.isclose(gradient_sin(tan(1*pi/6)), 1/2)
        assert np.isclose(gradient_sin(tan(2*pi/6)), sqrt(3)/2)
        assert np.isclose(gradient_sin(tan(3*pi/6)), 1)
        assert np.isclose(gradient_sin(tan(4*pi/6)), -sqrt(3)/2)
        assert np.isclose(gradient_sin(tan(5*pi/6)), -1/2)

    def test_gradient_cos(self):
        assert np.isclose(gradient_cos(tan(0*pi/6)), 1)
        assert np.isclose(gradient_cos(tan(1*pi/6)), sqrt(3)/2)
        assert np.isclose(gradient_cos(tan(2*pi/6)), 1/2)
        assert np.isclose(gradient_cos(tan(3*pi/6)), 0)
        assert np.isclose(gradient_cos(tan(4*pi/6)), 1/2)
        assert np.isclose(gradient_cos(tan(5*pi/6)), sqrt(3)/2)


if __name__ == "__main__":
    setup_logger(stream_log_level=logging.DEBUG)
    for suite in [
        unittest.TestLoader().loadTestsFromTestCase(TestTrig),
    ]:
        debugTestRunner(verbosity=10).run(suite)

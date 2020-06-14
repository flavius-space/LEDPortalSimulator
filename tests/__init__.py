import os
import unittest
import traceback
import pdb
import pytest

TESTS_DIR = os.path.dirname(__file__)
REPO_DIR = os.path.dirname(TESTS_DIR)
TOOLS_DIR = os.path.join(REPO_DIR, 'tools')
FAKE_BLENDER_DIR = os.path.join(TESTS_DIR, 'fake_blender_modules')


def debugTestRunner(post_mortem=None, *args, **kwargs):
    """unittest runner doing post mortem debugging on failing tests"""
    if post_mortem is None:
        post_mortem = pdb.post_mortem

    class DebugTestResult(unittest.TextTestResult):
        def addError(self, test, err):
            # called before tearDown()
            traceback.print_exception(*err)
            post_mortem(err[2])
            super(DebugTestResult, self).addError(test, err)
            pytest.exit('exit after post mortem')

        def addFailure(self, test, err):
            traceback.print_exception(*err)
            post_mortem(err[2])
            super(DebugTestResult, self).addFailure(test, err)
            pytest.exit('exit after post mortem')

    kwargs['resultclass'] = DebugTestResult
    return unittest.TextTestRunner(*args, **kwargs)

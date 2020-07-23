import unittest
import sys

from . import *

suite = unittest.TestLoader().discover("tests", pattern="*_tests.py")
result = unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)
sys.exit(bool(result.errors or result.failures))

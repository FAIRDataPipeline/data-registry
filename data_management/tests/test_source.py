"""
The source compiles cleanly: an invalid escape in a docstring is a SyntaxWarning on
Python 3.12 and later, and a SyntaxError in a later Python.
"""

from pathlib import Path
import warnings

from django.test import SimpleTestCase

import data_management


class SourceTests(SimpleTestCase):

    def test_modules_compile_without_warnings(self):
        package = Path(data_management.__file__).parent
        for path in package.glob("*.py"):
            with self.subTest(module=path.name), warnings.catch_warnings():
                warnings.simplefilter("error")
                compile(path.read_text(), str(path), "exec")

from djappdep.djappdep import _read_imports

from tests.base import BaseTestCase


class ImportTests(BaseTestCase):
    """Test parsing of python `import` statements"""

    def test_full_path(self):
        """import dotted.package.path"""
        imports = 'import os\nimport os.path'

        result = _read_imports(imports, 'app')
        self.assertListEqual(result, ['os', 'os.path'])

    def test_relative_dotted_path(self):
        """import .localfile"""
        line = 'import .localfile'
        result = _read_imports(line, 'app')
        self.assertListEqual(result, ['app.localfile'])

    def test_from_full_path(self):
        """from dotted.package.path import somefunction"""
        line = 'from dotted.package.path import somefunction'
        result = _read_imports(line, 'app')
        self.assertListEqual(result, ['dotted.package.path.somefunction'])

    #
    def test_from_relative_path(self):
        """from .localpackage import somefunction"""
        line = 'from .localpackage.path import somefunction'
        result = _read_imports(line, 'app')
        self.assertListEqual(result, ['app.localpackage.path.somefunction'])

    def test_multiple_imports_in_single_line(self):
        line = 'from package.localfile import One, Two'
        result = _read_imports(line, 'app')
        self.assertListEqual(
            result,
            ['package.localfile.One',
             'package.localfile.Two'])

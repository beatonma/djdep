from unittest import (
    TestCase,
)
from djappdep.djappdep import (
    _read_import_line as read_import_line,
    _convert_path_filesystem_to_python as convert_path_filesystem_to_python,
    _set_granularity as set_granularity,
)


class BaseTestCase(TestCase):
    """"""
    pass


class ImportTests(BaseTestCase):
    """Test parsing of python `import` lines"""
    def test_full_path(self):
        """import dotted.package.path"""
        line = 'import os'
        result = read_import_line(line, dotted_filepath='app')
        self.assertEqual(result, 'os')

        line = 'import os.path'
        result = read_import_line(line, dotted_filepath='app')
        self.assertEqual(result, 'os.path')

    def test_relative_dotted_path(self):
        """import .localfile"""
        line = 'import .localfile'
        result = read_import_line(line, dotted_filepath='app')
        self.assertEqual(result, 'app.localfile')

    def test_from_full_path(self):
        """from dotted.package.path import somefunction"""
        line = 'from dotted.package.path import somefunction'
        result = read_import_line(line, dotted_filepath='app')
        self.assertEqual(result, 'dotted.package.path.somefunction')

    def test_from_relative_path(self):
        """from .localpackage import somefunction"""
        line = 'from .localpackage.path import somefunction'
        result = read_import_line(line, dotted_filepath='app')
        self.assertEqual(result, 'app.localpackage.path.somefunction')


class PathConversionTests(BaseTestCase):
    def test_convert_windows_filesystem_to_python(self):
        windows_cwd = r'F:\\Desktop\\project'
        windows_filepath = r'F:\\Desktop\\project\\app\\file.py'
        self.assertEqual(
            convert_path_filesystem_to_python(windows_filepath, cwd=windows_cwd),
            'app.file'
        )

    def test_convert_nix_filesystem_to_python(self):
        nix_cwd = r'/home/User/project/'
        nix_filepath = r'/home/User/project/app/file.py'
        self.assertEqual(
            convert_path_filesystem_to_python(nix_filepath, cwd=nix_cwd),
            'app.file'
        )


class GranularityTests(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.dependency_map = {
            'app_one.submodule.file': [
                'app_two.submodule.file.somefunction'
            ],
            'app_one.another_submodule.file': [
                'app_two.submodule.file.someotherfunction'
            ],
            'app_two.submodule.file': []
        }

    def test_app_granularity(self):
        granularity = 1
        set_granularity(self.dependency_map, granularity)
        import json
        print('GRANULAR:', json.dumps(self.dependency_map, indent=2))
        self.assertDictEqual(
            {
                'app_one': [
                    'app_two.submodule.file.somefunction',
                    'app_two.submodule.file.someotherfunction'
                ],
                'app_two': []
            },
            self.dependency_map
        )

    def test_app_submodule_granularity(self):
        granularity = 2
        set_granularity(self.dependency_map, granularity)
        import json
        print('GRANULAR:', json.dumps(self.dependency_map, indent=2))
        self.assertDictEqual(
            {
                'app_one.submodule': [
                    'app_two.submodule.file.somefunction'
                ],
                'app_one.another_submodule': [
                    'app_two.submodule.file.someotherfunction'
                ],
                'app_two.submodule': []
            },
            self.dependency_map
        )

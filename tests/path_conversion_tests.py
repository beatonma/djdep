from djappdep.djappdep import _convert_path_filesystem_to_python
from tests.base import BaseTestCase


class PathConversionTests(BaseTestCase):
    def test_convert_windows_filesystem_to_python(self):
        windows_cwd = r'F:\\Desktop\\project'
        windows_filepath = r'F:\\Desktop\\project\\app\\file.py'
        self.assertEqual(
            _convert_path_filesystem_to_python(windows_filepath, cwd=windows_cwd),
            'app.file'
        )

    def test_convert_nix_filesystem_to_python(self):
        nix_cwd = r'/home/User/project/'
        nix_filepath = r'/home/User/project/app/file.py'
        self.assertEqual(
            _convert_path_filesystem_to_python(nix_filepath, cwd=nix_cwd),
            'app.file'
        )

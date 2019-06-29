from djappdep.djappdep import (
    _remove_empty_imports,
    _remove_external_imports,
    _remove_internal_app_imports,
    _remove_tests,
)
from tests.base import BaseTestCase


class PruningTests(BaseTestCase):
    """Tests about removing items from the final results"""

    def test_remove_tests(self):
        dependency_map = {
            'app': [
                'otherapp.somefunction',
                'otherapp.SomeClass',
            ],
            'app.test': [
                'otherapp.somefunction',
                'otherapp.SomeClass',
                'otherapp.tests.test_some_module',
            ],
            'otherapp.tests.test_some_module': [],
        }

        _remove_tests(dependency_map)

        self.assertDictEqual(
            {
                'app': [
                    'otherapp.somefunction',
                    'otherapp.SomeClass',
                ],
            },
            dependency_map)

    def test_remove_external_imports(self):
        dependency_map = {
            'app': [
                'argparse.ArgumentParser',
                'os',
                'otherapp.somemodule.some_function',
                'sys',
            ],
            'otherapp': [
                'time',
            ],
        }

        _remove_external_imports(dependency_map)

        self.assertDictEqual(
            {
                'app': [
                    'otherapp.somemodule.some_function',
                ],
                'otherapp': [],
            },
            dependency_map)

    def test_remove_internal_imports(self):
        dependency_map = {
            'app': [
                'app.submodule.some_func',
                'argparse.ArgumentParser',
                'os',
                'otherapp.somemodule.some_function',
                'app.anothermodule.InternalClass',
                'app2.anothermodule.InternalClass',
                'sys',
            ],
            'app2': [
                'app.anothermodule.InternalClass',
                'app2.anothermodule.InternalClass',
            ],
            'otherapp': [
                'time',
                'yetanother.app.FancyClass',
            ],
        }

        _remove_internal_app_imports(dependency_map)

        self.assertDictEqual(
            {
                'app': [
                    'argparse.ArgumentParser',
                    'os',
                    'otherapp.somemodule.some_function',
                    'app2.anothermodule.InternalClass',
                    'sys',
                ],
                'app2': [
                    'app.anothermodule.InternalClass',
                ],
                'otherapp': [
                    'time',
                    'yetanother.app.FancyClass',
                ],
            },
            dependency_map)

    def test_remove_empty_imports(self):
        dependency_map = {
            'app': [
                'argparse.ArgumentParser',
                'os',
                'otherapp.somemodule.some_function',
                'sys',
            ],
            'otherapp': [],
        }

        _remove_empty_imports(dependency_map)

        self.assertDictEqual(
            {
                'app': [
                    'argparse.ArgumentParser',
                    'os',
                    'otherapp.somemodule.some_function',
                    'sys',
                ],
            },
            dependency_map
        )

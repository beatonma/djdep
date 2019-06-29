from djappdep.djappdep import _set_granularity
from tests.base import BaseTestCase


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
        _set_granularity(self.dependency_map, granularity)
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
        _set_granularity(self.dependency_map, granularity)
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

from typing import (
    Any,
    Dict,
)
from unittest import TestCase


class BaseTestCase(TestCase):
    """"""

    def assertDictEqual(
            self,
            first: Dict[Any, Any],
            second: Dict[Any, Any],
            msg: Any = ...
    ) -> None:
        """Sort lists to avoid ordering issues that super method can't handle"""
        for value in first.values():
            if isinstance(value, list):
                value.sort()
        for value in second.values():
            if isinstance(value, list):
                value.sort()
        super().assertDictEqual(first, second, msg)

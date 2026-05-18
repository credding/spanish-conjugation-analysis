import pytest

from .test_annotated_string import SampleAnnotation


class TestStringAnnotation:
    def test_lt_unsupported_type(self) -> None:
        with pytest.raises(TypeError):
            _ = SampleAnnotation("test", 0, 1) < object()  # ty:ignore[unsupported-operator]

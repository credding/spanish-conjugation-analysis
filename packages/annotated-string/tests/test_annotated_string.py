from collections.abc import Hashable
from dataclasses import dataclass

import pytest
from annotated_string import (
    AnnotatedString,
    ConflictError,
    ConstraintError,
    StringAnnotation,
)


@dataclass(repr=False)
class SampleAnnotation(StringAnnotation):
    pass


@dataclass(repr=False)
class SampleAnnotation2(StringAnnotation):
    pass


class TestAnnotatedString:
    def test_add_annotation(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert string.get_annotations() == [SampleAnnotation("test", 2, 3)]

    @pytest.mark.parametrize(
        ("start", "stop"),
        [
            (3, 2),  # te]s[t
            (-1, 3),  # [-tes]t
            (2, 5),  # te[st-]
        ],
    )
    def test_add_annotation_invalid_range(self, start: int, stop: int) -> None:
        string = AnnotatedString("test")
        with pytest.raises(ConstraintError):
            string.add_annotation(SampleAnnotation("test", start, stop))
        assert string.get_annotations() == []

    def test_add_annotation_duplicate(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert string.get_annotations() == [SampleAnnotation("test", 2, 3)]

    def test_add_annotation_duplicate_not_equal(self) -> None:
        @dataclass(repr=False)
        class DataAnnotation(StringAnnotation):
            data: str

        string = AnnotatedString("test")
        string.add_annotation(DataAnnotation("test", 2, 3, "a"))
        with pytest.raises(ConflictError):
            string.add_annotation(DataAnnotation("test", 2, 3, "b"))
        assert string.get_annotations() == [DataAnnotation("test", 2, 3, "a")]

    def test_add_annotation_overlap(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        with pytest.raises(ConflictError):
            string.add_annotation(SampleAnnotation("test", 1, 3))
        assert string.get_annotations() == [SampleAnnotation("test", 2, 3)]

    def test_add_annotation_invalid_string(self) -> None:
        string = AnnotatedString("test")
        with pytest.raises(ConstraintError):
            string.add_annotation(SampleAnnotation("badtest", 2, 3))
        assert string.get_annotations() == []

    def test_annotations_contains(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert SampleAnnotation("test", 2, 3) in string.annotations

    def test_annotations_contains_overlap(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert SampleAnnotation("test", 1, 3) not in string.annotations

    def test_annotations_contains_duplicate_not_equal(self) -> None:
        @dataclass(repr=False)
        class DataAnnotation(StringAnnotation):
            data: str

        string = AnnotatedString("test")
        string.add_annotation(DataAnnotation("test", 2, 3, "a"))
        assert DataAnnotation("test", 2, 3, "b") not in string.annotations

    def test_annotations_contains_object(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert object() not in string.annotations

    def test_get_annotations_sort(self) -> None:
        class OverlapAnnotation(StringAnnotation):
            @property
            def unique_key(self) -> Hashable:
                return type(self), self.start, self.stop

        string = AnnotatedString("test")
        string.add_annotation(OverlapAnnotation("test", 2, 3))  # te[s]t
        string.add_annotation(OverlapAnnotation("test", 1, 3))  # t[es]t
        string.add_annotation(OverlapAnnotation("test", 0, 2))  # [te]st
        string.add_annotation(OverlapAnnotation("test", 0, 1))  # [t]est
        assert string.get_annotations() == [
            OverlapAnnotation("test", 0, 1),  # [t]est
            OverlapAnnotation("test", 0, 2),  # [te]st
            OverlapAnnotation("test", 1, 3),  # t[es]t
            OverlapAnnotation("test", 2, 3),  # te[s]t
        ]

    def test_get_annotations_one(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 1, 2))
        string.add_annotation(SampleAnnotation2("test", 1, 2))
        assert string.get_annotations(SampleAnnotation) == [
            SampleAnnotation("test", 1, 2)
        ]

    def test_get_annotations_none(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation2("test", 1, 2))
        assert string.get_annotations(SampleAnnotation) == []

    def test_get_annotations_many(self) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", 1, 2))
        string.add_annotation(SampleAnnotation("test", 2, 3))
        assert string.get_annotations(SampleAnnotation) == [
            SampleAnnotation("test", 1, 2),
            SampleAnnotation("test", 2, 3),
        ]

    @pytest.mark.parametrize(
        (
            "start",
            "stop",
            "slice_start",
            "slice_stop",
            "expected_start",
            "expected_stop",
        ),
        [
            (2, 3, 1, 4, 1, 2),  # t|e[s]t|
            (1, 2, 1, 3, 0, 1),  # t|[e]s|t
            (2, 3, 1, 3, 1, 2),  # t|e[s]|t
            (1, 3, 2, 4, 0, 1),  # t[e|s]t|
            (2, 4, 1, 3, 1, 2),  # t|e[s|t]
            (1, 4, 2, 3, 0, 1),  # t[e|s|t]
        ],
    )
    def test_getitem_annotation_intersect(
        self,
        start: int,
        stop: int,
        slice_start: int,
        slice_stop: int,
        expected_start: int,
        expected_stop: int,
    ) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", start, stop))
        sliced_string = string[slice_start:slice_stop]
        assert sliced_string.string == "test"[slice_start:slice_stop]
        assert sliced_string.get_annotations() == [
            SampleAnnotation(sliced_string.string, expected_start, expected_stop)
        ]

    @pytest.mark.parametrize(
        ("start", "stop", "slice_start", "slice_stop"),
        [
            (3, 4, 1, 2),  # t|e|s[t]
            (1, 2, 3, 4),  # t[e]s|t|
            (2, 3, 1, 2),  # t|e|[s]t
            (1, 2, 2, 3),  # t[e]|s|t
            (3, 3, 1, 2),  # t|e|s[]t
            (1, 1, 2, 3),  # t[]e|s|t
            (2, 3, 1, 1),  # t||e[s]t
            (1, 2, 3, 3),  # t[e]s||t
            (1, 2, 1, 1),  # t||[e]st
            (1, 2, 2, 2),  # t[e]||st
            (2, 2, 2, 2),  # te||[]st
            (1, 1, 1, 2),  # t[]|e|st
            (2, 2, 1, 2),  # t|e|[]st
        ],
    )
    def test_getitem_annotation_disjoint(
        self, start: int, stop: int, slice_start: int, slice_stop: int
    ) -> None:
        string = AnnotatedString("test")
        string.add_annotation(SampleAnnotation("test", start, stop))
        sliced_string = string[slice_start:slice_stop]
        assert sliced_string.string == "test"[slice_start:slice_stop]
        assert sliced_string.get_annotations() == []

    def test_add_string(self) -> None:
        string = AnnotatedString("foo")
        string.add_annotation(SampleAnnotation("foo", 2, 3))

        result = string + "bar"
        assert result.string == "foobar"
        assert result.get_annotations() == [SampleAnnotation("foobar", 2, 3)]

    def test_add_annotated_string(self) -> None:
        string = AnnotatedString("foo")
        string.add_annotation(SampleAnnotation("foo", 2, 3))
        string2 = AnnotatedString("bar")
        string2.add_annotation(SampleAnnotation("bar", 1, 2))
        string2.add_annotation(SampleAnnotation2("bar", 2, 3))

        result = string + string2
        assert result.string == "foobar"
        assert result.get_annotations() == [
            SampleAnnotation("foobar", 2, 3),
            SampleAnnotation("foobar", 4, 5),
            SampleAnnotation2("foobar", 5, 6),
        ]

    def test_add_unsupported_type(self) -> None:
        string = AnnotatedString("foo")
        string.add_annotation(SampleAnnotation("foo", 2, 3))

        with pytest.raises(TypeError):
            _ = string + object()  # ty:ignore[unsupported-operator]


class TestStringAnnotation:
    def test_lt_unsupported_type(self) -> None:
        with pytest.raises(TypeError):
            _ = SampleAnnotation("test", 0, 1) < object()  # ty:ignore[unsupported-operator]

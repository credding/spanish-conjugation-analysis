from dataclasses import dataclass

import pytest
from annotated_string import AnnotatedString, StringAnnotation


@dataclass(repr=False)
class SampleAnnotation(StringAnnotation):
    pass


@dataclass(repr=False)
class SampleAnnotation2(StringAnnotation):
    pass


class TestAnnotatedString:
    @pytest.mark.parametrize(
        ("start", "stop", "expected_text"),
        [
            (2, 3, "s"),  # te[s]t
            (2, 2, ""),  # te[]st
            (0, 4, "test"),  # [test]
        ],
    )
    def test_annotate(self, start: int, stop: int, expected_text: str) -> None:
        string = AnnotatedString("test")
        annotation = string.annotate(SampleAnnotation, start, stop)
        assert string.annotations == [annotation]
        assert annotation == SampleAnnotation("test", start, stop)
        assert annotation.text == expected_text

    def test_annotate_stop_none(self) -> None:
        string = AnnotatedString("test")
        annotation = string.annotate(SampleAnnotation, 2)
        assert string.annotations == [annotation]
        assert annotation == SampleAnnotation("test", 2, 4)

    @pytest.mark.parametrize(
        ("start", "stop"),
        [
            (3, 2),  # te]s[t
            (-1, 3),  # [-tes]t
            (2, 5),  # te[st-]
        ],
    )
    def test_annotate_invalid_range(self, start: int, stop: int) -> None:
        string = AnnotatedString("test")
        with pytest.raises(ValueError):
            string.annotate(SampleAnnotation, start, stop)
        assert string.annotations == []

    def test_annotate_duplicate(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 2, 3)
        with pytest.raises(ValueError):
            string.annotate(SampleAnnotation, 2, 3)
        assert string.annotations == [SampleAnnotation("test", 2, 3)]

    def test_add_annotation_invalid_string(self) -> None:
        string = AnnotatedString("test")
        annotation = SampleAnnotation("badtest", 2, 3)
        with pytest.raises(ValueError):
            string.add_annotation(annotation)
        assert string.annotations == []

    def test_annotations_sort(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 2, 3)  # te[s]t
        string.annotate(SampleAnnotation, 1, 3)  # t[es]t
        string.annotate(SampleAnnotation, 0, 2)  # [te]st
        string.annotate(SampleAnnotation, 0, 1)  # [t]est
        assert string.annotations == [
            SampleAnnotation("test", 0, 1),  # [t]est
            SampleAnnotation("test", 0, 2),  # [te]st
            SampleAnnotation("test", 1, 3),  # t[es]t
            SampleAnnotation("test", 2, 3),  # te[s]t
        ]

    def test_get_annotations_one(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotations(SampleAnnotation) == [
            SampleAnnotation("test", 1, 2)
        ]

    def test_get_annotations_none(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotations(SampleAnnotation) == []

    def test_get_annotations_many(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation, 2, 3)
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotations(SampleAnnotation) == [
            SampleAnnotation("test", 1, 2),
            SampleAnnotation("test", 2, 3),
        ]

    def test_get_annotation_or_none_one(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotation_or_none(SampleAnnotation) == SampleAnnotation(
            "test", 1, 2
        )

    def test_get_annotation_or_none_none(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotation_or_none(SampleAnnotation) is None

    def test_get_annotation_or_none_many(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation, 2, 3)
        string.annotate(SampleAnnotation2, 1, 2)
        with pytest.raises(ValueError):
            string.get_annotation_or_none(SampleAnnotation)

    def test_get_annotation_one(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation2, 1, 2)
        assert string.get_annotation(SampleAnnotation) == SampleAnnotation("test", 1, 2)

    def test_get_annotation_none(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation2, 1, 2)
        with pytest.raises(KeyError):
            string.get_annotation(SampleAnnotation)

    def test_get_annotation_many(self) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, 1, 2)
        string.annotate(SampleAnnotation, 2, 3)
        string.annotate(SampleAnnotation2, 1, 2)
        with pytest.raises(ValueError):
            string.get_annotation(SampleAnnotation)

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
            (1, 1, 1, 3, 0, 0),  # t|[]es|t
            (3, 3, 1, 3, 2, 2),  # t|es[]|t
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
        string.annotate(SampleAnnotation, start, stop)
        sliced_string = string[slice_start:slice_stop]
        assert sliced_string.string == "test"[slice_start:slice_stop]
        assert sliced_string.annotations == [
            SampleAnnotation(sliced_string.string, expected_start, expected_stop)
        ]

    @pytest.mark.parametrize(
        ("start", "stop", "slice_start", "slice_stop"),
        [
            (2, 3, 0, 1),  # |t|e[s]t
            (1, 2, 3, 4),  # t[e]s|t|
            (2, 3, 1, 2),  # t|e|[s]t
            (1, 2, 2, 3),  # t[e]|s|t
        ],
    )
    def test_getitem_annotation_disjoint(
        self, start: int, stop: int, slice_start: int, slice_stop: int
    ) -> None:
        string = AnnotatedString("test")
        string.annotate(SampleAnnotation, start, stop)
        sliced_string = string[slice_start:slice_stop]
        assert sliced_string.string == "test"[slice_start:slice_stop]
        assert sliced_string.annotations == []

    def test_add_string(self) -> None:
        string = AnnotatedString("foo")
        string.annotate(SampleAnnotation, 2, 3)

        result = string + "bar"
        assert result.string == "foobar"
        assert result.annotations == [SampleAnnotation("foobar", 2, 3)]

    def test_add_annotated_string(self) -> None:
        string = AnnotatedString("foo")
        string.annotate(SampleAnnotation, 2, 3)
        string2 = AnnotatedString("bar")
        string2.annotate(SampleAnnotation, 1, 2)
        string2.annotate(SampleAnnotation2, 2, 3)

        result = string + string2
        assert result.string == "foobar"
        assert result.annotations == [
            SampleAnnotation("foobar", 2, 3),
            SampleAnnotation("foobar", 4, 5),
            SampleAnnotation2("foobar", 5, 6),
        ]

    def test_add_unsupported_type(self) -> None:
        string = AnnotatedString("foo")
        string.annotate(SampleAnnotation, 2, 3)

        with pytest.raises(TypeError):
            _ = string + object()  # ty:ignore[unsupported-operator]


class TestStringAnnotation:
    def test_lt_unsupported_type(self) -> None:
        with pytest.raises(TypeError):
            _ = SampleAnnotation("test", 0, 1) < object()  # ty:ignore[unsupported-operator]

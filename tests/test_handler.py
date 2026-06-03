"""Unit tests for the Lambda parse logic.

These tests cover the pure `parse_line` function. They do not require
boto3, AWS credentials, or any mocking, because parsing has no side
effects.
"""
from handler import parse_line


def test_parse_line_basic_csv() -> None:
    """Three comma-separated values produce three positional fields."""
    result = parse_line("apple,banana,cherry")
    assert result == {
        "field_1": "apple",
        "field_2": "banana",
        "field_3": "cherry",
    }


def test_parse_line_single_field() -> None:
    """A line with no delimiter is a single field."""
    result = parse_line("only-one")
    assert result == {"field_1": "only-one"}


def test_parse_line_empty_string() -> None:
    """An empty line returns an empty dict."""
    assert parse_line("") == {}


def test_parse_line_quoted_field_with_comma() -> None:
    """Quoted fields preserve embedded commas via the csv module."""
    result = parse_line('"hello, world",foo,bar')
    assert result == {
        "field_1": "hello, world",
        "field_2": "foo",
        "field_3": "bar",
    }


def test_parse_line_preserves_whitespace_in_fields() -> None:
    """The csv module does not strip whitespace from unquoted fields."""
    result = parse_line("a, b ,c")
    assert result == {"field_1": "a", "field_2": " b ", "field_3": "c"}


def test_parse_line_trailing_empty_field() -> None:
    """A trailing comma produces an empty final field."""
    result = parse_line("a,b,")
    assert result == {"field_1": "a", "field_2": "b", "field_3": ""}


def test_parse_line_numeric_strings_stay_strings() -> None:
    """Values are not coerced to numeric types."""
    result = parse_line("1,2.5,3")
    assert result == {"field_1": "1", "field_2": "2.5", "field_3": "3"}
    assert all(isinstance(v, str) for v in result.values())

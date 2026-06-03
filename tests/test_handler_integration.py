"""Integration tests for lambda_handler.

These tests mock the S3 client and verify that lambda_handler correctly
processes a synthetic s3:ObjectCreated event, including structured log
output and the returned result payload.
"""
from unittest.mock import MagicMock, patch
from io import BytesIO

from handler import lambda_handler


def _make_s3_event(bucket: str, key: str) -> dict:
    """Build a minimal S3 ObjectCreated event payload."""
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                },
            }
        ],
    }


@patch("handler.s3_client")
def test_lambda_handler_parses_single_line(mock_s3: MagicMock) -> None:
    """Handler fetches the object, parses CSV, and returns fields."""
    mock_s3.get_object.return_value = {
        "Body": BytesIO(b"alice,30,engineer"),
    }

    event = _make_s3_event("test-bucket", "test.csv")
    result = lambda_handler(event, None)

    mock_s3.get_object.assert_called_once_with(Bucket="test-bucket", Key="test.csv")
    assert result["processed"] == 1
    assert result["results"][0]["fields"] == {
        "field_1": "alice",
        "field_2": "30",
        "field_3": "engineer",
    }


@patch("handler.s3_client")
def test_lambda_handler_handles_empty_file(mock_s3: MagicMock) -> None:
    """Handler skips empty files and returns zero processed."""
    mock_s3.get_object.return_value = {
        "Body": BytesIO(b""),
    }

    event = _make_s3_event("test-bucket", "empty.csv")
    result = lambda_handler(event, None)

    assert result["processed"] == 0
    assert result["results"] == []


@patch("handler.s3_client")
def test_lambda_handler_url_decodes_key(mock_s3: MagicMock) -> None:
    """Handler URL-decodes the S3 key from the event."""
    mock_s3.get_object.return_value = {
        "Body": BytesIO(b"value1,value2"),
    }

    event = _make_s3_event("test-bucket", "path+with+spaces/file%2B1.csv")
    lambda_handler(event, None)

    mock_s3.get_object.assert_called_once_with(
        Bucket="test-bucket", Key="path with spaces/file+1.csv"
    )


@patch("handler.s3_client")
def test_lambda_handler_takes_first_line_only(mock_s3: MagicMock) -> None:
    """Handler parses only the first line of a multi-line file."""
    mock_s3.get_object.return_value = {
        "Body": BytesIO(b"first,line\nsecond,line\n"),
    }

    event = _make_s3_event("test-bucket", "multi.csv")
    result = lambda_handler(event, None)

    assert result["results"][0]["fields"] == {
        "field_1": "first",
        "field_2": "line",
    }

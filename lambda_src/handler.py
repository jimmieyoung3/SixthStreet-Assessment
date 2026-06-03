"""Lambda handler that processes single-line files uploaded to S3.

The handler is invoked by S3 event notifications on s3:ObjectCreated:*.
For each record in the event, it:

1. Extracts the bucket name and object key.
2. Fetches the object from S3.
3. Decodes the body as UTF-8 and reads the first line.
4. Parses the line as comma-separated values using the standard library
   `csv` module, producing a dict with positional field names
   (field_1, field_2, ...). This handles quoted fields containing
   commas correctly.
5. Emits a structured JSON log entry describing the parse result.

Errors are logged and re-raised so that Lambda marks the invocation as
failed and S3 / Lambda retry behavior applies.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import urllib.parse
from typing import Any

import boto3

# ---------------------------------------------------------------------------
# Module-level setup
# ---------------------------------------------------------------------------
# boto3 clients are created once per container and reused across invocations,
# which is the standard pattern for Lambda cold-start optimization.

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

s3_client = boto3.client("s3")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_line(line: str) -> dict[str, str]:
    """Parse a single CSV line into a dict with positional field names.

    Uses the stdlib `csv` module so quoted fields containing commas are
    handled correctly. Field names are positional (`field_1`, `field_2`, ...)
    because the prompt does not specify a schema.

    Args:
        line: A single line of CSV-formatted text. May be empty.

    Returns:
        A dict mapping `field_<n>` to the n-th field. Empty dict if the
        input is empty.
    """
    if not line:
        return {}
    reader = csv.reader([line])
    fields = next(reader, [])
    return {f"field_{i + 1}": value for i, value in enumerate(fields)}


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
def _log(event: str, **fields: Any) -> None:
    """Emit a single-line JSON log entry to CloudWatch Logs."""
    logger.info(json.dumps({"event": event, **fields}, default=str))


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Entry point invoked by S3 ObjectCreated event notifications.

    The S3 event schema is documented at:
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html
    """
    records = event.get("Records", [])
    _log("invocation_start", record_count=len(records))

    results: list[dict[str, Any]] = []

    for record in records:
        try:
            bucket = record["s3"]["bucket"]["name"]
            # Keys in S3 event notifications are URL-encoded.
            key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        except KeyError as exc:
            _log("malformed_record", error=str(exc), record=record)
            raise

        _log("object_received", bucket=bucket, key=key)

        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read().decode("utf-8")
        except Exception as exc:
            _log("s3_get_object_failed", bucket=bucket, key=key, error=str(exc))
            raise

        content = body.strip()
        if not content:
            _log("empty_file", bucket=bucket, key=key)
            continue

        # Take the first line. The prompt specifies single-line files, but
        # guarding against trailing newlines or accidental multi-line input
        # is cheap and avoids surprising behavior.
        first_line = content.splitlines()[0]
        parsed = parse_line(first_line)

        _log(
            "object_parsed",
            bucket=bucket,
            key=key,
            field_count=len(parsed),
            fields=parsed,
        )

        results.append({"bucket": bucket, "key": key, "fields": parsed})

    _log("invocation_complete", processed=len(results))
    return {"processed": len(results), "results": results}

"""Pytest configuration.

Adds the `lambda_src/` directory to `sys.path` so test modules can
`from handler import ...` directly. Lambda code lives in `lambda_src/`
without a package wrapper because that mirrors how it is deployed:
Lambda invokes `handler.lambda_handler` against the bare module.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "lambda_src"))

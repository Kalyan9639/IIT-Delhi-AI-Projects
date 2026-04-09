from __future__ import annotations

import sys


def assert_expected_interpreter() -> None:
    """
    Fail fast when the app is launched from the global interpreter instead of a virtual environment.
    """
    if sys.prefix == sys.base_prefix:
        raise RuntimeError(
            "This project should be run from a virtual environment. "
            "Activate your 'cs' venv and start the app with 'python -m uvicorn src.api:app --reload'."
        )

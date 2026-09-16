"""Narrowing helpers for values pulled out of a pandas frame.

``DataFrame.loc`` on a frame with mixed column types is typed as a union wide enough to include
timestamps and strings, so a plain ``float(...)`` on it does not type-check. Going through
``numpy`` narrows it for real rather than silencing the checker: ``item()`` raises on anything
that is not a scalar, so a shape error surfaces here instead of propagating as a wrong number.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def as_float(value: Any) -> float:
    """One scalar out of a frame, as a float."""
    return float(np.asarray(value).item())


def as_int(value: Any) -> int:
    """One scalar out of a frame, as an int."""
    return int(np.asarray(value).item())

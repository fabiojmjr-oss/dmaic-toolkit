"""Shared fixtures. The dataset is built once per session because it is deterministic."""

from __future__ import annotations

import pandas as pd
import pytest

from dmaic.synth import Dataset, generate_dataset


@pytest.fixture(scope="session")
def full() -> Dataset:
    """The published dataset, from the default seed."""
    return generate_dataset()


@pytest.fixture
def balanced() -> pd.DataFrame:
    """A 2x2x2 study whose ANOVA can be worked out by hand.

    The values are chosen so every sum of squares is an integer: part 242, operator 50,
    interaction 2, repeatability 8, total 302.
    """
    cells = {
        ("P1", "A"): [10.0, 12.0],
        ("P1", "B"): [14.0, 16.0],
        ("P2", "A"): [20.0, 22.0],
        ("P2", "B"): [26.0, 28.0],
    }
    rows = [
        {"part": part, "operator": operator, "replicate": index, "value": value}
        for (part, operator), values in cells.items()
        for index, value in enumerate(values, start=1)
    ]
    return pd.DataFrame(rows)

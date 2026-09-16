"""Two-group comparisons, each chosen to land in a different assumption regime.

Two of the four are drawn under the null - the group means are identical - which is what makes
the module's argument checkable rather than rhetorical. A significant result on those is a false
positive that can be named as one, and the procedure that produces it can be held responsible.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import COMPARISONS, ComparisonProfile

COMPARISON_COLUMNS = ("comparison", "group", "observation", "value")


def _draw(rng: np.random.Generator, n: int, mean: float, sd: float, shape: str) -> np.ndarray:
    if shape == "normal":
        return rng.normal(mean, sd, size=n)
    # Standardised lognormal, so only the shape differs from a normal with the same mean and sd.
    sigma = 0.75
    raw = rng.lognormal(0.0, sigma, size=n)
    centre = math.exp(sigma**2 / 2)
    spread = math.sqrt((math.exp(sigma**2) - 1) * math.exp(sigma**2))
    return mean + (raw - centre) / spread * sd


def _one_comparison(profile: ComparisonProfile, rng: np.random.Generator) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group, n, mean, sd in (
        (profile.first, profile.n_first, profile.mean_first, profile.sd_first),
        (profile.second, profile.n_second, profile.mean_second, profile.sd_second),
    ):
        for index, value in enumerate(_draw(rng, n, mean, sd, profile.shape), start=1):
            rows.append(
                {
                    "comparison": profile.comparison,
                    "group": group,
                    "observation": index,
                    "value": float(value),
                }
            )
    return pd.DataFrame(rows)


def group_comparisons(rng: np.random.Generator) -> pd.DataFrame:
    """Every comparison, tidy: one row per observation.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`COMPARISON_COLUMNS`.
    """
    frame = pd.concat([_one_comparison(profile, rng) for profile in COMPARISONS], ignore_index=True)
    frame["comparison"] = frame["comparison"].astype("category")
    frame["group"] = frame["group"].astype("category")
    return frame[list(COMPARISON_COLUMNS)]


def comparison_designs() -> pd.DataFrame:
    """What each comparison was built to exercise, including whether a difference exists.

    ``true_difference`` is zero for the comparisons drawn under the null. It is the column that
    turns "the flowchart and Welch disagree" into "the flowchart is wrong here", which is a
    different and much stronger statement.
    """
    return pd.DataFrame(
        [
            {
                "comparison": profile.comparison,
                "question": profile.question,
                "unit": profile.unit,
                "n_first": profile.n_first,
                "n_second": profile.n_second,
                "sd_first": profile.sd_first,
                "sd_second": profile.sd_second,
                "shape": profile.shape,
                "true_difference": profile.mean_second - profile.mean_first,
                "regime": profile.regime,
            }
            for profile in COMPARISONS
        ]
    )

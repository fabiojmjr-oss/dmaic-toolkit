"""A panel that keeps going after the project closes, with a gain that decays as it does.

The effect decays exponentially from the period after the split, so the audit a year later sees
half of what the audit at closure did. The trend keeps running throughout, which is the feature
that matters: a sustain report built against the original baseline gets *better* every quarter
while the gain it is supposed to be verifying gets smaller.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SUSTAINS, SustainProfile

SUSTAIN_COLUMNS = ("process", "site", "period", "treated", "value")
DESIGN_COLUMNS = (
    "process",
    "unit",
    "sites",
    "periods",
    "split",
    "treated",
    "trend",
    "effect_at_close",
    "half_life",
    "close_window",
    "audit_window",
)


def true_effect(profile: SustainProfile, period: int) -> float:
    """The effect actually present in a given period, which is what an audit is estimating.

    Zero up to and including the split, then decaying from the first period after it.

    Args:
        profile: The panel's parameters.
        period: The period to evaluate, counted from one.

    Returns:
        The effect in that period, signed.
    """
    if period <= profile.split:
        return 0.0
    elapsed = period - profile.split - 1
    return profile.effect_at_close * 0.5 ** (elapsed / profile.half_life)


def mean_true_effect(profile: SustainProfile, first: int, last: int) -> float:
    """The average effect over a window, which is what a window's estimate is an estimate of."""
    if last < first:
        raise ValueError(f"the window {first}-{last} runs backwards")
    return float(np.mean([true_effect(profile, period) for period in range(first, last + 1)]))


def _one_panel(profile: SustainProfile, rng: np.random.Generator) -> pd.DataFrame:
    level = profile.level + rng.normal(0.0, profile.site_sd, size=profile.sites)
    treated = np.zeros(profile.sites, dtype=bool)
    treated[rng.choice(profile.sites, size=profile.treated, replace=False)] = True

    rows: list[dict[str, object]] = []
    for index in range(profile.sites):
        for period in range(1, profile.periods + 1):
            value = (
                level[index] + profile.trend * (period - 1) + float(rng.normal(0.0, profile.noise))
            )
            if treated[index]:
                value += true_effect(profile, period)
            rows.append(
                {
                    "process": profile.process,
                    "site": f"CD-{index + 1:02d}",
                    "period": period,
                    "treated": bool(treated[index]),
                    "value": value,
                }
            )
    return pd.DataFrame(rows)


def sustain_panel(rng: np.random.Generator) -> pd.DataFrame:
    """The long panel, tidy: one row per site and period.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`SUSTAIN_COLUMNS`.
    """
    frame = pd.concat([_one_panel(profile, rng) for profile in SUSTAINS], ignore_index=True)
    for column in ("process", "site"):
        frame[column] = frame[column].astype("category")
    return frame[list(SUSTAIN_COLUMNS)]


def sustain_designs() -> pd.DataFrame:
    """The decay that was built in, which is the column a sustain audit is trying to recover."""
    return pd.DataFrame(
        [
            {
                "process": profile.process,
                "unit": profile.unit,
                "sites": profile.sites,
                "periods": profile.periods,
                "split": profile.split,
                "treated": profile.treated,
                "trend": profile.trend,
                "effect_at_close": profile.effect_at_close,
                "half_life": profile.half_life,
                "close_window": profile.close_window,
                "audit_window": profile.audit_window,
            }
            for profile in SUSTAINS
        ]
    )[list(DESIGN_COLUMNS)]

"""Sites measured over periods, with the improvement, the trend and the selection kept separate.

The treated sites are chosen at random. That is not realism - projects are chartered on the worst
performers, and everybody knows it - it is what makes the panel usable: with selection random, the
true effect is recoverable, so an estimator can be checked against it. Selection on performance is
simulated separately in :func:`dmaic.improve.regression_to_the_mean`, because a panel carrying both
errors at once would leave no way to say which of them produced which part of a wrong answer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PANELS, PanelProfile

PANEL_COLUMNS = ("stream", "site", "period", "phase", "treated", "value")
DESIGN_COLUMNS = (
    "stream",
    "unit",
    "sites",
    "periods",
    "split",
    "trend",
    "true_effect",
    "treated",
    "units_per_period",
    "variable_share",
    "project_cost",
)
PHASES = ("before", "after")


def _one_panel(profile: PanelProfile, rng: np.random.Generator) -> pd.DataFrame:
    level = profile.level + rng.normal(0.0, profile.site_sd, size=profile.sites)
    treated = np.zeros(profile.sites, dtype=bool)
    treated[rng.choice(profile.sites, size=profile.treated, replace=False)] = True

    rows: list[dict[str, object]] = []
    for index in range(profile.sites):
        for period in range(1, profile.periods + 1):
            value = (
                level[index] + profile.trend * (period - 1) + float(rng.normal(0.0, profile.noise))
            )
            if treated[index] and period > profile.split:
                value += profile.true_effect
            rows.append(
                {
                    "stream": profile.stream,
                    "site": f"CD-{index + 1:02d}",
                    "period": period,
                    "phase": PHASES[0] if period <= profile.split else PHASES[1],
                    "treated": bool(treated[index]),
                    "value": value,
                }
            )
    return pd.DataFrame(rows)


def site_performance(rng: np.random.Generator) -> pd.DataFrame:
    """The panel, tidy: one row per site and period.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`PANEL_COLUMNS`.
    """
    frame = pd.concat([_one_panel(profile, rng) for profile in PANELS], ignore_index=True)
    for column in ("stream", "site", "phase"):
        frame[column] = frame[column].astype("category")
    return frame[list(PANEL_COLUMNS)]


def improvement_designs() -> pd.DataFrame:
    """What was done to the panel, including the effect and the trend that were put into it.

    ``trend`` is the column a real project never has, and it is the one that decides whether a
    reported saving belongs to the project or to the calendar.
    """
    return pd.DataFrame(
        [
            {
                "stream": profile.stream,
                "unit": profile.unit,
                "sites": profile.sites,
                "periods": profile.periods,
                "split": profile.split,
                "trend": profile.trend,
                "true_effect": profile.true_effect,
                "treated": profile.treated,
                "units_per_period": profile.units_per_period,
                "variable_share": profile.variable_share,
                "project_cost": profile.project_cost,
            }
            for profile in PANELS
        ]
    )[list(DESIGN_COLUMNS)]

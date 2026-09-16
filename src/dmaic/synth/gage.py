"""A crossed gage study: every operator measures every part, several times."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import GAGES, OPERATORS, PARTS, REPLICATES, GageProfile

GAGE_COLUMNS = ("gage", "part", "operator", "replicate", "value")


def _one_study(profile: GageProfile, rng: np.random.Generator) -> pd.DataFrame:
    """One gage's study, drawn in a fixed order so the stream stays stable."""
    part_true = profile.nominal + rng.normal(0.0, profile.part_sd, size=PARTS)
    operator_bias = rng.normal(0.0, profile.operator_sd, size=len(OPERATORS))
    interaction = rng.normal(0.0, profile.interaction_sd, size=(PARTS, len(OPERATORS)))

    rows = []
    for part_index in range(PARTS):
        for operator_index, operator in enumerate(OPERATORS):
            # The cell mean an operator would converge on if they measured this part forever.
            cell = (
                part_true[part_index]
                + operator_bias[operator_index]
                + interaction[part_index, operator_index]
            )
            for replicate in range(1, REPLICATES + 1):
                rows.append(
                    {
                        "gage": profile.gage,
                        "part": f"P-{part_index + 1:02d}",
                        "operator": operator,
                        "replicate": replicate,
                        "value": cell + rng.normal(0.0, profile.repeat_sd),
                    }
                )
    return pd.DataFrame(rows)


def gage_studies(rng: np.random.Generator) -> pd.DataFrame:
    """Every gage study, tidy: one row per measurement.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`GAGE_COLUMNS`.
    """
    frame = pd.concat([_one_study(profile, rng) for profile in GAGES], ignore_index=True)
    frame["gage"] = frame["gage"].astype("category")
    frame["part"] = frame["part"].astype("category")
    frame["operator"] = frame["operator"].astype("category")
    return frame[list(GAGE_COLUMNS)]


def specifications() -> pd.DataFrame:
    """The specification each gage is judged against.

    Kept as its own table rather than as columns on the measurements, because a specification is
    a property of the product and a gage study is a property of the measurement system. Joining
    them is a decision the caller makes, and :func:`dmaic.measure.gage_rr` asks for the tolerance
    explicitly rather than finding it.
    """
    return pd.DataFrame(
        [
            {
                "gage": profile.gage,
                "measurand": profile.measurand,
                "unit": profile.unit,
                "nominal": profile.nominal,
                "lsl": profile.lsl,
                "usl": profile.usl,
                "tolerance": profile.tolerance,
            }
            for profile in GAGES
        ]
    )

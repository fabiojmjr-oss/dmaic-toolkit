"""Lots arriving for acceptance inspection, with the state of each one declared.

The realised defective count is generated, not just the probability, because an acceptance
sampling plan draws from a finite lot: the sample is hypergeometric in the defectives that are
actually in it, and a plan evaluated on the binomial approximation is being flattered whenever the
sample is a material share of the lot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import LOTS, LotProfile

LOT_COLUMNS = ("stream", "lot", "lot_size", "state", "defectives", "fraction")
STATE_IN_CONTROL = "in control"
STATE_EXCURSION = "excursion"


def _one_stream(profile: LotProfile, rng: np.random.Generator) -> pd.DataFrame:
    excursion = rng.random(profile.lots) < profile.excursion_share
    rows: list[dict[str, object]] = []
    for index, is_excursion in enumerate(excursion, start=1):
        rate = profile.excursion_fraction if is_excursion else profile.in_control_fraction
        defectives = int(rng.binomial(profile.lot_size, rate))
        rows.append(
            {
                "stream": profile.stream,
                "lot": index,
                "lot_size": profile.lot_size,
                "state": STATE_EXCURSION if is_excursion else STATE_IN_CONTROL,
                "defectives": defectives,
                "fraction": defectives / profile.lot_size,
            }
        )
    return pd.DataFrame(rows)


def inspection_lots(rng: np.random.Generator) -> pd.DataFrame:
    """Every lot, with the realised number of defective units in it.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`LOT_COLUMNS`.
    """
    frame = pd.concat([_one_stream(profile, rng) for profile in LOTS], ignore_index=True)
    frame["stream"] = frame["stream"].astype("category")
    frame["state"] = frame["state"].astype("category")
    return frame[list(LOT_COLUMNS)]


def lot_designs() -> pd.DataFrame:
    """What each stream was built to contain, including the two states' true rates."""
    return pd.DataFrame(
        [
            {
                "stream": profile.stream,
                "lots": profile.lots,
                "lot_size": profile.lot_size,
                "excursion_share": profile.excursion_share,
                "in_control_fraction": profile.in_control_fraction,
                "excursion_fraction": profile.excursion_fraction,
            }
            for profile in LOTS
        ]
    )

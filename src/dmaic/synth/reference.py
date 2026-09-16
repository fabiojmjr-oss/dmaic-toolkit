"""Readings taken on calibrated masters, which is the only way accuracy becomes measurable.

A crossed gage study compares the gage to itself and to the parts. Nothing in it refers to what
the parts actually are, so no arrangement of its arithmetic can say whether the readings are
right - only whether they agree. Accuracy needs an outside value, and this table is where that
value enters the repository.

The masters here are exact by construction. A real one is not, and that limitation is stated in
the module documentation rather than hidden: a reference study measures the difference between
two measurement systems and attributes all of it to the one being studied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import GAGES, REFERENCES, GageProfile, ReferenceProfile

REFERENCE_COLUMNS = ("gage", "reference", "reading", "value")
DESIGN_COLUMNS = (
    "gage",
    "nominal",
    "tolerance",
    "repeat_sd",
    "bias_at_nominal",
    "bias_slope",
    "references",
    "repeats",
)


def _gage(name: str) -> GageProfile:
    """The crossed study's profile for this gage, so both studies describe one instrument."""
    for profile in GAGES:
        if profile.gage == name:
            return profile
    raise KeyError(f"{name!r} is not one of the gages in the generator")


def _true_bias(profile: ReferenceProfile, gage: GageProfile, reference: float) -> float:
    """What the gage adds at this reference value, which is what the study has to recover."""
    return profile.bias_at_nominal + profile.bias_slope * (reference - gage.nominal)


def _one_study(profile: ReferenceProfile, rng: np.random.Generator) -> pd.DataFrame:
    gage = _gage(profile.gage)
    rows: list[dict[str, object]] = []
    for reference in profile.references:
        offset = _true_bias(profile, gage, reference)
        draws = rng.normal(reference + offset, gage.repeat_sd, size=profile.repeats)
        rows.extend(
            {
                "gage": profile.gage,
                "reference": reference,
                "reading": index,
                "value": float(value),
            }
            for index, value in enumerate(draws, start=1)
        )
    return pd.DataFrame(rows)


def reference_studies(rng: np.random.Generator) -> pd.DataFrame:
    """Every reference study, tidy: one row per reading.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`REFERENCE_COLUMNS`.
    """
    frame = pd.concat([_one_study(profile, rng) for profile in REFERENCES], ignore_index=True)
    frame["gage"] = frame["gage"].astype("category")
    return frame[list(REFERENCE_COLUMNS)]


def reference_designs() -> pd.DataFrame:
    """The bias actually built into each gage, next to the specification it matters against.

    ``bias_at_nominal`` and ``bias_slope`` are the columns a real study does not have. They are
    what turns "the study found an offset" into "the study found the offset that is there", and
    what makes a study that finds nothing on `INSPECAO-03` a correct answer rather than a miss.
    """
    return pd.DataFrame(
        [
            {
                "gage": profile.gage,
                "nominal": _gage(profile.gage).nominal,
                "tolerance": _gage(profile.gage).tolerance,
                "repeat_sd": _gage(profile.gage).repeat_sd,
                "bias_at_nominal": profile.bias_at_nominal,
                "bias_slope": profile.bias_slope,
                "references": len(profile.references),
                "repeats": profile.repeats,
            }
            for profile in REFERENCES
        ]
    )[list(DESIGN_COLUMNS)]

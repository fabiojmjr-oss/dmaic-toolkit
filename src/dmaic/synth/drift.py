"""A gage that moves, generated so that only the schedule differs between two studies.

The part values, the operator biases, the part-by-operator interaction and every repeatability
draw are taken once and shared. What changes between the two schedules is which day each reading
falls on, and therefore how much drift is in it. Holding the draws fixed is what makes the
comparison a statement about the schedule rather than about luck - the same device wave 4 uses to
compare two fractions of one experiment.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DRIFTS, GAGES, OPERATORS, PARTS, REPLICATES, DriftProfile, GageProfile

DRIFT_COLUMNS = ("gage", "schedule", "part", "operator", "replicate", "day", "value")
CHECK_COLUMNS = ("gage", "day", "reading", "reference", "value")
DRIFT_DESIGN_COLUMNS = (
    "gage",
    "drift_per_day",
    "session_gap_days",
    "study_span_days",
    "check_span_days",
    "tolerance",
    "repeat_sd",
)


def _gage(name: str) -> GageProfile:
    for profile in GAGES:
        if profile.gage == name:
            return profile
    raise KeyError(f"{name!r} is not one of the gages in the generator")


def _day(schedule: str, operator_index: int, replicate_index: int, gap: int) -> int:
    """Which day a reading falls on, which is the only thing the schedule decides.

    Both schedules use the same days and the same number of readings on each. Sequential gives
    each operator one day; interleaved gives each replicate one day, so every operator measures
    on every day.
    """
    if schedule == "sequential":
        return gap * operator_index
    if schedule == "interleaved":
        return gap * replicate_index
    raise ValueError(f"unknown schedule {schedule!r}")


def _one_drift_study(profile: DriftProfile, rng: np.random.Generator) -> pd.DataFrame:
    gage = _gage(profile.gage)
    part_true = gage.nominal + rng.normal(0.0, gage.part_sd, size=PARTS)
    operator_bias = rng.normal(0.0, gage.operator_sd, size=len(OPERATORS))
    interaction = rng.normal(0.0, gage.interaction_sd, size=(PARTS, len(OPERATORS)))
    repeatability = rng.normal(0.0, gage.repeat_sd, size=(PARTS, len(OPERATORS), REPLICATES))

    rows: list[dict[str, object]] = []
    for schedule in profile.schedules:
        for part_index in range(PARTS):
            for operator_index, operator in enumerate(OPERATORS):
                for replicate_index in range(REPLICATES):
                    day = _day(schedule, operator_index, replicate_index, profile.session_gap_days)
                    rows.append(
                        {
                            "gage": profile.gage,
                            "schedule": schedule,
                            "part": f"P-{part_index + 1:02d}",
                            "operator": operator,
                            "replicate": replicate_index + 1,
                            "day": day,
                            "value": float(
                                part_true[part_index]
                                + operator_bias[operator_index]
                                + interaction[part_index, operator_index]
                                + repeatability[part_index, operator_index, replicate_index]
                                + profile.drift_per_day * day
                            ),
                        }
                    )
    return pd.DataFrame(rows)


def _one_check_series(profile: DriftProfile, rng: np.random.Generator) -> pd.DataFrame:
    gage = _gage(profile.gage)
    rows: list[dict[str, object]] = []
    for day in range(0, profile.check_span_days + 1, profile.check_every_days):
        offset = profile.drift_per_day * day
        draws = rng.normal(gage.nominal + offset, gage.repeat_sd, size=profile.readings_per_check)
        rows.extend(
            {
                "gage": profile.gage,
                "day": day,
                "reading": index,
                "reference": gage.nominal,
                "value": float(value),
            }
            for index, value in enumerate(draws, start=1)
        )
    return pd.DataFrame(rows)


def drift_studies(rng: np.random.Generator) -> pd.DataFrame:
    """The crossed study under each schedule, one row per reading.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`DRIFT_COLUMNS`.
    """
    frame = pd.concat([_one_drift_study(profile, rng) for profile in DRIFTS], ignore_index=True)
    for column in ("gage", "schedule", "part", "operator"):
        frame[column] = frame[column].astype("category")
    return frame[list(DRIFT_COLUMNS)]


def stability_checks(rng: np.random.Generator) -> pd.DataFrame:
    """Periodic readings on the master, which is what says how long a calibration lasts.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`CHECK_COLUMNS`.
    """
    frame = pd.concat([_one_check_series(profile, rng) for profile in DRIFTS], ignore_index=True)
    frame["gage"] = frame["gage"].astype("category")
    return frame[list(CHECK_COLUMNS)]


def drift_designs() -> pd.DataFrame:
    """The drift rate that was built in, next to the specification it eats into."""
    return pd.DataFrame(
        [
            {
                "gage": profile.gage,
                "drift_per_day": profile.drift_per_day,
                "session_gap_days": profile.session_gap_days,
                "study_span_days": profile.session_gap_days * (len(OPERATORS) - 1),
                "check_span_days": profile.check_span_days,
                "tolerance": _gage(profile.gage).tolerance,
                "repeat_sd": _gage(profile.gage).repeat_sd,
            }
            for profile in DRIFTS
        ]
    )[list(DRIFT_DESIGN_COLUMNS)]

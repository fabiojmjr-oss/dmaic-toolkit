"""Two-arm improvement trials, with the true effect declared rather than hidden.

The generator knows the effect it put in. That is the advantage of synthetic data over a case
study here, and it is used deliberately: a real project that finds nothing cannot tell whether
the effect was absent or merely out of reach, which is exactly the ambiguity
:mod:`dmaic.analyze.power` exists to remove. With the truth on the record, a non-significant
result can be shown to be a type II error rather than argued about.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import TRIALS, TrialProfile

TRIAL_COLUMNS = ("trial", "arm", "observation", "value")
ARMS = ("baseline", "improved")


def _one_trial(profile: TrialProfile, rng: np.random.Generator) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for arm in ARMS:
        # The improved arm carries the true effect. For a scrap rate the effect is negative and
        # the measurement is a Bernoulli draw, so a "better" arm is a lower probability.
        shift = profile.true_effect if arm == "improved" else 0.0
        if profile.kind == "binary":
            probability = profile.baseline + shift
            draws = rng.binomial(1, probability, size=profile.n_per_arm).astype(float)
        else:
            draws = rng.normal(profile.baseline + shift, profile.sd, size=profile.n_per_arm)
        rows.extend(
            {
                "trial": profile.trial,
                "arm": arm,
                "observation": index,
                "value": float(value),
            }
            for index, value in enumerate(draws, start=1)
        )
    return pd.DataFrame(rows)


def improvement_trials(rng: np.random.Generator) -> pd.DataFrame:
    """Every trial, tidy: one row per observation.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with the columns in :data:`TRIAL_COLUMNS`.
    """
    frame = pd.concat([_one_trial(profile, rng) for profile in TRIALS], ignore_index=True)
    frame["trial"] = frame["trial"].astype("category")
    frame["arm"] = frame["arm"].astype("category")
    return frame[list(TRIAL_COLUMNS)]


def trial_designs() -> pd.DataFrame:
    """What each trial was designed to do, and the effect actually put into it.

    ``true_effect`` is the honest column and the one a real project never has. It is what makes
    the difference between "the test found nothing" and "the test missed something" checkable
    rather than rhetorical.
    """
    return pd.DataFrame(
        [
            {
                "trial": profile.trial,
                "measurand": profile.measurand,
                "unit": profile.unit,
                "kind": profile.kind,
                "n_per_arm": profile.n_per_arm,
                "baseline": profile.baseline,
                "true_effect": profile.true_effect,
                "sd": profile.sd,
            }
            for profile in TRIALS
        ]
    )

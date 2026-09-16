"""One seeded dataset feeding every module, so no example needs its own fixture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .comparison import comparison_designs, group_comparisons
from .config import SEED
from .factorial import factorial_effects, factorial_runs
from .gage import gage_studies, specifications
from .reference import reference_designs, reference_studies
from .trial import improvement_trials, trial_designs


@dataclass(frozen=True)
class Dataset:
    """Every table the toolkit's examples and tests are built on.

    Attributes:
        gage_studies: One row per measurement in a crossed gage study.
        specifications: One row per gage, with the tolerance it is judged against.
        improvement_trials: One row per observation in a two-arm pilot.
        trial_designs: One row per pilot, including the effect actually put into it.
        group_comparisons: One row per observation in a two-group comparison.
        comparison_designs: One row per comparison, including whether a difference exists.
        factorial_runs: One row per run of a designed experiment, factors coded -1 and +1.
        factorial_effects: One row per effect of each experiment, including the ones set to zero.
        reference_studies: One row per reading taken on a calibrated master.
        reference_designs: One row per gage, with the bias actually built into it.
    """

    gage_studies: pd.DataFrame
    specifications: pd.DataFrame
    improvement_trials: pd.DataFrame
    trial_designs: pd.DataFrame
    group_comparisons: pd.DataFrame
    comparison_designs: pd.DataFrame
    factorial_runs: pd.DataFrame
    factorial_effects: pd.DataFrame
    reference_studies: pd.DataFrame
    reference_designs: pd.DataFrame


def generate_dataset(seed: int = SEED) -> Dataset:
    """Build the whole dataset from one seed.

    New tables are appended at the end of this function rather than inserted, because the
    generator is consumed in stream order: inserting a draw shifts every later table and every
    published figure with it.

    Args:
        seed: Seed for the shared generator. The published figures all use the default.

    Returns:
        A :class:`Dataset`.
    """
    rng = np.random.default_rng(seed)
    return Dataset(
        gage_studies=gage_studies(rng),
        specifications=specifications(),
        # Appended after the gage study, so wave 1's published figures are untouched by wave 2.
        improvement_trials=improvement_trials(rng),
        trial_designs=trial_designs(),
        # Appended after the trials, so waves 1 and 2 are untouched by wave 3.
        group_comparisons=group_comparisons(rng),
        comparison_designs=comparison_designs(),
        # Appended after the comparisons, so waves 1 to 3 are untouched by wave 4.
        factorial_runs=factorial_runs(rng),
        factorial_effects=factorial_effects(),
        # Appended after the experiment, so waves 1 to 4 are untouched by wave 5.
        reference_studies=reference_studies(rng),
        reference_designs=reference_designs(),
    )

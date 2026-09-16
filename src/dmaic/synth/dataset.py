"""One seeded dataset feeding every module, so no example needs its own fixture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import SEED
from .gage import gage_studies, specifications
from .trial import improvement_trials, trial_designs


@dataclass(frozen=True)
class Dataset:
    """Every table the toolkit's examples and tests are built on.

    Attributes:
        gage_studies: One row per measurement in a crossed gage study.
        specifications: One row per gage, with the tolerance it is judged against.
        improvement_trials: One row per observation in a two-arm pilot.
        trial_designs: One row per pilot, including the effect actually put into it.
    """

    gage_studies: pd.DataFrame
    specifications: pd.DataFrame
    improvement_trials: pd.DataFrame
    trial_designs: pd.DataFrame


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
    )

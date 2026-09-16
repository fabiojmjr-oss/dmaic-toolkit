"""Seeded synthetic data for every module in the toolkit.

No operation's data is used anywhere in this repository. See ``DISCLAIMER.md``.
"""

from .comparison import COMPARISON_COLUMNS, comparison_designs, group_comparisons
from .config import (
    COMPARISONS,
    GAGES,
    OPERATORS,
    PARTS,
    REPLICATES,
    SEED,
    TRIALS,
    ComparisonProfile,
    GageProfile,
    TrialProfile,
)
from .dataset import Dataset, generate_dataset
from .gage import GAGE_COLUMNS, gage_studies, specifications
from .trial import ARMS, TRIAL_COLUMNS, improvement_trials, trial_designs

__all__ = [
    "ARMS",
    "COMPARISONS",
    "COMPARISON_COLUMNS",
    "GAGES",
    "GAGE_COLUMNS",
    "OPERATORS",
    "PARTS",
    "REPLICATES",
    "SEED",
    "TRIALS",
    "TRIAL_COLUMNS",
    "ComparisonProfile",
    "Dataset",
    "GageProfile",
    "TrialProfile",
    "comparison_designs",
    "gage_studies",
    "generate_dataset",
    "group_comparisons",
    "improvement_trials",
    "specifications",
    "trial_designs",
]

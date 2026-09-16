"""Seeded synthetic data for every module in the toolkit.

No operation's data is used anywhere in this repository. See ``DISCLAIMER.md``.
"""

from .comparison import COMPARISON_COLUMNS, comparison_designs, group_comparisons
from .config import (
    COMPARISONS,
    FACTORIALS,
    GAGES,
    OPERATORS,
    PARTS,
    REFERENCES,
    REPLICATES,
    SEED,
    TRIALS,
    ComparisonProfile,
    FactorialProfile,
    FactorSetting,
    GageProfile,
    ReferenceProfile,
    TrialProfile,
)
from .dataset import Dataset, generate_dataset
from .factorial import factorial_effects, factorial_runs
from .gage import GAGE_COLUMNS, gage_studies, specifications
from .reference import REFERENCE_COLUMNS, reference_designs, reference_studies
from .trial import ARMS, TRIAL_COLUMNS, improvement_trials, trial_designs

__all__ = [
    "ARMS",
    "COMPARISONS",
    "COMPARISON_COLUMNS",
    "FACTORIALS",
    "GAGES",
    "GAGE_COLUMNS",
    "OPERATORS",
    "PARTS",
    "REFERENCES",
    "REFERENCE_COLUMNS",
    "REPLICATES",
    "SEED",
    "TRIALS",
    "TRIAL_COLUMNS",
    "ComparisonProfile",
    "Dataset",
    "FactorSetting",
    "FactorialProfile",
    "GageProfile",
    "ReferenceProfile",
    "TrialProfile",
    "comparison_designs",
    "factorial_effects",
    "factorial_runs",
    "gage_studies",
    "generate_dataset",
    "group_comparisons",
    "improvement_trials",
    "reference_designs",
    "reference_studies",
    "specifications",
    "trial_designs",
]

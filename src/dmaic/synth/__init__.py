"""Seeded synthetic data for every module in the toolkit.

No operation's data is used anywhere in this repository. See ``DISCLAIMER.md``.
"""

from .config import GAGES, OPERATORS, PARTS, REPLICATES, SEED, TRIALS, GageProfile, TrialProfile
from .dataset import Dataset, generate_dataset
from .gage import GAGE_COLUMNS, gage_studies, specifications
from .trial import ARMS, TRIAL_COLUMNS, improvement_trials, trial_designs

__all__ = [
    "ARMS",
    "GAGES",
    "GAGE_COLUMNS",
    "OPERATORS",
    "PARTS",
    "REPLICATES",
    "SEED",
    "TRIALS",
    "TRIAL_COLUMNS",
    "Dataset",
    "GageProfile",
    "TrialProfile",
    "gage_studies",
    "generate_dataset",
    "improvement_trials",
    "specifications",
    "trial_designs",
]

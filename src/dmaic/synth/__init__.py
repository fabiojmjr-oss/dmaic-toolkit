"""Seeded synthetic data for every module in the toolkit.

No operation's data is used anywhere in this repository. See ``DISCLAIMER.md``.
"""

from .comparison import COMPARISON_COLUMNS, comparison_designs, group_comparisons
from .config import (
    COMPARISONS,
    DRIFTS,
    FACTORIALS,
    GAGES,
    LOTS,
    OPERATORS,
    PANELS,
    PARTS,
    REFERENCES,
    REPLICATES,
    SEED,
    SUSTAINS,
    TRIALS,
    ComparisonProfile,
    DriftProfile,
    FactorialProfile,
    FactorSetting,
    GageProfile,
    LotProfile,
    PanelProfile,
    ReferenceProfile,
    SustainProfile,
    TrialProfile,
)
from .dataset import Dataset, generate_dataset
from .drift import CHECK_COLUMNS, DRIFT_COLUMNS, drift_designs, drift_studies, stability_checks
from .factorial import factorial_effects, factorial_runs
from .gage import GAGE_COLUMNS, gage_studies, specifications
from .lots import LOT_COLUMNS, inspection_lots, lot_designs
from .panel import PANEL_COLUMNS, PHASES, improvement_designs, site_performance
from .reference import REFERENCE_COLUMNS, reference_designs, reference_studies
from .sustain import (
    SUSTAIN_COLUMNS,
    mean_true_effect,
    sustain_designs,
    sustain_panel,
    true_effect,
)
from .trial import ARMS, TRIAL_COLUMNS, improvement_trials, trial_designs

__all__ = [
    "ARMS",
    "CHECK_COLUMNS",
    "COMPARISONS",
    "COMPARISON_COLUMNS",
    "ComparisonProfile",
    "DRIFTS",
    "DRIFT_COLUMNS",
    "Dataset",
    "DriftProfile",
    "FACTORIALS",
    "FactorSetting",
    "FactorialProfile",
    "GAGES",
    "GAGE_COLUMNS",
    "GageProfile",
    "LOTS",
    "LOT_COLUMNS",
    "LotProfile",
    "OPERATORS",
    "PANELS",
    "PANEL_COLUMNS",
    "PARTS",
    "PHASES",
    "PanelProfile",
    "REFERENCES",
    "REFERENCE_COLUMNS",
    "REPLICATES",
    "ReferenceProfile",
    "SEED",
    "SUSTAINS",
    "SUSTAIN_COLUMNS",
    "SustainProfile",
    "TRIALS",
    "TRIAL_COLUMNS",
    "TrialProfile",
    "comparison_designs",
    "drift_designs",
    "drift_studies",
    "factorial_effects",
    "factorial_runs",
    "gage_studies",
    "generate_dataset",
    "group_comparisons",
    "improvement_designs",
    "improvement_trials",
    "inspection_lots",
    "lot_designs",
    "mean_true_effect",
    "reference_designs",
    "reference_studies",
    "site_performance",
    "specifications",
    "stability_checks",
    "sustain_designs",
    "sustain_panel",
    "trial_designs",
    "true_effect",
]

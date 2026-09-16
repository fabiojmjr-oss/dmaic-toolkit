"""Analyze: does the evidence support the conclusion being drawn from it?

Two gates, and neither is a p-value.

:mod:`~dmaic.analyze.power` asks what a test could possibly find. A study whose sample size was
fixed before anyone asked what it could detect has already decided its own conclusion for any
effect below its detection limit, and no amount of care in the analysis recovers that.

:mod:`~dmaic.analyze.compare` asks whether the test that was run holds the error rate it claims.
The taught answer - check normality, check variance, choose accordingly - is measurably worse than
skipping the checks and using Welch, and the module says so with simulated error rates rather
than with an appeal to authority.

:mod:`~dmaic.analyze.factorial` asks what a design can separate at all. A fraction makes pairs of
effects arithmetically identical, so a resolution III design does not return a main effect with
extra uncertainty on it - it returns the sum of that main effect and an interaction, and reports a
factor that does nothing as one of the largest in the study.
"""

from .compare import (
    NORMALITY_OVERSENSITIVE_ABOVE,
    NORMALITY_UNINFORMATIVE_BELOW,
    PROCEDURES,
    SIZE_RATIO_MATERIAL,
    SKEW_MATERIAL,
    SKEW_STANDARD_ERRORS,
    VARIANCE_RATIO_MATERIAL,
    Comparison,
    NormalityCheck,
    VarianceCheck,
    compare_means,
    equal_variance,
    normality,
    normality_test_tradeoff,
    skewness_standard_error,
    type_one_error_rates,
)
from .factorial import (
    IDENTITY,
    LETTERS,
    MAX_FACTORS,
    Design,
    alias_structure,
    detectable_effect,
    effects,
    fractional_factorial,
    full_factorial,
)
from .power import (
    DEFAULT_ALPHA,
    DEFAULT_POWER,
    UNDERPOWERED,
    Alternative,
    PowerAnalysis,
    detectable_difference,
    observed_power_is_circular,
    power_paired,
    power_two_means,
    power_two_proportions,
    sample_size_normal_approximation,
    sample_size_two_means,
    sample_size_two_proportions,
)

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_POWER",
    "IDENTITY",
    "LETTERS",
    "MAX_FACTORS",
    "NORMALITY_OVERSENSITIVE_ABOVE",
    "NORMALITY_UNINFORMATIVE_BELOW",
    "PROCEDURES",
    "SIZE_RATIO_MATERIAL",
    "SKEW_MATERIAL",
    "SKEW_STANDARD_ERRORS",
    "UNDERPOWERED",
    "VARIANCE_RATIO_MATERIAL",
    "Alternative",
    "Comparison",
    "Design",
    "NormalityCheck",
    "PowerAnalysis",
    "VarianceCheck",
    "alias_structure",
    "compare_means",
    "detectable_difference",
    "detectable_effect",
    "effects",
    "equal_variance",
    "fractional_factorial",
    "full_factorial",
    "normality",
    "normality_test_tradeoff",
    "observed_power_is_circular",
    "power_paired",
    "power_two_means",
    "power_two_proportions",
    "sample_size_normal_approximation",
    "sample_size_two_means",
    "sample_size_two_proportions",
    "skewness_standard_error",
    "type_one_error_rates",
]

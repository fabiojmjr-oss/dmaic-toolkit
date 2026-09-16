"""Analyze: does the evidence support the conclusion being drawn from it?

The first gate in this phase is not a test, it is the question of what a test could possibly find.
A study whose sample size was fixed before anyone asked what it could detect has already decided
its own conclusion for any effect below its detection limit, and no amount of care in the analysis
recovers that.
"""

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
    "UNDERPOWERED",
    "Alternative",
    "PowerAnalysis",
    "detectable_difference",
    "observed_power_is_circular",
    "power_paired",
    "power_two_means",
    "power_two_proportions",
    "sample_size_normal_approximation",
    "sample_size_two_means",
    "sample_size_two_proportions",
]

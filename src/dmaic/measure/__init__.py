"""Measure: is the measurement system good enough to detect what you are looking for?

The phase gate this module exists for is the one improvement projects skip most often. Every
later number - a capability index, a hypothesis test, a factorial effect - is computed on
readings, and a study that cannot resolve the parts it measures makes all of them noise with a
decimal point on.
"""

from .msa import (
    ACCEPTABLE,
    ANOVA_COLUMNS,
    INTERACTION_ALPHA,
    MARGINAL,
    NDC_ADEQUATE,
    NDC_CONSTANT,
    SIGMA_MULTIPLIER,
    GageStudy,
    anova,
    gage_rr,
)

__all__ = [
    "ACCEPTABLE",
    "ANOVA_COLUMNS",
    "INTERACTION_ALPHA",
    "MARGINAL",
    "NDC_ADEQUATE",
    "NDC_CONSTANT",
    "SIGMA_MULTIPLIER",
    "GageStudy",
    "anova",
    "gage_rr",
]

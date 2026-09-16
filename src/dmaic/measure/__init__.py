"""Measure: is the measurement system good enough to detect what you are looking for?

The phase gate this module exists for is the one improvement projects skip most often. Every
later number - a capability index, a hypothesis test, a factorial effect - is computed on
readings, and a study that cannot resolve the parts it measures makes all of them noise with a
decimal point on.

:mod:`~dmaic.measure.msa` answers whether the gage can tell the parts apart.
:mod:`~dmaic.measure.accuracy` answers whether it is right, which the crossed study is
*invariant* to: add a constant to every reading and every AIAG figure is unchanged exactly, so a
gage reading 4 g heavy on every part passes as well as the same gage calibrated. Accuracy needs a
value from outside the study, and the second module is about what a calibrated master buys.
"""

from .accuracy import (
    BIAS_MATERIAL_PCT,
    LINEARITY_MATERIAL_PCT,
    TAIL_SIGMAS,
    TRADEOFF_COLUMNS,
    BiasStudy,
    LinearityStudy,
    Misclassification,
    bias_significance_tradeoff,
    bias_study,
    detectable_bias,
    guard_band,
    linearity_study,
    misclassification,
)
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
    "BIAS_MATERIAL_PCT",
    "ANOVA_COLUMNS",
    "INTERACTION_ALPHA",
    "LINEARITY_MATERIAL_PCT",
    "MARGINAL",
    "NDC_ADEQUATE",
    "NDC_CONSTANT",
    "SIGMA_MULTIPLIER",
    "TAIL_SIGMAS",
    "TRADEOFF_COLUMNS",
    "BiasStudy",
    "GageStudy",
    "LinearityStudy",
    "Misclassification",
    "anova",
    "bias_significance_tradeoff",
    "bias_study",
    "detectable_bias",
    "gage_rr",
    "guard_band",
    "linearity_study",
    "misclassification",
]

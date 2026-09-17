"""Improve: did it happen, was it yours, and is it cash?

The phase is usually written up as a single number - the difference between the months after a
project and the months before it - and that number is the sum of three things, of which the
project is one. The other two are a trend that was already running and the selection that put
these sites in the charter rather than others.

:mod:`~dmaic.improve.realisation` separates them. A comparison group removes the trend without
having to model it; a longer baseline removes the selection artefact and the module prices how much
each period of baseline is worth. What is left is the part that is the project's, and then one
question that is not statistical at all: how much of a modelled saving is avoidable cash rather
than freed capacity. :class:`~dmaic.improve.realisation.BenefitCase` reports the two separately and
declines to add them up.
"""

from .realisation import (
    METHODS,
    RTM_COLUMNS,
    SELECTIONS,
    BenefitCase,
    Estimate,
    before_after,
    difference_in_differences,
    regression_to_the_mean,
)

__all__ = [
    "METHODS",
    "RTM_COLUMNS",
    "SELECTIONS",
    "BenefitCase",
    "Estimate",
    "before_after",
    "difference_in_differences",
    "regression_to_the_mean",
]

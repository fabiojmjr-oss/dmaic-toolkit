"""Limits taken explicitly where a fitted standard error is zero or undefined.

Noiseless data is not a pathological input in measurement work. A digital indicator reading the
same displayed digit at every check produces it, and so does a gage whose offset happens not to
move at all between masters. In both cases a regression's standard error on the slope comes back as
zero or as ``nan`` - ``scipy`` returns ``nan`` when the response is constant - and a p-value
computed from it is not a number.

The limit is well defined and points in two directions, so it is taken here once rather than in
each module that needs it: with no scatter around the fit, a non-zero slope is *known* to be
non-zero and a zero slope is *known* to be zero. Getting this wrong is not academic. An earlier
version of :mod:`dmaic.measure.accuracy` returned ``nan`` here, which made its ``significant`` flag
false and printed "no linearity error detected" next to a slope of 0.5.
"""

from __future__ import annotations

import math

from scipy import stats


def slope_p_value(slope: float, stderr: float, df: int) -> float:
    """Two-sided p-value for a zero slope, with the noiseless case handled rather than divided.

    Args:
        slope: The fitted slope.
        stderr: Its standard error. Zero or non-finite means the points lie on the line exactly.
        df: Residual degrees of freedom.

    Returns:
        The p-value: ``0.0`` for a slope known to be non-zero, ``1.0`` for one known to be zero.

    Raises:
        ValueError: If there are no residual degrees of freedom to test against.
    """
    if df < 1:
        raise ValueError(f"a slope test needs at least one residual degree of freedom, got {df}")
    if stderr == 0.0 or not math.isfinite(stderr):
        return 0.0 if slope != 0.0 else 1.0
    return float(2.0 * stats.t.sf(abs(slope / stderr), df))

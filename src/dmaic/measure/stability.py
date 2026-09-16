"""How long a calibration lasts, and where a drift goes when nobody records the date.

A gage study and a bias study are both snapshots. They describe the instrument on the day the
readings were taken, and neither has a field for how far that day is from the last calibration.
That omission has two consequences, and the second one is the expensive one.

**A drift decides its own acceptance criterion.** An instrument moving a tenth of a gram a day is
within a twentieth of its tolerance for twenty-five days and outside it afterwards, so the verdict
on a bias study is a statement about the calendar as much as about the gage. Periodic checks
against a master turn that into an interval, which is an action; a single study turns it into a
number, which is not.

**And the schedule of a crossed study decides which term the drift lands in.** Operators are
rarely free on the same day, so sessions get spread over weeks - and then each operator's readings
carry their own day's drift. The ANOVA has no day term, so it attributes the calendar to whichever
factor the schedule aligned it with. Give every operator their own day and the drift comes back as
**reproducibility**: the study blames the people, and the project trains them. Interleave the
operators and the same drift comes back as **repeatability**, which blames the instrument and
hides the operators entirely. Same readings, same days, same instrument. Only the schedule differs,
and nothing on the form records it.

That second finding needed no function added here, which is the point of it: the study a project
has already run contains the evidence, as long as the date of each reading was written down.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .._limits import slope_p_value
from ..analyze.power import DEFAULT_ALPHA

#: Share of the tolerance a drift is allowed to consume before the gage is recalibrated. The
#: convention matches :data:`dmaic.measure.accuracy.BIAS_MATERIAL_PCT`, because a drift that has
#: arrived is a bias and there is no reason for the two rules to disagree.
DRIFT_BUDGET_PCT = 5.0

CHECK_COLUMNS = ("day", "offset", "readings")


@dataclass(frozen=True)
class StabilityStudy:
    """Periodic readings on a master, regressed on the day they were taken.

    Attributes:
        gage: Label carried through for reporting.
        n: Total readings.
        first_day: Day of the earliest check.
        last_day: Day of the latest check.
        drift_per_day: Fitted change in offset per day, signed.
        intercept: Fitted offset on day zero, which is the state the gage was left in.
        stderr: Standard error of the drift rate.
        r_squared: Share of the offset variation the line explains.
        residual_sd: Spread of the readings around the fitted line, which is the gage's
            repeatability with the drift taken out.
        tolerance: Specification width, or ``None``.
        alpha: Significance level for the drift test.
    """

    gage: str
    n: int
    first_day: int
    last_day: int
    drift_per_day: float
    intercept: float
    stderr: float
    r_squared: float
    residual_sd: float
    tolerance: float | None
    alpha: float

    @property
    def p_value(self) -> float:
        """Two-sided p-value for a zero drift rate.

        A gage whose checks land on the fitted line exactly - which a coarse digital readout does
        routinely - has no standard error to divide by, so the limit is taken in
        :func:`dmaic._limits.slope_p_value` instead.
        """
        return slope_p_value(self.drift_per_day, self.stderr, self.n - 2)

    @property
    def significant(self) -> bool:
        """Whether the gage moved measurably over the period it was watched."""
        return self.p_value < self.alpha

    def offset_at(self, day: float) -> float:
        """The fitted offset on a given day, extrapolation included and clearly labelled as such."""
        return self.intercept + self.drift_per_day * day

    def pct_tolerance_at(self, day: float) -> float:
        """That offset as a percentage of the tolerance, or ``nan`` without a tolerance."""
        if self.tolerance is None or self.tolerance <= 0:
            return float("nan")
        return 100.0 * abs(self.offset_at(day)) / self.tolerance

    def days_to(self, share_of_tolerance: float = DRIFT_BUDGET_PCT) -> float:
        """Days from the last calibration until the drift consumes this share of the tolerance.

        This is the output a plant can act on, because it is a date rather than a coefficient.

        Args:
            share_of_tolerance: Percentage of the tolerance the offset is allowed to reach.

        Returns:
            The interval in days, or ``inf`` when the gage is not drifting, or ``nan`` when no
            tolerance was supplied.

        Raises:
            ValueError: If the share is not a positive percentage below 100.
        """
        if not 0.0 < share_of_tolerance < 100.0:
            raise ValueError(f"the share must be between 0 and 100, got {share_of_tolerance}")
        if self.tolerance is None or self.tolerance <= 0:
            return float("nan")
        if self.drift_per_day == 0.0:
            return float("inf")
        budget = self.tolerance * share_of_tolerance / 100.0
        return float((budget - abs(self.intercept)) / abs(self.drift_per_day))

    def verdict(self) -> str:
        """What the checks say about how long this gage can be trusted."""
        if not self.significant:
            return (
                f"no drift detected over {self.last_day - self.first_day} days - "
                "one calibration describes the period"
            )
        if self.tolerance is None:
            return (
                f"drifting {self.drift_per_day:+.4f} per day, interval unknown - "
                "no tolerance supplied"
            )
        return (
            f"drifting {self.drift_per_day:+.4f} per day - "
            f"{DRIFT_BUDGET_PCT:.0f}% of tolerance is spent in {self.days_to():.1f} days"
        )

    def summary(self) -> pd.DataFrame:
        """One row, for printing next to other gages."""
        return pd.DataFrame(
            [
                {
                    "gage": self.gage,
                    "drift_per_day": self.drift_per_day,
                    "p_value": self.p_value,
                    "offset_day_0": self.offset_at(self.first_day),
                    "offset_last_day": self.offset_at(self.last_day),
                    "pct_tolerance_last_day": self.pct_tolerance_at(self.last_day),
                    "residual_sd": self.residual_sd,
                    "interval_days": self.days_to(),
                    "verdict": self.verdict(),
                }
            ]
        )


def stability_study(
    data: pd.DataFrame,
    value: str = "value",
    reference: str = "reference",
    day: str = "day",
    tolerance: float | None = None,
    alpha: float = DEFAULT_ALPHA,
    gage: str = "",
) -> StabilityStudy:
    """Fit the offset against the day it was measured on.

    Args:
        data: Tidy readings, one row each, with a reference value and a day.
        value: Column holding the reading.
        reference: Column holding the master's accepted value.
        day: Column holding the day the reading was taken, counted from the last calibration.
        tolerance: Specification width, or ``None``.
        alpha: Significance level for the drift test.
        gage: Label carried into the result.

    Returns:
        A :class:`StabilityStudy`.

    Raises:
        ValueError: If fewer than two distinct days are present, which is a bias study rather than
            a stability study and would fit a line through one point.
    """
    frame = data[[day, reference, value]].dropna()
    days = np.asarray(frame[day], dtype=float)
    if np.unique(days).size < 2:
        raise ValueError(
            "a stability study needs checks on at least two distinct days; with one, use "
            "bias_study - a snapshot cannot see a drift"
        )
    offset = np.asarray(frame[value], dtype=float) - np.asarray(frame[reference], dtype=float)
    fit = stats.linregress(days, offset)
    residuals = offset - (fit.intercept + fit.slope * days)
    return StabilityStudy(
        gage=gage,
        n=int(days.size),
        first_day=int(days.min()),
        last_day=int(days.max()),
        drift_per_day=float(fit.slope),
        intercept=float(fit.intercept),
        stderr=float(fit.stderr),
        r_squared=float(fit.rvalue**2),
        residual_sd=float(residuals.std(ddof=2)),
        tolerance=tolerance,
        alpha=alpha,
    )


def calibration_interval(
    drift_per_day: float,
    tolerance: float,
    share_of_tolerance: float = DRIFT_BUDGET_PCT,
) -> float:
    """How long a calibration lasts at a given drift rate, without needing a study.

    Useful for planning before any checks exist, and for reading a manufacturer's drift
    specification as the interval it implies rather than as a number in a datasheet.

    Args:
        drift_per_day: Rate the gage moves at.
        tolerance: Specification width.
        share_of_tolerance: Percentage of the tolerance the offset may reach.

    Returns:
        The interval in days, or ``inf`` for a gage that does not drift.

    Raises:
        ValueError: If the tolerance is not positive or the share is outside ``(0, 100)``.
    """
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")
    if not 0.0 < share_of_tolerance < 100.0:
        raise ValueError(f"the share must be between 0 and 100, got {share_of_tolerance}")
    if drift_per_day == 0.0:
        return float("inf")
    return float(tolerance * share_of_tolerance / 100.0 / abs(drift_per_day))

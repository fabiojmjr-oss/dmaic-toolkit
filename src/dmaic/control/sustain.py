"""Did the gain hold? Two answers, and the one a report shows is the wrong one.

A project closes with a verified improvement and a control plan. A year later somebody checks. The
check almost always takes the form of comparing the current months to the original baseline - the
same before-and-after that :mod:`dmaic.improve` shows is inflated by the trend, except that by now
the trend has had twice as long to run.

So a decaying gain reports as a growing one. The gain here halves over a year; the report built
against the original baseline goes from 8.48 to 11.73. Both numbers are arithmetically correct and
they point in opposite directions, and the one that gets into the pack is the flattering one.

The comparison group fixes the direction. What it does not fix is the power, and that is the second
finding: an audit on twelve treated sites over a twelve-period window can resolve a decay of about
2.87, and the decay it is looking for is 1.86. **The two audits' confidence intervals overlap
completely**, so the honest conclusion of a correctly conducted sustain audit is that it cannot tell
whether the gain held - which is not the same as concluding that it did.

That is not an argument against auditing. It is an argument for sizing the audit when the project
closes, while there is still somebody to argue with about how many sites it gets, rather than a year
later when the answer is due.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..analyze.power import DEFAULT_ALPHA, DEFAULT_POWER, detectable_difference, power_two_means
from ..improve.realisation import Estimate, before_after, difference_in_differences

RETENTION_COLUMNS = ("first_period", "last_period", "true_effect", "estimate", "low", "high")
REPORTED_COLUMNS = ("first_period", "last_period", "reported_gain", "attributable")
DETECTION_COLUMNS = ("decay", "detectable", "power")


@dataclass(frozen=True)
class SustainAudit:
    """Two audits of one gain, and whether the difference between them can be seen.

    Attributes:
        close: The estimate at closure, against a comparison group.
        audit: The estimate a year later, against the same comparison group.
        detectable_decay: The smallest change between the two windows the later audit could have
            resolved, at :data:`~dmaic.analyze.power.DEFAULT_POWER`.
        change_sd: Spread of a site's own change between the baseline and the audit window, pooled
            across the two groups. It is carried because it is the figure
            :func:`decay_detection` needs, and taking it from anywhere else would price a different
            audit from the one that was run.
    """

    close: Estimate
    audit: Estimate
    detectable_decay: float
    change_sd: float

    @property
    def retention(self) -> float:
        """The later effect as a share of the earlier one, or ``nan`` if the first was nothing."""
        if self.close.effect == 0:
            return float("nan")
        return self.audit.effect / self.close.effect

    @property
    def decay(self) -> float:
        """How much of the effect went away, in the measurand's units."""
        return abs(self.close.effect) - abs(self.audit.effect)

    @property
    def intervals_overlap(self) -> bool:
        """Whether the two audits' intervals overlap, which decides what can be concluded.

        Overlapping intervals mean the two audits are consistent with the same effect. Reporting a
        retention figure from them is reporting a ratio of two numbers that have not been shown to
        differ.
        """
        if self.close.comparison is None or self.audit.comparison is None:
            return True
        first_low, first_high = self.close.comparison.confidence_interval
        second_low, second_high = self.audit.comparison.confidence_interval
        return first_low <= second_high and second_low <= first_high

    @property
    def decay_detectable(self) -> bool:
        """Whether the decay that happened is larger than the smallest one the audit could see."""
        return self.decay >= self.detectable_decay

    def verdict(self) -> str:
        """What this pair of audits establishes, which is usually less than it is asked for."""
        if self.intervals_overlap:
            return (
                f"{self.close.effect:+.4f} at closure and {self.audit.effect:+.4f} at audit, "
                f"intervals overlapping - the audit cannot tell whether the gain held, and it "
                f"would need a decay of {self.detectable_decay:.4f} to say so"
            )
        if self.retention < 1.0:
            return (
                f"gain decayed to {self.retention:.0%} of closure, and the audit can establish it"
            )
        return f"gain held or grew, at {self.retention:.0%} of closure"


def retention_path(
    panel: pd.DataFrame,
    split: int,
    windows: tuple[tuple[int, int], ...],
    baseline: tuple[int, int] | None = None,
    value: str = "value",
    site: str = "site",
    period: str = "period",
    treated: str = "treated",
    alpha: float = DEFAULT_ALPHA,
) -> pd.DataFrame:
    """The effect estimated window by window, against a comparison group each time.

    Args:
        panel: Tidy performance data, one row per site and period.
        split: Last period before the improvement.
        windows: The post-improvement windows to estimate in, as ``(first, last)`` pairs.
        baseline: The pre-improvement window, defaulting to everything up to the split.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period.
        treated: Boolean column marking the treated sites.
        alpha: Significance level for the intervals.

    Returns:
        A frame with the columns in :data:`RETENTION_COLUMNS`, with ``true_effect`` left as ``nan``
        for the caller to fill from whatever it knows - a real audit knows nothing there.

    Raises:
        ValueError: If a window runs backwards or starts at or before the split.
    """
    periods = np.asarray(panel[period], dtype=int)
    first_period = int(periods.min()) if baseline is None else baseline[0]
    last_baseline = split if baseline is None else baseline[1]
    rows = []
    for first, last in windows:
        if last < first:
            raise ValueError(f"the window {first}-{last} runs backwards")
        if first <= split:
            raise ValueError(
                f"the window {first}-{last} starts at or before the split at {split}, so it is "
                "partly baseline"
            )
        selected = panel[
            ((periods >= first_period) & (periods <= last_baseline))
            | ((periods >= first) & (periods <= last))
        ]
        estimate = difference_in_differences(
            selected,
            split=last_baseline,
            value=value,
            site=site,
            period=period,
            treated=treated,
            alpha=alpha,
        )
        low, high = (
            estimate.comparison.confidence_interval
            if estimate.comparison is not None
            else (float("nan"), float("nan"))
        )
        rows.append(
            {
                "first_period": first,
                "last_period": last,
                "true_effect": float("nan"),
                "estimate": estimate.effect,
                "low": low,
                "high": high,
            }
        )
    return pd.DataFrame(rows)[list(RETENTION_COLUMNS)]


def reported_gain(
    panel: pd.DataFrame,
    split: int,
    windows: tuple[tuple[int, int], ...],
    value: str = "value",
    site: str = "site",
    period: str = "period",
    treated: str = "treated",
) -> pd.DataFrame:
    """The number a sustain report actually carries: the treated sites against their old baseline.

    Computed so that it can be shown pointing the wrong way. Every period between the baseline and
    the window is another period of trend inside the figure, so the same decaying gain reports as a
    growing one.

    Args:
        panel: Tidy performance data, one row per site and period.
        split: Last period before the improvement, which ends the baseline.
        windows: The windows to report, as ``(first, last)`` pairs.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period.
        treated: Boolean column marking the treated sites.

    Returns:
        A frame with the columns in :data:`REPORTED_COLUMNS`. ``attributable`` is ``False`` in
        every row, because it is the same before-and-after comparison throughout.
    """
    periods = np.asarray(panel[period], dtype=int)
    rows = []
    for first, last in windows:
        selected = panel[((periods <= split) | ((periods >= first) & (periods <= last)))]
        estimate = before_after(
            selected, split=split, value=value, site=site, period=period, treated=treated
        )
        rows.append(
            {
                "first_period": first,
                "last_period": last,
                "reported_gain": estimate.effect,
                "attributable": estimate.attributable,
            }
        )
    return pd.DataFrame(rows)[list(REPORTED_COLUMNS)]


def sustain_audit(
    panel: pd.DataFrame,
    split: int,
    close: tuple[int, int],
    audit: tuple[int, int],
    value: str = "value",
    site: str = "site",
    period: str = "period",
    treated: str = "treated",
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
) -> SustainAudit:
    """Audit the gain twice and say what the pair establishes.

    Args:
        panel: Tidy performance data, one row per site and period.
        split: Last period before the improvement.
        close: The window audited at closure, as ``(first, last)``.
        audit: The window audited later.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period.
        treated: Boolean column marking the treated sites.
        alpha: Significance level for both intervals.
        power: Power the detectable decay is computed at.

    Returns:
        A :class:`SustainAudit`.

    Raises:
        ValueError: If either window starts at or before the split.
    """
    periods = np.asarray(panel[period], dtype=int)
    estimates = {}
    for label, (first, last) in (("close", close), ("audit", audit)):
        selected = panel[(periods <= split) | ((periods >= first) & (periods <= last))]
        estimates[label] = difference_in_differences(
            selected,
            split=split,
            value=value,
            site=site,
            period=period,
            treated=treated,
            alpha=alpha,
        )

    # The spread the later audit has to work against: how much sites' own changes vary. Taken from
    # the later window, because that is the audit whose power is in question.
    baseline = panel[periods <= split]
    later = panel[(periods >= audit[0]) & (periods <= audit[1])]
    changes = (
        later.groupby(site, observed=True)[value].mean()
        - baseline.groupby(site, observed=True)[value].mean()
    )
    flags = panel.groupby(site, observed=True)[treated].first().astype(bool)
    treated_changes = changes[flags].to_numpy()
    control_changes = changes[~flags].to_numpy()
    pooled = float(np.sqrt((treated_changes.var(ddof=1) + control_changes.var(ddof=1)) / 2.0))
    smaller = min(treated_changes.size, control_changes.size)
    # Sites whose changes do not vary at all resolve any decay, so the limit is zero rather than
    # an error. This is the same limit :mod:`dmaic._limits` takes for a fitted standard error and
    # :attr:`dmaic.measure.accuracy.BiasStudy.detectable_bias` takes for a flat set of readings;
    # the solver stays strict because outside these limits a zero spread is a mistake.
    resolvable = (
        0.0 if pooled == 0.0 else detectable_difference(smaller, pooled, power=power, alpha=alpha)
    )
    return SustainAudit(
        close=estimates["close"],
        audit=estimates["audit"],
        detectable_decay=resolvable,
        change_sd=pooled,
    )


def decay_detection(
    decays: tuple[float, ...],
    units: int,
    change_sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
) -> pd.DataFrame:
    """For each possible decay, whether an audit of this size could see it.

    The question a control plan should be sized on, and the one nobody asks until the audit has
    already come back inconclusive.

    Args:
        decays: Decays to evaluate, in the measurand's units.
        units: Sites per group in the audit.
        change_sd: Spread of a site's own change between the baseline and the audit window.
        power: Power the detectable decay is reported at.
        alpha: Significance level.

    Returns:
        A frame with the columns in :data:`DETECTION_COLUMNS`: the decay, the smallest decay the
        audit could resolve, and the power it actually has against this one.

    Raises:
        ValueError: If a decay is negative or the spread is not positive.
    """
    if any(decay < 0 for decay in decays):
        raise ValueError("a decay is a magnitude and cannot be negative")
    if change_sd <= 0:
        raise ValueError(f"change_sd must be positive, got {change_sd}")
    resolvable = detectable_difference(units, change_sd, power=power, alpha=alpha)
    return pd.DataFrame(
        [
            {
                "decay": decay,
                "detectable": resolvable,
                "power": power_two_means(units, decay, change_sd, alpha=alpha),
            }
            for decay in decays
        ]
    )[list(DETECTION_COLUMNS)]

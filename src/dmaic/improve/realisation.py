"""Did the improvement happen, was it yours, and is it cash? Three questions, three answers.

A project reports a saving by comparing the months after it to the months before. That comparison
is the sum of three things and only one of them belongs to the project:

- **The improvement**, which is what the project did.
- **The trend**, which was already running. Everything gets cheaper, or worse, over a year, and a
  before-and-after difference credits whoever happened to have a project open at the time.
- **The selection.** Projects are chartered on the worst-performing sites, and the worst performer
  in any period is partly a site that is genuinely bad and partly a site that had a bad period.
  The second part comes back on its own, and it comes back as an improvement with a name on it.

None of the three is visible in a before-and-after number, and the first is usually the smallest.
On the synthetic panel here, a project with a real effect of 5.00 per order reports 9.95 - twice
what it delivered - and the surplus is the trend that the untreated sites also enjoyed.

The fix for the trend is a comparison group: the difference in differences, which is the change in
the treated sites minus the change in everyone else. The fix for the selection is a longer
baseline, and :func:`regression_to_the_mean` prices it - one period of baseline manufactures an
apparent improvement of 4.35 out of nothing at all, and twelve periods bring that to 0.46.

And then there is the last question, which is not statistical. A modelled unit saving becomes cash
only to the extent the cost was avoidable, and :class:`BenefitCase` will not add the rest up for
you: it reports the gross case and the cash case separately, because a project that books capacity
as cash is not wrong about the process, it is wrong about the bank account.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..analyze.compare import Comparison, compare_means

#: Selection rules :func:`regression_to_the_mean` simulates. ``"worst"`` is how projects are
#: actually chartered; ``"random"`` is the control case, where the artefact must vanish.
SELECTIONS = ("worst", "random")

RTM_COLUMNS = ("baseline_periods", "worst_selected", "random_selected")

#: Methods :func:`before_after` and :func:`difference_in_differences` identify themselves by.
METHODS = ("before and after", "difference in differences")


@dataclass(frozen=True)
class Estimate:
    """One estimate of an improvement, with what it is an estimate of written on it.

    Attributes:
        method: Which comparison produced it, from :data:`METHODS`.
        effect: The estimated change, signed in the units of the measurand.
        treated: Sites the project touched.
        controls: Sites used as a comparison group. Zero for a before-and-after estimate, which
            is the whole difficulty with one.
        baseline_periods: Periods averaged before the change.
        follow_periods: Periods averaged after it.
        comparison: The two-sample test behind a difference in differences, or ``None``. The unit
            of analysis is the site rather than the site-period, which is what keeps the
            inference honest: twenty sites measured monthly are twenty observations of a change,
            not four hundred and eighty.
        untested_because: Why no comparison was computed, when one was expected. An estimate can
            be attributable and still untestable - three sites per group is the floor for the
            assumption checks, and a group whose sites all changed by exactly the same amount has
            no spread to test against.
    """

    method: str
    effect: float
    treated: int
    controls: int
    baseline_periods: int
    follow_periods: int
    comparison: Comparison | None = None
    untested_because: str = ""

    @property
    def attributable(self) -> bool:
        """Whether anything in this estimate rules out the trend.

        ``False`` for a before-and-after difference. Not "less precise" - a before-and-after
        difference contains the trend in full, and no amount of data narrows that away.
        """
        return self.controls > 0

    @property
    def significant(self) -> bool:
        """Whether the estimate is distinguishable from no effect at all.

        A before-and-after estimate has nothing to test against, so this is ``False`` for one:
        there is no null it could reject that is not also consistent with the trend.
        """
        return self.comparison is not None and self.comparison.significant

    def verdict(self) -> str:
        """What this estimate can and cannot be claimed as."""
        if not self.attributable:
            return (
                f"{self.effect:+.4f} over {self.baseline_periods} periods, with no comparison "
                "group - the trend is inside this number and cannot be taken out"
            )
        if self.untested_because:
            return (
                f"{self.effect:+.4f} against {self.controls} untreated sites, untested - "
                f"{self.untested_because}"
            )
        if self.significant:
            return f"{self.effect:+.4f} against {self.controls} untreated sites, significant"
        return (
            f"{self.effect:+.4f} against {self.controls} untreated sites, not distinguishable "
            "from no effect"
        )


@dataclass(frozen=True)
class BenefitCase:
    """A unit effect turned into money, with the part that is cash kept separate.

    Attributes:
        effect: Change per unit, signed. Negative is a saving for a cost measurand.
        units_per_period: Transactions per period the effect applies to.
        periods: Periods the case is claimed over.
        variable_share: Share of the modelled saving that is avoidable cash within the horizon.
            One means every unit of cost modelled here leaves the business when the work does.
        project_cost: One-off cost of delivering the improvement.
    """

    effect: float
    units_per_period: float
    periods: int
    variable_share: float
    project_cost: float = 0.0

    def __post_init__(self) -> None:
        if self.units_per_period < 0:
            raise ValueError(f"volume cannot be negative, got {self.units_per_period}")
        if self.periods < 1:
            raise ValueError(f"a case needs at least one period, got {self.periods}")
        if not 0.0 <= self.variable_share <= 1.0:
            raise ValueError(f"the variable share must be in [0, 1], got {self.variable_share}")
        if self.project_cost < 0:
            raise ValueError(f"the project cost cannot be negative, got {self.project_cost}")

    @property
    def gross(self) -> float:
        """The whole modelled saving, which is the figure charters are written with."""
        return abs(self.effect) * self.units_per_period * self.periods

    @property
    def cash(self) -> float:
        """The part of it that is avoidable cost rather than freed capacity."""
        return self.gross * self.variable_share

    @property
    def capacity(self) -> float:
        """The rest. Real, useful, and not money until something is done with it."""
        return self.gross - self.cash

    @property
    def net(self) -> float:
        """Cash less the cost of getting it."""
        return self.cash - self.project_cost

    @property
    def payback_periods(self) -> float:
        """Periods of cash saving needed to cover the project cost, or ``inf`` if never."""
        per_period = self.cash / self.periods
        if per_period <= 0:
            return float("inf")
        return self.project_cost / per_period

    def verdict(self) -> str:
        """The case in the form a finance review asks for it."""
        if self.net <= 0:
            return (
                f"{self.gross:,.0f} gross, {self.cash:,.0f} cash, "
                f"{self.net:,.0f} net of a {self.project_cost:,.0f} cost - does not pay back"
            )
        return (
            f"{self.gross:,.0f} gross, {self.cash:,.0f} cash, {self.net:,.0f} net, "
            f"payback in {self.payback_periods:.1f} periods"
        )

    def summary(self) -> pd.DataFrame:
        """One row, for printing next to another case built on another estimate."""
        return pd.DataFrame(
            [
                {
                    "effect": self.effect,
                    "gross": self.gross,
                    "cash": self.cash,
                    "capacity": self.capacity,
                    "net": self.net,
                    "payback_periods": self.payback_periods,
                }
            ]
        )


#: Observations a group needs before the assumption checks in :mod:`dmaic.analyze.compare` can
#: run at all. Shapiro-Wilk is undefined below three.
MIN_TESTABLE = 3


def _why_untestable(first: np.ndarray, second: np.ndarray) -> str:
    """Why these two groups cannot carry a test, or an empty string when they can."""
    for label, group in (("treated", second), ("untreated", first)):
        if group.size < MIN_TESTABLE:
            return (
                f"{group.size} {label} site(s), and the assumption checks need at least "
                f"{MIN_TESTABLE}"
            )
        if float(np.ptp(group)) == 0.0:
            return f"every {label} site changed by exactly the same amount, so there is no spread"
    return ""


def _site_changes(
    panel: pd.DataFrame,
    value: str,
    site: str,
    period: str,
    split: int,
) -> pd.DataFrame:
    """Each site's average before and after the split, and the change between them."""
    frame = panel[[site, period, value]].copy()
    frame["phase"] = np.where(np.asarray(frame[period], dtype=int) <= split, "before", "after")
    wide = frame.pivot_table(index=site, columns="phase", values=value, aggfunc="mean")
    missing = [phase for phase in ("before", "after") if phase not in wide.columns]
    if missing:
        raise ValueError(
            f"the panel has no periods {'and '.join(missing)} a split at {split}; "
            "a change cannot be computed from one side of it"
        )
    wide["change"] = wide["after"] - wide["before"]
    return wide.reset_index()


def before_after(
    panel: pd.DataFrame,
    split: int,
    value: str = "value",
    site: str = "site",
    period: str = "period",
    treated: str = "treated",
) -> Estimate:
    """The comparison a project actually reports: the treated sites, before against after.

    It is computed here so that it can be shown losing, rather than described. Everything the
    trend did over the window is inside the number it returns, and nothing about the calculation
    reveals that.

    Args:
        panel: Tidy performance data, one row per site and period.
        split: Last period before the improvement.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period, as an integer.
        treated: Boolean column marking the sites the project touched.

    Returns:
        An :class:`Estimate` with no comparison group and ``attributable`` false.

    Raises:
        ValueError: If no site is treated, or the split leaves one phase empty.
    """
    marked = panel[panel[treated].astype(bool)]
    if marked.empty:
        raise ValueError(f"no site is marked in {treated!r}, so there is nothing to measure")
    changes = _site_changes(marked, value, site, period, split)
    periods = np.asarray(panel[period], dtype=int)
    return Estimate(
        method=METHODS[0],
        effect=float(changes["change"].mean()),
        treated=int(len(changes)),
        controls=0,
        baseline_periods=int((periods <= split).sum() / panel[site].nunique()),
        follow_periods=int((periods > split).sum() / panel[site].nunique()),
    )


def difference_in_differences(
    panel: pd.DataFrame,
    split: int,
    value: str = "value",
    site: str = "site",
    period: str = "period",
    treated: str = "treated",
    alpha: float = 0.05,
) -> Estimate:
    """The change in the treated sites, minus the change in everyone else.

    The subtraction is what removes the trend, and it removes it whatever the trend is - nothing
    here has to model it, which is the point of a comparison group over a fitted line.

    The test behind it is Welch's on the *site-level* changes, one observation per site. That is
    deliberate: a panel of twenty sites over twenty-four months is not four hundred and eighty
    independent observations of anything, and treating it as such is how a difference in
    differences ends up with a p-value three orders of magnitude too small.

    The effect itself is a difference of two averages and does not depend on any diagnostic, so
    where the groups are too small or too flat to support the assumption checks the estimate is
    still returned and ``untested_because`` says why no test came with it. That distinction
    matters: :mod:`dmaic.analyze.compare` deliberately returns its checks as evidence rather than
    using them as a gate, and a check that *raises* is a gate by another name.

    Args:
        panel: Tidy performance data, one row per site and period.
        split: Last period before the improvement.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period, as an integer.
        treated: Boolean column marking the sites the project touched.
        alpha: Significance level for the comparison.

    Returns:
        An :class:`Estimate`, carrying the :class:`~dmaic.analyze.compare.Comparison` behind it
        where one could be computed.

    Raises:
        ValueError: If either group is empty, or the split leaves one phase empty.
    """
    flags = panel[treated].astype(bool)
    if not flags.any():
        raise ValueError(f"no site is marked in {treated!r}, so there is nothing to measure")
    if flags.all():
        raise ValueError(
            "every site is treated, so there is no comparison group; a difference in differences "
            "needs someone the project did not touch"
        )
    changes = _site_changes(panel.assign(**{treated: flags}), value, site, period, split)
    marks = panel.groupby(site, observed=True)[treated].first()
    changes = changes.merge(marks.rename("_treated"), left_on=site, right_index=True)
    treated_changes = changes.loc[changes["_treated"].astype(bool), "change"].to_numpy()
    control_changes = changes.loc[~changes["_treated"].astype(bool), "change"].to_numpy()
    # Controls first, so the reported difference reads as treated minus control - the effect,
    # with the sign the measurand has rather than the sign the argument order happens to give.
    reason = _why_untestable(control_changes, treated_changes)
    comparison = None if reason else compare_means(control_changes, treated_changes, alpha=alpha)
    periods = np.asarray(panel[period], dtype=int)
    return Estimate(
        method=METHODS[1],
        effect=float(treated_changes.mean() - control_changes.mean()),
        treated=int(treated_changes.size),
        controls=int(control_changes.size),
        baseline_periods=int((periods <= split).sum() / panel[site].nunique()),
        follow_periods=int((periods > split).sum() / panel[site].nunique()),
        comparison=comparison,
        untested_because=reason,
    )


def regression_to_the_mean(
    baselines: tuple[int, ...],
    sites: int,
    selected: int,
    site_sd: float,
    noise: float,
    follow_periods: int,
    replications: int = 4000,
    seed: int = 0,
) -> pd.DataFrame:
    """How much improvement a project shows when it does nothing at all.

    Every site here is unchanged: no effect, and no trend either. The trend is held at zero on
    purpose, so the two errors a before-and-after comparison makes are priced one at a time rather
    than confounded in one number.

    What remains is the selection. Choosing the worst performers of a baseline picks sites that are
    genuinely worse *and* sites that had a bad run, and only the first kind stays worse. The second
    kind returns, and returns as an improvement attributed to whoever opened a project.

    A generator per row rather than one shared stream, so a figure depends only on its own baseline
    length and the seed - the reproducibility discipline the whole package runs on.

    Args:
        baselines: Baseline lengths to walk through, in periods.
        sites: Sites available to choose from.
        selected: Sites the project takes.
        site_sd: Real, permanent spread between sites.
        noise: Period-to-period spread within a site.
        follow_periods: Periods averaged after selection.
        replications: Simulated projects per row.
        seed: Base seed. Each row uses ``seed + baseline`` so the rows are independent and pinned.

    Returns:
        A frame with the columns in :data:`RTM_COLUMNS`: the apparent improvement under selection
        on the worst performers, and under random selection, which is the control case and has to
        come back at zero.

    Raises:
        ValueError: If the selection is impossible or a spread is negative.
    """
    if not 0 < selected <= sites:
        raise ValueError(f"cannot take {selected} of {sites} sites")
    if site_sd < 0 or noise <= 0:
        raise ValueError(
            "the between-site spread cannot be negative and the noise must be positive"
        )
    if any(baseline < 1 for baseline in baselines):
        raise ValueError("a baseline needs at least one period")

    rows = []
    for baseline in baselines:
        rng = np.random.default_rng(seed + baseline)
        level = rng.normal(0.0, site_sd, size=(replications, sites))
        before = level + rng.normal(0.0, noise / np.sqrt(baseline), size=(replications, sites))
        after = level + rng.normal(0.0, noise / np.sqrt(follow_periods), size=(replications, sites))
        # The worst performers of the baseline, which is how a charter is written.
        worst = np.argsort(before, axis=1)[:, -selected:]
        picked = np.take_along_axis(before, worst, axis=1)
        returned = np.take_along_axis(after, worst, axis=1)
        # And the same count chosen without looking, which is the control.
        chosen = np.argsort(rng.random((replications, sites)), axis=1)[:, :selected]
        rows.append(
            {
                "baseline_periods": baseline,
                "worst_selected": float((returned - picked).mean()),
                "random_selected": float(
                    (
                        np.take_along_axis(after, chosen, axis=1)
                        - np.take_along_axis(before, chosen, axis=1)
                    ).mean()
                ),
            }
        )
    return pd.DataFrame(rows)[list(RTM_COLUMNS)]

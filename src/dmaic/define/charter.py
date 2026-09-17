"""A charter that computes, and the two ends of its gap - both of which are inflated.

Define is the phase with the least arithmetic in it and the most leverage. A charter fixes the
measurand, the baseline window, the target and the benefit before any data is analysed, and every
one of those is a decision that moves the answer. Written as prose they look like description.
Written as arithmetic they turn out to disagree with each other.

The finding this module exists for is the mirror image of :mod:`dmaic.improve`'s. A project is
chartered against a **baseline**, usually recent and usually bad, and towards an **entitlement**,
usually the best site's observed performance. The worst performer of a short window is partly a site
having a bad run, and it comes back up on its own. The best performer of the same window is partly a
site having a good run, and it goes back down. So a charter takes the most inflated available
estimate at *both* ends of its gap, and the two errors add rather than cancel.

They are also quantifiable. On twenty sites with the spreads of the synthetic panel, a
one-period baseline puts the charter's entitlement gap at 18.58 where the truth is 14.91: a quarter
of the gap does not exist. Shrinking the best site's estimate toward the grand mean - one line of
arithmetic - errs the other way, at 11.89. The truth sits between the two in every window tried,
which is the most useful thing this module can say: quote one of them and you have chosen a
direction; quote both and you have stated a range.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..improve.realisation import BenefitCase

#: How a target can be justified. ``"entitlement"`` is the best observed performer,
#: ``"benchmark"`` an outside figure, ``"absolute"`` a number somebody chose. The basis is
#: recorded because it decides whether the gap is measurable at all.
TARGET_BASES = ("entitlement", "benchmark", "absolute")

ENTITLEMENT_COLUMNS = ("window", "charter_gap", "true_gap", "shrunk_gap", "inflation")
GAP_COLUMNS = ("window", "mean", "best", "worst", "gap_to_best", "worst_to_best")
CTQ_COLUMNS = ("path", "measurand", "contribution", "measurable", "depth")


@dataclass(frozen=True)
class Charter:
    """A problem statement with its arithmetic exposed.

    Attributes:
        measurand: What is measured. A charter without one is an intention.
        unit: Unit of measure.
        baseline: Current performance, on the window named below.
        baseline_window: Periods averaged to get the baseline. Recorded because it changes the
            baseline, and because a shorter one is systematically worse - which flatters the gap.
        target: Performance being aimed at.
        target_basis: One of :data:`TARGET_BASES`.
        volume_per_period: Transactions the measurand applies to.
        periods: Periods the benefit is claimed over.
        variable_share: Share of a unit saving that is avoidable cash. Passed straight to
            :class:`~dmaic.improve.realisation.BenefitCase`, which keeps it separate from the rest.
        project_cost: One-off cost of the project.
    """

    measurand: str
    unit: str
    baseline: float
    baseline_window: int
    target: float
    target_basis: str
    volume_per_period: float
    periods: int
    variable_share: float
    project_cost: float = 0.0

    def __post_init__(self) -> None:
        if self.target_basis not in TARGET_BASES:
            raise ValueError(
                f"target_basis must be one of {TARGET_BASES}, got {self.target_basis!r}"
            )
        if self.baseline_window < 1:
            raise ValueError(f"the baseline needs at least one period, got {self.baseline_window}")
        if not self.measurand:
            raise ValueError("a charter without a measurand is an intention, not a charter")

    @property
    def gap(self) -> float:
        """Baseline less target, signed the way the measurand runs."""
        return self.target - self.baseline

    @property
    def gap_pct(self) -> float:
        """The gap as a percentage of the baseline, or ``nan`` when the baseline is zero."""
        if self.baseline == 0:
            return float("nan")
        return 100.0 * abs(self.gap) / abs(self.baseline)

    def benefit_case(self) -> BenefitCase:
        """The gap turned into money, by the same object the Improve phase audits it with.

        Using one class for the promise and for the audit is deliberate: a charter whose benefit is
        computed differently from the way it will be verified has built in a discrepancy that
        somebody will later have to explain.
        """
        return BenefitCase(
            effect=self.gap,
            units_per_period=self.volume_per_period,
            periods=self.periods,
            variable_share=self.variable_share,
            project_cost=self.project_cost,
        )

    def verdict(self) -> str:
        """The charter in one line, with the two things that qualify it."""
        case = self.benefit_case()
        return (
            f"{self.measurand}: {self.baseline:.4f} to {self.target:.4f} {self.unit} "
            f"({self.gap_pct:.1f}% on a {self.baseline_window}-period baseline, "
            f"{self.target_basis} target), {case.cash:,.0f} cash of {case.gross:,.0f} gross"
        )


@dataclass(frozen=True)
class Entitlement:
    """The best performer, read twice: as observed, and shrunk toward the average.

    Attributes:
        units: How many sites were compared.
        window: Periods each site's average covers.
        grand_mean: Average across sites.
        observed_best: The best site's observed average.
        shrunk_best: The best site's average pulled toward the grand mean by its reliability.
        reliability: Share of the observed spread between sites that is real rather than noise -
            the shrinkage factor, which is the between-site variance over the total.
    """

    units: int
    window: int
    grand_mean: float
    observed_best: float
    shrunk_best: float
    reliability: float

    @property
    def charter_gap(self) -> float:
        """What a charter would claim: the average, less the best observed performer."""
        return abs(self.grand_mean - self.observed_best)

    @property
    def shrunk_gap(self) -> float:
        """The same gap against the shrunk best, which errs the other way."""
        return abs(self.grand_mean - self.shrunk_best)

    def verdict(self) -> str:
        """The gap as a range, which is the only form of it that is defensible."""
        return (
            f"entitlement gap between {self.shrunk_gap:.4f} and {self.charter_gap:.4f} "
            f"({self.reliability:.0%} of the spread between sites is real)"
        )


@dataclass(frozen=True)
class Ctq:
    """One node of a critical-to-quality tree, with the share of the gap it claims.

    Attributes:
        name: What this branch is.
        measurand: How it would be measured. Empty means nobody has said, which is the state most
            trees are published in and the reason their arithmetic cannot be checked.
        contribution: Share of the parent's gap attributed to this branch, in the gap's units.
            Ignored for a node with children, whose contribution is its children's sum.
        children: Sub-branches.
    """

    name: str
    measurand: str = ""
    contribution: float = 0.0
    children: tuple[Ctq, ...] = field(default_factory=tuple)

    @property
    def measurable(self) -> bool:
        """Whether this node names a measurand. A branch is measurable if its leaves are."""
        if self.children:
            return all(child.measurable for child in self.children)
        return bool(self.measurand)

    @property
    def claimed(self) -> float:
        """What this node claims, which for a branch is the sum of what its children claim."""
        if self.children:
            return sum(child.claimed for child in self.children)
        return self.contribution

    @property
    def unmeasurable_claim(self) -> float:
        """How much of the claim sits under a leaf that names no measurand."""
        if self.children:
            return sum(child.unmeasurable_claim for child in self.children)
        return 0.0 if self.measurand else self.contribution


def entitlement(
    averages: np.ndarray | pd.Series | list[float],
    noise_sd: float,
    window: int,
    site_sd: float | None = None,
    lower_is_better: bool = True,
) -> Entitlement:
    """Read the best performer both ways, and say how much of the spread is real.

    The shrinkage factor is the classic reliability: the between-unit variance over the between-unit
    variance plus the sampling variance of a unit's average. It needs no extra data - the spread
    between the observed averages already contains both, and subtracting the known sampling part
    leaves the real one.

    Args:
        averages: One average per site, over ``window`` periods.
        noise_sd: Period-to-period spread within a site.
        window: Periods each average covers.
        site_sd: Real spread between sites, when it is known. Estimated from the averages when not,
            by removing the sampling variance from the observed spread.
        lower_is_better: Which end of the range is the good one. A cost or a cycle time wants the
            minimum; a yield or an on-time rate wants the maximum, and getting it wrong turns the
            best site into the worst one silently.

    Returns:
        An :class:`Entitlement`.

    Raises:
        ValueError: If there are fewer than two sites, the window is below one, or ``noise_sd`` is
            not positive.
    """
    values = np.asarray(averages, dtype=float).ravel()
    if values.size < 2:
        raise ValueError("an entitlement needs at least two sites to compare")
    if window < 1:
        raise ValueError(f"the window needs at least one period, got {window}")
    if noise_sd <= 0:
        raise ValueError(f"noise_sd must be positive, got {noise_sd}")

    sampling_variance = noise_sd**2 / window
    if site_sd is None:
        # What is left of the observed spread once the sampling part is taken out. Clamped at zero,
        # because a negative variance means the sites are indistinguishable rather than negatively
        # spread - the same clamping the gage ANOVA documents.
        between = max(float(values.var(ddof=1)) - sampling_variance, 0.0)
    else:
        between = float(site_sd) ** 2
    reliability = between / (between + sampling_variance) if between + sampling_variance else 0.0

    grand = float(values.mean())
    observed_best = float(values.min() if lower_is_better else values.max())
    return Entitlement(
        units=int(values.size),
        window=window,
        grand_mean=grand,
        observed_best=observed_best,
        shrunk_best=grand + reliability * (observed_best - grand),
        reliability=reliability,
    )


def entitlement_inflation(
    windows: tuple[int, ...],
    units: int,
    site_sd: float,
    noise_sd: float,
    replications: int = 4000,
    seed: int = 0,
) -> pd.DataFrame:
    """How much of a charter's entitlement gap is the best site having a good run.

    Simulated because it cannot be measured: the true level of each site is exactly what a real
    charter does not have. A generator per window, so each row depends only on its own window and
    the seed.

    Args:
        windows: Baseline lengths to walk through, in periods.
        units: Sites compared.
        site_sd: Real, permanent spread between sites.
        noise_sd: Period-to-period spread within a site.
        replications: Simulated charters per row.
        seed: Base seed; each row uses ``seed + window``.

    Returns:
        A frame with the columns in :data:`ENTITLEMENT_COLUMNS`: the gap a charter would claim, the
        gap that is really there, the gap against the shrunk best, and the difference between the
        first two.

    Raises:
        ValueError: If a window is below one, or a spread is not positive.
    """
    if any(window < 1 for window in windows):
        raise ValueError("a window needs at least one period")
    if site_sd <= 0 or noise_sd <= 0:
        raise ValueError("both spreads must be positive")

    rows = []
    for window in windows:
        rng = np.random.default_rng(seed + window)
        level = rng.normal(0.0, site_sd, size=(replications, units))
        observed = level + rng.normal(0.0, noise_sd / np.sqrt(window), size=(replications, units))
        reliability = site_sd**2 / (site_sd**2 + noise_sd**2 / window)
        grand = observed.mean(axis=1, keepdims=True)
        shrunk = grand + reliability * (observed - grand)
        charter_gap = (grand[:, 0] - observed.min(axis=1)).mean()
        true_gap = (level.mean(axis=1) - level.min(axis=1)).mean()
        rows.append(
            {
                "window": window,
                "charter_gap": float(charter_gap),
                "true_gap": float(true_gap),
                "shrunk_gap": float((grand[:, 0] - shrunk.min(axis=1)).mean()),
                "inflation": float(charter_gap - true_gap),
            }
        )
    return pd.DataFrame(rows)[list(ENTITLEMENT_COLUMNS)]


def gap_by_window(
    panel: pd.DataFrame,
    last_period: int,
    windows: tuple[int, ...],
    value: str = "value",
    site: str = "site",
    period: str = "period",
    lower_is_better: bool = True,
) -> pd.DataFrame:
    """The same data, read as several baselines, giving several gaps.

    A charter quotes one of these. Which one is a choice, it is rarely recorded, and the shortest
    window flatters the gap at both ends - the worst site is worse and the best site is better.

    Args:
        panel: Tidy performance data, one row per site and period.
        last_period: Last period of the baseline, counting backwards from here.
        windows: Baseline lengths to compute, in periods.
        value: Column holding the measurement.
        site: Column identifying the site.
        period: Column holding the period, as an integer.
        lower_is_better: Which end of the range is the good one.

    Returns:
        A frame with the columns in :data:`GAP_COLUMNS`. ``best`` and ``worst`` follow
        ``lower_is_better`` rather than the arithmetic order.

    Raises:
        ValueError: If a window is below one, or a window reaches past the start of the panel.
    """
    periods = np.asarray(panel[period], dtype=int)
    earliest = int(periods.min())
    rows = []
    for window in windows:
        if window < 1:
            raise ValueError("a window needs at least one period")
        first = last_period - window + 1
        if first < earliest:
            raise ValueError(
                f"a {window}-period window ending at {last_period} starts before the panel does"
            )
        selected = panel[(periods >= first) & (periods <= last_period)]
        averages = selected.groupby(site, observed=True)[value].mean()
        best = float(averages.min() if lower_is_better else averages.max())
        worst = float(averages.max() if lower_is_better else averages.min())
        rows.append(
            {
                "window": window,
                "mean": float(averages.mean()),
                "best": best,
                "worst": worst,
                "gap_to_best": abs(float(averages.mean()) - best),
                "worst_to_best": abs(worst - best),
            }
        )
    return pd.DataFrame(rows)[list(GAP_COLUMNS)]


def ctq_table(tree: Ctq, gap: float) -> pd.DataFrame:
    """Flatten a tree and check its arithmetic against the gap it is supposed to explain.

    Two checks, and both fail routinely in published trees. The leaves can claim more than the gap,
    which means the same saving has been counted twice under different names. And a leaf can name
    no measurand, which means that share of the gap is attributed to something nobody will be able
    to verify afterwards.

    Args:
        tree: The root node.
        gap: The gap the tree decomposes, in the same units as the contributions.

    Returns:
        A frame with the columns in :data:`CTQ_COLUMNS`, one row per node, depth-first.

    Raises:
        ValueError: If the gap is zero, since every share of it would be undefined.
    """
    if gap == 0:
        raise ValueError("a tree cannot decompose a gap of zero")

    rows: list[dict[str, object]] = []

    def walk(node: Ctq, path: str, depth: int) -> None:
        rows.append(
            {
                "path": path,
                "measurand": node.measurand,
                "contribution": node.claimed,
                "measurable": node.measurable,
                "depth": depth,
            }
        )
        for child in node.children:
            walk(child, f"{path} / {child.name}", depth + 1)

    walk(tree, tree.name, 0)
    return pd.DataFrame(rows)[list(CTQ_COLUMNS)]


def overattribution(tree: Ctq, gap: float) -> float:
    """How much more than the gap the tree's leaves claim, as a multiple.

    One means the decomposition adds up. Above one, the same saving appears under more than one
    name, and a portfolio built from the tree will promise more than the process contains.

    Args:
        tree: The root node.
        gap: The gap being decomposed.

    Returns:
        Claimed over gap, as a positive multiple.

    Raises:
        ValueError: If the gap is zero.
    """
    if gap == 0:
        raise ValueError("a tree cannot decompose a gap of zero")
    return abs(tree.claimed) / abs(gap)

"""Comparing two groups, with the assumptions measured instead of assumed.

Every Six Sigma course teaches the same flowchart: test for normality, test for equal variance,
then pick a test from what the two checks said. Simulated against the truth, that procedure is
worse than skipping it.

Every figure below comes from :func:`type_one_error_rates` and
:func:`normality_test_tradeoff` in this module, so none of it has to be taken on trust.

**Welch's test is the default here, not the fallback.** Under equal variances it loses essentially
nothing, and under unequal variances the pooled t-test is wrong in *both* directions depending on
which group is larger: 21.30% actual type I error when the wider group is the smaller one, and
0.38% when it is the larger one, both at a nominal 5%. Welch holds between 4.77% and 5.07% across
every normal scenario tried. There is no case in which the pooled test earns the exposure.

**The flowchart is strictly worse than always using Welch.** Choosing between the two tests on the
outcome of a variance pre-test inherits the pooled test's inflation whenever the pre-test fails to
notice the inequality: 6.28% against Welch's 5.07% in the case that matters. A pre-test does not
protect a procedure, it launders it.

**The reflex to reach for a rank test makes it worse, not better.** Mann-Whitney is not a
distribution-free version of the t-test, it is a test of a different hypothesis, and unequal
spread breaks it too: 12.70% where Welch holds 5.07%, and 6.63% even with balanced group sizes.

**The normality test is least informative exactly where it matters most.** Its power to detect a
departure and the cost of that departure move in opposite directions. At five per group a real
skew is detected 16.33% of the time, so the check passes - and that is where the t-test's error
rate is most distorted, at 2.40% against a nominal 5%. At three hundred per group the skew is
detected every single time, so the check fails and sends the project to a rank test - and there
the t-test is already fine, at 5.22%. The verdict is anti-correlated with the need for it.

**And the two problems the flowchart treats alike have opposite consequences.** Skew at small n
makes the test *conservative*, costing power. Unequal variance with unequal n makes it *liberal*,
manufacturing findings. Confusing those is not a technicality: one wastes a project, the other
publishes a result that is not there, and no single flowchart branch can be right for both.

So :func:`compare_means` runs Welch, reports the assumptions as evidence rather than as a gate,
and flags the one regime where nothing standard holds - strong skew together with unequal spread
and unequal group sizes, where the four procedures land at 11.12%, 14.54%, 23.31% and 28.50%.
Picking the least bad of those is not a solution. There the honest output is that a different
design is needed, not a different test.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats

from .power import DEFAULT_ALPHA, Alternative

# Shapiro-Wilk below this many observations has so little power that a pass means nothing.
# Above it, a pass is weak evidence and a failure is usually a departure too small to matter.
NORMALITY_UNINFORMATIVE_BELOW = 15
NORMALITY_OVERSENSITIVE_ABOVE = 100

# Standard deviation ratio past which the pooled test's exposure is material rather than academic.
VARIANCE_RATIO_MATERIAL = 1.5

# Group-size ratio past which unequal variance turns from a nuisance into a type I error problem.
# Below it the pooled test's inflation is small; above it, it is the dominant failure mode.
SIZE_RATIO_MATERIAL = 1.5

# Absolute skewness past which the central limit theorem needs real sample size to rescue a mean.
# Read together with the standard error of the estimate, never on its own - see
# :func:`skewness_standard_error` for why a bare threshold here is the bug this module is about.
SKEW_MATERIAL = 1.0

# Standard errors of the skewness estimate that the point estimate has to clear as well. Two is
# the usual "distinguishable from zero" convention, and it is what calibrates the small-n end.
SKEW_STANDARD_ERRORS = 2.0


def skewness_standard_error(n: int) -> float:
    """Standard error of the sample skewness for a normal population.

    The exact expression rather than the ``sqrt(6/n)`` approximation, because the two differ by
    enough at the sample sizes an improvement project actually collects to change a verdict.

    Args:
        n: Observations.

    Returns:
        The standard error.

    Raises:
        ValueError: If ``n`` is below four, where the quantity is undefined.
    """
    if n < 4:
        raise ValueError(
            f"the skewness standard error is undefined below four observations, got {n}"
        )
    return math.sqrt(6.0 * n * (n - 1) / ((n - 2) * (n + 1) * (n + 3)))


@dataclass(frozen=True)
class NormalityCheck:
    """What a normality test can and cannot tell you about one group.

    Attributes:
        n: Observations.
        statistic: Shapiro-Wilk W.
        p_value: Its p-value.
        skewness: Sample skewness, reported because it is the departure that actually moves a
            mean comparison, while the test statistic only says "not normal".
        excess_kurtosis: Sample excess kurtosis, same reasoning.
        alpha: Level the verdict is read at.
    """

    n: int
    statistic: float
    p_value: float
    skewness: float
    excess_kurtosis: float
    alpha: float

    @property
    def rejects_normality(self) -> bool:
        """Whether the test fires. Not the same as whether it matters."""
        return bool(self.p_value < self.alpha)

    @property
    def informative(self) -> str:
        """Whether this group's size puts the test in a range where its verdict means anything.

        ``"underpowered"`` below fifteen observations: a pass is the absence of evidence, and the
        t-test's own distortion is at its worst there. ``"oversensitive"`` above a hundred: a
        failure is usually a departure the central limit theorem has already absorbed.
        ``"usable"`` in between, which is the only band where the flowchart's question is the
        right question.
        """
        if self.n < NORMALITY_UNINFORMATIVE_BELOW:
            return "underpowered"
        if self.n > NORMALITY_OVERSENSITIVE_ABOVE:
            return "oversensitive"
        return "usable"

    @property
    def skewness_standard_error(self) -> float:
        """Standard error of the sample skewness at this ``n``.

        Large, and it shrinks slowly: 0.69 at ten observations, 0.39 at thirty-six, 0.24 at a
        hundred. Any judgement about skew that ignores it is reading noise.
        """
        return skewness_standard_error(self.n)

    @property
    def materially_skewed(self) -> bool:
        """Whether the skew is both large enough to matter and large enough to be believed.

        Two conditions, and the second one is a correction to an earlier version of this
        property that used only the first. A bare ``abs(skewness) >= 1.0`` has a false-alarm
        rate on genuinely normal data that depends entirely on ``n``: 13.9% at ten observations,
        11.4% at twelve, 1.4% at thirty-six and 0.02% at a hundred. That is the same
        anti-correlation with usefulness this module criticises the normality test for, and it
        was reproduced here before being measured.

        Requiring the estimate to clear two of its own standard errors as well caps the
        small-n end at about 5%, where the bare threshold ran to 14%. Above roughly twenty
        observations the absolute threshold is the binding one again and the rate falls away on
        its own - 1.4% at thirty-six, 0.02% at a hundred - which is the correct behaviour rather
        than a gap: at those sizes a sample skewness past 1.0 really is unusual for a normal
        population, and a criterion calibrated to 5% everywhere would start firing on departures
        too small to move a mean. Neither condition works alone, and each governs a different
        end of the range.
        """
        return bool(
            abs(self.skewness) >= SKEW_MATERIAL
            and abs(self.skewness) >= SKEW_STANDARD_ERRORS * self.skewness_standard_error
        )


@dataclass(frozen=True)
class VarianceCheck:
    """Whether two groups have comparable spread, and whether the answer changes anything.

    Attributes:
        test: Which test was used.
        statistic: Its statistic.
        p_value: Its p-value.
        sd_ratio: Larger standard deviation over smaller - the quantity that actually drives the
            pooled test's exposure, where the p-value only says "unequal".
        size_ratio: Larger group over smaller. Unequal variance is a nuisance when the groups are
            balanced and a type I error problem when they are not, so the two ratios have to be
            read together.
        alpha: Level the verdict is read at.
    """

    test: str
    statistic: float
    p_value: float
    sd_ratio: float
    size_ratio: float
    alpha: float

    @property
    def rejects_equality(self) -> bool:
        return bool(self.p_value < self.alpha)

    @property
    def pooled_test_is_exposed(self) -> bool:
        """Whether the pooled t-test's error rate would be materially wrong here.

        Read from the two ratios rather than from the p-value, because that is what the
        simulation shows drives it: balanced groups tolerate a lot of inequality, and unbalanced
        groups tolerate very little.
        """
        return bool(
            self.sd_ratio >= VARIANCE_RATIO_MATERIAL and self.size_ratio >= SIZE_RATIO_MATERIAL
        )


@dataclass(frozen=True)
class Comparison:
    """The result of comparing two groups, with the evidence for trusting it attached.

    Attributes:
        test: Which test produced ``p_value``. Always Welch here, stated rather than implied.
        statistic: The t statistic.
        p_value: Its p-value.
        df: Welch-Satterthwaite degrees of freedom, which are generally fractional.
        difference: Mean of the second group minus the first.
        confidence_interval: Interval for that difference at ``1 - alpha``.
        normality: One check per group, in order.
        variance: The spread comparison.
        alpha: Level the verdict is read at.
    """

    test: str
    statistic: float
    p_value: float
    df: float
    difference: float
    confidence_interval: tuple[float, float]
    normality: tuple[NormalityCheck, NormalityCheck]
    variance: VarianceCheck
    alpha: float

    @property
    def significant(self) -> bool:
        return bool(self.p_value < self.alpha)

    @property
    def unreliable_regime(self) -> bool:
        """Whether this is the combination where no standard procedure holds its nominal level.

        Strong skew together with unequal spread and unequal group sizes. Simulated at ten
        against thirty observations with spreads three to one, the four procedures give 11.12%
        for Welch, 14.54% for the flowchart, 23.31% for the pooled t and 28.50% for
        Mann-Whitney, all at a nominal 5%. Picking the least bad of those is not a solution, and
        reporting any of them as a 5% test is wrong.
        """
        skewed = any(check.materially_skewed for check in self.normality)
        return bool(skewed and self.variance.pooled_test_is_exposed)

    def diagnosis(self) -> str:
        """One line on how much the p-value can carry."""
        if self.unreliable_regime:
            return "unreliable: skew, unequal spread and unequal sizes together"
        if (
            any(check.materially_skewed for check in self.normality)
            and min(check.n for check in self.normality) < NORMALITY_UNINFORMATIVE_BELOW
        ):
            return "conservative: skew at small n costs power rather than inventing findings"
        if self.variance.pooled_test_is_exposed:
            return "sound: Welch holds its level here, and a pooled test would not"
        return "sound"


def normality(
    sample: npt.ArrayLike, alpha: float = DEFAULT_ALPHA, name: str = ""
) -> NormalityCheck:
    """Shapiro-Wilk, with the shape statistics that say whether the verdict matters.

    Shapiro-Wilk is used rather than Anderson-Darling because its p-value has a stable API; the
    choice is not load-bearing, because the argument of this module is that the *question* is
    poorly posed rather than that one test answers it better.

    Args:
        sample: Observations.
        alpha: Level the verdict is read at.
        name: Label carried into errors, for a caller checking several groups.

    Returns:
        A :class:`NormalityCheck`.

    Raises:
        ValueError: If fewer than three observations are supplied, which is the minimum
            Shapiro-Wilk is defined for, or if the sample has no variation at all.
    """
    values = np.asarray(sample, dtype=float).ravel()
    values = values[np.isfinite(values)]
    label = f" for {name}" if name else ""
    if values.size < 3:
        raise ValueError(f"Shapiro-Wilk needs at least three observations{label}")
    if float(np.ptp(values)) == 0.0:
        raise ValueError(f"every observation is identical{label}, so normality is undefined")

    result = stats.shapiro(values)
    return NormalityCheck(
        n=int(values.size),
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        skewness=float(stats.skew(values, bias=False)),
        excess_kurtosis=float(stats.kurtosis(values, bias=False)),
        alpha=alpha,
    )


def equal_variance(
    first: npt.ArrayLike,
    second: npt.ArrayLike,
    alpha: float = DEFAULT_ALPHA,
    test: str = "brown-forsythe",
) -> VarianceCheck:
    """Compare two spreads, defaulting to the version that does not assume normality.

    ``"brown-forsythe"`` is Levene's test centred on the median, which is robust to the skew that
    is usually the reason anyone is checking. ``"levene"`` centres on the mean. ``"bartlett"`` is
    available and should almost never be used: it assumes normality, so using it to check an
    assumption of the t-test means assuming something stronger than what is being checked.

    Args:
        first: Observations in the first group.
        second: Observations in the second group.
        alpha: Level the verdict is read at.
        test: ``"brown-forsythe"``, ``"levene"`` or ``"bartlett"``.

    Returns:
        A :class:`VarianceCheck`.

    Raises:
        ValueError: If either group has fewer than two observations, or ``test`` is unknown.
    """
    a = np.asarray(first, dtype=float).ravel()
    b = np.asarray(second, dtype=float).ravel()
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        raise ValueError("comparing spreads needs at least two observations in each group")

    # Narrowed to plain floats rather than kept as the result objects, whose types differ
    # between levene and bartlett and carry nothing else this function needs.
    if test == "brown-forsythe":
        levene = stats.levene(a, b, center="median")
        statistic, p_value = float(levene.statistic), float(levene.pvalue)
    elif test == "levene":
        levene = stats.levene(a, b, center="mean")
        statistic, p_value = float(levene.statistic), float(levene.pvalue)
    elif test == "bartlett":
        bartlett = stats.bartlett(a, b)
        statistic, p_value = float(bartlett.statistic), float(bartlett.pvalue)
    else:
        raise ValueError(f"test must be 'brown-forsythe', 'levene' or 'bartlett', got {test!r}")

    sd_a, sd_b = float(a.std(ddof=1)), float(b.std(ddof=1))
    smaller, larger = sorted((sd_a, sd_b))
    sizes = sorted((a.size, b.size))
    return VarianceCheck(
        test=test,
        statistic=statistic,
        p_value=p_value,
        sd_ratio=larger / smaller if smaller > 0 else float("inf"),
        size_ratio=sizes[1] / sizes[0],
        alpha=alpha,
    )


def compare_means(
    first: npt.ArrayLike,
    second: npt.ArrayLike,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
    strict: bool = False,
) -> Comparison:
    """Compare two group means with Welch's test, and report what the assumptions permit.

    Welch unconditionally. The variance check is computed and returned as evidence, not consulted
    to choose a test: the simulation in this module's documentation shows that choosing on it is
    worse than not choosing at all.

    Args:
        first: Observations in the first group.
        second: Observations in the second group.
        alpha: Significance level.
        alternative: One- or two-sided.
        strict: Raise instead of returning a result in the regime where no standard procedure
            holds its nominal level. The default returns the result with
            :attr:`Comparison.unreliable_regime` set, because a caller who reads the flag is
            better served than one whose pipeline crashed; a caller who will not read it should
            pass ``True``.

    Returns:
        A :class:`Comparison`.

    Raises:
        ValueError: If either group has fewer than three observations, or ``strict`` is set and
            the comparison falls in the unreliable regime.
    """
    a = np.asarray(first, dtype=float).ravel()
    b = np.asarray(second, dtype=float).ravel()
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 3 or b.size < 3:
        raise ValueError("comparing means needs at least three observations in each group")

    result = stats.ttest_ind(b, a, equal_var=False, alternative=alternative)
    difference = float(b.mean() - a.mean())
    standard_error = math.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    df = float(result.df)
    critical = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    interval = (difference - critical * standard_error, difference + critical * standard_error)

    comparison = Comparison(
        test="Welch t",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        df=df,
        difference=difference,
        confidence_interval=interval,
        normality=(
            normality(a, alpha=alpha, name="the first group"),
            normality(b, alpha=alpha, name="the second group"),
        ),
        variance=equal_variance(a, b, alpha=alpha),
        alpha=alpha,
    )
    if strict and comparison.unreliable_regime:
        raise ValueError(
            "no standard two-sample procedure holds its nominal level with this combination of "
            "skew, unequal spread and unequal group sizes; the fix is a different design, not a "
            "different test"
        )
    return comparison


# --------------------------------------------------------------------------------------------
# Measuring a procedure instead of trusting it
# --------------------------------------------------------------------------------------------

PROCEDURES = ("pooled t", "Welch", "flowchart", "Mann-Whitney")


def _pooled_p(a: npt.NDArray[np.float64], b: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    n1, n2 = a.shape[1], b.shape[1]
    v1, v2 = a.var(1, ddof=1), b.var(1, ddof=1)
    pooled = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
    statistic = (a.mean(1) - b.mean(1)) / np.sqrt(pooled * (1 / n1 + 1 / n2))
    return np.asarray(2 * stats.t.sf(np.abs(statistic), n1 + n2 - 2))


def _welch_p(a: npt.NDArray[np.float64], b: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    n1, n2 = a.shape[1], b.shape[1]
    v1, v2 = a.var(1, ddof=1), b.var(1, ddof=1)
    variance = v1 / n1 + v2 / n2
    statistic = (a.mean(1) - b.mean(1)) / np.sqrt(variance)
    df = variance**2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    return np.asarray(2 * stats.t.sf(np.abs(statistic), df))


def _brown_forsythe_p(
    a: npt.NDArray[np.float64], b: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    z1 = np.abs(a - np.median(a, axis=1, keepdims=True))
    z2 = np.abs(b - np.median(b, axis=1, keepdims=True))
    n1, n2 = a.shape[1], b.shape[1]
    total = n1 + n2
    mean1, mean2 = z1.mean(1), z2.mean(1)
    overall = (n1 * mean1 + n2 * mean2) / total
    between = n1 * (mean1 - overall) ** 2 + n2 * (mean2 - overall) ** 2
    within = ((z1 - mean1[:, None]) ** 2).sum(1) + ((z2 - mean2[:, None]) ** 2).sum(1)
    statistic = (total - 2) * between / within
    return np.asarray(stats.f.sf(statistic, 1, total - 2))


def _mann_whitney_p(
    a: npt.NDArray[np.float64], b: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Normal approximation, which is what any routine uses at these sample sizes.

    No tie correction: the inputs are continuous draws, so ties occur with probability zero.
    """
    n1, n2 = a.shape[1], b.shape[1]
    combined = np.concatenate([a, b], axis=1)
    order = combined.argsort(axis=1)
    ranks = np.empty_like(order, dtype=float)
    np.put_along_axis(
        ranks, order, np.broadcast_to(np.arange(1.0, n1 + n2 + 1), combined.shape), axis=1
    )
    u = ranks[:, :n1].sum(1) - n1 * (n1 + 1) / 2
    mean = n1 * n2 / 2
    spread = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return np.asarray(2 * stats.norm.sf(np.abs((u - mean) / spread)))


def type_one_error_rates(
    n_first: int,
    n_second: int,
    sd_first: float = 1.0,
    sd_second: float = 1.0,
    shape: str = "normal",
    alpha: float = DEFAULT_ALPHA,
    replications: int = 20_000,
    seed: int = 42,
) -> dict[str, float]:
    """Simulate what each procedure's false-positive rate actually is under the null.

    Both groups are drawn from distributions with the same mean, so every rejection is a type I
    error and the nominal rate is ``alpha`` by construction. What comes back is what the
    procedures really do, which is the only way to compare them: no closed form covers the
    flowchart, because its behaviour depends on how often the variance pre-test happens to fire.

    This exists as a function rather than as a footnote so a project can measure the procedure it
    intends to standardise on, at its own sample sizes, before standardising on it.

    Args:
        n_first: Observations in the first group.
        n_second: Observations in the second group.
        sd_first: Standard deviation of the first group.
        sd_second: Standard deviation of the second group.
        shape: ``"normal"``, or ``"skewed"`` for a standardised lognormal - same mean and spread,
            skewness about 3.3.
        alpha: Nominal significance level, used both for the comparison and for the flowchart's
            variance pre-test.
        replications: Monte Carlo replications. The standard error of each rate is roughly
            ``sqrt(alpha * (1 - alpha) / replications)``, so the default resolves to about 0.0015.
        seed: Seed, so a published rate reproduces.

    Returns:
        One rate per entry in :data:`PROCEDURES`.

    Raises:
        ValueError: If either group size is below three, a standard deviation is not positive,
            ``shape`` is unknown, or ``replications`` is below one.
    """
    if n_first < 3 or n_second < 3:
        raise ValueError("each group needs at least three observations")
    if sd_first <= 0 or sd_second <= 0:
        raise ValueError("standard deviations must be positive")
    if replications < 1:
        raise ValueError("replications must be at least one")
    if shape not in ("normal", "skewed"):
        raise ValueError(f"shape must be 'normal' or 'skewed', got {shape!r}")

    rng = np.random.default_rng(seed)

    def draw(n: int, sd: float) -> npt.NDArray[np.float64]:
        if shape == "normal":
            return rng.normal(0.0, sd, size=(replications, n))
        # Standardised to mean zero and unit variance, so only the shape differs from normal.
        sigma = 0.75
        raw = rng.lognormal(0.0, sigma, size=(replications, n))
        centre = math.exp(sigma**2 / 2)
        spread = math.sqrt((math.exp(sigma**2) - 1) * math.exp(sigma**2))
        return (raw - centre) / spread * sd

    a = draw(n_first, sd_first)
    b = draw(n_second, sd_second)
    pooled = _pooled_p(a, b)
    welch = _welch_p(a, b)
    variance = _brown_forsythe_p(a, b)
    # The taught procedure: pooled when the pre-test passes, Welch when it fires.
    flowchart = np.where(variance > alpha, pooled, welch)
    return {
        "pooled t": float(np.mean(pooled < alpha)),
        "Welch": float(np.mean(welch < alpha)),
        "flowchart": float(np.mean(flowchart < alpha)),
        "Mann-Whitney": float(np.mean(_mann_whitney_p(a, b) < alpha)),
    }


def normality_test_tradeoff(
    n_per_group: int,
    shape: str = "skewed",
    alpha: float = DEFAULT_ALPHA,
    replications: int = 4_000,
    seed: int = 7,
) -> dict[str, float]:
    """How often the normality check fires, against how much the departure actually costs.

    The two numbers are the whole argument against the flowchart's first step. They are measured
    at the same ``n`` on the same distribution, so they can be read against each other: one is the
    probability that the check sends the project down the non-parametric branch, the other is
    what the t-test's error rate really is if it stays on the parametric one.

    Run across a range of ``n``, they move in opposite directions. The check is least likely to
    fire exactly where the departure does most damage, and certain to fire where the central limit
    theorem has already absorbed it.

    Args:
        n_per_group: Observations in each group.
        shape: ``"normal"`` or ``"skewed"``. With ``"normal"`` the detection rate should come out
            at ``alpha``, which is the control case.
        alpha: Level for both the normality check and the comparison.
        replications: Monte Carlo replications. Lower by default than
            :func:`type_one_error_rates` because Shapiro-Wilk is not vectorised.
        seed: Seed, so a published figure reproduces.

    Returns:
        ``detection_rate`` - the share of samples where Shapiro-Wilk rejects normality - and
        ``welch_type_one_error``, the actual false-positive rate of Welch's test under the null at
        this ``n`` and shape.

    Raises:
        ValueError: If ``n_per_group`` is below three, ``shape`` is unknown, or ``replications``
            is below one.
    """
    if n_per_group < 3:
        raise ValueError("Shapiro-Wilk needs at least three observations")
    if shape not in ("normal", "skewed"):
        raise ValueError(f"shape must be 'normal' or 'skewed', got {shape!r}")
    if replications < 1:
        raise ValueError("replications must be at least one")

    rng = np.random.default_rng(seed)

    def draw(n: int) -> npt.NDArray[np.float64]:
        if shape == "normal":
            return rng.normal(0.0, 1.0, size=(replications, n))
        sigma = 0.75
        raw = rng.lognormal(0.0, sigma, size=(replications, n))
        centre = math.exp(sigma**2 / 2)
        spread = math.sqrt((math.exp(sigma**2) - 1) * math.exp(sigma**2))
        return (raw - centre) / spread

    checked = draw(n_per_group)
    detections = sum(1 for row in checked if stats.shapiro(row).pvalue < alpha)

    # A second, independent pair for the error rate, so the two figures are not computed from
    # the same draws - which would correlate them and make the comparison look tighter than it is.
    a = draw(n_per_group)
    b = draw(n_per_group)
    return {
        "detection_rate": detections / replications,
        "welch_type_one_error": float(np.mean(_welch_p(a, b) < alpha)),
    }

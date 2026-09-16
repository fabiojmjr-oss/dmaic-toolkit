"""Power and sample size: what a test can detect, decided before it is run.

The commonest failure in an improvement project is not a wrong conclusion. It is a test with no
power concluding "no significant difference", and the project being closed on it. That failure is
invisible from the output - a non-significant p-value looks the same whether the effect is absent
or merely unmeasurable at the sample size collected - and it is entirely predictable beforehand.

So the load-bearing function here is not :func:`power_two_means`, it is
:func:`detectable_difference`. It answers the question a non-significant result actually raises:
**what is the smallest difference this study could have found?** Anything below that was never in
reach, and reporting "no difference" for it is a statement about the study rather than about the
process.

Three things this module does differently from the formula on the wall.

**Power comes from the noncentral t, not from a normal approximation.** The textbook sample-size
formula ``n = 2(z_{1-a/2} + z_{1-b})^2 s^2 / d^2`` replaces two t quantiles with two z quantiles
and always understates the sample size. Measured against the exact calculation, it is off by
exactly one observation per group across the whole practical range - so for most studies the
shortcut is harmless, which is worth saying plainly rather than implying otherwise. Where it does
bite is the small confirmation run: at an effect of two standard deviations the formula asks for
4 per group where 6 are needed, and delivers 66% power instead of the 80% it was asked for. The
approximation is available as :func:`sample_size_normal_approximation` so a project can measure
its own shortcut instead of trusting or dismissing it.

**Sample size is rounded up, and the achieved power is reported.** Rounding to the nearest integer
loses part of the power that was asked for. The returned :class:`PowerAnalysis` carries the power
actually achieved at the integer ``n``, which is at or above the target and not equal to it.

**Post-hoc power computed from the observed effect is refused.** It is not a weaker form of
evidence, it is arithmetic on the p-value: observed power is a monotone function of the p-value,
so it adds no information and cannot support the conclusion it is usually offered for. See
:func:`observed_power_is_circular`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from scipy import optimize, stats

Alternative = Literal["two-sided", "greater", "less"]

# Conventional power target. A convention, not a property of anything - stated as a constant so
# that a study reporting 80% is reporting a choice rather than a law.
DEFAULT_POWER = 0.80
DEFAULT_ALPHA = 0.05

# Below this, a test is reporting the absence of evidence and not evidence of absence.
UNDERPOWERED = 0.50

MAX_N = 1_000_000


@dataclass(frozen=True)
class PowerAnalysis:
    """What a test of a given size can and cannot detect.

    Attributes:
        test: Which test the analysis is for.
        n_per_group: Observations per group. For a paired or one-sample test, the number of pairs.
        delta: The difference the power refers to, in the units of the measurement.
        sd: Standard deviation used. For a paired test, the standard deviation of the differences.
        alpha: Significance level.
        power: Probability of detecting ``delta`` at this ``n``. For a sample-size calculation this
            is the power achieved at the integer ``n``, which is at or above the target rather
            than equal to it.
        alternative: One- or two-sided.
        target_power: The power that was asked for, when the analysis came from a sample-size
            calculation. ``None`` when the power was computed for a given ``n``.
    """

    test: str
    n_per_group: int
    delta: float
    sd: float
    alpha: float
    power: float
    alternative: Alternative
    target_power: float | None = None

    @property
    def beta(self) -> float:
        """Probability of missing a real difference of ``delta`` - the type II error rate."""
        return 1.0 - self.power

    @property
    def total_n(self) -> int:
        """Observations in the whole study."""
        return self.n_per_group * (1 if self.test.startswith("paired") else 2)

    @property
    def effect_size(self) -> float:
        """Cohen's d - the difference in standard deviations.

        Reported because it is the quantity power actually depends on: two studies with the same
        ``d`` have the same power whatever the units, and a ``delta`` quoted without its ``sd``
        cannot be turned into a sample size.
        """
        return self.delta / self.sd if self.sd > 0 else float("nan")

    @property
    def overshoot(self) -> float:
        """Power above the target, from rounding ``n`` up. ``nan`` when there was no target."""
        if self.target_power is None:
            return float("nan")
        return self.power - self.target_power

    def verdict(self) -> str:
        """Whether this study can support a conclusion about ``delta``."""
        if self.power >= DEFAULT_POWER:
            return "adequate"
        if self.power >= UNDERPOWERED:
            return "marginal"
        return "underpowered"


def _validate(alpha: float, alternative: str) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha}")
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(
            f"alternative must be 'two-sided', 'greater' or 'less', got {alternative!r}"
        )


def _power_from_noncentral_t(ncp: float, df: float, alpha: float, alternative: str) -> float:
    """Power of a t-test with noncentrality ``ncp``.

    The noncentral t is the exact null-to-alternative shift for a t statistic. Substituting a
    normal here is the approximation that understates sample size.
    """
    if df <= 0:
        raise ValueError("not enough degrees of freedom to compute power")
    if alternative == "two-sided":
        critical = stats.t.ppf(1.0 - alpha / 2.0, df)
        upper = float(stats.nct.sf(critical, df, ncp))
        lower = float(stats.nct.cdf(-critical, df, ncp))
        return upper + lower
    if alternative == "greater":
        return float(stats.nct.sf(stats.t.ppf(1.0 - alpha, df), df, ncp))
    return float(stats.nct.cdf(stats.t.ppf(alpha, df), df, ncp))


def power_two_means(
    n_per_group: int,
    delta: float,
    sd: float,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> float:
    """Power of a two-sample t-test to detect a difference of ``delta``.

    Args:
        n_per_group: Observations in each group.
        delta: Difference in means to detect, in measurement units.
        sd: Common standard deviation within a group.
        alpha: Significance level.
        alternative: One- or two-sided.

    Returns:
        Probability of rejecting the null when the true difference is ``delta``.

    Raises:
        ValueError: If ``n_per_group`` is below two, ``sd`` is not positive, ``alpha`` is not a
            probability, or ``alternative`` is not recognised.
    """
    _validate(alpha, alternative)
    if n_per_group < 2:
        raise ValueError("a two-sample t-test needs at least two observations per group")
    if sd <= 0:
        raise ValueError(f"sd must be positive, got {sd}")

    df = 2 * n_per_group - 2
    ncp = delta / (sd * math.sqrt(2.0 / n_per_group))
    return _power_from_noncentral_t(ncp, df, alpha, alternative)


def power_paired(
    n_pairs: int,
    delta: float,
    sd_diff: float,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> float:
    """Power of a paired t-test.

    Args:
        n_pairs: Number of pairs.
        delta: Mean difference to detect.
        sd_diff: Standard deviation of the *differences*, not of the measurements. Substituting
            the measurement standard deviation is the usual error and it throws away the pairing:
            when the pairs are correlated the difference varies less, which is the whole reason
            for pairing.
        alpha: Significance level.
        alternative: One- or two-sided.

    Returns:
        Probability of rejecting the null when the true mean difference is ``delta``.

    Raises:
        ValueError: If ``n_pairs`` is below two or ``sd_diff`` is not positive.
    """
    _validate(alpha, alternative)
    if n_pairs < 2:
        raise ValueError("a paired t-test needs at least two pairs")
    if sd_diff <= 0:
        raise ValueError(f"sd_diff must be positive, got {sd_diff}")

    df = n_pairs - 1
    ncp = delta / (sd_diff / math.sqrt(n_pairs))
    return _power_from_noncentral_t(ncp, df, alpha, alternative)


def sample_size_two_means(
    delta: float,
    sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> PowerAnalysis:
    """Smallest group size that detects ``delta`` with at least ``power``.

    Solved by search on the exact power rather than inverted from a normal approximation, and
    rounded up: the returned ``power`` is what the integer ``n`` achieves, which is at or above
    the target.

    Args:
        delta: Difference in means to detect.
        sd: Common within-group standard deviation.
        power: Target power.
        alpha: Significance level.
        alternative: One- or two-sided.

    Returns:
        A :class:`PowerAnalysis` whose ``n_per_group`` is the answer and whose ``power`` is what
        that ``n`` actually delivers.

    Raises:
        ValueError: If ``delta`` is zero, ``sd`` is not positive, ``power`` is not a probability,
            or the required sample size exceeds a million per group - which means the effect is
            too small relative to the noise for a study to be the right instrument.
    """
    _validate(alpha, alternative)
    if delta == 0:
        raise ValueError("no sample size detects a difference of zero")
    if sd <= 0:
        raise ValueError(f"sd must be positive, got {sd}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be strictly between 0 and 1, got {power}")

    # Start from the normal approximation, then walk up on the exact power. The approximation is
    # always optimistic, so walking up from it terminates and never overshoots downward.
    start = max(2, math.ceil(_normal_approximation_n(delta, sd, power, alpha, alternative)))
    for candidate in range(start, MAX_N + 1):
        achieved = power_two_means(candidate, delta, sd, alpha=alpha, alternative=alternative)
        if achieved >= power:
            return PowerAnalysis(
                test="two-sample t",
                n_per_group=candidate,
                delta=delta,
                sd=sd,
                alpha=alpha,
                power=achieved,
                alternative=alternative,
                target_power=power,
            )
    raise ValueError(
        f"detecting {delta} at {power:.0%} power needs more than {MAX_N:,} per group; "
        "the effect is too small relative to the noise for a study to be the right instrument"
    )


def _normal_approximation_n(
    delta: float, sd: float, power: float, alpha: float, alternative: str
) -> float:
    tail = alpha / 2.0 if alternative == "two-sided" else alpha
    z_alpha = stats.norm.ppf(1.0 - tail)
    z_beta = stats.norm.ppf(power)
    return 2.0 * (z_alpha + z_beta) ** 2 * sd**2 / delta**2


def sample_size_normal_approximation(
    delta: float,
    sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> int:
    """The textbook formula, rounded up, kept so its error can be measured.

    ``n = 2(z_{1-a/2} + z_{1-b})^2 s^2 / d^2`` is the formula on the wall of every training room.
    It substitutes normal quantiles for t quantiles, which is optimistic: it always returns a
    sample size at or below what the exact calculation requires.

    The size of that error is usually one observation per group, and the honest summary is that
    the shortcut is fine for most studies. It stops being fine when the study is small because
    the expected effect is large - the confirmation run, the validation batch - where at an
    effect of two standard deviations it asks for 4 per group against the 6 required and delivers
    66% power rather than 80%. This function exists so that gap can be computed for the study in
    hand rather than assumed either way.
    """
    _validate(alpha, alternative)
    if delta == 0:
        raise ValueError("no sample size detects a difference of zero")
    if sd <= 0:
        raise ValueError(f"sd must be positive, got {sd}")
    return max(2, math.ceil(_normal_approximation_n(delta, sd, power, alpha, alternative)))


def detectable_difference(
    n_per_group: int,
    sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> float:
    """The smallest difference a study of this size can detect with at least ``power``.

    This is the honest output of a non-significant result. A study that found nothing did not
    establish that nothing is there; it established that nothing larger than this was there to be
    found, and anything smaller was out of reach from the moment the sample size was fixed.

    Args:
        n_per_group: Observations in each group.
        sd: Common within-group standard deviation.
        power: Power the difference has to be detectable at.
        alpha: Significance level.
        alternative: One- or two-sided.

    Returns:
        The difference in measurement units.

    Raises:
        ValueError: If the inputs are outside their domains.
    """
    _validate(alpha, alternative)
    if n_per_group < 2:
        raise ValueError("a two-sample t-test needs at least two observations per group")
    if sd <= 0:
        raise ValueError(f"sd must be positive, got {sd}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be strictly between 0 and 1, got {power}")

    def shortfall(delta: float) -> float:
        return power_two_means(n_per_group, delta, sd, alpha=alpha, alternative=alternative) - power

    # Bracket: the normal approximation is optimistic, so it sits below the answer; doubling from
    # there reaches a delta with more than enough power in a handful of steps.
    low = 1e-12
    high = max(_normal_detectable(n_per_group, sd, power, alpha, alternative), 1e-9)
    for _ in range(60):
        if shortfall(high) > 0:
            break
        high *= 2.0
    else:  # pragma: no cover - unreachable for any finite sd
        raise ValueError("could not bracket a detectable difference")
    return float(optimize.brentq(shortfall, low, high, xtol=1e-12, rtol=1e-12))


def _normal_detectable(
    n_per_group: int, sd: float, power: float, alpha: float, alternative: str
) -> float:
    tail = alpha / 2.0 if alternative == "two-sided" else alpha
    z = stats.norm.ppf(1.0 - tail) + stats.norm.ppf(power)
    return float(z * sd * math.sqrt(2.0 / n_per_group))


def power_two_proportions(
    n_per_group: int,
    p_control: float,
    p_treatment: float,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> float:
    """Power of a two-proportion z-test, on the arcsine-stabilised effect size.

    Uses Cohen's ``h = 2*asin(sqrt(p1)) - 2*asin(sqrt(p2))`` rather than the raw difference in
    proportions, because the variance of a proportion depends on the proportion itself: a shift
    from 0.50 to 0.55 and a shift from 0.01 to 0.06 are the same five points and nothing like the
    same detection problem.

    Args:
        n_per_group: Observations in each group.
        p_control: Baseline proportion.
        p_treatment: Proportion under the alternative.
        alpha: Significance level.
        alternative: One- or two-sided.

    Returns:
        Probability of rejecting the null.

    Raises:
        ValueError: If either proportion is outside ``(0, 1)`` or ``n_per_group`` is below two.
    """
    _validate(alpha, alternative)
    if n_per_group < 2:
        raise ValueError("a two-proportion test needs at least two observations per group")
    for name, value in (("p_control", p_control), ("p_treatment", p_treatment)):
        if not 0.0 < value < 1.0:
            raise ValueError(f"{name} must be strictly between 0 and 1, got {value}")

    h = 2.0 * math.asin(math.sqrt(p_treatment)) - 2.0 * math.asin(math.sqrt(p_control))
    ncp = abs(h) * math.sqrt(n_per_group / 2.0)
    if alternative == "two-sided":
        critical = stats.norm.ppf(1.0 - alpha / 2.0)
        return float(stats.norm.sf(critical - ncp) + stats.norm.cdf(-critical - ncp))
    critical = stats.norm.ppf(1.0 - alpha)
    return float(stats.norm.sf(critical - ncp))


def sample_size_two_proportions(
    p_control: float,
    p_treatment: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    alternative: Alternative = "two-sided",
) -> PowerAnalysis:
    """Smallest group size that detects a shift from ``p_control`` to ``p_treatment``.

    Raises:
        ValueError: If the two proportions are equal, either is outside ``(0, 1)``, or the
            required sample size exceeds a million per group.
    """
    _validate(alpha, alternative)
    if p_control == p_treatment:
        raise ValueError("no sample size detects a difference of zero")
    for name, value in (("p_control", p_control), ("p_treatment", p_treatment)):
        if not 0.0 < value < 1.0:
            raise ValueError(f"{name} must be strictly between 0 and 1, got {value}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be strictly between 0 and 1, got {power}")

    h = abs(2.0 * math.asin(math.sqrt(p_treatment)) - 2.0 * math.asin(math.sqrt(p_control)))
    tail = alpha / 2.0 if alternative == "two-sided" else alpha
    approximate = 2.0 * ((stats.norm.ppf(1.0 - tail) + stats.norm.ppf(power)) / h) ** 2
    for candidate in range(max(2, math.floor(approximate) - 2), MAX_N + 1):
        achieved = power_two_proportions(
            candidate, p_control, p_treatment, alpha=alpha, alternative=alternative
        )
        if achieved >= power:
            return PowerAnalysis(
                test="two-proportion z",
                n_per_group=candidate,
                delta=p_treatment - p_control,
                sd=float("nan"),
                alpha=alpha,
                power=achieved,
                alternative=alternative,
                target_power=power,
            )
    raise ValueError(  # pragma: no cover - needs an effect below floating-point resolution
        f"detecting {p_control} to {p_treatment} at {power:.0%} needs more than {MAX_N:,} per group"
    )


def observed_power_is_circular(
    n_per_group: int,
    observed_delta: float,
    observed_sd: float,
    alpha: float = DEFAULT_ALPHA,
) -> tuple[float, float]:
    """Post-hoc power from the observed effect, and the p-value it is a function of.

    Offered together, and only together, because that is the whole point. Computing power from
    the effect you observed adds no information to the p-value you already have: the two are
    locked to each other, so a non-significant result *always* comes with a low observed power
    and the low power cannot then be cited as the reason the result was non-significant.

    At the two-sided 5% level the correspondence is exact at the boundary: ``p = alpha`` gives an
    observed power of almost exactly one half, so "we had only 40% power" is another way of
    writing "p was above 0.05" and is not an additional finding.

    What a non-significant result does support is :func:`detectable_difference`, which uses the
    sample size and the spread but *not* the observed effect - and so says something the p-value
    does not.

    Args:
        n_per_group: Observations in each group.
        observed_delta: The difference that was actually observed.
        observed_sd: The pooled standard deviation that was actually observed.
        alpha: Significance level the test was run at.

    Returns:
        ``(observed_power, p_value)``, in that order.

    Raises:
        ValueError: If the inputs are outside their domains.
    """
    if n_per_group < 2:
        raise ValueError("a two-sample t-test needs at least two observations per group")
    if observed_sd <= 0:
        raise ValueError(f"observed_sd must be positive, got {observed_sd}")

    df = 2 * n_per_group - 2
    t_statistic = observed_delta / (observed_sd * math.sqrt(2.0 / n_per_group))
    p_value = float(2.0 * stats.t.sf(abs(t_statistic), df))
    power = power_two_means(n_per_group, observed_delta, observed_sd, alpha=alpha)
    return power, p_value

"""Is the gage right? A crossed gage study cannot answer it, and not because it is a weak test.

Repeatability, reproducibility and part variation are all computed from differences between
readings. Add a constant to every reading in a study and every one of those quantities is
unchanged - not approximately, exactly - so percent study variation, percent contribution,
percent tolerance, ndc and the verdict that follows are all **invariant to bias**. A gage that
reads 4 g heavy on every part passes exactly as well as the same gage correctly calibrated.

That is a property of the design rather than a defect in it. "Can this gage tell the parts apart?"
and "is this gage right?" are different questions, and the second one cannot be asked without a
value from outside the study: a calibrated master. This module is about what that master buys.

Three things it makes visible, none of which the crossed study can see:

- **Bias**, a constant offset. It does not degrade discrimination at all, and it moves every
  conformance decision to one side.
- **Linearity**, an offset that depends on what is being measured. A gage can have *zero* average
  bias and be wrong at both ends of its range in opposite directions, which is why the one-point
  check that every procedure prescribes is not a check on the range.
- **The consequence**, in the only units a business acts on: good parts scrapped and bad parts
  shipped. Bias converts into both, and the conversion is steep.

The module also refuses the usual acceptance rule. "The confidence interval on the bias contains
zero, so the bias is acceptable" is a statement about the ratio of the bias to the gage's own
repeatability, and nothing else - a precise gage flags an offset far too small to matter, and a
sloppy one passes an offset that matters a great deal. :func:`bias_significance_tradeoff`
measures that, and :class:`BiasStudy` reports significance and materiality as two separate
findings because they are two separate findings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import integrate, optimize, stats

from ..analyze.power import DEFAULT_ALPHA, DEFAULT_POWER, power_paired

#: A bias larger than this share of the tolerance is material whatever its p-value. Like the
#: 10% / 30% GRR bands this is a convention rather than a derivation, and it is exposed as a
#: parameter for that reason.
BIAS_MATERIAL_PCT = 5.0

#: The same convention applied to linearity, against the *span* of the bias across the range.
#: A gage whose offset swings by more than this much of the tolerance is not usable across it,
#: however small the average offset is.
LINEARITY_MATERIAL_PCT = 5.0

#: How many process standard deviations out the nonconforming tails are integrated over. Beyond
#: eight the normal density contributes less than 1e-15, which is below the quadrature tolerance.
TAIL_SIGMAS = 8.0

TRADEOFF_COLUMNS = ("repeat_sd", "pct_tolerance_precision", "bias_to_sd", "flagged", "material")


@dataclass(frozen=True)
class BiasStudy:
    """Readings on one master, against the value the master actually has.

    Attributes:
        gage: Label carried through for reporting.
        reference: The master's accepted value.
        n: Readings taken.
        mean: Average reading.
        sd: Standard deviation of the readings, which is this gage's repeatability at this point.
        alpha: Significance level the interval and the test use.
        tolerance: Specification width, or ``None`` when it is not known. Without it there is no
            materiality verdict, only a significance one - which is precisely the situation this
            module argues is not enough.
    """

    gage: str
    reference: float
    n: int
    mean: float
    sd: float
    alpha: float
    tolerance: float | None

    @property
    def bias(self) -> float:
        """The offset, signed: positive means the gage reads high."""
        return self.mean - self.reference

    @property
    def standard_error(self) -> float:
        """Standard error of the mean reading."""
        return self.sd / math.sqrt(self.n)

    @property
    def t_statistic(self) -> float:
        """The one-sample t statistic on the bias.

        Identical readings give a standard error of zero, which is not a pathological input: a
        digital indicator reading the same displayed digit every time does it routinely. The
        limit is taken rather than the division attempted - an offset with no spread around it is
        known exactly, and no offset with no spread is no evidence at all.
        """
        if self.standard_error == 0.0:
            if self.bias == 0.0:
                return 0.0
            return math.inf if self.bias > 0 else -math.inf
        return self.bias / self.standard_error

    @property
    def p_value(self) -> float:
        """Two-sided p-value for the bias being zero."""
        statistic = self.t_statistic
        if math.isinf(statistic):
            return 0.0
        return float(2.0 * stats.t.sf(abs(statistic), self.n - 1))

    @property
    def interval(self) -> tuple[float, float]:
        """Confidence interval on the bias at ``1 - alpha``."""
        half = float(stats.t.ppf(1.0 - self.alpha / 2.0, self.n - 1)) * self.standard_error
        return (self.bias - half, self.bias + half)

    @property
    def significant(self) -> bool:
        """Whether the interval excludes zero. This is the criterion AIAG's rule uses."""
        return self.p_value < self.alpha

    @property
    def pct_tolerance(self) -> float:
        """The bias as a percentage of the tolerance, or ``nan`` without a tolerance."""
        if self.tolerance is None or self.tolerance <= 0:
            return float("nan")
        return 100.0 * abs(self.bias) / self.tolerance

    @property
    def material(self) -> bool:
        """Whether the bias is large against the specification, which is a different question.

        ``False`` when no tolerance was supplied, because an unknown consequence is not a small
        one and the caller is told so by :meth:`verdict` rather than by this flag.
        """
        if self.tolerance is None:
            return False
        return self.pct_tolerance > BIAS_MATERIAL_PCT

    @property
    def detectable_bias(self) -> float:
        """The smallest offset this many readings could have found, at 80% power.

        A one-sample t-test is arithmetically the paired test of :mod:`dmaic.analyze.power` - same
        degrees of freedom, same noncentrality - so this reuses that calculation rather than
        reimplementing it. It is the honest reading of a study that found nothing.

        Zero spread is the third place the same limit has to be taken: readings with no scatter
        resolve any offset at all, so the smallest detectable one is zero. The solver itself
        keeps rejecting a zero standard deviation, because outside this limit it is an error.
        """
        if self.sd == 0.0:
            return 0.0
        return detectable_bias(self.n, self.sd, alpha=self.alpha)

    def verdict(self) -> str:
        """Significance and materiality, reported as the two separate findings they are."""
        if self.tolerance is None:
            found = "bias found" if self.significant else "no bias found"
            return f"{found}, consequence unknown - no tolerance supplied"
        if self.material and self.significant:
            return f"biased and it matters - {self.pct_tolerance:.2f}% of tolerance"
        if self.material:
            return (
                f"{self.pct_tolerance:.2f}% of tolerance and not significant - the study is too "
                "small to settle an offset this size"
            )
        if self.significant:
            return (
                f"significant but small - {self.pct_tolerance:.2f}% of tolerance, below the "
                f"{BIAS_MATERIAL_PCT:.0f}% convention"
            )
        return f"no bias detected at this point, down to {self.detectable_bias:.4f}"

    def summary(self) -> pd.DataFrame:
        """One row, for printing next to other gages."""
        low, high = self.interval
        return pd.DataFrame(
            [
                {
                    "gage": self.gage,
                    "reference": self.reference,
                    "n": self.n,
                    "bias": self.bias,
                    "ci_low": low,
                    "ci_high": high,
                    "p_value": self.p_value,
                    "pct_tolerance": self.pct_tolerance,
                    "significant": self.significant,
                    "material": self.material,
                    "verdict": self.verdict(),
                }
            ]
        )


@dataclass(frozen=True)
class LinearityStudy:
    """Bias regressed on the reference value, across the working range.

    Attributes:
        gage: Label carried through for reporting.
        n: Total readings.
        low: Lowest reference measured.
        high: Highest reference measured.
        slope: Change in bias per unit of reference. Zero is a gage whose offset is the same
            everywhere, which is the only case a one-point bias study generalises from.
        intercept: Bias at a reference of zero, which is rarely inside the range and is kept only
            because the fitted line needs it.
        slope_stderr: Standard error of the slope. Zero when the points lie on a line exactly.
        r_squared: Share of the bias variation the line explains, or ``nan`` when the bias does
            not vary at all - a constant offset has nothing for a line to explain, which is a
            statement about the gage rather than about the fit.
        tolerance: Specification width, or ``None``.
        alpha: Significance level for the slope test.
    """

    gage: str
    n: int
    low: float
    high: float
    slope: float
    intercept: float
    slope_stderr: float
    r_squared: float
    tolerance: float | None
    alpha: float

    def bias_at(self, reference: float) -> float:
        """The fitted offset at a reference value."""
        return self.intercept + self.slope * reference

    @property
    def span(self) -> float:
        """How far the offset moves across the measured range, as an absolute width."""
        return abs(self.bias_at(self.high) - self.bias_at(self.low))

    @property
    def pct_tolerance_span(self) -> float:
        """The span as a percentage of the tolerance, or ``nan`` without one."""
        if self.tolerance is None or self.tolerance <= 0:
            return float("nan")
        return 100.0 * self.span / self.tolerance

    @property
    def p_value(self) -> float:
        """Two-sided p-value for a zero slope.

        A standard error of zero means the readings lie on a line exactly, so the slope is known
        rather than estimated. Returning ``nan`` there - as the first version of this did - made
        ``significant`` false and produced the verdict "no linearity error detected" next to a
        slope of 0.5, which is the same kind of contradiction between a number and its label that
        this module exists to point at.
        """
        if self.slope_stderr == 0.0:
            return 0.0 if self.slope != 0.0 else 1.0
        return float(2.0 * stats.t.sf(abs(self.slope / self.slope_stderr), self.n - 2))

    @property
    def significant(self) -> bool:
        """Whether the slope differs from zero."""
        return self.p_value < self.alpha

    @property
    def material(self) -> bool:
        """Whether the offset moves enough across the range to change conformance decisions."""
        if self.tolerance is None:
            return False
        return self.pct_tolerance_span > LINEARITY_MATERIAL_PCT

    def verdict(self) -> str:
        """What the line says about using this gage across its range."""
        if not self.significant:
            return "no linearity error detected - one offset describes the whole range"
        if self.material:
            return (
                f"offset moves {self.span:.4f} across the range "
                f"({self.pct_tolerance_span:.2f}% of tolerance) - a one-point check cannot "
                "stand in for it"
            )
        return f"slope detected but small - {self.pct_tolerance_span:.2f}% of tolerance"

    def summary(self) -> pd.DataFrame:
        """One row, for printing next to other gages."""
        return pd.DataFrame(
            [
                {
                    "gage": self.gage,
                    "slope": self.slope,
                    "p_value": self.p_value,
                    "bias_low": self.bias_at(self.low),
                    "bias_high": self.bias_at(self.high),
                    "span": self.span,
                    "pct_tolerance_span": self.pct_tolerance_span,
                    "r_squared": self.r_squared,
                    "verdict": self.verdict(),
                }
            ]
        )


@dataclass(frozen=True)
class Misclassification:
    """What a gage's error costs, in parts rather than in percentages of a standard deviation.

    Attributes:
        bias: Offset the gage adds to every reading.
        gage_sd: Measurement standard deviation - the GRR sigma, not the repeatability alone,
            when operators are part of the inspection.
        part_sd: Process standard deviation of the true part values.
        nominal: Centre of the process.
        lsl: Lower specification limit.
        usl: Upper specification limit.
        guard: How far each acceptance limit is pulled inside the specification.
        false_reject: Probability a conforming part is rejected.
        false_accept: Probability a nonconforming part is accepted.
        conforming: Share of production that is genuinely inside specification.
    """

    bias: float
    gage_sd: float
    part_sd: float
    nominal: float
    lsl: float
    usl: float
    guard: float
    false_reject: float
    false_accept: float
    conforming: float

    @property
    def scrap_ppm(self) -> float:
        """Conforming parts rejected, per million produced."""
        return 1e6 * self.false_reject * self.conforming

    @property
    def escape_ppm(self) -> float:
        """Nonconforming parts accepted, per million produced."""
        return 1e6 * self.false_accept * (1.0 - self.conforming)

    def verdict(self) -> str:
        """The two rates in the units a plant argues about."""
        return (
            f"{self.scrap_ppm:,.0f} ppm good parts rejected, "
            f"{self.escape_ppm:,.0f} ppm bad parts accepted"
        )


def bias_study(
    values: np.ndarray | pd.Series | list[float],
    reference: float,
    tolerance: float | None = None,
    alpha: float = DEFAULT_ALPHA,
    gage: str = "",
) -> BiasStudy:
    """Repeated readings on one master, against what the master actually is.

    Args:
        values: The readings.
        reference: The master's accepted value.
        tolerance: Specification width. Omitted rather than guessed, because a percent-tolerance
            figure against an invented specification reads like evidence.
        alpha: Significance level for the test and the interval.
        gage: Label carried into the result.

    Returns:
        A :class:`BiasStudy`.

    Raises:
        ValueError: If there are fewer than two readings or ``alpha`` is not a probability.
    """
    array = np.asarray(values, dtype=float)
    if array.size < 2:
        raise ValueError(f"a bias study needs at least two readings, got {array.size}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha}")
    return BiasStudy(
        gage=gage,
        reference=float(reference),
        n=int(array.size),
        mean=float(array.mean()),
        sd=float(array.std(ddof=1)),
        alpha=alpha,
        tolerance=tolerance,
    )


def linearity_study(
    data: pd.DataFrame,
    value: str = "value",
    reference: str = "reference",
    tolerance: float | None = None,
    alpha: float = DEFAULT_ALPHA,
    gage: str = "",
) -> LinearityStudy:
    """Regress the bias on the reference value, which is what a range of masters is for.

    Args:
        data: Tidy readings, one row each, with a reference column.
        value: Column holding the reading.
        reference: Column holding the master's accepted value.
        tolerance: Specification width, or ``None``.
        alpha: Significance level for the slope test.
        gage: Label carried into the result.

    Returns:
        A :class:`LinearityStudy`.

    Raises:
        ValueError: If fewer than two distinct reference values are present, which is a bias
            study rather than a linearity study and would fit a line through one point.
    """
    frame = data[[reference, value]].dropna()
    references = np.asarray(frame[reference], dtype=float)
    if np.unique(references).size < 2:
        raise ValueError(
            "a linearity study needs at least two distinct reference values; with one, use "
            "bias_study - a line through a single point is not a finding"
        )
    bias = np.asarray(frame[value], dtype=float) - references
    fit = stats.linregress(references, bias)
    return LinearityStudy(
        gage=gage,
        n=int(references.size),
        low=float(references.min()),
        high=float(references.max()),
        slope=float(fit.slope),
        intercept=float(fit.intercept),
        slope_stderr=float(fit.stderr),
        r_squared=float(fit.rvalue**2),
        tolerance=tolerance,
        alpha=alpha,
    )


def detectable_bias(
    n: int,
    sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
) -> float:
    """The smallest offset a study of ``n`` readings could have found.

    A one-sample t-test has the same degrees of freedom and the same noncentrality as the paired
    test, so this solves :func:`dmaic.analyze.power.power_paired` rather than reimplementing the
    noncentral t. The reuse is the point: nothing about measurement makes the arithmetic of a
    one-sample test different.

    Args:
        n: Readings taken.
        sd: Repeatability at this point.
        power: Power the offset has to be detectable at.
        alpha: Significance level.

    Returns:
        The offset in measurement units.

    Raises:
        ValueError: If ``n`` is below two, ``sd`` is not positive, or ``power`` is not a
            probability.
    """
    if n < 2:
        raise ValueError(f"a bias study needs at least two readings, got {n}")
    if sd <= 0:
        raise ValueError(f"sd must be positive, got {sd}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be strictly between 0 and 1, got {power}")

    def shortfall(delta: float) -> float:
        return power_paired(n, delta, sd, alpha=alpha) - power

    high = sd
    for _ in range(60):
        if shortfall(high) > 0:
            break
        high *= 2.0
    else:  # pragma: no cover - unreachable for any finite sd
        raise ValueError("could not bracket a detectable bias")
    return float(optimize.brentq(shortfall, 1e-12, high, xtol=1e-12, rtol=1e-12))


def misclassification(
    bias: float,
    gage_sd: float,
    part_sd: float,
    nominal: float,
    lsl: float,
    usl: float,
    guard: float = 0.0,
) -> Misclassification:
    """What share of parts this measurement system judges wrongly, and in which direction.

    A part is accepted when its *reading* falls inside the acceptance limits, while conformance
    is a property of its *true* value. The two come apart through the gage's bias and spread, and
    the arithmetic is one integral over the process distribution.

    Args:
        bias: Offset the gage adds to every reading.
        gage_sd: Measurement standard deviation.
        part_sd: Process standard deviation of the true values.
        nominal: Process centre.
        lsl: Lower specification limit.
        usl: Upper specification limit.
        guard: Guard band, pulling each acceptance limit this far inside the specification.

    Returns:
        A :class:`Misclassification`.

    Raises:
        ValueError: If the limits are not ordered, a standard deviation is not positive, or the
            guard band is wide enough to close the acceptance window.
    """
    if usl <= lsl:
        raise ValueError(f"usl must exceed lsl, got {lsl} and {usl}")
    if gage_sd <= 0 or part_sd <= 0:
        raise ValueError("both standard deviations must be positive")
    if guard < 0:
        raise ValueError(f"guard must not be negative, got {guard}")
    if 2.0 * guard >= usl - lsl:
        raise ValueError("the guard band closes the acceptance window entirely")

    low, high = lsl + guard, usl - guard

    def accepted(true_value: float) -> float:
        reading = true_value + bias
        return float(stats.norm.cdf(high, reading, gage_sd) - stats.norm.cdf(low, reading, gage_sd))

    conforming = float(
        stats.norm.cdf(usl, nominal, part_sd) - stats.norm.cdf(lsl, nominal, part_sd)
    )
    if conforming <= 0.0 or conforming >= 1.0:
        raise ValueError("the process is entirely inside or outside specification")

    def rejected_conforming(x: float) -> float:
        return (1.0 - accepted(x)) * float(stats.norm.pdf(x, nominal, part_sd))

    def accepted_nonconforming(x: float) -> float:
        return accepted(x) * float(stats.norm.pdf(x, nominal, part_sd))

    reach = TAIL_SIGMAS * part_sd
    false_reject = integrate.quad(rejected_conforming, lsl, usl, limit=200)[0] / conforming
    escapes = (
        integrate.quad(accepted_nonconforming, nominal - reach, lsl, limit=200)[0]
        + integrate.quad(accepted_nonconforming, usl, nominal + reach, limit=200)[0]
    )
    return Misclassification(
        bias=bias,
        gage_sd=gage_sd,
        part_sd=part_sd,
        nominal=nominal,
        lsl=lsl,
        usl=usl,
        guard=guard,
        false_reject=false_reject,
        false_accept=escapes / (1.0 - conforming),
        conforming=conforming,
    )


def guard_band(
    target_false_accept: float,
    bias: float,
    gage_sd: float,
    part_sd: float,
    nominal: float,
    lsl: float,
    usl: float,
) -> float:
    """How far to tighten the acceptance limits to hold escapes at a target.

    This is what a project does when it cannot fix the gage, and the figure it should be compared
    against is the cost of fixing the gage - which for a constant bias is a calibration. The
    guard band buys the escape rate back by rejecting conforming parts instead, and
    :func:`misclassification` at the returned width says how many.

    Args:
        target_false_accept: Acceptable probability that a nonconforming part is accepted.
        bias: Offset the gage adds.
        gage_sd: Measurement standard deviation.
        part_sd: Process standard deviation.
        nominal: Process centre.
        lsl: Lower specification limit.
        usl: Upper specification limit.

    Returns:
        The guard band width, in measurement units. Zero when the target is already met. A width
        always exists: closing the acceptance window drives the escape rate to zero, so
        feasibility is never the question here and cost always is.

    Raises:
        ValueError: If the target is not a probability.
    """
    if not 0.0 < target_false_accept < 1.0:
        raise ValueError(f"the target must be strictly between 0 and 1, got {target_false_accept}")

    def gap(width: float) -> float:
        return (
            misclassification(bias, gage_sd, part_sd, nominal, lsl, usl, guard=width).false_accept
            - target_false_accept
        )

    if gap(0.0) <= 0.0:
        return 0.0
    widest = 0.499 * (usl - lsl)
    if gap(widest) > 0.0:  # pragma: no cover - a window this narrow accepts almost nothing
        raise ValueError(f"no representable guard band reaches {target_false_accept}")
    return float(optimize.brentq(gap, 0.0, widest, xtol=1e-10, rtol=1e-12))


def bias_significance_tradeoff(
    repeat_sds: tuple[float, ...],
    bias: float,
    tolerance: float,
    n: int,
    replications: int = 4000,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> pd.DataFrame:
    """How often a fixed, immaterial bias is called significant, as the gage's precision varies.

    The point of the table is that the answer moves a great deal while the thing being judged
    does not move at all. The bias is the same number in every row and its consequence is the
    same share of the same tolerance; only the gage's repeatability changes, and with it the
    verdict. A precise gage flags an offset too small to matter, and a sloppy gage passes the
    same offset - which is the wrong way round for an acceptance rule.

    One set of standard normal draws is scaled by each standard deviation rather than drawn
    again, which is both common random numbers across the rows and exact: the t statistic depends
    on the bias and the spread only through their ratio, so scaling is the same experiment.

    Args:
        repeat_sds: Repeatabilities to walk through.
        bias: The offset present in every row, in measurement units.
        tolerance: Specification width, for the materiality column.
        n: Readings per simulated study.
        replications: Studies simulated per row.
        alpha: Significance level.
        seed: Seed for the shared draws.

    Returns:
        A frame with the columns in :data:`TRADEOFF_COLUMNS`.

    Raises:
        ValueError: If any standard deviation is not positive.
    """
    if any(sd <= 0 for sd in repeat_sds):
        raise ValueError("every repeatability must be positive")
    draws = np.random.default_rng(seed).normal(size=(replications, n))
    material = 100.0 * abs(bias) / tolerance > BIAS_MATERIAL_PCT
    rows = []
    for sd in repeat_sds:
        readings = bias + sd * draws
        t = readings.mean(axis=1) / (readings.std(axis=1, ddof=1) / math.sqrt(n))
        flagged = float(np.mean(2.0 * stats.t.sf(np.abs(t), n - 1) < alpha))
        rows.append(
            {
                "repeat_sd": sd,
                "pct_tolerance_precision": 100.0 * 6.0 * sd / tolerance,
                "bias_to_sd": abs(bias) / sd,
                "flagged": flagged,
                "material": material,
            }
        )
    return pd.DataFrame(rows)[list(TRADEOFF_COLUMNS)]

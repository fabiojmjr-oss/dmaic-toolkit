"""Assumption checks and the Welch comparison, anchored where they can be anchored.

The simulation functions are the module's evidence, so their own behaviour is pinned first: a
procedure whose error rate is measured wrongly would make every claim in the README wrong in the
same direction and none of them detectably so.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from dmaic.analyze import (
    DEFAULT_ALPHA,
    PROCEDURES,
    SKEW_MATERIAL,
    SKEW_STANDARD_ERRORS,
    VARIANCE_RATIO_MATERIAL,
    compare_means,
    equal_variance,
    normality,
    skewness_standard_error,
    type_one_error_rates,
)
from dmaic.analyze.compare import normality_test_tradeoff


def test_the_skewness_standard_error_matches_the_closed_form() -> None:
    """And is materially different from the sqrt(6/n) approximation at project sample sizes."""
    for n in (4, 10, 30, 100, 1000):
        expected = math.sqrt(6.0 * n * (n - 1) / ((n - 2) * (n + 1) * (n + 3)))
        assert skewness_standard_error(n) == pytest.approx(expected, abs=1e-12)
    # The sqrt(6/n) approximation runs high, not low, and by enough to matter: 12.7% at ten
    # observations, 4.0% at thirty-six, 1.5% at a hundred. A criterion built on it is therefore
    # stricter than intended rather than looser - the opposite of what I first assumed here.
    for n, excess in ((10, 0.127), (36, 0.040), (100, 0.015)):
        assert math.sqrt(6 / n) > skewness_standard_error(n), n
        assert math.sqrt(6 / n) / skewness_standard_error(n) - 1 == pytest.approx(
            excess, abs=5e-4
        ), n
    assert skewness_standard_error(10_000) == pytest.approx(math.sqrt(6 / 10_000), rel=0.001)
    with pytest.raises(ValueError, match="undefined below four"):
        skewness_standard_error(3)


def test_the_dual_skew_criterion_caps_the_small_n_false_alarm_rate() -> None:
    """The correction to an earlier bare threshold, verified as the thing it fixed.

    A fixed ``abs(skew) >= 1.0`` fires on genuinely normal data at a rate that depends entirely
    on n. Adding the standard-error condition caps the small-n end; above about twenty the
    absolute threshold binds again and the rate falls on its own, which is intended.
    """
    # A generator per n rather than one shared stream, so each figure depends only on (n, seed)
    # and not on the order the sizes happen to be checked in. An earlier version shared one
    # generator and the n=36 figure moved when the list of sizes changed.
    rates = {}
    for n, bare, dual in ((10, 0.1421, 0.0518), (12, 0.1151, 0.0482), (36, 0.0138, 0.0138)):
        skew = stats.skew(
            np.random.default_rng(n).normal(0.0, 1.0, (20_000, n)), axis=1, bias=False
        )
        error = skewness_standard_error(n)
        measured_bare = float(np.mean(np.abs(skew) >= SKEW_MATERIAL))
        measured_dual = float(
            np.mean(
                (np.abs(skew) >= SKEW_MATERIAL) & (np.abs(skew) >= SKEW_STANDARD_ERRORS * error)
            )
        )
        assert measured_bare == pytest.approx(bare, abs=5e-4), n
        assert measured_dual == pytest.approx(dual, abs=5e-4), n
        rates[n] = (measured_bare, measured_dual)

    # The defect: the bare threshold is ten times looser at n=10 than at n=36, on data that is
    # normal in both cases. The dual criterion caps the small end near alpha.
    assert rates[10][0] / rates[36][0] > 10
    assert rates[10][1] == pytest.approx(DEFAULT_ALPHA, abs=0.005)
    # And above about twenty the absolute threshold binds again, so the two agree. Intended.
    assert rates[36][0] == rates[36][1]


def test_normality_reports_the_band_its_verdict_is_usable_in() -> None:
    rng = np.random.default_rng(3)
    assert normality(rng.normal(0, 1, 10)).informative == "underpowered"
    assert normality(rng.normal(0, 1, 40)).informative == "usable"
    assert normality(rng.normal(0, 1, 500)).informative == "oversensitive"


def test_normality_refuses_what_it_cannot_answer() -> None:
    with pytest.raises(ValueError, match="at least three observations"):
        normality([1.0, 2.0])
    with pytest.raises(ValueError, match="every observation is identical"):
        normality([5.0] * 10)
    # And the label reaches the message, for a caller checking several groups at once.
    with pytest.raises(ValueError, match="for the left arm"):
        normality([1.0], name="the left arm")


def test_equal_variance_defaults_to_the_version_that_assumes_less() -> None:
    rng = np.random.default_rng(4)
    a, b = rng.normal(0, 1, 30), rng.normal(0, 3, 30)
    check = equal_variance(a, b)
    assert check.test == "brown-forsythe"
    assert check.rejects_equality
    assert check.sd_ratio == pytest.approx(
        max(a.std(ddof=1), b.std(ddof=1)) / min(a.std(ddof=1), b.std(ddof=1))
    )
    assert check.size_ratio == 1.0
    # Bartlett is reachable and assumes normality, which is stronger than what it is checking.
    assert equal_variance(a, b, test="bartlett").test == "bartlett"
    with pytest.raises(ValueError, match="must be 'brown-forsythe'"):
        equal_variance(a, b, test="fligner")
    with pytest.raises(ValueError, match="at least two observations"):
        equal_variance([1.0], b)


def test_the_pooled_exposure_flag_reads_both_ratios_not_the_p_value() -> None:
    """Unequal spread is a nuisance when the groups are balanced and a problem when they are not."""
    rng = np.random.default_rng(5)
    balanced = equal_variance(rng.normal(0, 1, 40), rng.normal(0, 3, 40))
    unbalanced = equal_variance(rng.normal(0, 3, 12), rng.normal(0, 1, 36))
    assert balanced.rejects_equality and not balanced.pooled_test_is_exposed
    assert unbalanced.rejects_equality and unbalanced.pooled_test_is_exposed


def test_compare_means_always_uses_welch_and_says_so() -> None:
    rng = np.random.default_rng(6)
    a, b = rng.normal(0, 3, 12), rng.normal(0, 1, 36)
    result = compare_means(a, b)
    assert result.test == "Welch t"
    # Matches scipy's Welch exactly, and is not the pooled test.
    expected = stats.ttest_ind(b, a, equal_var=False)
    assert result.p_value == pytest.approx(float(expected.pvalue), abs=1e-12)
    assert result.statistic == pytest.approx(float(expected.statistic), abs=1e-12)
    assert result.p_value != pytest.approx(float(stats.ttest_ind(b, a, equal_var=True).pvalue))
    # Welch degrees of freedom are fractional, which is a cheap way to prove which test ran.
    assert result.df != int(result.df)
    # The checks come back as evidence, computed but not consulted to choose the test.
    assert len(result.normality) == 2
    assert result.variance.test == "brown-forsythe"


def test_the_confidence_interval_brackets_the_difference_and_matches_the_verdict() -> None:
    rng = np.random.default_rng(8)
    a, b = rng.normal(0, 1, 40), rng.normal(2, 1, 40)
    result = compare_means(a, b)
    low, high = result.confidence_interval
    assert low < result.difference < high
    # A significant two-sided result is exactly one that excludes zero.
    assert result.significant == (low > 0 or high < 0)


def _skewed(rng: np.random.Generator, shape: tuple[int, ...], sd: float) -> np.ndarray:
    """Standardised lognormal, so only the shape differs from a normal of the same mean and sd."""
    sigma = 0.75
    centre = math.exp(sigma**2 / 2)
    spread = math.sqrt((math.exp(sigma**2) - 1) * math.exp(sigma**2))
    return (rng.lognormal(0.0, sigma, shape) - centre) / spread * sd


def test_strict_refuses_the_regime_where_nothing_holds() -> None:
    """And the default returns the result with the flag set, which is the documented choice.

    The draw comes from a seed where the diagnostic does fire, and finding one took a search:
    on this population it fires on 151 of the first 200 seeds, which is the 75% the test below
    measures. Two earlier versions of this test used seeds where it missed, and that failure was
    the finding rather than a broken assertion - it is why this test exists alongside the one
    that quantifies the miss rate, rather than in place of it.

    Note which group carries the flag here. The ten-observation group has a sample skewness of
    0.946, below the 1.374 its size demands; the thirty-observation group has 1.454 and clears
    1.000. The regime is recognised through the larger group, which is the only one where the
    estimator can see anything.
    """
    rng = np.random.default_rng(0)
    a, b = _skewed(rng, (10,), 6.0), _skewed(rng, (30,), 2.0)
    lenient = compare_means(a, b)
    assert lenient.unreliable_regime
    assert lenient.diagnosis().startswith("unreliable")
    assert lenient.variance.sd_ratio == pytest.approx(3.0820, abs=5e-4)
    assert not lenient.normality[0].materially_skewed
    assert lenient.normality[1].materially_skewed
    with pytest.raises(ValueError, match="a different design, not a different test"):
        compare_means(a, b, strict=True)


def test_the_regime_flag_misses_one_case_in_four() -> None:
    """The honest limitation of the flag, measured rather than asserted.

    Both of its inputs are unreliable in exactly the regime it exists to detect. At ten
    observations the sample skewness cannot reach the population value of 3.26 at all, and on a
    skewed population the sample spread ratio is wild: drawn from a true 3.00, its middle 90%
    spans 1.15 to 6.76. So the flag catches the regime three times in four and misses the rest,
    which is why ``strict`` is documented as a blunt instrument rather than a safeguard.
    """
    rng = np.random.default_rng(23)
    replications = 20_000
    a = _skewed(rng, (replications, 10), 6.0)
    b = _skewed(rng, (replications, 30), 2.0)

    skew_a = stats.skew(a, axis=1, bias=False)
    skew_b = stats.skew(b, axis=1, bias=False)

    def material(skew: np.ndarray, n: int) -> np.ndarray:
        error = skewness_standard_error(n)
        return (np.abs(skew) >= SKEW_MATERIAL) & (np.abs(skew) >= SKEW_STANDARD_ERRORS * error)

    flagged_skew = material(skew_a, 10) | material(skew_b, 30)
    sd_a, sd_b = a.std(axis=1, ddof=1), b.std(axis=1, ddof=1)
    ratio = np.maximum(sd_a, sd_b) / np.minimum(sd_a, sd_b)
    flagged_spread = ratio >= VARIANCE_RATIO_MATERIAL

    # The sample spread ratio, drawn from a population ratio of exactly 3.00.
    assert float(np.median(ratio)) == pytest.approx(2.601, abs=5e-3)
    assert float(np.percentile(ratio, 5)) == pytest.approx(1.152, abs=5e-3)
    assert float(np.percentile(ratio, 95)) == pytest.approx(6.762, abs=5e-3)

    assert float(np.mean(flagged_skew)) == pytest.approx(0.9001, abs=5e-4)
    assert float(np.mean(flagged_spread)) == pytest.approx(0.8434, abs=5e-4)
    assert float(np.mean(flagged_skew & flagged_spread)) == pytest.approx(0.7501, abs=5e-4)


def test_compare_means_refuses_groups_too_small_to_check() -> None:
    with pytest.raises(ValueError, match="at least three observations"):
        compare_means([1.0, 2.0], [1.0, 2.0, 3.0])


def test_the_simulation_recovers_the_nominal_rate_where_every_assumption_holds() -> None:
    """The control case. If this drifts, every other row in the table is suspect."""
    rates = type_one_error_rates(n_first=20, n_second=20, replications=20_000)
    assert set(rates) == set(PROCEDURES)
    for procedure, rate in rates.items():
        assert rate == pytest.approx(DEFAULT_ALPHA, abs=0.004), procedure


def test_the_simulation_refuses_inputs_it_cannot_simulate() -> None:
    with pytest.raises(ValueError, match="at least three observations"):
        type_one_error_rates(n_first=2, n_second=20)
    with pytest.raises(ValueError, match="standard deviations must be positive"):
        type_one_error_rates(n_first=20, n_second=20, sd_first=0.0)
    with pytest.raises(ValueError, match="replications must be at least one"):
        type_one_error_rates(n_first=20, n_second=20, replications=0)
    with pytest.raises(ValueError, match="shape must be"):
        type_one_error_rates(n_first=20, n_second=20, shape="cauchy")


def test_the_simulation_is_reproducible_and_seed_dependent() -> None:
    first = type_one_error_rates(n_first=10, n_second=30, sd_first=3.0, replications=2_000)
    again = type_one_error_rates(n_first=10, n_second=30, sd_first=3.0, replications=2_000)
    other = type_one_error_rates(n_first=10, n_second=30, sd_first=3.0, replications=2_000, seed=99)
    assert first == again
    assert first != other


def test_the_normality_tradeoff_control_case_is_calibrated() -> None:
    """On normal data the detection rate has to come out at alpha, or the instrument is broken."""
    result = normality_test_tradeoff(30, shape="normal", replications=2_000)
    assert result["detection_rate"] == pytest.approx(DEFAULT_ALPHA, abs=0.015)
    assert result["welch_type_one_error"] == pytest.approx(DEFAULT_ALPHA, abs=0.015)


def test_the_normality_tradeoff_refuses_what_it_cannot_measure() -> None:
    with pytest.raises(ValueError, match="at least three observations"):
        normality_test_tradeoff(2)
    with pytest.raises(ValueError, match="shape must be"):
        normality_test_tradeoff(30, shape="weibull")
    with pytest.raises(ValueError, match="replications must be at least one"):
        normality_test_tradeoff(30, replications=0)

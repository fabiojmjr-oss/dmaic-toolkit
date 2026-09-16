"""Power arithmetic, checked against closed forms and against its own invariants.

A power routine tested only against its own output tests nothing, so the checks here anchor on
things that can be derived independently: the power at the null, the exact relationship between
the two percentages a study reports, and the direction every monotonicity has to run in.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from dmaic.analyze import (
    DEFAULT_ALPHA,
    DEFAULT_POWER,
    PowerAnalysis,
    detectable_difference,
    observed_power_is_circular,
    power_paired,
    power_two_means,
    power_two_proportions,
    sample_size_normal_approximation,
    sample_size_two_means,
    sample_size_two_proportions,
)


def test_power_at_a_zero_effect_is_the_significance_level() -> None:
    """The one point where power has a closed form: under the null, rejecting is a type I error."""
    for n in (5, 30, 200):
        for alpha in (0.01, 0.05, 0.10):
            assert power_two_means(n, 0.0, 1.0, alpha=alpha) == pytest.approx(alpha, abs=1e-9)
            assert power_paired(n, 0.0, 1.0, alpha=alpha) == pytest.approx(alpha, abs=1e-9)


def test_power_matches_the_noncentral_t_computed_by_hand() -> None:
    """Recomputed from scipy primitives rather than trusting the wrapper."""
    n, delta, sd, alpha = 30, 4.0, 12.0, 0.05
    df = 2 * n - 2
    ncp = delta / (sd * math.sqrt(2.0 / n))
    critical = stats.t.ppf(1.0 - alpha / 2.0, df)
    expected = stats.nct.sf(critical, df, ncp) + stats.nct.cdf(-critical, df, ncp)
    assert power_two_means(n, delta, sd, alpha=alpha) == pytest.approx(expected, abs=1e-12)
    # And it is not the normal approximation, which is what a lazier implementation would give.
    normal = stats.norm.sf(stats.norm.ppf(1 - alpha / 2) - ncp)
    assert abs(power_two_means(n, delta, sd) - normal) > 1e-4


def test_power_rises_with_n_effect_and_alpha() -> None:
    """Three monotonicities that have to hold or the function is wired wrong."""
    base = power_two_means(30, 4.0, 12.0)
    assert power_two_means(60, 4.0, 12.0) > base
    assert power_two_means(30, 6.0, 12.0) > base
    assert power_two_means(30, 4.0, 6.0) > base
    assert power_two_means(30, 4.0, 12.0, alpha=0.10) > base
    # A one-sided test in the right direction beats a two-sided one at the same alpha.
    assert power_two_means(30, 4.0, 12.0, alternative="greater") > base


def test_power_is_symmetric_in_the_sign_of_the_effect_when_two_sided() -> None:
    assert power_two_means(30, 4.0, 12.0) == pytest.approx(power_two_means(30, -4.0, 12.0))
    # And the one-sided alternatives mirror each other.
    assert power_two_means(30, 4.0, 12.0, alternative="greater") == pytest.approx(
        power_two_means(30, -4.0, 12.0, alternative="less")
    )


def test_power_depends_only_on_the_effect_size() -> None:
    """Two studies with the same Cohen's d have the same power, whatever the units."""
    assert power_two_means(40, 2.0, 4.0) == pytest.approx(power_two_means(40, 50.0, 100.0))


def test_sample_size_delivers_the_power_it_was_asked_for() -> None:
    """And one fewer observation does not, which is what makes it the smallest such n."""
    for delta, sd, target in ((4.0, 12.0, 0.80), (1.0, 1.0, 0.90), (0.5, 1.0, 0.95)):
        analysis = sample_size_two_means(delta, sd, power=target)
        assert analysis.power >= target
        assert analysis.overshoot >= 0.0
        assert power_two_means(analysis.n_per_group - 1, delta, sd) < target


def test_the_normal_approximation_is_always_optimistic() -> None:
    """Never larger than the exact answer - the published claim, across the range."""
    for effect in (2.0, 1.5, 1.2, 1.0, 0.8, 0.5, 0.33, 0.2, 0.1):
        exact = sample_size_two_means(effect, 1.0).n_per_group
        approximate = sample_size_normal_approximation(effect, 1.0)
        assert approximate <= exact, effect
        # And the power it actually delivers falls short of the target it was given.
        assert power_two_means(approximate, effect, 1.0) <= DEFAULT_POWER


def test_detectable_difference_is_the_inverse_of_power() -> None:
    """Round-tripping is the check: the difference it returns has exactly the target power."""
    for n, sd, target in ((30, 12.0, 0.80), (10, 1.0, 0.90), (200, 5.0, 0.50)):
        delta = detectable_difference(n, sd, power=target)
        assert power_two_means(n, delta, sd) == pytest.approx(target, abs=1e-9)


def test_detectable_difference_shrinks_faster_than_one_over_root_n() -> None:
    """It falls as the study grows, and by more than the standard error alone would give.

    A first guess is that going from 10 to 400 per group shrinks the reach by sqrt(40). It
    shrinks by more, because the small study is penalised twice: it has fewer observations *and*
    a wider t quantile. The measured ratio is 6.68 against sqrt(40) = 6.32, and the gap is the
    degrees of freedom rather than a rounding artefact - which is also why the normal
    approximation understates what a small study needs.
    """
    reach = [detectable_difference(n, 12.0) for n in (10, 30, 100, 400)]
    assert reach == sorted(reach, reverse=True)
    ratio = reach[0] / reach[3]
    assert ratio > math.sqrt(40)
    assert ratio == pytest.approx(6.680, abs=5e-4)


def test_paired_uses_the_spread_of_the_differences() -> None:
    """A paired test on n pairs beats a two-sample test on n per group at the same sd.

    Because it spends its degrees of freedom on one sample rather than two, and because the
    standard error carries sqrt(n) rather than sqrt(n/2).
    """
    assert power_paired(30, 4.0, 12.0) > power_two_means(30, 4.0, 12.0)


def test_proportions_are_harder_to_detect_near_zero() -> None:
    """Five points from 0.50 and five points from 0.02 are not the same detection problem."""
    middle = sample_size_two_proportions(0.50, 0.55).n_per_group
    edge = sample_size_two_proportions(0.02, 0.07).n_per_group
    assert edge < middle
    # The published scrap case: 8% to 5.5% needs a sample nobody budgets for.
    scrap = sample_size_two_proportions(0.08, 0.055)
    assert scrap.n_per_group == 1568
    assert scrap.power >= DEFAULT_POWER
    assert np.isnan(scrap.sd)
    assert np.isnan(scrap.effect_size)


def test_observed_power_is_locked_to_the_p_value() -> None:
    """The claim the module refuses post-hoc power on, verified as a monotone correspondence."""
    pairs = [observed_power_is_circular(30, delta, 12.0) for delta in np.linspace(0.1, 15.0, 40)]
    powers = [power for power, _ in pairs]
    p_values = [p_value for _, p_value in pairs]
    assert powers == sorted(powers)
    assert p_values == sorted(p_values, reverse=True)


def test_observed_power_at_the_significance_boundary_is_one_half() -> None:
    """And converges on exactly one half as the study grows, which is why it says nothing."""
    from scipy import optimize

    previous = 1.0
    for n in (10, 30, 100, 500):
        boundary = optimize.brentq(
            lambda delta, n=n: observed_power_is_circular(n, delta, 12.0)[1] - DEFAULT_ALPHA,
            1e-9,
            200.0,
        )
        power, p_value = observed_power_is_circular(n, boundary, 12.0)
        assert p_value == pytest.approx(DEFAULT_ALPHA, abs=1e-9)
        assert power == pytest.approx(0.5, abs=0.02)
        # Monotonically closer to one half with every increase in n.
        assert abs(power - 0.5) < previous
        previous = abs(power - 0.5)


@pytest.mark.parametrize(
    ("power", "expected"),
    [
        (0.95, "adequate"),
        (DEFAULT_POWER, "adequate"),
        (0.7999, "marginal"),
        (0.50, "marginal"),
        (0.4999, "underpowered"),
        (0.2456, "underpowered"),
    ],
)
def test_the_verdict_bands_are_the_boundaries_they_claim(power: float, expected: str) -> None:
    """Tested on the boundaries themselves rather than on a sample size that lands near one.

    An earlier version guessed at n=70 to land in the marginal band and got 0.49938 - just
    underneath it. Constructing the analysis directly tests the classifier instead of testing
    my arithmetic about where a given n falls.
    """
    analysis = PowerAnalysis(
        test="two-sample t",
        n_per_group=30,
        delta=1.0,
        sd=1.0,
        alpha=DEFAULT_ALPHA,
        power=power,
        alternative="two-sided",
    )
    assert analysis.verdict() == expected
    assert analysis.beta == pytest.approx(1.0 - power)
    assert math.isnan(analysis.overshoot)


def test_a_sized_study_reports_the_target_it_overshot() -> None:
    analysis = sample_size_two_means(4.0, 12.0)
    assert analysis.verdict() == "adequate"
    assert analysis.target_power == DEFAULT_POWER
    assert analysis.overshoot == pytest.approx(analysis.power - DEFAULT_POWER)
    assert analysis.total_n == 2 * analysis.n_per_group


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: power_two_means(1, 1.0, 1.0), "at least two observations"),
        (lambda: power_two_means(30, 1.0, 0.0), "sd must be positive"),
        (lambda: power_two_means(30, 1.0, 1.0, alpha=0.0), "alpha must be"),
        (lambda: power_two_means(30, 1.0, 1.0, alternative="sideways"), "alternative must be"),
        (lambda: power_paired(1, 1.0, 1.0), "at least two pairs"),
        (lambda: power_paired(30, 1.0, -1.0), "sd_diff must be positive"),
        (lambda: sample_size_two_means(0.0, 1.0), "difference of zero"),
        (lambda: sample_size_two_means(1.0, 1.0, power=1.0), "power must be"),
        (lambda: detectable_difference(1, 1.0), "at least two observations"),
        (lambda: power_two_proportions(30, 0.0, 0.5), "p_control must be"),
        (lambda: power_two_proportions(30, 0.5, 1.0), "p_treatment must be"),
        (lambda: sample_size_two_proportions(0.3, 0.3), "difference of zero"),
        (lambda: observed_power_is_circular(1, 1.0, 1.0), "at least two observations"),
    ],
)
def test_it_refuses_inputs_outside_its_domain(call, message: str) -> None:
    """A number returned for an input the arithmetic does not cover is worse than an exception."""
    with pytest.raises(ValueError, match=message):
        call()


def test_a_hopeless_effect_is_refused_rather_than_answered() -> None:
    """At some point the honest answer is that a study is the wrong instrument."""
    with pytest.raises(ValueError, match="too small relative to the noise"):
        sample_size_two_means(1e-9, 1.0)

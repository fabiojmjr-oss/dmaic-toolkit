"""Every figure quoted in a README, re-derived.

Marked slow because they run the full studies and every example script. The point is not
coverage: it is that a change which moves a published number breaks the build instead of leaving
the text quietly wrong.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.analyze import (
    DEFAULT_ALPHA,
    PROCEDURES,
    Design,
    detectable_effect,
    effects,
    fractional_factorial,
    full_factorial,
)
from dmaic.analyze.factorial import IDENTITY
from dmaic.control import (
    SamplingPlan,
    inspect_lots,
    matched_plan,
    oc_curve,
    percentage_plan,
    plan_for,
)
from dmaic.define import (
    Charter,
    Ctq,
    entitlement,
    entitlement_inflation,
    gap_by_window,
    overattribution,
)
from dmaic.improve import (
    BenefitCase,
    before_after,
    difference_in_differences,
    regression_to_the_mean,
)
from dmaic.measure import (
    bias_significance_tradeoff,
    bias_study,
    calibration_interval,
    gage_rr,
    guard_band,
    linearity_study,
    misclassification,
    stability_study,
)
from dmaic.synth import DRIFTS, FACTORIALS, GAGES, PANELS, Dataset

FACTORIAL = FACTORIALS[0]


def _estimates(design: Design, full: Dataset) -> pd.Series:
    """One design's estimates, read off the one measured experiment.

    Every factorial figure below comes through here, so no table can be produced from a different
    noise draw than another: the fractions select rows of the sixteen runs rather than being
    generated separately.
    """
    runs = full.factorial_runs
    coded = runs[list(FACTORIAL.factors)].to_numpy()
    response = runs["response"].to_numpy()
    table = effects(design, response[design.rows_of(coded)])
    return table.set_index("effect")["estimate"]


@pytest.mark.slow
def test_the_gage_table_reproduces(full: Dataset) -> None:
    """The three-gage table in the module README and both root READMEs."""
    specs = full.specifications.set_index("gage")
    expected = {
        # gage: (EV, AV, GRR, PV, %contribution, %study, %tolerance, ndc, verdict, dominant)
        "BALANCA-01": (
            0.3956,
            0.2616,
            0.4743,
            7.5277,
            0.40,
            6.29,
            5.69,
            22,
            "acceptable",
            "repeatability",
        ),
        "PAQUIMETRO-02": (
            0.0659,
            0.0830,
            0.1060,
            0.6439,
            2.64,
            16.24,
            63.58,
            8,
            "unacceptable",
            "reproducibility",
        ),
        "INSPECAO-03": (
            1.2467,
            3.9790,
            4.1698,
            5.0036,
            40.99,
            64.02,
            62.55,
            1,
            "unacceptable",
            "reproducibility",
        ),
    }
    for gage, row in expected.items():
        ev, av, grr, pv, contribution, study, tolerance, ndc, verdict, dominant = row
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        fitted = gage_rr(group, tolerance=float(specs.loc[gage, "tolerance"]), gage=gage)
        assert fitted.ev == pytest.approx(ev, abs=5e-5), gage
        assert fitted.av == pytest.approx(av, abs=5e-5), gage
        assert fitted.grr == pytest.approx(grr, abs=5e-5), gage
        assert fitted.pv == pytest.approx(pv, abs=5e-5), gage
        assert fitted.pct_contribution == pytest.approx(contribution, abs=5e-3), gage
        assert fitted.pct_study == pytest.approx(study, abs=5e-3), gage
        assert fitted.pct_tolerance == pytest.approx(tolerance, abs=5e-3), gage
        assert fitted.ndc == ndc, gage
        assert fitted.verdict() == verdict, gage
        assert fitted.dominant_source == dominant, gage


@pytest.mark.slow
def test_the_three_ways_of_reading_one_gage(full: Dataset) -> None:
    """The headline claim: 2.64, 16.24 and 63.58 are the same measurement system."""
    group = full.gage_studies[full.gage_studies["gage"] == "PAQUIMETRO-02"]
    fitted = gage_rr(group, tolerance=1.0)

    # Contribution reads as excellent, study variation as conditional, tolerance as hopeless.
    assert fitted.pct_contribution < 10.0
    assert 10.0 < fitted.pct_study < 30.0
    assert fitted.pct_tolerance > 30.0
    # The first is the second squared, which is why the confusion is so expensive.
    assert fitted.pct_contribution == pytest.approx(fitted.pct_study**2 / 100.0, abs=1e-9)
    # And the tolerance criterion is nearly four times the study criterion here.
    assert fitted.pct_tolerance / fitted.pct_study == pytest.approx(3.915, abs=5e-3)

    # INSPECAO-03's reproducibility is 3.2x its repeatability, so the instrument is not at fault.
    coating = gage_rr(full.gage_studies[full.gage_studies["gage"] == "INSPECAO-03"], tolerance=40.0)
    assert coating.av / coating.ev == pytest.approx(3.19, abs=5e-3)


@pytest.mark.slow
def test_pooling_the_interaction_flips_the_diagnosis(full: Dataset) -> None:
    """The pooling table in the module README, and the interaction p-values quoted beside it."""
    expected_p = {"BALANCA-01": 0.0357, "PAQUIMETRO-02": 0.0, "INSPECAO-03": 0.0}
    for gage, p_value in expected_p.items():
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        assert gage_rr(group).interaction_p_value == pytest.approx(p_value, abs=5e-5), gage
        # AIAG's rule retains the interaction for all three, which is the rule working.
        assert gage_rr(group).interaction_pooled is False, gage

    pooling = {
        # gage: ((EV, AV, GRR, %study) retained, (EV, AV, GRR, %study) pooled)
        "PAQUIMETRO-02": (
            (0.0659, 0.0830, 0.1060, 16.24),
            (0.0954, 0.0000, 0.0954, 14.63),
        ),
        "INSPECAO-03": (
            (1.2467, 3.9790, 4.1698, 64.02),
            (2.9918, 2.4435, 3.8628, 59.12),
        ),
    }
    for gage, (retained_row, pooled_row) in pooling.items():
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        retained = gage_rr(group, interaction_alpha=1.0)
        pooled = gage_rr(group, interaction_alpha=0.0)
        for fitted, (ev, av, grr, study) in ((retained, retained_row), (pooled, pooled_row)):
            assert fitted.ev == pytest.approx(ev, abs=5e-5), gage
            assert fitted.av == pytest.approx(av, abs=5e-5), gage
            assert fitted.grr == pytest.approx(grr, abs=5e-5), gage
            assert fitted.pct_study == pytest.approx(study, abs=5e-3), gage
        # The GRR barely moves and the diagnosis inverts, which is the finding.
        assert retained.dominant_source == "reproducibility", gage
        assert pooled.dominant_source == "repeatability", gage
        assert pooled.av == 0.0 or pooled.av < retained.av


@pytest.mark.slow
def test_the_hand_computed_anova_quoted_in_the_readme(balanced) -> None:
    """The root READMEs quote 242, 50, 2 and 8 adding to 302."""
    from dmaic.measure import anova

    table = anova(balanced).set_index("source")
    assert [
        table.loc["part", "ss"],
        table.loc["operator", "ss"],
        table.loc["part * operator", "ss"],
        table.loc["repeatability", "ss"],
    ] == [242.0, 50.0, 2.0, 8.0]
    assert table.loc["total", "ss"] == 302.0

    # And the multiplier claim: exactly 1.1650x on percent tolerance, nothing on percent study.
    from dmaic.synth import generate_dataset

    group = generate_dataset().gage_studies
    group = group[group["gage"] == "PAQUIMETRO-02"]
    modern = gage_rr(group, tolerance=1.0, sigma_multiplier=6.0)
    legacy = gage_rr(group, tolerance=1.0, sigma_multiplier=5.15)
    assert modern.pct_tolerance / legacy.pct_tolerance == pytest.approx(1.1650, abs=5e-5)
    assert modern.pct_study == legacy.pct_study


@pytest.mark.slow
def test_the_three_pilots_all_missed_a_real_effect(full: Dataset) -> None:
    """The trial table in the module README and both root READMEs.

    The load-bearing claim is not any single figure: it is that all three studies returned a
    non-significant result and all three had a real effect. That is pinned as a conjunction, so
    a change that rescued one of them would break the build rather than quietly weaken the point.
    """
    from scipy import stats

    from dmaic.analyze import (
        detectable_difference,
        power_two_means,
        power_two_proportions,
        sample_size_two_means,
        sample_size_two_proportions,
    )

    designs = full.trial_designs.set_index("trial")
    expected = {
        # trial: (observed, p_value, power_for_truth, n_needed)
        "PILOTO-CICLO": (-0.2917, 0.9234, 0.2456, 143),
        "PILOTO-SETUP": (-2.7709, 0.2345, 0.7905, 6),
        "PILOTO-REFUGO": (-0.0350, 0.2152, 0.1702, 1568),
    }
    for trial, (observed, p_value, power, needed) in expected.items():
        group = full.improvement_trials[full.improvement_trials["trial"] == trial]
        baseline = group.loc[group["arm"] == "baseline", "value"].to_numpy()
        improved = group.loc[group["arm"] == "improved", "value"].to_numpy()
        n = int(designs.loc[trial, "n_per_arm"])
        truth = float(designs.loc[trial, "true_effect"])

        assert float(improved.mean() - baseline.mean()) == pytest.approx(observed, abs=5e-5), trial
        if designs.loc[trial, "kind"] == "binary":
            control = float(designs.loc[trial, "baseline"])
            table = [
                [baseline.sum(), n - baseline.sum()],
                [improved.sum(), n - improved.sum()],
            ]
            assert float(stats.chi2_contingency(table).pvalue) == pytest.approx(p_value, abs=5e-5)
            assert power_two_proportions(n, control, control + truth) == pytest.approx(
                power, abs=5e-5
            )
            assert sample_size_two_proportions(control, control + truth).n_per_group == needed
        else:
            sd = float(designs.loc[trial, "sd"])
            assert float(stats.ttest_ind(improved, baseline).pvalue) == pytest.approx(
                p_value, abs=5e-5
            )
            assert power_two_means(n, truth, sd) == pytest.approx(power, abs=5e-5)
            assert sample_size_two_means(abs(truth), sd).n_per_group == needed

        # The conjunction: not significant, and yet a real effect was there to be found.
        assert p_value > 0.05, trial
        assert truth != 0.0, trial
        # And every one of them ran less than the sample it needed.
        assert n < needed, trial

    # PILOTO-CICLO's detectable difference, twice its own effect and then some.
    cycle_reach = detectable_difference(30, 12.0)
    assert cycle_reach == pytest.approx(8.8275, abs=5e-5)
    assert cycle_reach > 2 * abs(float(designs.loc["PILOTO-CICLO", "true_effect"]))
    # PILOTO-REFUGO observed a bigger improvement than the one that existed and still failed.
    assert abs(-0.0350) > abs(float(designs.loc["PILOTO-REFUGO", "true_effect"]))
    assert pytest.approx(7.84, abs=5e-3) == 1568 / 200


@pytest.mark.slow
def test_the_normal_approximation_table_reproduces() -> None:
    """The formula-on-the-wall table, including the claim that it is harmless in the middle."""
    from dmaic.analyze import (
        DEFAULT_POWER,
        power_two_means,
        sample_size_normal_approximation,
        sample_size_two_means,
    )

    expected = {
        # d: (exact n, formula n, power the formula delivers)
        2.00: (6, 4, 0.6569),
        1.50: (9, 7, 0.7313),
        1.00: (17, 16, 0.7814),
        0.50: (64, 63, 0.7952),
        0.33: (146, 145, 0.7997),
        0.10: (1571, 1570, 0.7998),
    }
    for effect, (exact, formula, delivered) in expected.items():
        assert sample_size_two_means(effect, 1.0).n_per_group == exact, effect
        assert sample_size_normal_approximation(effect, 1.0) == formula, effect
        assert power_two_means(formula, effect, 1.0) == pytest.approx(delivered, abs=5e-5), effect

    # The published nuance: off by one per group through the practical range, and only material
    # at an effect so large the study is tiny.
    for effect in (1.00, 0.50, 0.33, 0.10):
        assert expected[effect][0] - expected[effect][1] == 1
        assert expected[effect][2] > DEFAULT_POWER - 0.02
    assert expected[2.00][2] < 0.70


@pytest.mark.slow
def test_observed_power_is_a_function_of_the_p_value() -> None:
    """The circularity table, and the convergence on one half at the boundary."""
    from scipy import optimize

    from dmaic.analyze import DEFAULT_ALPHA, observed_power_is_circular

    expected = {
        2.0: (0.5212, 0.0973),
        4.0: (0.2018, 0.2456),
        6.0: (0.0577, 0.4779),
        6.2: (0.0501, 0.5032),
        8.0: (0.0124, 0.7187),
        12.0: (0.0003, 0.9677),
    }
    for observed, (p_value, power) in expected.items():
        got_power, got_p = observed_power_is_circular(30, observed, 12.0)
        assert got_p == pytest.approx(p_value, abs=5e-5), observed
        assert got_power == pytest.approx(power, abs=5e-5), observed

    boundaries = {10: 0.5114, 30: 0.5035, 100: 0.5010, 500: 0.5002}
    for n, at_boundary in boundaries.items():
        effect = optimize.brentq(
            lambda delta, n=n: observed_power_is_circular(n, delta, 12.0)[1] - DEFAULT_ALPHA,
            1e-9,
            200.0,
        )
        power, _ = observed_power_is_circular(n, effect, 12.0)
        assert power == pytest.approx(at_boundary, abs=5e-5), n
    # Which is the whole point: the figure converges on one half and says nothing else.
    assert list(boundaries.values()) == sorted(boundaries.values(), reverse=True)


@pytest.mark.slow
def test_the_type_one_error_table_reproduces() -> None:
    """The six-row table in README-compare.md and both root READMEs.

    Asserted against the exact simulated values rather than their four-decimal display, because
    several of these rates land on a rounding tie and the published digits depend on which way
    the formatter breaks it.
    """
    from dmaic.analyze import type_one_error_rates

    expected = {
        # scenario keywords: (pooled t, Welch, flowchart, Mann-Whitney)
        (20, 20, 1.0, 1.0, "normal"): (0.04795, 0.04770, 0.04780, 0.04810),
        (20, 20, 1.0, 3.0, "normal"): (0.05400, 0.04995, 0.05005, 0.06625),
        (10, 30, 1.0, 3.0, "normal"): (0.00380, 0.04780, 0.04315, 0.01505),
        (10, 30, 3.0, 1.0, "normal"): (0.21305, 0.05070, 0.06280, 0.12700),
        (20, 20, 1.0, 1.0, "skewed"): (0.04350, 0.04110, 0.04245, 0.04810),
        (10, 30, 3.0, 1.0, "skewed"): (0.23310, 0.11120, 0.14535, 0.28500),
    }
    measured = {}
    for key, rates in expected.items():
        n_first, n_second, sd_first, sd_second, shape = key
        got = type_one_error_rates(
            n_first=n_first,
            n_second=n_second,
            sd_first=sd_first,
            sd_second=sd_second,
            shape=shape,
        )
        measured[key] = got
        for procedure, value in zip(PROCEDURES, rates, strict=True):
            assert got[procedure] == pytest.approx(value, abs=1e-6), (key, procedure)

    balanced = measured[(20, 20, 1.0, 1.0, "normal")]
    wide_on_small = measured[(10, 30, 3.0, 1.0, "normal")]
    wide_on_large = measured[(10, 30, 1.0, 3.0, "normal")]
    unusable = measured[(10, 30, 3.0, 1.0, "skewed")]

    # The pooled test is wrong in both directions, and by more than an order of magnitude apart.
    assert wide_on_small["pooled t"] > 4 * DEFAULT_ALPHA
    assert wide_on_large["pooled t"] < DEFAULT_ALPHA / 10
    assert wide_on_small["pooled t"] / wide_on_large["pooled t"] > 50

    # Welch holds its level in every normal scenario, and costs nothing under equal spread.
    for key, rates in measured.items():
        if key[4] == "normal":
            assert abs(rates["Welch"] - DEFAULT_ALPHA) < 0.004, key
    assert abs(balanced["Welch"] - balanced["pooled t"]) < 0.001

    # The flowchart is strictly worse than always using Welch, in the case that matters.
    assert wide_on_small["flowchart"] > wide_on_small["Welch"]
    assert wide_on_small["flowchart"] / DEFAULT_ALPHA - 1 == pytest.approx(0.256, abs=5e-3)

    # A rank test does not rescue it: unequal spread breaks Mann-Whitney too, balanced or not.
    assert wide_on_small["Mann-Whitney"] > 2 * DEFAULT_ALPHA
    assert measured[(20, 20, 1.0, 3.0, "normal")]["Mann-Whitney"] > DEFAULT_ALPHA * 1.3

    # And in the last row nothing holds, so picking the least bad is not a solution.
    assert min(unusable.values()) > 2 * DEFAULT_ALPHA


@pytest.mark.slow
def test_the_normality_paradox_reproduces() -> None:
    """The two columns that move in opposite directions, and the control that calibrates them."""
    from dmaic.analyze.compare import normality_test_tradeoff

    expected = {
        5: (0.16325, 0.02400),
        10: (0.43475, 0.03900),
        20: (0.80325, 0.04400),
        50: (0.99775, 0.04825),
        100: (1.00000, 0.04675),
        300: (1.00000, 0.05225),
    }
    detection, error = [], []
    for n, (rate, welch) in expected.items():
        got = normality_test_tradeoff(n)
        assert got["detection_rate"] == pytest.approx(rate, abs=1e-6), n
        assert got["welch_type_one_error"] == pytest.approx(welch, abs=1e-6), n
        detection.append(got["detection_rate"])
        error.append(got["welch_type_one_error"])

    # The paradox: detection rises monotonically, and the cost of the departure falls away until
    # it reaches the nominal level and then only Monte Carlo noise separates the rows - 0.04825
    # at fifty against 0.04675 at a hundred. Asserting monotonicity across all six would be
    # asserting that noise has a direction, so the claim is split at the point where the error
    # rate arrives at alpha.
    assert detection == sorted(detection)
    informative = [rate for rate, n in zip(error, expected, strict=True) if n <= 20]
    assert informative == sorted(informative)
    for rate, n in zip(error, expected, strict=True):
        if n >= 50:
            assert rate == pytest.approx(DEFAULT_ALPHA, abs=0.004), n
    # At the small end the check passes most of the time and the test is badly conservative.
    assert detection[0] < 0.2 and error[0] < DEFAULT_ALPHA / 2
    # At the large end it fails every time and the test is already fine.
    assert detection[-1] == 1.0
    assert error[-1] == pytest.approx(DEFAULT_ALPHA, abs=0.003)

    # The control: on normal data the detection rate is alpha, so the instrument is calibrated
    # and the problem is the question being asked of it.
    for n in (10, 50, 300):
        control = normality_test_tradeoff(n, shape="normal")
        assert control["detection_rate"] == pytest.approx(DEFAULT_ALPHA, abs=0.005), n


@pytest.mark.slow
def test_the_diagnostic_cannot_see_what_breaks_the_test() -> None:
    """The estimator's blind spot: population skewness 3.2629, unreachable at ten observations."""
    import math

    import numpy as np
    from scipy import stats

    from dmaic.analyze import SKEW_MATERIAL, SKEW_STANDARD_ERRORS, skewness_standard_error

    sigma = 0.75
    population = (math.exp(sigma**2) + 2) * math.sqrt(math.exp(sigma**2) - 1)
    assert population == pytest.approx(3.2629, abs=5e-5)
    # The algebraic ceiling on a sample skewness, which sits below the truth at n = 10.
    assert (10 - 2) / math.sqrt(10 - 1) == pytest.approx(2.667, abs=5e-4)
    assert (10 - 2) / math.sqrt(10 - 1) < population

    centre = math.exp(sigma**2 / 2)
    spread = math.sqrt((math.exp(sigma**2) - 1) * math.exp(sigma**2))
    # A generator per n, so each figure depends only on (n, seed). An earlier version shared one
    # stream and every figure moved when n=50 was dropped from the list.
    expected = {
        10: (1.2073, 1.374, 0.3975),
        20: (1.5886, 1.024, 0.7326),
        30: (1.8045, 1.000, 0.8443),
        100: (2.3779, 1.000, 0.9907),
        300: (2.7777, 1.000, 0.9999),
    }
    rates = []
    for n, (mean_skew, threshold, detection) in expected.items():
        rng = np.random.default_rng(n)
        sample = (rng.lognormal(0.0, sigma, (20_000, n)) - centre) / spread
        skew = stats.skew(sample, axis=1, bias=False)
        error = skewness_standard_error(n)
        assert float(skew.mean()) == pytest.approx(mean_skew, abs=5e-4), n
        assert max(SKEW_MATERIAL, SKEW_STANDARD_ERRORS * error) == pytest.approx(
            threshold, abs=5e-4
        ), n
        got = float(
            np.mean(
                (np.abs(skew) >= SKEW_MATERIAL) & (np.abs(skew) >= SKEW_STANDARD_ERRORS * error)
            )
        )
        assert got == pytest.approx(detection, abs=5e-4), n
        rates.append(got)

    # The estimator is biased downward throughout, and the bias is what hides the problem.
    assert all(expected[n][0] < population for n in expected)
    assert rates == sorted(rates)
    # At the sample size where the pooled test runs at 23.31%, the skew is seen 40% of the time.
    assert rates[0] < 0.4
    # And it never reaches certainty even at three hundred, because the estimator stays biased.
    assert rates[-1] < 1.0


@pytest.mark.slow
def test_the_four_comparisons_reproduce(full: Dataset) -> None:
    """The comparison table, and the 34.6x gap between two tests on the same forty observations."""
    from scipy import stats

    from dmaic.analyze import compare_means

    designs = full.comparison_designs.set_index("comparison")
    expected = {
        # comparison: (sd_ratio, pooled p, Welch p, diagnosis prefix)
        "TURNO-A vs TURNO-B": (1.28447, 0.63062, 0.63075, "sound"),
        "LINHA-1 vs LINHA-2": (2.29861, 0.57238, 0.70014, "unreliable"),
        "CELULA-X vs CELULA-Y": (2.24954, 0.83570, 0.76784, "sound"),
        "FORN-X vs FORN-Y": (3.50240, 0.00190, 0.06571, "sound"),
    }
    for name, (sd_ratio, pooled_p, welch_p, prefix) in expected.items():
        frame = full.group_comparisons[full.group_comparisons["comparison"] == name]
        names = list(dict.fromkeys(frame["group"].tolist()))
        first = frame.loc[frame["group"] == names[0], "value"].to_numpy()
        second = frame.loc[frame["group"] == names[1], "value"].to_numpy()
        result = compare_means(first, second)
        assert result.variance.sd_ratio == pytest.approx(sd_ratio, abs=5e-5), name
        assert float(stats.ttest_ind(second, first, equal_var=True).pvalue) == pytest.approx(
            pooled_p, abs=5e-5
        ), name
        assert result.p_value == pytest.approx(welch_p, abs=5e-5), name
        assert result.diagnosis().startswith(prefix), name

    # The headline: the two tests differ by a factor of 34.6 on the one comparison with a real
    # effect, and the pooled test is the one that reaches significance.
    supplier = full.group_comparisons[full.group_comparisons["comparison"] == "FORN-X vs FORN-Y"]
    groups = list(dict.fromkeys(supplier["group"].tolist()))
    x = supplier.loc[supplier["group"] == groups[0], "value"].to_numpy()
    y = supplier.loc[supplier["group"] == groups[1], "value"].to_numpy()
    welch = compare_means(x, y)
    pooled = float(stats.ttest_ind(y, x, equal_var=True).pvalue)
    assert welch.p_value / pooled == pytest.approx(34.613, abs=5e-3)
    assert pooled < 0.01 < DEFAULT_ALPHA < welch.p_value
    assert float(designs.loc["FORN-X vs FORN-Y", "true_difference"]) == -2.0

    # Two of the four are drawn under the null, so nothing should reach significance on them.
    for name in ("TURNO-A vs TURNO-B", "LINHA-1 vs LINHA-2", "CELULA-X vs CELULA-Y"):
        assert float(designs.loc[name, "true_difference"]) == 0.0

    # The diagnostic's one false alarm and one miss, which is the empirical case against gating.
    linha = full.group_comparisons[full.group_comparisons["comparison"] == "LINHA-1 vs LINHA-2"]
    linha_names = list(dict.fromkeys(linha["group"].tolist()))
    flagged = compare_means(
        linha.loc[linha["group"] == linha_names[0], "value"].to_numpy(),
        linha.loc[linha["group"] == linha_names[1], "value"].to_numpy(),
    )
    # Normal population, 36 observations, and the skew flag fires anyway.
    assert designs.loc["LINHA-1 vs LINHA-2", "shape"] == "normal"
    assert flagged.normality[1].skewness == pytest.approx(-1.2674, abs=5e-4)
    assert flagged.normality[1].materially_skewed
    # Skewed population, 10 observations, and the flag misses it.
    assert designs.loc["FORN-X vs FORN-Y", "shape"] == "skewed"
    assert welch.normality[0].skewness == pytest.approx(1.0747, abs=5e-4)
    assert not welch.normality[0].materially_skewed


@pytest.mark.slow
def test_every_example_runs_and_prints_something() -> None:
    """A broken example is a broken README."""
    import runpy
    import sys
    from io import StringIO
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scripts = sorted((root / "examples").glob("*.py"))
    assert len(scripts) == 9

    for script in scripts:
        captured, sys.stdout = sys.stdout, StringIO()
        try:
            runpy.run_path(str(script), run_name="__main__")
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = captured
        assert output.strip(), f"{script.name} printed nothing"


@pytest.mark.slow
def test_the_planted_truth_is_what_the_factorial_readme_says(full: Dataset) -> None:
    """The truth table, and the two zeros the whole document rests on."""
    truth = full.factorial_effects.set_index("effect")["true_effect"]
    assert FACTORIAL.factors == ("temperatura", "pressao", "tempo de cura", "lote de resina")
    assert truth["A"] == 12.0
    assert truth["B"] == 5.0
    assert truth["C"] == 0.0
    assert truth["D"] == 0.0
    assert truth["AB"] == 8.0
    assert FACTORIAL.noise_sd == 1.5
    assert len(full.factorial_runs) == 16


@pytest.mark.slow
def test_the_three_design_table_reproduces(full: Dataset) -> None:
    """The estimate table in the factorial README, and the resolution row under it."""
    designs = {
        "full": full_factorial(FACTORIAL.factors),
        "resIV": fractional_factorial(FACTORIAL.factors, ("D=ABC",)),
        "resIII": fractional_factorial(FACTORIAL.factors, ("D=AB",)),
    }
    expected = {
        # term: (full 2^4, 2^(4-1) D=ABC, 2^(4-1) D=AB)
        "A": (12.5810, 11.8174, 13.1256),
        "B": (4.9727, 4.5785, 5.8547),
        "C": (0.2853, -0.3577, -0.4082),
        "D": (1.5494, 0.5307, 9.4067),
        "AB": (7.8573, 7.7678, 9.4067),
    }
    estimates = {name: _estimates(design, full) for name, design in designs.items()}
    for term, row in expected.items():
        for (name, series), value in zip(estimates.items(), row, strict=True):
            assert series[term] == pytest.approx(value, abs=5e-5), f"{name} {term}"

    assert designs["full"].resolution_label == "full"
    assert designs["resIV"].resolution_label == "IV"
    assert designs["resIII"].resolution_label == "III"

    # The headline: a factor with an effect of exactly zero, reported as the second largest in
    # the study, at 1.88 times the real pressure effect.
    assert full.factorial_effects.set_index("effect").loc["D", "true_effect"] == 0.0
    assert estimates["resIII"]["D"] / 5.0 == pytest.approx(1.88, abs=5e-3)
    # And the good fraction's cost, on the interaction, against the full sixteen runs.
    gap = abs(estimates["resIV"]["AB"] - estimates["full"]["AB"])
    assert gap == pytest.approx(0.0895, abs=5e-5)


@pytest.mark.slow
def test_the_two_fractions_rank_the_factors_differently(full: Dataset) -> None:
    """The ranking table, which is what a project would actually act on."""
    expected = {
        ("D=ABC",): ["A", "B", "D", "C"],
        ("D=AB",): ["A", "D", "B", "C"],
    }
    for generators, order in expected.items():
        design = fractional_factorial(FACTORIAL.factors, generators)
        estimates = _estimates(design, full)
        mains = estimates[list("ABCD")].abs().sort_values(ascending=False)
        assert list(mains.index) == order, generators


@pytest.mark.slow
def test_aliasing_is_an_exact_sum_of_the_full_designs_estimates(full: Dataset) -> None:
    """The claim that the fraction adds rather than blurs, to floating-point tolerance.

    This is the finding that does not depend on the noise draw: the resolution III design reports
    ``D + AB`` whatever the data. The 5.3e-15 quoted in the README is the worst deviation across
    every alias pair of both fractions.
    """
    complete = _estimates(full_factorial(FACTORIAL.factors), full)
    worst = 0.0
    for generators in (("D=ABC",), ("D=AB",)):
        design = fractional_factorial(FACTORIAL.factors, generators)
        estimates = _estimates(design, full)
        for effect, partners in design.aliases().items():
            if partners == (IDENTITY,):
                assert np.isnan(estimates[effect])
                continue
            total = complete[effect] + sum(complete[word] for word in partners)
            worst = max(worst, abs(total - estimates[effect]))
    assert worst < 5.4e-15

    # The two rows the README quotes, spelled out.
    aliased = _estimates(fractional_factorial(FACTORIAL.factors, ("D=AB",)), full)
    assert complete["D"] + complete["AB"] == pytest.approx(aliased["D"], abs=1e-12)
    fourth = _estimates(fractional_factorial(FACTORIAL.factors, ("D=ABC",)), full)
    assert complete["AB"] + complete["CD"] == pytest.approx(fourth["AB"], abs=1e-12)
    assert complete["CD"] == pytest.approx(-0.0895, abs=5e-5)


@pytest.mark.slow
def test_the_detection_limit_table_reproduces(full: Dataset) -> None:
    """What each run count could have seen, and the two ratios read off it."""
    expected = {8: 3.5711, 16: 2.2600, 32: 1.5355, 64: 1.0672}
    for n_runs, limit in expected.items():
        assert detectable_effect(n_runs, FACTORIAL.noise_sd) == pytest.approx(limit, abs=5e-5)

    complete = _estimates(full_factorial(FACTORIAL.factors), full)
    spurious = complete[["C", "D", "AC", "AD", "BC", "BD", "CD"]].abs().max()
    # The limit does its job against noise: the largest purely spurious estimate in the full
    # design is below it.
    assert spurious == pytest.approx(1.5494, abs=5e-5)
    assert spurious < expected[16]

    # And nothing at all against aliasing, which is a real effect in the wrong column.
    aliased = _estimates(fractional_factorial(FACTORIAL.factors, ("D=AB",)), full)
    assert aliased["D"] / expected[8] == pytest.approx(2.63, abs=5e-3)


@pytest.mark.slow
def test_two_four_letter_generators_can_still_give_resolution_two() -> None:
    """The trap the README names: the relation closes, the generators do not."""
    with pytest.raises(ValueError, match="resolution II"):
        fractional_factorial(("a", "b", "c", "d", "e"), ("D=ABC", "E=BCD"))


def _at_nominal(full: Dataset, gage: str) -> pd.Series:
    """The readings taken on the master nearest the centre of the range."""
    designs = full.reference_designs.set_index("gage")
    nominal = float(designs.loc[gage, "nominal"])
    readings = full.reference_studies
    selected = readings[(readings["gage"] == gage) & (readings["reference"] == nominal)]
    return selected["value"]


@pytest.mark.slow
def test_a_crossed_study_is_invariant_to_bias_to_the_quoted_precision(full: Dataset) -> None:
    """The 9.2e-12 in the accuracy README and both root READMEs.

    The figure is a residual of floating-point arithmetic, so it is bounded rather than matched:
    what is published is that the largest change across all three gages is under 1e-11, and a
    change that was actually a sensitivity would be orders of magnitude above it.
    """
    specs = full.specifications.set_index("gage")
    worst = 0.0
    for gage in specs.index:
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        tolerance = float(specs.loc[gage, "tolerance"])
        base = gage_rr(group, tolerance=tolerance, gage=str(gage))
        shifted = group.copy()
        shifted["value"] = shifted["value"] + 1000.0
        offset = gage_rr(shifted, tolerance=tolerance, gage=str(gage))
        for field in ("grr", "pct_study", "pct_contribution", "pct_tolerance", "ndc"):
            worst = max(worst, abs(getattr(base, field) - getattr(offset, field)))
    assert worst < 1e-11


@pytest.mark.slow
def test_the_accuracy_table_reproduces(full: Dataset) -> None:
    """The bias and linearity table in the accuracy README and both root READMEs."""
    designs = full.reference_designs.set_index("gage")
    expected = {
        # gage: (bias at nominal, p, % of tolerance, detectable, slope, span, span % of tolerance)
        "BALANCA-01": (3.9076, 0.0000, 7.8151, 0.3646, 0.0011, 0.0456, 0.0913),
        "PAQUIMETRO-02": (0.0058, 0.7113, 0.5779, 0.0468, -0.2205, 0.1764, 17.6419),
        "INSPECAO-03": (-0.0521, 0.8721, 0.1304, 0.9745, -0.0132, 0.4231, 1.0579),
    }
    for gage, row in expected.items():
        bias, p_value, pct, detectable, slope, span, span_pct = row
        tolerance = float(designs.loc[gage, "tolerance"])
        study = bias_study(
            _at_nominal(full, gage),
            reference=float(designs.loc[gage, "nominal"]),
            tolerance=tolerance,
            gage=gage,
        )
        assert study.bias == pytest.approx(bias, abs=5e-5), f"{gage} bias"
        assert study.p_value == pytest.approx(p_value, abs=5e-5), f"{gage} p"
        assert study.pct_tolerance == pytest.approx(pct, abs=5e-5), f"{gage} pct"
        assert study.detectable_bias == pytest.approx(detectable, abs=5e-5), f"{gage} detectable"

        group = full.reference_studies[full.reference_studies["gage"] == gage]
        linearity = linearity_study(group, tolerance=tolerance, gage=gage)
        assert linearity.slope == pytest.approx(slope, abs=5e-5), f"{gage} slope"
        assert linearity.span == pytest.approx(span, abs=5e-5), f"{gage} span"
        assert linearity.pct_tolerance_span == pytest.approx(span_pct, abs=5e-5), f"{gage} span %"

    # The three corners of the two-by-two the document is built on.
    balance = bias_study(
        _at_nominal(full, "BALANCA-01"), reference=500.0, tolerance=50.0, gage="BALANCA-01"
    )
    crossed = gage_rr(
        full.gage_studies[full.gage_studies["gage"] == "BALANCA-01"],
        tolerance=50.0,
        gage="BALANCA-01",
    )
    # Passes on precision, and its accuracy error is larger than its whole precision error.
    assert crossed.verdict() == "acceptable"
    assert balance.pct_tolerance > crossed.pct_tolerance

    caliper = full.reference_studies[full.reference_studies["gage"] == "PAQUIMETRO-02"]
    one_point = bias_study(
        _at_nominal(full, "PAQUIMETRO-02"), reference=25.0, tolerance=1.0, gage="PAQUIMETRO-02"
    )
    # The one-point check passes a gage whose offset spans 17.64% of the tolerance.
    assert not one_point.significant
    assert not one_point.material
    assert linearity_study(caliper, tolerance=1.0).material


@pytest.mark.slow
def test_what_the_bias_costs_reproduces(full: Dataset) -> None:
    """The ppm table, the guard band, and the three multiples quoted next to it."""
    profile = next(item for item in GAGES if item.gage == "BALANCA-01")
    crossed = gage_rr(
        full.gage_studies[full.gage_studies["gage"] == "BALANCA-01"],
        tolerance=profile.tolerance,
        gage="BALANCA-01",
    )
    found = bias_study(
        _at_nominal(full, "BALANCA-01"),
        reference=profile.nominal,
        tolerance=profile.tolerance,
    )
    limits = {
        "gage_sd": crossed.grr,
        "part_sd": profile.part_sd,
        "nominal": profile.nominal,
        "lsl": profile.lsl,
        "usl": profile.usl,
    }
    assert crossed.grr == pytest.approx(0.4743, abs=5e-5)
    assert found.bias == pytest.approx(3.9076, abs=5e-5)

    calibrated = misclassification(0.0, **limits)
    assert calibrated.conforming == pytest.approx(0.998222, abs=5e-7)
    assert calibrated.scrap_ppm == pytest.approx(161, abs=0.5)
    assert calibrated.escape_ppm == pytest.approx(128, abs=0.5)

    as_found = misclassification(found.bias, **limits)
    assert as_found.scrap_ppm == pytest.approx(3356, abs=0.5)
    assert as_found.escape_ppm == pytest.approx(734, abs=0.5)
    assert as_found.scrap_ppm / calibrated.scrap_ppm == pytest.approx(20.8, abs=5e-2)
    assert as_found.escape_ppm / calibrated.escape_ppm == pytest.approx(5.7, abs=5e-2)

    band = guard_band(calibrated.false_accept, found.bias, **limits)
    assert band == pytest.approx(3.5890, abs=5e-5)
    banded = misclassification(found.bias, guard=band, **limits)
    assert banded.escape_ppm == pytest.approx(calibrated.escape_ppm, abs=1e-6)
    assert banded.scrap_ppm == pytest.approx(13618, abs=0.5)
    assert banded.scrap_ppm / calibrated.scrap_ppm == pytest.approx(84.5, abs=5e-2)
    # 1.36% of everything produced, which is the figure the document quotes in percent.
    assert banded.scrap_ppm / 1e6 == pytest.approx(0.0136, abs=5e-5)


@pytest.mark.slow
def test_the_significance_rule_table_reproduces() -> None:
    """The four rows showing the verdict tracking the gage instead of the consequence."""
    table = bias_significance_tradeoff(
        (0.2, 0.56, 1.5, 4.0), bias=0.5, tolerance=50.0, n=12
    ).set_index("repeat_sd")
    expected = {
        # repeatability: (6 sigma as % of tolerance, bias / sd, flagged)
        0.2: (2.40, 2.5000, 1.0000),
        0.56: (6.72, 0.8929, 0.7983),
        1.5: (18.00, 0.3333, 0.1893),
        4.0: (48.00, 0.1250, 0.0717),
    }
    for sd, (precision, ratio, flagged) in expected.items():
        assert table.loc[sd, "pct_tolerance_precision"] == pytest.approx(precision, abs=5e-3)
        assert table.loc[sd, "bias_to_sd"] == pytest.approx(ratio, abs=5e-5)
        assert table.loc[sd, "flagged"] == pytest.approx(flagged, abs=5e-5)
        assert not bool(table.loc[sd, "material"])


@pytest.mark.slow
def test_the_calibration_interval_reproduces(full: Dataset) -> None:
    """The stability table in the stability README and both root READMEs."""
    design = full.drift_designs.set_index("gage").loc["BALANCA-01"]
    tolerance = float(design["tolerance"])
    study = stability_study(full.stability_checks, tolerance=tolerance, gage="BALANCA-01")

    assert study.n == 52
    assert study.last_day == 60
    assert study.drift_per_day == pytest.approx(0.105428, abs=5e-7)
    assert study.p_value < 1e-25
    assert study.r_squared == pytest.approx(0.9209, abs=5e-5)
    assert study.intercept == pytest.approx(-0.0932, abs=5e-5)
    assert study.offset_at(60) == pytest.approx(6.2325, abs=5e-5)
    assert study.pct_tolerance_at(60) == pytest.approx(12.47, abs=5e-3)
    assert study.days_to() == pytest.approx(22.8, abs=5e-2)
    assert calibration_interval(0.10, tolerance) == pytest.approx(25.0, abs=5e-2)

    # The residual spread lands on the gage's own repeatability, which is the check that this is
    # a drift rather than scatter given a slope.
    assert study.residual_sd == pytest.approx(0.5894, abs=5e-5)
    assert study.residual_sd == pytest.approx(float(design["repeat_sd"]), abs=0.05)

    # And the number that links this wave to wave 5: the 4 g offset as days of drift.
    assert 4.0 / study.drift_per_day == pytest.approx(37.9, abs=5e-2)
    assert 4.0 / DRIFTS[0].drift_per_day == pytest.approx(40.0)


@pytest.mark.slow
def test_the_schedule_table_reproduces(full: Dataset) -> None:
    """The three-schedule table, where only the day mapping differs."""
    tolerance = float(full.drift_designs.set_index("gage").loc["BALANCA-01", "tolerance"])
    studies = full.drift_studies
    results = {
        str(schedule): gage_rr(group, tolerance=tolerance, gage=str(schedule))
        for schedule, group in studies.groupby("schedule", observed=True)
    }
    without = studies[studies["schedule"] == "sequential"].copy()
    without["value"] = without["value"] - DRIFTS[0].drift_per_day * without["day"]
    results["drift removed"] = gage_rr(without, tolerance=tolerance, gage="drift removed")

    expected = {
        # schedule: (EV, AV, GRR, % study, % tolerance, ndc, dominant, verdict)
        "sequential": (0.6430, 1.0081, 1.1957, 12.68, 14.35, 11, "reproducibility", "conditional"),
        "interleaved": (0.9161, 0.3829, 0.9929, 10.56, 11.92, 13, "repeatability", "conditional"),
        "drift removed": (0.6430, 0.4010, 0.7578, 8.08, 9.09, 17, "repeatability", "acceptable"),
    }
    for schedule, row in expected.items():
        ev, av, grr, study, tol, ndc, dominant, verdict = row
        result = results[schedule]
        assert result.ev == pytest.approx(ev, abs=5e-5), f"{schedule} EV"
        assert result.av == pytest.approx(av, abs=5e-5), f"{schedule} AV"
        assert result.grr == pytest.approx(grr, abs=5e-5), f"{schedule} GRR"
        assert result.pct_study == pytest.approx(study, abs=5e-3), f"{schedule} % study"
        assert result.pct_tolerance == pytest.approx(tol, abs=5e-3), f"{schedule} % tolerance"
        assert result.ndc == ndc, f"{schedule} ndc"
        assert result.dominant_source == dominant, f"{schedule} dominant"
        assert result.verdict() == verdict, f"{schedule} verdict"

    # The two multiples quoted in the prose.
    truth = results["drift removed"]
    assert results["sequential"].av / truth.av == pytest.approx(2.51, abs=5e-3)
    assert results["interleaved"].ev / truth.ev == pytest.approx(1.42, abs=5e-3)


@pytest.mark.slow
def test_the_percentage_rule_table_reproduces() -> None:
    """The lot-size table, and the constancy a fixed sample has instead."""
    expected = {
        # lot size: (10% n, accepts good, accepts excursions, n=80 good, n=80 excursions)
        100: (10, 1.000000, 0.651631, 1.000000, 0.001236),
        500: (50, 0.809820, 0.116411, 0.705331, 0.028394),
        1000: (100, 0.589832, 0.013520, 0.658507, 0.033206),
        5000: (500, 0.071311, 0.0, 0.667502, 0.037165),
        20000: (2000, 0.000026, 0.0, 0.669115, 0.037917),
    }
    for lot_size, row in expected.items():
        n, good, bad, fixed_good, fixed_bad = row
        share = percentage_plan(lot_size)
        fixed = SamplingPlan(80, 0, lot_size)
        assert share.n == n
        assert share.accept_probability(0.005) == pytest.approx(good, abs=5e-7)
        assert share.accept_probability(0.040) == pytest.approx(bad, abs=5e-7)
        assert fixed.accept_probability(0.005) == pytest.approx(fixed_good, abs=5e-7)
        assert fixed.accept_probability(0.040) == pytest.approx(fixed_bad, abs=5e-7)


@pytest.mark.slow
def test_the_published_plan_curve_reproduces() -> None:
    """The operating characteristic table for n=125 c=3, and the c=0 comparison under it."""
    published = SamplingPlan(125, 3, 1000)
    expected = {
        0.005: (0.9989, 0.00437),
        0.010: (0.9732, 0.00852),
        0.020: (0.7668, 0.01342),
        0.030: (0.4713, 0.01237),
        0.040: (0.2408, 0.00843),
        0.050: (0.1077, 0.00471),
    }
    curve = oc_curve(published, tuple(expected)).set_index("fraction_defective")
    for fraction, (accepted, outgoing) in expected.items():
        assert curve.loc[fraction, "accept_probability"] == pytest.approx(accepted, abs=5e-5)
        assert curve.loc[fraction, "average_outgoing_quality"] == pytest.approx(outgoing, abs=5e-6)
    assert published.producer_risk(0.01) == pytest.approx(0.027, abs=5e-4)

    matched = matched_plan(published, 0, 0.01)
    assert matched.n == 3
    assert matched.producer_risk(0.01) == pytest.approx(0.030, abs=5e-4)
    assert matched.accept_probability(0.03) == pytest.approx(0.913, abs=5e-4)
    assert matched.accept_probability(0.04) == pytest.approx(0.885, abs=5e-4)

    same_sample = SamplingPlan(published.n, 0, published.lot_size)
    assert same_sample.producer_risk(0.01) == pytest.approx(0.739, abs=5e-4)
    assert same_sample.accept_probability(0.03) == pytest.approx(0.017, abs=5e-4)

    designed = plan_for(0.01, 0.04, lot_size=1000)
    assert (designed.n, designed.c) == (189, 4)
    assert designed.sampled_share == pytest.approx(0.189, abs=5e-4)


@pytest.mark.slow
def test_what_each_plan_bought_reproduces(full: Dataset) -> None:
    """The inspection table, on the seed it is published under."""
    lots = full.inspection_lots
    assert len(lots) == 200
    assert int((lots["state"] == "excursion").sum()) == 12
    assert int(lots["defectives"].sum()) == 1478

    published = SamplingPlan(125, 3, 1000)
    plans = {
        "percentage": (percentage_plan(1000), 20000, 12, 70, 543),
        "published": (published, 25000, 9, 0, 1098),
        "same sample c=0": (SamplingPlan(125, 0, 1000), 25000, 12, 86, 474),
        "matched c=0": (matched_plan(published, 0, 0.01), 600, 2, 4, 1383),
        "designed": (plan_for(0.01, 0.04, lot_size=1000), 37800, 10, 1, 1066),
    }
    for label, (plan, inspected, caught, rejected_good, shipped) in plans.items():
        decided = inspect_lots(plan, lots, seed=6)
        bad = decided[decided["state"] == "excursion"]
        good = decided[decided["state"] == "in control"]
        assert plan.n * len(decided) == inspected, f"{label} units inspected"
        assert int((~bad["accepted"]).sum()) == caught, f"{label} excursions caught"
        assert int((~good["accepted"]).sum()) == rejected_good, f"{label} good lots rejected"
        assert int(decided.loc[decided["accepted"], "defectives"].sum()) == shipped, label


@pytest.mark.slow
def test_the_three_estimates_of_one_effect_reproduce(full: Dataset) -> None:
    """The attribution table in the improve README and both root READMEs."""
    profile = PANELS[0]
    panel = full.site_performance
    naive = before_after(panel, split=profile.split)
    did = difference_in_differences(panel, split=profile.split)

    assert naive.effect == pytest.approx(-10.0637, abs=5e-5)
    assert naive.controls == 0
    assert not naive.attributable
    assert naive.effect / profile.true_effect == pytest.approx(2.01, abs=5e-3)

    assert did.effect == pytest.approx(-4.2241, abs=5e-5)
    assert did.treated == 5
    assert did.controls == 15
    assert did.attributable
    assert did.significant
    assert did.comparison is not None
    low, high = did.comparison.confidence_interval
    assert low == pytest.approx(-5.2545, abs=5e-5)
    assert high == pytest.approx(-3.1938, abs=5e-5)
    # The published claim about that interval: it contains the effect that was applied.
    assert low < profile.true_effect < high

    # The trend accounts for almost the whole of the before-and-after surplus.
    follow = profile.periods - profile.split
    assert profile.trend * follow == pytest.approx(-4.80)
    assert naive.effect - profile.true_effect == pytest.approx(-5.06, abs=5e-3)


@pytest.mark.slow
def test_the_selection_artefact_table_reproduces() -> None:
    """The regression-to-the-mean sweep, and the control column that has to be zero."""
    profile = PANELS[0]
    table = regression_to_the_mean(
        (1, 3, 6, 12, 24),
        sites=profile.sites,
        selected=profile.treated,
        site_sd=profile.site_sd,
        noise=profile.noise,
        follow_periods=profile.periods - profile.split,
    ).set_index("baseline_periods")
    expected = {
        # baseline: (worst selected, randomly selected)
        1: (-4.3401, -0.0524),
        3: (-1.6997, -0.0262),
        6: (-0.8365, -0.0063),
        12: (-0.4562, 0.0005),
        24: (-0.2294, -0.0022),
    }
    for baseline, (worst, random_pick) in expected.items():
        assert table.loc[baseline, "worst_selected"] == pytest.approx(worst, abs=5e-5)
        assert table.loc[baseline, "random_selected"] == pytest.approx(random_pick, abs=5e-5)

    # The published reading of the first row: 87% of a real five-unit improvement, from nothing.
    assert abs(table.loc[1, "worst_selected"]) / abs(profile.true_effect) == pytest.approx(
        0.87, abs=5e-3
    )


@pytest.mark.slow
def test_the_money_table_reproduces(full: Dataset) -> None:
    """The benefit case on each basis, and the decomposition of the gap between them."""
    profile = PANELS[0]
    panel = full.site_performance
    follow = profile.periods - profile.split
    volume = profile.units_per_period * profile.treated
    assert volume == 60000.0

    naive = before_after(panel, split=profile.split)
    did = difference_in_differences(panel, split=profile.split)

    def case(effect: float) -> BenefitCase:
        return BenefitCase(
            effect=effect,
            units_per_period=volume,
            periods=follow,
            variable_share=profile.variable_share,
            project_cost=profile.project_cost,
        )

    expected = {
        # basis: (gross, cash, capacity, net, payback)
        "booked": (case(naive.effect), 7245895, 2536063, 4709832, 2286063, 1.18),
        "did": (case(did.effect), 3041368, 1064479, 1976889, 814479, 2.82),
        "truth": (case(profile.true_effect), 3600000, 1260000, 2340000, 1010000, 2.38),
    }
    for label, row in expected.items():
        built, gross, cash, capacity, net, payback = row
        assert built.gross == pytest.approx(gross, abs=1.0), f"{label} gross"
        assert built.cash == pytest.approx(cash, abs=1.0), f"{label} cash"
        assert built.capacity == pytest.approx(capacity, abs=1.0), f"{label} capacity"
        assert built.net == pytest.approx(net, abs=1.0), f"{label} net"
        assert built.payback_periods == pytest.approx(payback, abs=5e-3), f"{label} payback"

    booked = case(naive.effect).gross
    real = case(profile.true_effect).cash
    # The headline multiple, and the two factors it is the product of.
    assert booked / real == pytest.approx(5.75, abs=5e-3)
    attribution = naive.effect / profile.true_effect
    conversion = 1.0 / profile.variable_share
    assert attribution == pytest.approx(2.01, abs=5e-3)
    assert conversion == pytest.approx(2.86, abs=5e-3)
    assert attribution * conversion == pytest.approx(booked / real, abs=1e-9)


@pytest.mark.slow
def test_the_gap_by_window_table_reproduces(full: Dataset) -> None:
    """The four-baseline table in the define README and both root READMEs."""
    profile = PANELS[0]
    table = gap_by_window(
        full.site_performance, last_period=profile.split, windows=(1, 3, 6, 12)
    ).set_index("window")
    expected = {
        # window: (mean, best, worst, gap to best, worst to best)
        1: (94.7895, 75.9952, 120.3974, 18.7943, 44.4022),
        3: (95.7523, 81.8822, 112.2490, 13.8701, 30.3668),
        6: (96.3559, 80.8312, 111.9404, 15.5247, 31.1092),
        12: (96.9307, 79.4887, 109.9823, 17.4420, 30.4936),
    }
    for window, row in expected.items():
        mean, best, worst, gap, spread = row
        assert table.loc[window, "mean"] == pytest.approx(mean, abs=5e-5)
        assert table.loc[window, "best"] == pytest.approx(best, abs=5e-5)
        assert table.loc[window, "worst"] == pytest.approx(worst, abs=5e-5)
        assert table.loc[window, "gap_to_best"] == pytest.approx(gap, abs=5e-5)
        assert table.loc[window, "worst_to_best"] == pytest.approx(spread, abs=5e-5)

    # The published reading: 46% more apparent spread between sites, from the window alone.
    ratio = table.loc[1, "worst_to_best"] / table.loc[12, "worst_to_best"]
    assert ratio - 1.0 == pytest.approx(0.46, abs=5e-3)


@pytest.mark.slow
def test_the_entitlement_inflation_table_reproduces() -> None:
    """The simulation, and the bracket that is the module's main claim."""
    profile = PANELS[0]
    table = entitlement_inflation(
        (1, 3, 6, 12, 24),
        units=profile.sites,
        site_sd=profile.site_sd,
        noise_sd=profile.noise,
    ).set_index("window")
    expected = {
        # window: (charter gap, true gap, shrunk gap, inflation)
        1: (18.6274, 14.8561, 11.9215, 3.7713),
        3: (16.2542, 14.9069, 13.6878, 1.3474),
        6: (15.6095, 14.9185, 14.2716, 0.6910),
        12: (15.2783, 14.9599, 14.5942, 0.3184),
        24: (15.2348, 15.0210, 14.8859, 0.2137),
    }
    for window, row in expected.items():
        charter_gap, true_gap, shrunk_gap, inflation = row
        assert table.loc[window, "charter_gap"] == pytest.approx(charter_gap, abs=5e-5)
        assert table.loc[window, "true_gap"] == pytest.approx(true_gap, abs=5e-5)
        assert table.loc[window, "shrunk_gap"] == pytest.approx(shrunk_gap, abs=5e-5)
        assert table.loc[window, "inflation"] == pytest.approx(inflation, abs=5e-5)

    # The published reading of the first row, and the bracket in every row.
    assert table.loc[1, "inflation"] / table.loc[1, "true_gap"] == pytest.approx(0.25, abs=5e-3)
    assert bool((table["shrunk_gap"] < table["true_gap"]).all())
    assert bool((table["true_gap"] < table["charter_gap"]).all())


@pytest.mark.slow
def test_the_charter_this_panel_would_produce_reproduces(full: Dataset) -> None:
    """The charter table, including the benefit the Improve phase's class computes."""
    profile = PANELS[0]
    panel = full.site_performance
    recent = panel[(panel["period"] > 0) & (panel["period"] <= profile.split)]
    averages = recent.groupby("site", observed=True)["value"].mean()
    reference = entitlement(averages, noise_sd=profile.noise, window=profile.split)

    assert reference.grand_mean == pytest.approx(96.9307, abs=5e-5)
    assert reference.observed_best == pytest.approx(79.4887, abs=5e-5)
    assert reference.charter_gap == pytest.approx(17.4420, abs=5e-5)
    assert reference.shrunk_gap == pytest.approx(16.6681, abs=5e-5)
    assert reference.reliability == pytest.approx(0.96, abs=5e-3)

    charter = Charter(
        measurand=profile.stream,
        unit=profile.unit,
        baseline=reference.grand_mean,
        baseline_window=profile.split,
        target=reference.observed_best,
        target_basis="entitlement",
        volume_per_period=profile.units_per_period * profile.sites,
        periods=profile.periods - profile.split,
        variable_share=profile.variable_share,
        project_cost=profile.project_cost,
    )
    assert charter.gap == pytest.approx(-17.4420, abs=5e-5)
    assert charter.gap_pct == pytest.approx(18.0, abs=5e-2)
    case = charter.benefit_case()
    assert case.gross == pytest.approx(50233061, abs=1.0)
    assert case.cash == pytest.approx(17581571, abs=1.0)
    assert case.capacity == pytest.approx(32651489, abs=1.0)
    assert case.net == pytest.approx(17331571, abs=1.0)


@pytest.mark.slow
def test_the_ctq_tree_over_attributes_by_the_published_multiple(full: Dataset) -> None:
    """The tree in example 09, against the gap the panel produces."""
    tree = Ctq(
        name="gap por pedido",
        children=(
            Ctq(
                name="separacao",
                children=(
                    Ctq("caminhamento", measurand="metros por linha", contribution=5.2),
                    Ctq("conferencia", measurand="segundos por linha", contribution=3.1),
                ),
            ),
            Ctq(
                name="embalagem",
                children=(
                    Ctq("material", measurand="BRL por caixa", contribution=2.4),
                    Ctq("retrabalho", contribution=1.8),
                ),
            ),
            Ctq(
                name="transporte",
                children=(
                    Ctq("ocupacao", measurand="m3 por veiculo", contribution=4.5),
                    Ctq("cultura de servico", contribution=2.6),
                ),
            ),
        ),
    )
    profile = PANELS[0]
    panel = full.site_performance
    recent = panel[panel["period"] <= profile.split]
    averages = recent.groupby("site", observed=True)["value"].mean()
    gap = entitlement(averages, noise_sd=profile.noise, window=profile.split).charter_gap

    assert tree.claimed == pytest.approx(19.60)
    assert overattribution(tree, gap) == pytest.approx(1.12, abs=5e-3)
    assert tree.unmeasurable_claim == pytest.approx(4.40)
    assert tree.unmeasurable_claim / tree.claimed == pytest.approx(0.224, abs=5e-4)
    assert not tree.measurable

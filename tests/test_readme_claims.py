"""Every figure quoted in a README, re-derived.

Marked slow because they run the full studies and every example script. The point is not
coverage: it is that a change which moves a published number breaks the build instead of leaving
the text quietly wrong.
"""

from __future__ import annotations

import pytest

from dmaic.analyze import DEFAULT_ALPHA, PROCEDURES
from dmaic.measure import gage_rr
from dmaic.synth import Dataset


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
    assert len(scripts) == 3

    for script in scripts:
        captured, sys.stdout = sys.stdout, StringIO()
        try:
            runpy.run_path(str(script), run_name="__main__")
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = captured
        assert output.strip(), f"{script.name} printed nothing"

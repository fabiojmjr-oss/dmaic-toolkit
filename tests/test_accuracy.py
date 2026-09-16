"""Accuracy, verified against exact cases and against the control cases that must hold.

The headline claim of the module - that a crossed gage study is invariant to bias - is arithmetic
rather than statistics, so it is asserted as equality within floating point rather than within a
tolerance. The rest follows the same pattern: a line fitted to points that lie on a line has to
come back exact, a perfect gage has to misjudge nothing, and a bias of zero has to be called
significant at exactly the significance level whatever the gage's precision.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.analyze.power import power_paired
from dmaic.measure import (
    BIAS_MATERIAL_PCT,
    bias_significance_tradeoff,
    bias_study,
    detectable_bias,
    gage_rr,
    guard_band,
    linearity_study,
    misclassification,
)
from dmaic.synth import GAGES, REFERENCES, Dataset

INVARIANT_FIELDS = ("ev", "av", "grr", "pv", "tv", "pct_study", "pct_contribution", "ndc")
LIMITS = {"gage_sd": 0.5, "part_sd": 8.0, "nominal": 500.0, "lsl": 475.0, "usl": 525.0}


def test_a_crossed_study_is_invariant_to_bias(full: Dataset) -> None:
    """The reason this module exists, measured on all three gages.

    Every AIAG figure is computed from differences between readings, so a constant added to all
    of them cancels. This is not a small sensitivity to be reported as a caveat; it is exact, and
    the residual below is floating-point representation of a 1000-unit shift.
    """
    specs = full.specifications.set_index("gage")
    for gage in specs.index:
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        tolerance = float(specs.loc[gage, "tolerance"])
        base = gage_rr(group, tolerance=tolerance, gage=str(gage))
        shifted = group.copy()
        shifted["value"] = shifted["value"] + 1000.0
        offset = gage_rr(shifted, tolerance=tolerance, gage=str(gage))
        for field in (*INVARIANT_FIELDS, "pct_tolerance"):
            assert getattr(base, field) == pytest.approx(
                getattr(offset, field), rel=1e-9, abs=1e-9
            ), f"{gage} {field}"
        assert base.verdict() == offset.verdict()
        assert base.dominant_source == offset.dominant_source


def test_the_bias_arithmetic_is_the_one_sample_t_worked_out_by_hand() -> None:
    """Readings 1, 2, 3 against a reference of 0: bias 2, sd 1, t = 2 / (1 / sqrt(3))."""
    study = bias_study([1.0, 2.0, 3.0], reference=0.0)
    assert study.bias == pytest.approx(2.0)
    assert study.sd == pytest.approx(1.0)
    assert study.standard_error == pytest.approx(1.0 / np.sqrt(3))
    assert study.t_statistic == pytest.approx(2.0 * np.sqrt(3))
    low, high = study.interval
    assert low < study.bias < high


def test_identical_readings_do_not_divide_by_zero() -> None:
    """A digital indicator reading the same digit every time, which is not a rare input.

    The first version of ``t_statistic`` divided the bias by a standard error of zero. Both
    limits are well defined and they point in opposite directions: no offset with no spread is no
    evidence, and an offset with no spread is certainty.
    """
    exact = bias_study([10.0, 10.0, 10.0, 10.0], reference=10.0, tolerance=1.0)
    assert exact.bias == 0.0
    assert exact.t_statistic == 0.0
    assert exact.p_value == 1.0
    assert not exact.significant
    assert not exact.material
    assert "no bias detected" in exact.verdict()

    offset = bias_study([10.5, 10.5, 10.5, 10.5], reference=10.0, tolerance=1.0)
    assert offset.t_statistic == np.inf
    assert offset.p_value == 0.0
    assert offset.significant
    assert offset.material


def test_without_a_tolerance_the_consequence_is_reported_as_unknown() -> None:
    """An unknown consequence is not a small one, and the verdict has to say which it is."""
    study = bias_study([12.0, 11.0, 13.0, 12.5], reference=10.0)
    assert np.isnan(study.pct_tolerance)
    assert not study.material
    assert "consequence unknown" in study.verdict()


def test_significance_and_materiality_are_reported_separately() -> None:
    """A precise gage with a trivial offset, and a sloppy one with a large offset."""
    rng = np.random.default_rng(3)
    trivial = bias_study(0.2 + rng.normal(0.0, 0.05, 30), reference=0.0, tolerance=100.0)
    assert trivial.significant
    assert not trivial.material
    assert trivial.pct_tolerance < BIAS_MATERIAL_PCT
    assert "significant but small" in trivial.verdict()

    large = bias_study(20.0 + rng.normal(0.0, 40.0, 4), reference=0.0, tolerance=100.0)
    assert large.material
    assert not large.significant
    assert "too small to settle" in large.verdict()


def test_a_bias_study_refuses_what_it_cannot_compute() -> None:
    with pytest.raises(ValueError, match="at least two readings"):
        bias_study([1.0], reference=0.0)
    with pytest.raises(ValueError, match="alpha"):
        bias_study([1.0, 2.0], reference=0.0, alpha=1.5)


def test_the_detectable_bias_round_trips_the_power_it_was_solved_for() -> None:
    for n, sd in ((5, 0.56), (12, 0.56), (30, 1.2)):
        delta = detectable_bias(n, sd)
        assert power_paired(n, delta, sd) == pytest.approx(0.80, abs=1e-9)
    # And more readings lower it, which is the only monotonicity worth asserting here.
    limits = [detectable_bias(n, 0.56) for n in (5, 10, 20, 40)]
    assert limits == sorted(limits, reverse=True)


def test_detectable_bias_refuses_its_own_domain_errors() -> None:
    with pytest.raises(ValueError, match="at least two readings"):
        detectable_bias(1, 0.5)
    with pytest.raises(ValueError, match="sd must be positive"):
        detectable_bias(10, 0.0)
    with pytest.raises(ValueError, match="power"):
        detectable_bias(10, 0.5, power=1.0)


def test_a_line_fitted_to_points_on_a_line_comes_back_exact() -> None:
    """bias = 2 + 0.5 * reference, so the span across 10 to 40 is 15."""
    reference = np.repeat([10.0, 20.0, 30.0, 40.0], 3)
    frame = pd.DataFrame({"reference": reference, "value": reference + 2.0 + 0.5 * reference})
    study = linearity_study(frame, tolerance=100.0)
    assert study.slope == pytest.approx(0.5)
    assert study.intercept == pytest.approx(2.0)
    assert study.r_squared == pytest.approx(1.0)
    assert study.span == pytest.approx(15.0)
    assert study.pct_tolerance_span == pytest.approx(15.0)
    assert study.material
    assert "one-point check cannot stand in" in study.verdict()


def test_a_gage_with_one_constant_offset_has_no_linearity_error() -> None:
    reference = np.repeat([10.0, 20.0, 30.0], 4)
    frame = pd.DataFrame({"reference": reference, "value": reference + 3.0})
    study = linearity_study(frame, tolerance=100.0)
    assert study.slope == pytest.approx(0.0)
    assert study.span == pytest.approx(0.0)
    assert not study.material
    assert not np.isnan(study.pct_tolerance_span)
    assert "no linearity error" in study.verdict()


def test_a_linearity_study_needs_more_than_one_reference() -> None:
    frame = pd.DataFrame({"reference": [10.0] * 5, "value": [10.5, 10.2, 10.9, 10.1, 10.4]})
    with pytest.raises(ValueError, match="two distinct reference values"):
        linearity_study(frame)


def test_a_slope_without_a_tolerance_has_no_materiality_verdict() -> None:
    reference = np.repeat([10.0, 20.0, 30.0], 4)
    frame = pd.DataFrame({"reference": reference, "value": reference * 1.5})
    study = linearity_study(frame)
    assert np.isnan(study.pct_tolerance_span)
    assert not study.material


def test_a_perfect_gage_misjudges_nothing() -> None:
    result = misclassification(0.0, gage_sd=1e-6, part_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0)
    assert result.false_reject == pytest.approx(0.0, abs=1e-12)
    assert result.false_accept == pytest.approx(0.0, abs=1e-12)
    assert result.scrap_ppm == pytest.approx(0.0, abs=1e-6)


def test_a_centred_process_misjudges_symmetrically_in_both_bias_directions() -> None:
    """Nothing in the arithmetic should prefer a direction, so the two have to agree exactly."""
    high = misclassification(3.0, **LIMITS)
    low = misclassification(-3.0, **LIMITS)
    assert high.false_reject == pytest.approx(low.false_reject, abs=1e-12)
    assert high.false_accept == pytest.approx(low.false_accept, abs=1e-12)


def test_bias_makes_both_kinds_of_mistake_more_likely() -> None:
    clean = misclassification(0.0, **LIMITS)
    biased = misclassification(3.0, **LIMITS)
    assert biased.false_reject > clean.false_reject
    assert biased.false_accept > clean.false_accept
    assert biased.scrap_ppm > clean.scrap_ppm
    assert "ppm" in biased.verdict()


def test_a_guard_band_trades_one_mistake_for_the_other() -> None:
    biased = misclassification(3.0, **LIMITS)
    banded = misclassification(3.0, guard=2.0, **LIMITS)
    assert banded.false_accept < biased.false_accept
    assert banded.false_reject > biased.false_reject


def test_the_guard_band_solves_for_the_escape_rate_it_was_asked_for() -> None:
    width = guard_band(0.05, 3.0, **LIMITS)
    assert width > 0
    assert misclassification(3.0, guard=width, **LIMITS).false_accept == pytest.approx(
        0.05, abs=1e-9
    )
    # Already met, so there is nothing to buy.
    assert guard_band(0.9, 3.0, **LIMITS) == 0.0


def test_misclassification_refuses_impossible_geometry() -> None:
    with pytest.raises(ValueError, match="usl must exceed lsl"):
        misclassification(0.0, gage_sd=1.0, part_sd=1.0, nominal=0.0, lsl=1.0, usl=1.0)
    with pytest.raises(ValueError, match="standard deviations"):
        misclassification(0.0, gage_sd=0.0, part_sd=1.0, nominal=0.0, lsl=-1.0, usl=1.0)
    with pytest.raises(ValueError, match="must not be negative"):
        misclassification(0.0, guard=-1.0, **LIMITS)
    with pytest.raises(ValueError, match="closes the acceptance window"):
        misclassification(0.0, guard=30.0, **LIMITS)
    with pytest.raises(ValueError, match="entirely inside or outside"):
        misclassification(0.0, gage_sd=1.0, part_sd=1e-9, nominal=500.0, lsl=475.0, usl=525.0)
    with pytest.raises(ValueError, match="between 0 and 1"):
        guard_band(0.0, 3.0, **LIMITS)


def test_with_no_bias_the_significance_rule_holds_its_level_at_every_precision() -> None:
    """The control case, and it has to be exact rather than close.

    With a bias of zero the t statistic does not depend on the standard deviation at all, so
    scaling one set of draws gives the same statistic in every row. Four identical numbers are
    the confirmation that the simulation is measuring what it claims to; four merely similar ones
    would mean the rows are not comparable.
    """
    table = bias_significance_tradeoff((0.2, 0.56, 1.5, 4.0), bias=0.0, tolerance=50.0, n=12)
    rates = table["flagged"].tolist()
    assert len(set(rates)) == 1
    assert rates[0] == pytest.approx(0.05, abs=0.01)
    assert not bool(table["material"].any())


def test_the_significance_rule_follows_the_gage_rather_than_the_consequence() -> None:
    table = bias_significance_tradeoff((0.2, 0.56, 1.5, 4.0), bias=0.5, tolerance=50.0, n=12)
    flagged = table["flagged"].tolist()
    assert flagged == sorted(flagged, reverse=True)
    assert flagged[0] > 0.99
    assert flagged[-1] < 0.10
    # The offset is the same in every row and immaterial in every row.
    assert not bool(table["material"].any())


def test_the_tradeoff_refuses_a_non_positive_repeatability() -> None:
    with pytest.raises(ValueError, match="positive"):
        bias_significance_tradeoff((0.5, 0.0), bias=1.0, tolerance=10.0, n=10)


def test_the_reference_study_is_the_size_its_design_declares(full: Dataset) -> None:
    readings = full.reference_studies
    expected = sum(len(profile.references) * profile.repeats for profile in REFERENCES)
    assert len(readings) == expected == 180
    counts = readings.groupby(["gage", "reference"], observed=True).size()
    assert set(counts.unique()) == {12}
    # Every gage in the reference study is one of the gages the crossed study measured.
    assert set(readings["gage"].unique()) <= {profile.gage for profile in GAGES}


def test_the_reference_design_declares_the_bias_that_was_built_in(full: Dataset) -> None:
    designs = full.reference_designs.set_index("gage")
    for profile in REFERENCES:
        assert designs.loc[profile.gage, "bias_at_nominal"] == profile.bias_at_nominal
        assert designs.loc[profile.gage, "bias_slope"] == profile.bias_slope
    # One of each kind, which is what makes the two-by-two of precision and accuracy checkable.
    assert designs.loc["BALANCA-01", "bias_at_nominal"] != 0.0
    assert designs.loc["PAQUIMETRO-02", "bias_at_nominal"] == 0.0
    assert designs.loc["PAQUIMETRO-02", "bias_slope"] != 0.0
    assert designs.loc["INSPECAO-03", "bias_at_nominal"] == 0.0
    assert designs.loc["INSPECAO-03", "bias_slope"] == 0.0


def test_adding_wave_five_left_the_earlier_waves_byte_identical(full: Dataset) -> None:
    """Four waves of published figures behind the stream-order contract now."""
    assert float(full.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)
    assert float(full.improvement_trials.iloc[0]["value"]) == pytest.approx(91.543921, abs=5e-7)
    assert float(full.group_comparisons.iloc[0]["value"]) == pytest.approx(102.019499, abs=5e-7)
    assert float(full.factorial_runs.iloc[0]["response"]) == pytest.approx(36.547850, abs=5e-7)
    assert float(full.reference_studies.iloc[0]["value"]) == pytest.approx(484.066275, abs=5e-7)

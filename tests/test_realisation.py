"""Attribution, the selection artefact, and the money - each anchored on a case with an answer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.improve import (
    METHODS,
    BenefitCase,
    before_after,
    difference_in_differences,
    regression_to_the_mean,
)
from dmaic.synth import PANELS, Dataset

PROFILE = PANELS[0]


def _panel(
    treated_effect: float,
    trend: float = 0.0,
    sites: int = 6,
    periods: int = 8,
    split: int = 4,
    noise: float = 0.0,
) -> pd.DataFrame:
    """A panel with no noise unless asked for, so the estimators have an exact answer to hit."""
    rng = np.random.default_rng(0)
    rows = []
    for index in range(sites):
        treated = index < sites // 2
        for period in range(1, periods + 1):
            value = 100.0 + index + trend * (period - 1)
            if treated and period > split:
                value += treated_effect
            if noise:
                value += float(rng.normal(0.0, noise))
            rows.append(
                {
                    "site": f"S{index}",
                    "period": period,
                    "treated": treated,
                    "value": value,
                }
            )
    return pd.DataFrame(rows)


def test_with_no_trend_both_estimators_return_the_effect_exactly() -> None:
    """The control case. Where there is nothing to attribute, attribution cannot go wrong."""
    panel = _panel(treated_effect=-5.0, trend=0.0)
    assert before_after(panel, split=4).effect == pytest.approx(-5.0)
    assert difference_in_differences(panel, split=4).effect == pytest.approx(-5.0)


def test_a_trend_lands_entirely_in_the_before_and_after_number() -> None:
    """And exactly, which is what makes it a bias rather than noise.

    With a trend of -1 per period, a four-period baseline and a four-period follow-up, the mean
    period moves by four, so a before-and-after difference picks up -4 on top of the effect. The
    difference in differences picks up none of it.
    """
    panel = _panel(treated_effect=-5.0, trend=-1.0)
    assert before_after(panel, split=4).effect == pytest.approx(-9.0)
    assert difference_in_differences(panel, split=4).effect == pytest.approx(-5.0)
    # And with no effect at all, the whole of the reported improvement is the trend.
    flat = _panel(treated_effect=0.0, trend=-1.0)
    assert before_after(flat, split=4).effect == pytest.approx(-4.0)
    assert difference_in_differences(flat, split=4).effect == pytest.approx(0.0)


def test_a_before_and_after_estimate_says_it_cannot_attribute() -> None:
    panel = _panel(treated_effect=-5.0, trend=-1.0)
    estimate = before_after(panel, split=4)
    assert estimate.method == METHODS[0]
    assert estimate.controls == 0
    assert not estimate.attributable
    assert not estimate.significant
    assert estimate.comparison is None
    assert "cannot be taken out" in estimate.verdict()


def test_a_difference_in_differences_carries_the_test_behind_it() -> None:
    panel = _panel(treated_effect=-5.0, trend=-1.0, noise=1.0)
    estimate = difference_in_differences(panel, split=4)
    assert estimate.method == METHODS[1]
    assert estimate.treated == 3
    assert estimate.controls == 3
    assert estimate.attributable
    assert estimate.comparison is not None
    low, high = estimate.comparison.confidence_interval
    assert low < -5.0 < high
    assert estimate.baseline_periods == 4
    assert estimate.follow_periods == 4


def test_the_unit_of_analysis_is_the_site_and_not_the_site_period() -> None:
    """Doubling the number of periods must not pretend to be more evidence about the change.

    Each site still contributes one change, so the comparison keeps the same degrees of freedom
    however long the panel is. Treating site-periods as independent is how this estimator ends up
    with an indefensible p-value.
    """
    short = difference_in_differences(_panel(-5.0, noise=1.0, periods=8, split=4), split=4)
    long = difference_in_differences(_panel(-5.0, noise=1.0, periods=24, split=12), split=12)
    assert short.comparison is not None
    assert long.comparison is not None
    assert short.comparison.df == pytest.approx(long.comparison.df, abs=1.0)
    assert short.treated == long.treated == 3


def test_the_estimators_refuse_a_panel_they_cannot_read() -> None:
    panel = _panel(treated_effect=-5.0)
    untouched = panel.assign(treated=False)
    with pytest.raises(ValueError, match="nothing to measure"):
        before_after(untouched, split=4)
    with pytest.raises(ValueError, match="nothing to measure"):
        difference_in_differences(untouched, split=4)
    with pytest.raises(ValueError, match="no comparison group"):
        difference_in_differences(panel.assign(treated=True), split=4)
    # A split outside the panel leaves one phase empty, and a change needs both.
    with pytest.raises(ValueError, match="one side of it"):
        difference_in_differences(panel, split=0)
    with pytest.raises(ValueError, match="one side of it"):
        before_after(panel, split=99)


def test_random_selection_shows_no_improvement_at_all() -> None:
    """The control case for the selection artefact, and it has to be zero at every baseline."""
    table = regression_to_the_mean(
        (1, 6, 24), sites=20, selected=5, site_sd=8.0, noise=6.0, follow_periods=12
    )
    assert bool((table["random_selected"].abs() < 0.1).all())
    assert list(table.columns) == ["baseline_periods", "worst_selected", "random_selected"]


def test_selecting_the_worst_manufactures_an_improvement_that_a_longer_baseline_removes() -> None:
    table = regression_to_the_mean(
        (1, 3, 6, 12, 24), sites=20, selected=5, site_sd=8.0, noise=6.0, follow_periods=12
    ).set_index("baseline_periods")
    artefact = table["worst_selected"].tolist()
    # Every row is an apparent improvement where nothing was done.
    assert all(value < 0 for value in artefact)
    # And it shrinks monotonically as the baseline lengthens.
    assert artefact == sorted(artefact)
    assert table.loc[1, "worst_selected"] < -3.0
    assert table.loc[24, "worst_selected"] > -0.5


def test_the_artefact_vanishes_when_there_is_nothing_to_select_on() -> None:
    """Taking every site is not a selection, so there is nothing to regress away from.

    This is the second control on the simulation: the artefact is a property of choosing a subset
    by its baseline, so choosing all of them has to return zero however noisy the baseline was.
    """
    everything = regression_to_the_mean(
        (1,), sites=20, selected=20, site_sd=8.0, noise=6.0, follow_periods=12
    )
    assert everything.loc[0, "worst_selected"] == pytest.approx(0.0, abs=0.1)
    assert everything.loc[0, "random_selected"] == pytest.approx(0.0, abs=0.1)


def test_the_simulation_refuses_impossible_selections() -> None:
    for selected in (0, 21):
        with pytest.raises(ValueError, match="cannot take"):
            regression_to_the_mean(
                (1,), sites=20, selected=selected, site_sd=8.0, noise=6.0, follow_periods=12
            )
    with pytest.raises(ValueError, match="noise must be positive"):
        regression_to_the_mean(
            (1,), sites=20, selected=5, site_sd=8.0, noise=0.0, follow_periods=12
        )
    with pytest.raises(ValueError, match="at least one period"):
        regression_to_the_mean(
            (0,), sites=20, selected=5, site_sd=8.0, noise=6.0, follow_periods=12
        )


def test_the_benefit_case_multiplies_out_and_keeps_cash_separate() -> None:
    case = BenefitCase(
        effect=-2.0, units_per_period=1000.0, periods=10, variable_share=0.25, project_cost=1000.0
    )
    assert case.gross == pytest.approx(20000.0)
    assert case.cash == pytest.approx(5000.0)
    assert case.capacity == pytest.approx(15000.0)
    assert case.cash + case.capacity == pytest.approx(case.gross)
    assert case.net == pytest.approx(4000.0)
    # 500 of cash a period against a 1000 cost.
    assert case.payback_periods == pytest.approx(2.0)
    assert "payback in 2.0 periods" in case.verdict()


def test_the_sign_of_the_effect_does_not_change_the_size_of_the_case() -> None:
    """An improvement of two and a deterioration of two are the same magnitude of money.

    The direction belongs to the measurand, not to the arithmetic, and a case that silently
    returned a negative benefit for a cost reduction would be read as a loss.
    """
    down = BenefitCase(effect=-2.0, units_per_period=100.0, periods=5, variable_share=1.0)
    up = BenefitCase(effect=2.0, units_per_period=100.0, periods=5, variable_share=1.0)
    assert down.gross == up.gross == pytest.approx(1000.0)


def test_a_case_that_does_not_pay_back_says_so() -> None:
    case = BenefitCase(
        effect=-0.01, units_per_period=100.0, periods=4, variable_share=0.5, project_cost=5000.0
    )
    assert case.net < 0
    assert "does not pay back" in case.verdict()
    # And an effect of nothing never pays back, rather than paying back in zero periods.
    nothing = BenefitCase(
        effect=0.0, units_per_period=100.0, periods=4, variable_share=0.5, project_cost=10.0
    )
    assert nothing.payback_periods == float("inf")


def test_the_benefit_case_refuses_inputs_it_cannot_price() -> None:
    with pytest.raises(ValueError, match="volume cannot be negative"):
        BenefitCase(effect=-1.0, units_per_period=-1.0, periods=1, variable_share=0.5)
    with pytest.raises(ValueError, match="at least one period"):
        BenefitCase(effect=-1.0, units_per_period=1.0, periods=0, variable_share=0.5)
    with pytest.raises(ValueError, match="variable share"):
        BenefitCase(effect=-1.0, units_per_period=1.0, periods=1, variable_share=1.5)
    with pytest.raises(ValueError, match="project cost"):
        BenefitCase(
            effect=-1.0, units_per_period=1.0, periods=1, variable_share=0.5, project_cost=-1.0
        )


def test_the_summary_row_carries_the_split_between_cash_and_capacity() -> None:
    case = BenefitCase(effect=-2.0, units_per_period=1000.0, periods=10, variable_share=0.25)
    row = case.summary()
    assert len(row) == 1
    assert list(row.columns) == ["effect", "gross", "cash", "capacity", "net", "payback_periods"]


def test_the_panel_is_the_size_its_design_declares(full: Dataset) -> None:
    panel = full.site_performance
    assert len(panel) == PROFILE.sites * PROFILE.periods == 480
    assert panel["site"].nunique() == PROFILE.sites
    assert int(panel["period"].max()) == PROFILE.periods
    treated_sites = panel.loc[panel["treated"], "site"].nunique()
    assert treated_sites == PROFILE.treated == 5
    # Every site is measured in every period, which the estimators assume.
    assert bool((panel.groupby("site", observed=True).size() == PROFILE.periods).all())
    # And the phase column agrees with the split it was built from.
    before = panel[panel["phase"] == "before"]
    assert int(before["period"].max()) == PROFILE.split


def test_the_design_declares_the_effect_and_the_trend(full: Dataset) -> None:
    """The trend is the column a real project never has, and the one that decides attribution."""
    design = full.improvement_designs.iloc[0]
    assert design["true_effect"] == PROFILE.true_effect
    assert design["trend"] == PROFILE.trend
    assert design["variable_share"] == PROFILE.variable_share
    # The trend over the follow-up window is of the same order as the effect, which is the
    # situation the whole wave is about.
    follow = PROFILE.periods - PROFILE.split
    assert abs(PROFILE.trend * follow) == pytest.approx(4.8)
    assert abs(PROFILE.trend * follow) > abs(PROFILE.true_effect) * 0.5


def test_adding_wave_seven_left_the_earlier_waves_byte_identical(full: Dataset) -> None:
    assert float(full.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)
    assert float(full.improvement_trials.iloc[0]["value"]) == pytest.approx(91.543921, abs=5e-7)
    assert float(full.group_comparisons.iloc[0]["value"]) == pytest.approx(102.019499, abs=5e-7)
    assert float(full.factorial_runs.iloc[0]["response"]) == pytest.approx(36.547850, abs=5e-7)
    assert float(full.reference_studies.iloc[0]["value"]) == pytest.approx(484.066275, abs=5e-7)
    assert int(full.inspection_lots["defectives"].sum()) == 1478


def test_an_estimate_can_be_attributable_and_still_untestable() -> None:
    """A noiseless panel has no spread for the assumption checks, and the effect survives anyway.

    ``compare_means`` refuses a group whose observations are identical, which is right for a test
    and wrong as a gate on an estimate: the effect is a difference of two averages and does not
    depend on any diagnostic. Wave 3's argument is that the checks are evidence rather than a
    gate, and a check that raises is a gate by another name.
    """
    exact = difference_in_differences(_panel(treated_effect=-5.0, trend=-1.0), split=4)
    assert exact.effect == pytest.approx(-5.0)
    assert exact.attributable
    assert exact.comparison is None
    assert not exact.significant
    assert "no spread" in exact.untested_because
    assert "untested" in exact.verdict()

    # And the other floor: two sites a side is below what the checks are defined for.
    small = difference_in_differences(_panel(treated_effect=-5.0, noise=1.0, sites=4), split=4)
    assert small.treated == 2
    assert small.comparison is None
    assert "at least 3" in small.untested_because

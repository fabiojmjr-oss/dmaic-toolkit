"""The drift arithmetic, and the schedule finding that needed no new arithmetic at all."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic._limits import slope_p_value
from dmaic.measure import (
    calibration_interval,
    gage_rr,
    stability_study,
)
from dmaic.synth import DRIFTS, Dataset

PROFILE = DRIFTS[0]


def test_a_noiseless_drift_is_recovered_exactly() -> None:
    """Offset = 2 + 0.5 per day, so day 0 reads 2 and the rate is 0.5."""
    days = np.repeat([0, 10, 20, 30], 3)
    frame = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 + 2.0 + 0.5 * days})
    study = stability_study(frame, tolerance=100.0)
    assert study.drift_per_day == pytest.approx(0.5)
    assert study.intercept == pytest.approx(2.0)
    assert study.offset_at(0) == pytest.approx(2.0)
    assert study.offset_at(30) == pytest.approx(17.0)
    assert study.r_squared == pytest.approx(1.0)
    assert study.significant
    assert study.p_value == 0.0


def test_the_interval_is_what_is_left_of_the_budget_over_the_rate() -> None:
    """Five percent of 100 is 5, an offset of 2 is already spent, so 3 remain at 0.5 a day."""
    days = np.repeat([0, 10, 20, 30], 3)
    frame = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 + 2.0 + 0.5 * days})
    study = stability_study(frame, tolerance=100.0)
    assert study.days_to(5.0) == pytest.approx(6.0)
    assert study.pct_tolerance_at(30) == pytest.approx(17.0)
    # And the planning form, which knows nothing about the offset already there.
    assert calibration_interval(0.5, tolerance=100.0, share_of_tolerance=5.0) == pytest.approx(10.0)


def test_a_gage_that_does_not_drift_has_no_interval_and_says_so() -> None:
    days = np.repeat([0, 10, 20], 4)
    frame = pd.DataFrame({"day": days, "reference": 50.0, "value": 50.0})
    study = stability_study(frame, tolerance=10.0)
    assert study.drift_per_day == 0.0
    assert study.p_value == 1.0
    assert not study.significant
    assert study.days_to() == float("inf")
    assert calibration_interval(0.0, tolerance=10.0) == float("inf")
    assert "no drift detected" in study.verdict()


def test_the_direction_of_the_drift_does_not_change_the_interval() -> None:
    """The budget is spent by the size of the offset, not by its sign."""
    days = np.repeat([0, 10, 20, 30], 3)
    up = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 + 0.5 * days})
    down = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 - 0.5 * days})
    rising = stability_study(up, tolerance=100.0)
    falling = stability_study(down, tolerance=100.0)
    assert rising.drift_per_day == pytest.approx(-falling.drift_per_day)
    assert rising.days_to() == pytest.approx(falling.days_to())


def test_without_a_tolerance_there_is_no_interval_to_report() -> None:
    days = np.repeat([0, 10, 20], 3)
    frame = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 + 0.5 * days})
    study = stability_study(frame)
    assert np.isnan(study.days_to())
    assert np.isnan(study.pct_tolerance_at(10))
    assert "interval unknown" in study.verdict()


def test_a_stability_study_needs_more_than_one_day() -> None:
    frame = pd.DataFrame({"day": [3] * 5, "reference": 10.0, "value": [10.1, 9.9, 10.2, 10.0, 9.8]})
    with pytest.raises(ValueError, match="two distinct days"):
        stability_study(frame)


def test_the_budget_share_has_to_be_a_percentage() -> None:
    days = np.repeat([0, 10], 3)
    frame = pd.DataFrame({"day": days, "reference": 100.0, "value": 100.0 + 0.5 * days})
    study = stability_study(frame, tolerance=100.0)
    for share in (0.0, 100.0, -1.0):
        with pytest.raises(ValueError, match="between 0 and 100"):
            study.days_to(share)
        with pytest.raises(ValueError, match="between 0 and 100"):
            calibration_interval(0.5, tolerance=100.0, share_of_tolerance=share)
    with pytest.raises(ValueError, match="tolerance must be positive"):
        calibration_interval(0.5, tolerance=0.0)


def test_the_two_schedules_hold_the_same_readings_on_the_same_days(full: Dataset) -> None:
    """The claim the whole schedule finding rests on, checked rather than asserted in prose.

    Taking the drift back out has to leave the two schedules with the same multiset of readings,
    because the generator drew them once. If that ever stops being true, the comparison stops
    being about the schedule.
    """
    studies = full.drift_studies
    undrifted = {}
    for schedule, group in studies.groupby("schedule", observed=True):
        undrifted[str(schedule)] = np.sort(
            group["value"].to_numpy() - PROFILE.drift_per_day * group["day"].to_numpy()
        )
        assert sorted(group["day"].unique()) == [0, 7, 14]
        assert len(group) == 90
    np.testing.assert_allclose(undrifted["sequential"], undrifted["interleaved"], atol=1e-12)


def test_the_schedule_decides_which_term_the_drift_lands_in(full: Dataset) -> None:
    """Sequential blames the operators; interleaved blames the instrument. Same readings."""
    tolerance = float(full.drift_designs.set_index("gage").loc["BALANCA-01", "tolerance"])
    studies = full.drift_studies
    results = {
        str(schedule): gage_rr(group, tolerance=tolerance, gage=str(schedule))
        for schedule, group in studies.groupby("schedule", observed=True)
    }
    without = studies[studies["schedule"] == "sequential"].copy()
    without["value"] = without["value"] - PROFILE.drift_per_day * without["day"]
    truth = gage_rr(without, tolerance=tolerance, gage="drift removed")

    sequential, interleaved = results["sequential"], results["interleaved"]
    # The drift goes entirely into reproducibility and leaves repeatability alone.
    assert sequential.ev == pytest.approx(truth.ev, abs=5e-5)
    assert sequential.av > 2 * truth.av
    assert sequential.dominant_source == "reproducibility"
    # Interleaving puts it in repeatability and leaves the operator estimate near the truth.
    assert interleaved.ev > 1.3 * truth.ev
    assert interleaved.av == pytest.approx(truth.av, rel=0.1)
    assert interleaved.dominant_source == "repeatability"
    # Both are honestly worse than the instrument on one day, and the verdict changes with it.
    assert truth.verdict() == "acceptable"
    assert sequential.verdict() == "conditional"
    assert interleaved.verdict() == "conditional"
    assert sequential.grr > truth.grr
    assert interleaved.grr > truth.grr


def test_the_check_series_is_the_size_its_design_declares(full: Dataset) -> None:
    checks = full.stability_checks
    expected_days = len(range(0, PROFILE.check_span_days + 1, PROFILE.check_every_days))
    assert len(checks) == expected_days * PROFILE.readings_per_check == 52
    assert int(checks["day"].max()) == PROFILE.check_span_days
    assert set(checks.groupby("day").size().unique()) == {PROFILE.readings_per_check}


def test_the_drift_design_declares_the_rate_that_was_built_in(full: Dataset) -> None:
    design = full.drift_designs.set_index("gage")
    assert design.loc[PROFILE.gage, "drift_per_day"] == PROFILE.drift_per_day
    assert design.loc[PROFILE.gage, "study_span_days"] == 14
    # The rate is chosen so wave 5's offset is exactly forty days of it. That is a construction,
    # and it is pinned here so a change to either number breaks the claim that links the waves.
    assert 4.0 / PROFILE.drift_per_day == pytest.approx(40.0)


def test_adding_wave_six_left_the_earlier_waves_byte_identical(full: Dataset) -> None:
    assert float(full.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)
    assert float(full.improvement_trials.iloc[0]["value"]) == pytest.approx(91.543921, abs=5e-7)
    assert float(full.group_comparisons.iloc[0]["value"]) == pytest.approx(102.019499, abs=5e-7)
    assert float(full.factorial_runs.iloc[0]["response"]) == pytest.approx(36.547850, abs=5e-7)
    assert float(full.reference_studies.iloc[0]["value"]) == pytest.approx(484.066275, abs=5e-7)


def test_the_summary_row_carries_the_interval_and_the_verdict(full: Dataset) -> None:
    """It is what the examples print, so its columns are part of the contract."""
    study = stability_study(full.stability_checks, tolerance=50.0, gage="BALANCA-01")
    row = study.summary()
    assert len(row) == 1
    assert list(row.columns) == [
        "gage",
        "drift_per_day",
        "p_value",
        "offset_day_0",
        "offset_last_day",
        "pct_tolerance_last_day",
        "residual_sd",
        "interval_days",
        "verdict",
    ]
    assert row.loc[0, "gage"] == "BALANCA-01"
    assert "5% of tolerance is spent" in str(row.loc[0, "verdict"])


def test_a_slope_test_needs_a_residual_degree_of_freedom() -> None:
    """Two points define a line exactly, so there is nothing left to test it against."""
    with pytest.raises(ValueError, match="residual degree of freedom"):
        slope_p_value(1.0, 0.0, df=0)
    assert slope_p_value(0.0, 0.0, df=1) == 1.0
    assert slope_p_value(1.0, float("nan"), df=1) == 0.0

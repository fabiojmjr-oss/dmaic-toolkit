"""The sustain audit, anchored on a panel whose decay is known and on a noiseless control."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.control import (
    decay_detection,
    reported_gain,
    retention_path,
    sustain_audit,
)
from dmaic.synth import SUSTAINS, Dataset, mean_true_effect, true_effect

PROFILE = SUSTAINS[0]
CLOSE = (13, 24)
AUDIT = (25, 36)


def _panel(
    effect: float,
    half_life: float,
    trend: float = 0.0,
    sites: int = 8,
    periods: int = 36,
    split: int = 12,
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
                value += effect * 0.5 ** ((period - split - 1) / half_life)
            if noise:
                value += float(rng.normal(0.0, noise))
            rows.append({"site": f"S{index}", "period": period, "treated": treated, "value": value})
    return pd.DataFrame(rows)


def test_the_declared_decay_halves_over_a_half_life() -> None:
    """The generator's own arithmetic, which every published figure is checked against."""
    assert true_effect(PROFILE, PROFILE.split) == 0.0
    assert true_effect(PROFILE, PROFILE.split + 1) == pytest.approx(PROFILE.effect_at_close)
    later = true_effect(PROFILE, PROFILE.split + 1 + int(PROFILE.half_life))
    assert later == pytest.approx(PROFILE.effect_at_close / 2)
    # And the two published windows are exactly a half-life apart, so their means halve too.
    assert mean_true_effect(PROFILE, *AUDIT) / mean_true_effect(PROFILE, *CLOSE) == pytest.approx(
        0.5, abs=1e-12
    )
    with pytest.raises(ValueError, match="runs backwards"):
        mean_true_effect(PROFILE, 10, 5)


def test_with_no_trend_the_two_comparisons_agree() -> None:
    """The control case: where there is no trend, a report against the old baseline is honest."""
    panel = _panel(effect=-4.0, half_life=12.0, trend=0.0)
    reported = reported_gain(panel, split=12, windows=(CLOSE, AUDIT))
    path = retention_path(panel, split=12, windows=(CLOSE, AUDIT))
    for row in range(2):
        assert reported.loc[row, "reported_gain"] == pytest.approx(
            path.loc[row, "estimate"], abs=1e-9
        )


def test_a_trend_makes_the_report_grow_while_the_gain_shrinks() -> None:
    """The finding, on a noiseless panel where both numbers are exact.

    The gain halves between the windows and the reported figure rises, because the twelve periods
    between the window midpoints are twelve more periods of trend inside it.
    """
    panel = _panel(effect=-4.0, half_life=12.0, trend=-1.0)
    reported = reported_gain(panel, split=12, windows=(CLOSE, AUDIT))
    path = retention_path(panel, split=12, windows=(CLOSE, AUDIT))
    assert abs(reported.loc[1, "reported_gain"]) > abs(reported.loc[0, "reported_gain"])
    assert abs(path.loc[1, "estimate"]) < abs(path.loc[0, "estimate"])
    # The difference in differences is unaffected by the trend, exactly.
    clean = retention_path(_panel(effect=-4.0, half_life=12.0), split=12, windows=(CLOSE, AUDIT))
    assert path["estimate"].tolist() == pytest.approx(clean["estimate"].tolist(), abs=1e-9)
    assert not bool(reported["attributable"].any())


def test_the_retention_path_reports_intervals_where_it_can() -> None:
    panel = _panel(effect=-4.0, half_life=12.0, trend=-1.0, noise=1.0)
    path = retention_path(panel, split=12, windows=(CLOSE, AUDIT))
    assert list(path.columns) == [
        "first_period",
        "last_period",
        "true_effect",
        "estimate",
        "low",
        "high",
    ]
    # true_effect is left for the caller, because a real audit knows nothing there.
    assert bool(path["true_effect"].isna().all())
    assert bool((path["low"] < path["estimate"]).all())
    assert bool((path["estimate"] < path["high"]).all())


def test_a_window_that_overlaps_the_baseline_is_refused() -> None:
    panel = _panel(effect=-4.0, half_life=12.0)
    with pytest.raises(ValueError, match="partly baseline"):
        retention_path(panel, split=12, windows=((10, 20),))
    with pytest.raises(ValueError, match="runs backwards"):
        retention_path(panel, split=12, windows=((24, 13),))


def test_an_audit_of_a_gain_that_held_says_so() -> None:
    """A half-life long enough that nothing decays, on a panel with enough sites to see it."""
    panel = _panel(effect=-4.0, half_life=1e6, sites=24, noise=0.5)
    audit = sustain_audit(panel, split=12, close=CLOSE, audit=AUDIT)
    assert audit.retention == pytest.approx(1.0, abs=0.05)
    assert audit.decay == pytest.approx(0.0, abs=0.2)
    assert not audit.decay_detectable
    assert audit.intervals_overlap
    assert "cannot tell whether the gain held" in audit.verdict()


def test_an_audit_reports_what_it_cannot_establish(full: Dataset) -> None:
    """The panel's own audit: right direction, and an overlap that forbids the conclusion."""
    audit = sustain_audit(full.sustain_panel, split=PROFILE.split, close=CLOSE, audit=AUDIT)
    assert abs(audit.audit.effect) < abs(audit.close.effect)
    assert audit.decay > 0
    assert audit.intervals_overlap
    assert not audit.decay_detectable
    assert audit.decay < audit.detectable_decay
    assert audit.change_sd > 0
    assert 0.0 < audit.retention < 1.0
    # Both audits are attributable, which is what separates them from the report.
    assert audit.close.attributable
    assert audit.audit.attributable


def test_a_large_decay_is_establishable_and_the_verdict_changes() -> None:
    """The other side of the same audit, so the verdict is not only ever one string."""
    panel = _panel(effect=-12.0, half_life=6.0, sites=24, noise=0.5)
    audit = sustain_audit(panel, split=12, close=CLOSE, audit=AUDIT)
    assert audit.retention < 0.5
    assert not audit.intervals_overlap
    assert audit.decay_detectable
    assert "decayed to" in audit.verdict()


def test_a_retention_of_nothing_from_nothing_is_not_a_number() -> None:
    panel = _panel(effect=0.0, half_life=12.0, sites=8)
    audit = sustain_audit(panel, split=12, close=CLOSE, audit=AUDIT)
    assert audit.close.effect == pytest.approx(0.0)
    assert np.isnan(audit.retention)


def test_the_detection_table_is_the_two_sample_calculation() -> None:
    from dmaic.analyze import detectable_difference, power_two_means

    table = decay_detection((1.0, 2.0, 4.0), units=12, change_sd=2.0).set_index("decay")
    limits = table["detectable"].to_numpy()
    assert bool((limits == limits[0]).all())
    assert table.loc[1.0, "detectable"] == pytest.approx(detectable_difference(12, 2.0))
    for decay in (1.0, 2.0, 4.0):
        assert table.loc[decay, "power"] == pytest.approx(power_two_means(12, decay, 2.0))
    # Power rises with the decay, and at the detectable decay it is the power it was solved for.
    assert table["power"].tolist() == sorted(table["power"].tolist())
    at_limit = decay_detection((table.loc[1.0, "detectable"],), units=12, change_sd=2.0)
    assert at_limit.loc[0, "power"] == pytest.approx(0.80, abs=1e-6)


def test_the_detection_table_refuses_its_domain_errors() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        decay_detection((-1.0,), units=12, change_sd=2.0)
    with pytest.raises(ValueError, match="change_sd must be positive"):
        decay_detection((1.0,), units=12, change_sd=0.0)


def test_the_sustain_panel_is_the_size_its_design_declares(full: Dataset) -> None:
    panel = full.sustain_panel
    assert len(panel) == PROFILE.sites * PROFILE.periods == 864
    assert panel.loc[panel["treated"], "site"].nunique() == PROFILE.treated == 12
    assert int(panel["period"].max()) == PROFILE.periods == 36
    assert bool((panel.groupby("site", observed=True).size() == PROFILE.periods).all())
    design = full.sustain_designs.iloc[0]
    assert design["half_life"] == PROFILE.half_life
    assert design["effect_at_close"] == PROFILE.effect_at_close
    # Two full post-project windows of the declared length, which the audit needs.
    assert PROFILE.periods - PROFILE.split == PROFILE.close_window + PROFILE.audit_window


def test_adding_wave_nine_left_the_earlier_waves_byte_identical(full: Dataset) -> None:
    assert float(full.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)
    assert float(full.improvement_trials.iloc[0]["value"]) == pytest.approx(91.543921, abs=5e-7)
    assert float(full.group_comparisons.iloc[0]["value"]) == pytest.approx(102.019499, abs=5e-7)
    assert float(full.factorial_runs.iloc[0]["response"]) == pytest.approx(36.547850, abs=5e-7)
    assert float(full.reference_studies.iloc[0]["value"]) == pytest.approx(484.066275, abs=5e-7)
    assert int(full.inspection_lots["defectives"].sum()) == 1478
    assert float(full.site_performance.iloc[0]["value"]) == pytest.approx(90.931045, abs=5e-7)


def test_an_untestable_audit_reports_overlap_rather_than_a_conclusion() -> None:
    """Two treated sites is below what the assumption checks need, so neither audit is tested.

    With no interval to compare, the honest answer is the same as for overlapping intervals: the
    audit cannot tell. Reporting anything stronger from an estimate that carries no test would be
    the gate-by-raising mistake wave 7 fixed, arrived at from the other side.
    """
    panel = _panel(effect=-6.0, half_life=6.0, sites=4, noise=0.5)
    audit = sustain_audit(panel, split=12, close=CLOSE, audit=AUDIT)
    assert audit.close.comparison is None
    assert audit.audit.comparison is None
    assert audit.intervals_overlap
    assert "cannot tell whether the gain held" in audit.verdict()


def test_a_gain_that_grew_is_reported_as_having_grown() -> None:
    """A negative half-life is a gain that keeps improving, which the verdict has to name.

    It is not a contrived case: a control plan that works, plus a practice that keeps being
    tightened, produces exactly this, and a verdict that could only ever say "decayed" or "cannot
    tell" would be wrong about the best outcome available.
    """
    panel = _panel(effect=-3.0, half_life=-12.0, sites=24, noise=0.5)
    audit = sustain_audit(panel, split=12, close=CLOSE, audit=AUDIT)
    assert audit.retention > 1.0
    assert not audit.intervals_overlap
    assert "held or grew" in audit.verdict()

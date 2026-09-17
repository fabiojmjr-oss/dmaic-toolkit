"""The charter's arithmetic, anchored on cases where the inflation is known exactly."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.define import (
    TARGET_BASES,
    Charter,
    Ctq,
    ctq_table,
    entitlement,
    entitlement_inflation,
    gap_by_window,
    overattribution,
)
from dmaic.synth import PANELS, Dataset

PROFILE = PANELS[0]


def _charter(**overrides: object) -> Charter:
    fields: dict[str, object] = {
        "measurand": "cost per order",
        "unit": "BRL",
        "baseline": 100.0,
        "baseline_window": 12,
        "target": 90.0,
        "target_basis": "entitlement",
        "volume_per_period": 1000.0,
        "periods": 12,
        "variable_share": 0.5,
        "project_cost": 10000.0,
    }
    fields.update(overrides)
    return Charter(**fields)  # type: ignore[arg-type]


def test_the_gap_and_the_benefit_multiply_out_by_hand() -> None:
    """100 to 90 is a gap of 10, which is 10% of the baseline and 120,000 gross over 12 periods."""
    charter = _charter()
    assert charter.gap == pytest.approx(-10.0)
    assert charter.gap_pct == pytest.approx(10.0)
    case = charter.benefit_case()
    assert case.gross == pytest.approx(120000.0)
    assert case.cash == pytest.approx(60000.0)
    assert case.net == pytest.approx(50000.0)
    assert "entitlement target" in charter.verdict()


def test_the_promise_is_computed_by_the_class_that_audits_it() -> None:
    """Not a wrapper of its own: the same BenefitCase the Improve phase uses, or they diverge."""
    from dmaic.improve import BenefitCase

    assert isinstance(_charter().benefit_case(), BenefitCase)


def test_an_improvement_upwards_gives_the_same_size_of_case() -> None:
    """A yield going from 90 to 95 is a five-point gain, not a negative one."""
    upwards = _charter(baseline=90.0, target=95.0)
    assert upwards.gap == pytest.approx(5.0)
    assert upwards.gap_pct == pytest.approx(5.0 / 90.0 * 100.0)
    assert upwards.benefit_case().gross == pytest.approx(60000.0)


def test_a_charter_refuses_what_it_cannot_state() -> None:
    with pytest.raises(ValueError, match="not a charter"):
        _charter(measurand="")
    with pytest.raises(ValueError, match="target_basis"):
        _charter(target_basis="vibes")
    with pytest.raises(ValueError, match="at least one period"):
        _charter(baseline_window=0)
    # A baseline of zero has no percentage gap, and says so rather than dividing.
    assert np.isnan(_charter(baseline=0.0).gap_pct)
    assert set(TARGET_BASES) == {"entitlement", "benchmark", "absolute"}


def test_the_entitlement_reads_the_best_site_both_ways() -> None:
    """With the window long enough that nothing is noise, the two readings converge."""
    averages = [10.0, 12.0, 14.0, 16.0, 18.0]
    tight = entitlement(averages, noise_sd=0.01, window=1000)
    assert tight.observed_best == pytest.approx(10.0)
    assert tight.reliability == pytest.approx(1.0, abs=1e-6)
    assert tight.shrunk_best == pytest.approx(10.0, abs=1e-3)
    assert tight.charter_gap == pytest.approx(4.0)
    assert tight.shrunk_gap == pytest.approx(4.0, abs=1e-3)

    # And with the window short enough that all of it is noise, the best site is not distinguishable
    # from the average, so the shrunk gap goes to nothing.
    loose = entitlement(averages, noise_sd=100.0, window=1)
    assert loose.reliability == pytest.approx(0.0, abs=1e-6)
    assert loose.shrunk_best == pytest.approx(loose.grand_mean, abs=1e-6)
    assert loose.shrunk_gap == pytest.approx(0.0, abs=1e-6)
    assert loose.charter_gap == pytest.approx(4.0)
    assert "entitlement gap between" in loose.verdict()


def test_which_end_is_best_follows_the_measurand_and_not_the_arithmetic() -> None:
    averages = [10.0, 12.0, 14.0, 20.0]
    assert entitlement(averages, noise_sd=2.0, window=4).observed_best == pytest.approx(10.0)
    assert entitlement(
        averages, noise_sd=2.0, window=4, lower_is_better=False
    ).observed_best == pytest.approx(20.0)


def test_a_known_between_site_spread_overrides_the_estimate() -> None:
    averages = [10.0, 12.0, 14.0, 16.0, 18.0]
    declared = entitlement(averages, noise_sd=3.0, window=9, site_sd=3.0)
    # reliability = 9 / (9 + 9/9) = 0.9
    assert declared.reliability == pytest.approx(0.9)


def test_the_entitlement_refuses_inputs_it_cannot_read() -> None:
    with pytest.raises(ValueError, match="at least two sites"):
        entitlement([1.0], noise_sd=1.0, window=1)
    with pytest.raises(ValueError, match="at least one period"):
        entitlement([1.0, 2.0], noise_sd=1.0, window=0)
    with pytest.raises(ValueError, match="noise_sd must be positive"):
        entitlement([1.0, 2.0], noise_sd=0.0, window=1)


def test_the_charter_gap_is_always_too_big_and_the_shrunk_gap_always_too_small() -> None:
    """The finding the module exists for, asserted as a bracket rather than as a correction."""
    table = entitlement_inflation((1, 3, 6, 12, 24), units=20, site_sd=8.0, noise_sd=6.0).set_index(
        "window"
    )
    assert bool((table["charter_gap"] > table["true_gap"]).all())
    assert bool((table["shrunk_gap"] < table["true_gap"]).all())
    # And the inflation shrinks as the baseline lengthens.
    inflation = table["inflation"].tolist()
    assert inflation == sorted(inflation, reverse=True)
    assert table.loc[1, "inflation"] > 3.0
    assert table.loc[24, "inflation"] < 0.3
    # The true gap does not depend on the window, which is the control on the simulation: only the
    # estimate moves, because only the estimate is made of data.
    assert table["true_gap"].max() - table["true_gap"].min() < 0.25


def test_the_inflation_simulation_refuses_its_domain_errors() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        entitlement_inflation((0,), units=20, site_sd=8.0, noise_sd=6.0)
    with pytest.raises(ValueError, match="both spreads must be positive"):
        entitlement_inflation((1,), units=20, site_sd=0.0, noise_sd=6.0)


def test_the_gap_by_window_reads_the_windows_it_was_given(full: Dataset) -> None:
    table = gap_by_window(full.site_performance, last_period=12, windows=(1, 3, 12))
    assert list(table["window"]) == [1, 3, 12]
    assert list(table.columns) == [
        "window",
        "mean",
        "best",
        "worst",
        "gap_to_best",
        "worst_to_best",
    ]
    assert bool((table["best"] < table["mean"]).all())
    assert bool((table["worst"] > table["mean"]).all())
    assert bool((table["worst_to_best"] > table["gap_to_best"]).all())
    # The single-period window exaggerates the spread between sites, which is the published claim.
    assert table.loc[0, "worst_to_best"] > table.loc[2, "worst_to_best"]


def test_the_window_direction_follows_the_measurand() -> None:
    frame = pd.DataFrame(
        {
            "site": ["A", "A", "B", "B"],
            "period": [1, 2, 1, 2],
            "value": [10.0, 10.0, 20.0, 20.0],
        }
    )
    low = gap_by_window(frame, last_period=2, windows=(2,)).iloc[0]
    high = gap_by_window(frame, last_period=2, windows=(2,), lower_is_better=False).iloc[0]
    assert low["best"] == pytest.approx(10.0)
    assert high["best"] == pytest.approx(20.0)
    assert low["gap_to_best"] == pytest.approx(high["gap_to_best"])


def test_a_window_reaching_past_the_panel_is_refused(full: Dataset) -> None:
    with pytest.raises(ValueError, match="starts before the panel"):
        gap_by_window(full.site_performance, last_period=3, windows=(12,))
    with pytest.raises(ValueError, match="at least one period"):
        gap_by_window(full.site_performance, last_period=12, windows=(0,))


def test_a_tree_that_adds_up_reports_one_times_the_gap() -> None:
    tree = Ctq(
        "gap",
        children=(
            Ctq("a", measurand="units", contribution=6.0),
            Ctq("b", measurand="units", contribution=4.0),
        ),
    )
    assert tree.claimed == pytest.approx(10.0)
    assert overattribution(tree, 10.0) == pytest.approx(1.0)
    assert tree.measurable
    assert tree.unmeasurable_claim == pytest.approx(0.0)


def test_a_tree_that_counts_a_saving_twice_reports_more_than_the_gap() -> None:
    tree = Ctq(
        "gap",
        children=(
            Ctq("a", measurand="units", contribution=8.0),
            Ctq("b", measurand="units", contribution=6.0),
        ),
    )
    assert overattribution(tree, 10.0) == pytest.approx(1.4)
    # The sign of the gap does not change the multiple: a cost reduction is still a decomposition.
    assert overattribution(tree, -10.0) == pytest.approx(1.4)


def test_a_leaf_without_a_measurand_makes_its_whole_branch_unverifiable() -> None:
    tree = Ctq(
        "gap",
        children=(
            Ctq("measured", measurand="units", contribution=6.0),
            Ctq("culture", contribution=4.0),
        ),
    )
    assert not tree.measurable
    assert tree.unmeasurable_claim == pytest.approx(4.0)
    assert tree.claimed == pytest.approx(10.0)
    table = ctq_table(tree, 10.0)
    assert list(table.columns) == ["path", "measurand", "contribution", "measurable", "depth"]
    assert list(table["depth"]) == [0, 1, 1]
    assert list(table["measurable"]) == [False, True, False]
    # A branch's contribution is its children's sum rather than its own field.
    assert table.loc[0, "contribution"] == pytest.approx(10.0)


def test_the_tree_walks_depth_first_and_names_the_full_path() -> None:
    tree = Ctq(
        "root",
        children=(Ctq("branch", children=(Ctq("leaf", measurand="units", contribution=1.0),)),),
    )
    paths = list(ctq_table(tree, 1.0)["path"])
    assert paths == ["root", "root / branch", "root / branch / leaf"]


def test_a_tree_cannot_decompose_a_gap_of_zero() -> None:
    tree = Ctq("gap", children=(Ctq("a", measurand="units", contribution=1.0),))
    with pytest.raises(ValueError, match="gap of zero"):
        overattribution(tree, 0.0)
    with pytest.raises(ValueError, match="gap of zero"):
        ctq_table(tree, 0.0)

"""Sampling plans, checked against closed forms and against the plans' own boundary cases."""

from __future__ import annotations

import numpy as np
import pytest

from dmaic.control import (
    SamplingPlan,
    inspect_lots,
    matched_plan,
    oc_curve,
    percentage_plan,
    plan_for,
)
from dmaic.synth import LOTS, Dataset

PROFILE = LOTS[0]


def test_the_binomial_plan_is_the_closed_form() -> None:
    """n=2, c=0 accepts only when neither unit is defective, so it is (1 - p) squared."""
    plan = SamplingPlan(2, 0)
    for fraction in (0.0, 0.1, 0.5, 1.0):
        assert plan.accept_probability(fraction) == pytest.approx((1 - fraction) ** 2)


def test_a_lot_with_no_defectives_always_passes_and_an_all_bad_lot_never_does() -> None:
    for plan in (SamplingPlan(10, 0), SamplingPlan(10, 2, lot_size=100)):
        assert plan.accept_probability(0.0) == pytest.approx(1.0)
        assert plan.accept_probability(1.0) == pytest.approx(0.0)


def test_the_hypergeometric_plan_knows_the_lot_is_finite() -> None:
    """Drawing 50 of 100 units cannot miss more defectives than the lot has left to hide."""
    finite = SamplingPlan(50, 0, lot_size=100)
    infinite = SamplingPlan(50, 0)
    # Two defectives in a hundred: sampling half the lot is stricter than the binomial says.
    assert finite.accept_probability(0.02) < infinite.accept_probability(0.02)
    # And a lot with more defectives than the acceptance number, sampled whole, cannot pass.
    assert SamplingPlan(99, 0, lot_size=100).accept_probability(0.02) == pytest.approx(0.0)


def test_accepting_more_defectives_accepts_more_lots() -> None:
    lot = 1000
    probabilities = [SamplingPlan(125, c, lot).accept_probability(0.02) for c in range(0, 6)]
    assert probabilities == sorted(probabilities)


def test_a_bigger_sample_discriminates_harder() -> None:
    """The property the whole document rests on: discrimination comes from n."""
    at_aql, at_rql = [], []
    for n in (20, 50, 100, 200):
        plan = SamplingPlan(n, 0, lot_size=1000)
        at_aql.append(plan.accept_probability(0.005))
        at_rql.append(plan.accept_probability(0.04))
    assert at_aql == sorted(at_aql, reverse=True)
    assert at_rql == sorted(at_rql, reverse=True)
    # And the ratio between them widens, which is what discrimination means.
    assert at_aql[-1] / at_rql[-1] > at_aql[0] / at_rql[0]


def test_the_percentage_rule_is_a_plan_whose_sample_the_lot_size_chose() -> None:
    assert percentage_plan(1000).n == 100
    assert percentage_plan(1000, share=0.05).n == 50
    assert percentage_plan(5, share=0.10).n == 1  # never rounds down to nothing
    protection = [percentage_plan(lot).accept_probability(0.04) for lot in (100, 500, 1000, 5000)]
    assert protection == sorted(protection, reverse=True)
    # Two orders of magnitude between the smallest and largest lot, from one written rule.
    assert protection[0] / protection[2] > 40


def test_a_fixed_sample_holds_its_protection_across_lot_sizes() -> None:
    """The property the percentage rule is usually assumed to have."""
    fixed = [SamplingPlan(80, 0, lot).accept_probability(0.04) for lot in (500, 1000, 5000, 20000)]
    assert max(fixed) / min(fixed) < 1.4


def test_plan_for_holds_both_risks_and_is_the_smallest_that_does() -> None:
    plan = plan_for(0.01, 0.04, lot_size=1000)
    assert plan.producer_risk(0.01) <= 0.05
    assert plan.consumer_risk(0.04) <= 0.10
    # Nothing smaller manages both, which is what "smallest" has to mean.
    for n in range(2, plan.n):
        assert not any(
            SamplingPlan(n, c, 1000).producer_risk(0.01) <= 0.05
            and SamplingPlan(n, c, 1000).consumer_risk(0.04) <= 0.10
            for c in range(0, n)
        ), f"n={n} also works, so the search is not returning the smallest plan"


def test_plan_for_refuses_quality_levels_it_cannot_separate() -> None:
    with pytest.raises(ValueError, match="aql < rql"):
        plan_for(0.04, 0.01)
    with pytest.raises(ValueError, match="producer_risk"):
        plan_for(0.01, 0.04, producer_risk=0.0)
    with pytest.raises(ValueError, match="consumer_risk"):
        plan_for(0.01, 0.04, consumer_risk=1.0)
    with pytest.raises(ValueError, match="too close to be told apart"):
        plan_for(0.010, 0.0101, max_sample=200)


def test_matching_a_plan_at_the_aql_is_what_makes_two_plans_comparable() -> None:
    reference = SamplingPlan(125, 3, 1000)
    matched = matched_plan(reference, 0, 0.01)
    assert matched.c == 0
    assert matched.accept_probability(0.01) == pytest.approx(
        reference.accept_probability(0.01), abs=0.01
    )
    # The point of the comparison: matched where good material passes, c=0 is far weaker where
    # it matters, because matching forced the sample down.
    assert matched.n < reference.n
    assert matched.accept_probability(0.04) > 3 * reference.accept_probability(0.04)
    with pytest.raises(ValueError, match="cannot be negative"):
        matched_plan(reference, -1, 0.01)


def test_a_plan_refuses_to_be_built_out_of_nonsense() -> None:
    with pytest.raises(ValueError, match="at least one unit"):
        SamplingPlan(0, 0)
    with pytest.raises(ValueError, match="cannot be negative"):
        SamplingPlan(10, -1)
    with pytest.raises(ValueError, match="accepts every lot"):
        SamplingPlan(5, 5)
    with pytest.raises(ValueError, match="full inspection"):
        SamplingPlan(50, 0, lot_size=20)
    with pytest.raises(ValueError, match="fraction must be in"):
        SamplingPlan(10, 0).accept_probability(1.5)
    with pytest.raises(ValueError, match="share must be in"):
        percentage_plan(100, share=0.0)


def test_average_outgoing_quality_is_bounded_and_peaks_in_the_middle() -> None:
    """A plan cannot improve on incoming quality; it bounds outgoing quality, above zero."""
    plan = SamplingPlan(125, 3, 1000)
    curve = oc_curve(plan, np.linspace(0.0, 0.12, 25))
    aoq = curve["average_outgoing_quality"]
    assert bool((aoq <= curve["fraction_defective"] + 1e-12).all())
    assert aoq.iloc[0] == pytest.approx(0.0)
    # It falls away on the right rather than reaching zero: a 12% lot is still accepted about
    # once in two thousand times, so the outgoing figure is small and not nil. My first version
    # of this test asserted zero there and the arithmetic was right.
    assert aoq.iloc[-1] < aoq.max() / 1000
    assert aoq.max() > 0.01
    assert 0 < int(aoq.idxmax()) < len(aoq) - 1
    assert list(curve.columns) == [
        "fraction_defective",
        "accept_probability",
        "average_outgoing_quality",
    ]


def test_a_full_inspection_ships_nothing_and_a_tiny_sample_ships_everything() -> None:
    """Two anchors on inspect_lots, where the answer is known without simulating."""
    lots = __import__("pandas").DataFrame(
        {"lot": [1, 2], "lot_size": [100, 100], "defectives": [5, 0]}
    )
    thorough = inspect_lots(SamplingPlan(99, 0, lot_size=100), lots, seed=1)
    assert list(thorough["accepted"]) == [False, True]
    assert int(thorough.loc[thorough["accepted"], "defectives"].sum()) == 0
    # A lot with no defectives cannot fail whatever the plan draws.
    clean = inspect_lots(SamplingPlan(2, 0, lot_size=100), lots, seed=1)
    assert bool(clean.loc[clean["defectives"] == 0, "accepted"].all())


def test_inspect_lots_refuses_a_lot_smaller_than_its_sample(full: Dataset) -> None:
    with pytest.raises(ValueError, match="fewer than the"):
        inspect_lots(SamplingPlan(2000, 0), full.inspection_lots, seed=1)


def test_the_lot_stream_is_the_size_its_design_declares(full: Dataset) -> None:
    lots = full.inspection_lots
    assert len(lots) == PROFILE.lots == 200
    assert set(lots["lot_size"].unique()) == {PROFILE.lot_size}
    assert set(lots["state"].unique()) == {"in control", "excursion"}
    by_state = lots.groupby("state", observed=True)["fraction"].mean()
    assert by_state["in control"] == pytest.approx(PROFILE.in_control_fraction, abs=2e-3)
    assert by_state["excursion"] == pytest.approx(PROFILE.excursion_fraction, abs=5e-3)
    assert bool((lots["defectives"] == lots["fraction"] * PROFILE.lot_size).all())


def test_inspection_is_reproducible_and_seed_dependent(full: Dataset) -> None:
    plan = SamplingPlan(125, 3, PROFILE.lot_size)
    first = inspect_lots(plan, full.inspection_lots, seed=6)
    again = inspect_lots(plan, full.inspection_lots, seed=6)
    other = inspect_lots(plan, full.inspection_lots, seed=7)
    assert list(first["found"]) == list(again["found"])
    assert list(first["found"]) != list(other["found"])


def test_a_plan_without_a_lot_size_says_so_rather_than_guessing() -> None:
    """The binomial plan is the published approximation and it does not know the lot."""
    plan = SamplingPlan(80, 1)
    assert np.isnan(plan.sampled_share)
    # With no lot size there is nothing left unsampled, so the outgoing figure drops the factor.
    fraction = 0.02
    assert plan.average_outgoing_quality(fraction) == pytest.approx(
        fraction * plan.accept_probability(fraction)
    )
    # And a finite lot of the same quality ships a little less, because part of it was inspected.
    finite = SamplingPlan(80, 1, lot_size=1000)
    assert finite.average_outgoing_quality(fraction) < plan.average_outgoing_quality(fraction)


def test_matching_refuses_an_acceptance_number_the_lot_cannot_support() -> None:
    """The case an assertion used to cover, which an assertion should never have covered.

    ``matched_plan`` started its search with the answer as ``None`` and asserted the loop had run.
    The assertion held and it was still the wrong construct: asserts are compiled out under
    optimisation, so a guarantee that matters cannot live in one.
    """
    reference = SamplingPlan(20, 1, lot_size=50)
    with pytest.raises(ValueError, match="needs a sample of at least"):
        matched_plan(reference, 60, 0.01, lot_size=50)
    # And the smallest workable sample is still reachable, which is the boundary next to it.
    assert matched_plan(reference, 49, 0.01, lot_size=50).n == 50

"""Reaction rules, priced against closed forms and against the limits they are promises about."""

from __future__ import annotations

import math

import pytest
from scipy import stats

from dmaic.control import (
    DEFAULT_SIGMAS,
    PERIODS_PER_YEAR,
    ReactionRule,
    alarms_against_delay,
    capability,
    compare_gages,
    rule_from_spread,
    spec_trigger,
)

GAGES = (("perfect", 0.0), ("poor", 5.3))


def test_the_move_has_twice_the_variance_of_a_single_average() -> None:
    """The first thing a plan written on "the move" gets wrong about its own sensitivity."""
    rule = ReactionRule(limit=1.0, subgroup=25, process_sd=5.0)
    assert rule.total_sd == pytest.approx(5.0)
    # Standard error of one average is 1.0; the move of two of them is sqrt(2) times that.
    assert rule.move_sd == pytest.approx(math.sqrt(2.0))


def test_the_false_alarm_rate_is_the_two_sided_normal_tail() -> None:
    rule = ReactionRule(limit=2.0 * math.sqrt(2.0), subgroup=25, process_sd=5.0)
    # The limit is two move-standard-errors, so the rate is the two-sided tail at two sigma.
    assert rule.false_alarm_rate == pytest.approx(2.0 * stats.norm.sf(2.0))
    assert rule.periods_to_alarm == pytest.approx(1.0 / rule.false_alarm_rate)
    assert rule.alarms_per_year == pytest.approx(rule.false_alarm_rate * PERIODS_PER_YEAR)


def test_the_gage_adds_in_quadrature_and_takes_its_share_of_the_alarms() -> None:
    clean = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0)
    dirty = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0, gage_sd=1.35)
    assert dirty.total_sd == pytest.approx(math.sqrt(2.0**2 + 1.35**2))
    assert dirty.false_alarm_rate > clean.false_alarm_rate
    assert clean.gage_share == pytest.approx(0.0)
    expected = (dirty.false_alarm_rate - clean.false_alarm_rate) / dirty.false_alarm_rate
    assert dirty.gage_share == pytest.approx(expected)
    assert 0.0 < dirty.gage_share < 1.0


def test_a_bigger_subgroup_tightens_the_rule_it_did_not_change() -> None:
    """The same written trigger is a different test at a different sample size."""
    rates = [
        ReactionRule(limit=1.0, subgroup=n, process_sd=2.0).false_alarm_rate for n in (1, 5, 20, 50)
    ]
    assert rates == sorted(rates, reverse=True)


def test_the_delay_falls_as_the_shift_grows_and_is_symmetric_in_its_sign() -> None:
    rule = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0)
    delays = [rule.delay(shift) for shift in (0.25, 0.5, 1.0, 2.0)]
    assert delays == sorted(delays, reverse=True)
    assert rule.delay(1.0) == pytest.approx(rule.delay(-1.0))
    # A shift at the limit itself trips about half the time, so it takes about two periods.
    assert rule.delay(rule.limit) == pytest.approx(2.0, abs=0.01)
    with pytest.raises(ValueError, match="false_alarm_rate instead"):
        rule.delay(0.0)


def test_the_shift_caught_within_a_period_count_inverts_the_delay() -> None:
    rule = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0)
    # One period means the trigger has to fire immediately, which needs a shift at the limit.
    assert rule.shift_caught_within(1) == pytest.approx(
        rule.limit + rule.move_sd * stats.norm.ppf(1)
    )
    two = rule.shift_caught_within(2)
    assert two == pytest.approx(rule.limit)
    # Allowing more periods lets a smaller shift through, which is the whole trade.
    assert rule.shift_caught_within(10) < two
    with pytest.raises(ValueError, match="less than one period"):
        rule.shift_caught_within(0.5)


def test_a_rule_refuses_what_it_cannot_price() -> None:
    for kwargs in (
        {"limit": 0.0},
        {"subgroup": 0},
        {"process_sd": 0.0},
        {"gage_sd": -1.0},
        {"periods_per_year": 0.0},
    ):
        base = {"limit": 1.0, "subgroup": 20, "process_sd": 2.0}
        base.update(kwargs)
        with pytest.raises(ValueError):
            ReactionRule(**base)  # type: ignore[arg-type]


def test_a_trigger_from_observed_spread_holds_its_alarm_rate_whatever_the_gage() -> None:
    """The finding, and it has to be exact rather than close.

    The limit is a multiple of the observed move's own spread, so the standardised limit is the
    same number in every row and the false-alarm rate cannot move at all. What moves is the shift
    the rule tolerates, which is the figure nobody reads.
    """
    rates, limits, delays = [], [], []
    for gage_sd in (0.0, 0.47, 1.35, 5.30):
        rule = rule_from_spread(subgroup=20, process_sd=2.0, gage_sd=gage_sd)
        rates.append(rule.false_alarm_rate)
        limits.append(rule.limit)
        delays.append(rule.delay(1.0))
    assert rates == pytest.approx([2.0 * stats.norm.sf(DEFAULT_SIGMAS)] * 4, abs=1e-12)
    assert limits == sorted(limits)
    assert delays == sorted(delays)
    # Ten times slower to react, for the same alarm rate and the same words on the page.
    assert delays[-1] / delays[0] > 10.0
    with pytest.raises(ValueError, match="sigmas must be positive"):
        rule_from_spread(subgroup=20, process_sd=2.0, sigmas=0.0)


def test_comparing_gages_returns_a_row_each_and_refuses_an_empty_list() -> None:
    table = compare_gages(GAGES, limit=1.0, subgroup=20, process_sd=2.0, shift=1.0)
    assert list(table["label"]) == ["perfect", "poor"]
    assert list(table.columns) == [
        "label",
        "gage_sd",
        "total_sd",
        "limit",
        "false_alarm_rate",
        "periods_to_alarm",
        "gage_share",
        "delay",
    ]
    assert table.loc[1, "false_alarm_rate"] > table.loc[0, "false_alarm_rate"]
    with pytest.raises(ValueError, match="nothing to compare"):
        compare_gages((), limit=1.0, subgroup=20, process_sd=2.0, shift=1.0)


def test_the_specification_trigger_is_the_binomial_on_the_out_of_spec_share() -> None:
    """A single unit's chance of being outside, raised to the subgroup, by hand."""
    table = spec_trigger(
        (0.0,), (1, 5), process_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0
    ).set_index("subgroup")
    outside = stats.norm.sf(525.0, 500.0, 8.0) + stats.norm.cdf(475.0, 500.0, 8.0)
    assert table.loc[1, "rate_per_period"] == pytest.approx(outside)
    assert table.loc[5, "rate_per_period"] == pytest.approx(1 - (1 - outside) ** 5)
    assert table.loc[5, "periods_to_react"] == pytest.approx(1 / table.loc[5, "rate_per_period"])


def test_a_specification_trigger_on_target_is_not_silent() -> None:
    """Its false-alarm rate is a consequence of the capability index, not of nothing."""
    assert capability(8.0, 475.0, 525.0) == pytest.approx(50.0 / 48.0)
    on_target = spec_trigger(
        (0.0,), (20,), process_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0
    ).iloc[0]
    assert on_target["rate_per_period"] > 0.03
    # And a capable process quiets it: at Cp 2 the same trigger almost never fires.
    capable = spec_trigger(
        (0.0,), (20,), process_sd=50.0 / 12.0, nominal=500.0, lsl=475.0, usl=525.0
    ).iloc[0]
    assert capability(50.0 / 12.0, 475.0, 525.0) == pytest.approx(2.0)
    assert capable["rate_per_period"] < 1e-7


def test_a_bigger_shift_and_a_bigger_subgroup_both_shorten_the_reaction() -> None:
    table = spec_trigger(
        (0.0, 1.0, 2.0), (5, 20), process_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0
    )
    for size in (5, 20):
        rows = table[table["subgroup"] == size].sort_values("shift_sigmas")
        assert rows["periods_to_react"].tolist() == sorted(
            rows["periods_to_react"].tolist(), reverse=True
        )
    for shift in (0.0, 1.0, 2.0):
        rows = table[table["shift_sigmas"] == shift].sort_values("subgroup")
        assert rows["periods_to_react"].tolist() == sorted(
            rows["periods_to_react"].tolist(), reverse=True
        )


def test_the_specification_trigger_refuses_impossible_geometry() -> None:
    limits = {"nominal": 500.0, "lsl": 525.0, "usl": 475.0}
    with pytest.raises(ValueError, match="usl must exceed lsl"):
        spec_trigger((0.0,), (5,), process_sd=8.0, **limits)
    with pytest.raises(ValueError, match="process_sd must be positive"):
        spec_trigger((0.0,), (5,), process_sd=0.0, nominal=500.0, lsl=475.0, usl=525.0)
    with pytest.raises(ValueError, match="at least one unit"):
        spec_trigger((0.0,), (0,), process_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0)
    with pytest.raises(ValueError, match="usl must exceed lsl"):
        capability(8.0, 525.0, 475.0)
    with pytest.raises(ValueError, match="process_sd must be positive"):
        capability(0.0, 475.0, 525.0)


def test_the_trade_table_moves_both_ways_at_once() -> None:
    """Every row buys detection with false alarms, which is the trade a plan does not state."""
    table = alarms_against_delay((0.5, 1.0, 2.0, 3.0), subgroup=20, process_sd=2.0, shift=1.0)
    assert table["alarms_per_year"].tolist() == sorted(
        table["alarms_per_year"].tolist(), reverse=True
    )
    assert table["delay"].tolist() == sorted(table["delay"].tolist())
    assert list(table.columns) == ["limit", "false_alarm_rate", "alarms_per_year", "delay"]
    # A gage makes every row of the same table worse on the alarm side.
    dirty = alarms_against_delay((1.0,), subgroup=20, process_sd=2.0, shift=1.0, gage_sd=5.3)
    clean = alarms_against_delay((1.0,), subgroup=20, process_sd=2.0, shift=1.0)
    assert dirty.loc[0, "alarms_per_year"] > clean.loc[0, "alarms_per_year"]


def test_the_verdict_names_both_promises() -> None:
    rule = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0, gage_sd=1.35)
    verdict = rule.verdict()
    assert "false alarm every" in verdict
    assert "from the gage" in verdict


def test_a_trigger_so_wide_it_never_fires_has_no_gage_share_to_report() -> None:
    """A limit far beyond any plausible move underflows to a rate of zero.

    Not a contrived case: a plan written in the measurand's natural units on a process far tighter
    than anybody expected produces it, and the honest answer is that none of a rate of zero belongs
    to the gage rather than that the share is undefined.
    """
    rule = ReactionRule(limit=1000.0, subgroup=20, process_sd=2.0, gage_sd=1.35)
    assert rule.false_alarm_rate == 0.0
    assert rule.periods_to_alarm == float("inf")
    assert rule.gage_share == 0.0

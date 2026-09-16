"""The design arithmetic, verified against cases that can be worked out without the code.

A two-level factorial is one of the few things in this package with a closed form simple enough
to check by hand, so most of what is below is arithmetic done twice: once by the module and once
in the test. The rest are properties that have to hold whatever the numbers - orthogonal columns,
a fraction whose runs are a subset of the full design's, and an alias pair whose two estimates
must come back byte-identical because they are the same column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.analyze import detectable_difference
from dmaic.analyze.factorial import (
    IDENTITY,
    MAX_FACTORS,
    alias_structure,
    detectable_effect,
    effects,
    fractional_factorial,
    full_factorial,
)
from dmaic.synth import FACTORIALS, Dataset

PROFILE = FACTORIALS[0]


def test_the_two_factor_effects_are_the_ones_worked_out_by_hand() -> None:
    """A 2x2 with responses 10, 20, 30, 60 in standard order.

    Standard order is (-,-), (-,+), (+,-), (+,+), so the A effect is (30+60)/2 - (10+20)/2 = 30,
    the B effect is (20+60)/2 - (10+30)/2 = 20, and AB is (10+60)/2 - (20+30)/2 = 10. Every one
    of those is a difference of two averages, which is the only claim the module makes about it.
    """
    design = full_factorial(("first", "second"))
    table = effects(design, np.array([10.0, 20.0, 30.0, 60.0])).set_index("effect")
    assert table.loc["A", "estimate"] == pytest.approx(30.0)
    assert table.loc["B", "estimate"] == pytest.approx(20.0)
    assert table.loc["AB", "estimate"] == pytest.approx(10.0)


def test_the_columns_are_orthogonal() -> None:
    """The reason the estimates do not depend on each other, and the reason to run the design."""
    for k in range(2, 6):
        runs = full_factorial(tuple(f"f{index}" for index in range(k))).runs
        product = runs.T @ runs
        np.testing.assert_array_equal(product, 2**k * np.eye(k, dtype=int))


def test_a_full_factorial_has_nothing_aliased() -> None:
    design = full_factorial(("a", "b", "c"))
    assert design.n_runs == 8
    assert design.fraction == "2^3"
    assert design.resolution is None
    assert design.resolution_label == "full"
    assert design.defining_relation == ()
    assert set(design.estimable()) == {"A", "B", "C", "AB", "AC", "BC", "ABC"}
    assert all(partners == () for partners in design.aliases().values())


def test_standard_order_starts_all_low_and_ends_all_high() -> None:
    runs = full_factorial(("a", "b", "c")).runs
    np.testing.assert_array_equal(runs[0], [-1, -1, -1])
    np.testing.assert_array_equal(runs[-1], [1, 1, 1])
    assert len({tuple(row) for row in runs}) == 8


def test_the_generator_fixes_the_defining_relation_and_the_resolution() -> None:
    fourth = fractional_factorial(PROFILE.factors, ("D=ABC",))
    assert fourth.n_runs == 8
    assert fourth.fraction == "2^(4-1)"
    assert fourth.defining_relation == ("ABCD",)
    assert fourth.resolution == 4
    assert fourth.resolution_label == "IV"
    assert fourth.confounded_main_effects() == {}

    third = fractional_factorial(PROFILE.factors, ("D=AB",))
    assert third.n_runs == 8
    assert third.defining_relation == ("ABD",)
    assert third.resolution == 3
    assert third.resolution_label == "III"
    assert third.confounded_main_effects() == {"A": ("BD",), "B": ("AD",), "D": ("AB",)}


def test_the_resolution_comes_from_the_relation_and_not_from_the_generators() -> None:
    """Two generators of length four whose product has length two.

    ``D=ABC`` and ``E=BCD`` both look like resolution IV generators. Their words multiply to
    ``AE``, so two factors share a column and the design cannot separate them at all. Reading the
    resolution off the shortest generator instead of off the closed defining relation would call
    this a resolution IV design, which is why the relation is computed rather than assumed.
    """
    with pytest.raises(ValueError, match="resolution II"):
        fractional_factorial(("a", "b", "c", "d", "e"), ("D=ABC", "E=BCD"))

    # And the same closure the other way round: a quarter fraction of five factors from two
    # three-letter generators has a four-letter third word, and stays resolution III.
    quarter = fractional_factorial(("a", "b", "c", "d", "e"), ("D=AB", "E=AC"))
    assert quarter.defining_relation == ("ABD", "ACE", "BCDE")
    assert quarter.n_runs == 8
    assert quarter.resolution == 3


def test_a_resolution_five_half_fraction_keeps_every_two_factor_interaction() -> None:
    design = fractional_factorial(("a", "b", "c", "d", "e"), ("E=ABCD",))
    assert design.resolution_label == "V"
    aliases = design.aliases()
    assert all(len(aliases[effect]) == 1 for effect in ("A", "AB"))
    assert aliases["AB"] == ("CDE",)
    assert "clear" in design.verdict()


def test_the_verdict_names_what_each_design_can_be_trusted_to_say() -> None:
    """It is the one-line summary the examples print, so every branch of it is exercised."""
    assert full_factorial(PROFILE.factors).verdict() == "2^4: every effect estimable, no aliasing"

    fourth = fractional_factorial(PROFILE.factors, ("D=ABC",)).verdict()
    assert fourth.startswith("2^(4-1) resolution IV:")
    assert "main effects clear" in fourth
    assert "aliased with each other" in fourth

    third = fractional_factorial(PROFILE.factors, ("D=AB",)).verdict()
    assert third.startswith("2^(4-1) resolution III:")
    assert "D+AB" in third

    fifth = fractional_factorial(("a", "b", "c", "d", "e"), ("E=ABCD",)).verdict()
    assert fifth.startswith("2^(5-1) resolution V:")
    assert "two-factor interactions clear" in fifth


def test_a_word_of_the_defining_relation_is_aliased_with_the_identity() -> None:
    """Its column is constant, so the contrast on it is the grand mean rather than an effect.

    Reporting that number next to the effects would be this module doing exactly what it accuses
    a resolution III run sheet of doing: returning a figure that is not what its label says.
    """
    design = fractional_factorial(PROFILE.factors, ("D=AB",))
    assert design.aliases()["ABD"] == (IDENTITY,)
    assert "ABD" not in design.estimable()
    np.testing.assert_array_equal(
        np.abs(design.runs[:, 0] * design.runs[:, 1] * design.runs[:, 3]), 1
    )

    table = effects(design, np.arange(8, dtype=float)).set_index("effect")
    assert np.isnan(table.loc["ABD", "estimate"])
    assert table.loc["ABD", "aliased_with"] == IDENTITY


def test_aliased_effects_come_back_identical_rather_than_merely_close() -> None:
    """They are the same column, so any difference at all would mean the contrast is wrong."""
    design = fractional_factorial(PROFILE.factors, ("D=AB",))
    rng = np.random.default_rng(11)
    table = effects(design, rng.normal(50.0, 3.0, size=8)).set_index("effect")
    for left, right in (("D", "AB"), ("A", "BD"), ("B", "AD")):
        assert table.loc[left, "estimate"] == table.loc[right, "estimate"]


def test_a_fraction_is_a_subset_of_the_runs_of_the_full_design() -> None:
    """Which is what lets two fractions be compared on one measured experiment."""
    everything = full_factorial(PROFILE.factors)
    for generators in (("D=ABC",), ("D=AB",)):
        design = fractional_factorial(PROFILE.factors, generators)
        rows = design.rows_of(everything.runs)
        assert len(set(rows.tolist())) == design.n_runs == 8
        np.testing.assert_array_equal(everything.runs[rows], design.runs)

    # The two half fractions of the same factors overlap, but are not the same eight runs.
    first = fractional_factorial(PROFILE.factors, ("D=ABC",)).rows_of(everything.runs)
    second = fractional_factorial(PROFILE.factors, ("D=AB",)).rows_of(everything.runs)
    assert set(first.tolist()) != set(second.tolist())


def test_rows_of_refuses_a_matrix_it_cannot_match() -> None:
    design = fractional_factorial(PROFILE.factors, ("D=AB",))
    with pytest.raises(ValueError, match="columns"):
        design.rows_of(full_factorial(("a", "b", "c")).runs)
    with pytest.raises(ValueError, match="expected once"):
        design.rows_of(design.runs[:4])


def test_the_letter_lookup_names_the_factor_it_was_given() -> None:
    design = full_factorial(PROFILE.factors)
    assert design.letter(PROFILE.factors[0]) == "A"
    assert design.letter(PROFILE.factors[3]) == "D"
    with pytest.raises(KeyError):
        design.letter("nao existe")


def test_the_design_constructors_refuse_what_they_cannot_build() -> None:
    with pytest.raises(ValueError, match="at least two factors"):
        full_factorial(("only",))
    with pytest.raises(ValueError, match="unique"):
        full_factorial(("a", "a", "b"))
    with pytest.raises(ValueError, match=f"at most {MAX_FACTORS}"):
        full_factorial(tuple(f"f{index}" for index in range(MAX_FACTORS + 1)))
    with pytest.raises(ValueError, match="at least one generator"):
        fractional_factorial(("a", "b", "c"), ())
    with pytest.raises(ValueError, match="no factorial to fraction"):
        fractional_factorial(("a", "b", "c"), ("B=A", "C=A"))
    with pytest.raises(ValueError, match="not of the form"):
        fractional_factorial(("a", "b", "c", "d"), ("D is ABC",))
    with pytest.raises(ValueError, match="generated factors last"):
        fractional_factorial(("a", "b", "c", "d"), ("C=AB",))
    with pytest.raises(ValueError, match="outside"):
        fractional_factorial(("a", "b", "c", "d"), ("D=ABG",))
    with pytest.raises(ValueError, match="in terms of itself"):
        fractional_factorial(("a", "b", "c", "d"), ("D=AD",))
    with pytest.raises(ValueError, match="generated twice"):
        fractional_factorial(("a", "b", "c", "d", "e"), ("E=AB", "E=AC"))


def test_effects_refuses_a_response_of_the_wrong_length() -> None:
    design = full_factorial(("a", "b"))
    with pytest.raises(ValueError, match="expected 4 responses"):
        effects(design, np.array([1.0, 2.0, 3.0]))


def test_effects_accepts_a_series_as_well_as_an_array() -> None:
    design = full_factorial(("a", "b"))
    values = [10.0, 20.0, 30.0, 60.0]
    from_series = effects(design, pd.Series(values))["estimate"]
    from_array = effects(design, np.array(values))["estimate"]
    pd.testing.assert_series_equal(from_series, from_array)


def test_the_alias_table_lists_every_effect_once() -> None:
    design = fractional_factorial(PROFILE.factors, ("D=ABC",))
    table = alias_structure(design)
    assert len(table) == 2**4 - 1 == 15
    assert list(table.columns) == ["effect", "order", "aliased_with", "estimable"]
    assert not bool(table["estimable"].any())
    assert bool((table["order"] == table["effect"].str.len()).all())


def test_the_detectable_effect_is_the_two_sample_calculation_on_half_the_runs() -> None:
    """Every effect in a two-level design is a comparison of two halves, so it has to be."""
    for n_runs in (8, 16, 32):
        assert detectable_effect(n_runs, 1.5) == pytest.approx(
            detectable_difference(n_runs // 2, 1.5)
        )


def test_the_detectable_effect_refuses_designs_that_cannot_estimate_one() -> None:
    with pytest.raises(ValueError, match="two runs per level"):
        detectable_effect(2, 1.5)
    with pytest.raises(ValueError, match="even number of runs"):
        detectable_effect(9, 1.5)


def test_more_runs_lower_the_detection_limit() -> None:
    limits = [detectable_effect(n_runs, 1.5) for n_runs in (8, 16, 32, 64)]
    assert limits == sorted(limits, reverse=True)


def test_the_synthetic_experiment_is_the_size_its_design_declares(full: Dataset) -> None:
    runs = full.factorial_runs
    assert len(runs) == 2 ** len(PROFILE.settings) == 16
    assert list(runs.columns) == ["process", "run", *PROFILE.factors, "response"]
    for factor in PROFILE.factors:
        assert set(runs[factor].unique()) == {-1, 1}
        assert int(runs[factor].sum()) == 0


def test_the_experiment_declares_every_effect_including_the_zeros(full: Dataset) -> None:
    """The zeros are the load-bearing rows: an estimate on one is entirely an artefact."""
    table = full.factorial_effects.set_index("effect")["true_effect"]
    assert len(table) == 2 ** len(PROFILE.settings) - 1 == 15
    for word, effect in PROFILE.true_effects:
        assert table[word] == effect
    assert table["C"] == 0.0
    assert table["D"] == 0.0
    assert table["AB"] == 8.0
    declared = {word for word, _ in PROFILE.true_effects}
    assert all(table[word] == 0.0 for word in table.index if word not in declared)


def test_adding_wave_four_left_the_earlier_waves_byte_identical(full: Dataset) -> None:
    """The stream-order contract again, now with three waves of published figures behind it.

    Wave 3's comparisons had no pin of their own until this test, which is a gap rather than a
    decision: the tripwire only works if every table drawn before the new one is on it.
    """
    assert float(full.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)
    assert float(full.improvement_trials.iloc[0]["value"]) == pytest.approx(91.543921, abs=5e-7)
    assert float(full.group_comparisons.iloc[0]["value"]) == pytest.approx(102.019499, abs=5e-7)
    assert float(full.factorial_runs.iloc[0]["response"]) == pytest.approx(36.547850, abs=5e-7)

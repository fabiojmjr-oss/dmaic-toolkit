"""The generator is the foundation every figure rests on, so its contract is tested."""

from __future__ import annotations

import pandas as pd
import pytest

from dmaic.synth import (
    ARMS,
    GAGE_COLUMNS,
    GAGES,
    OPERATORS,
    PARTS,
    REPLICATES,
    TRIAL_COLUMNS,
    TRIALS,
    generate_dataset,
)


def test_the_study_is_the_size_the_design_says() -> None:
    data = generate_dataset()
    expected = len(GAGES) * PARTS * len(OPERATORS) * REPLICATES
    assert len(data.gage_studies) == expected == 270
    assert tuple(data.gage_studies.columns) == GAGE_COLUMNS


def test_every_design_is_crossed_and_balanced() -> None:
    """The ANOVA decomposition assumes it, so the generator has to deliver it."""
    data = generate_dataset()
    for gage, group in data.gage_studies.groupby("gage", observed=True):
        counts = group.groupby(["part", "operator"], observed=True).size()
        assert len(counts) == PARTS * len(OPERATORS), gage
        assert bool((counts == REPLICATES).all()), gage


def test_the_same_seed_gives_the_same_bytes() -> None:
    """Without this, a published figure is an anecdote."""
    first = generate_dataset().gage_studies
    second = generate_dataset().gage_studies
    pd.testing.assert_frame_equal(first, second)


def test_a_different_seed_gives_different_data() -> None:
    """Guards against a generator that silently ignores its seed."""
    default = generate_dataset().gage_studies["value"]
    other = generate_dataset(seed=7).gage_studies["value"]
    assert not default.equals(other)


def test_specifications_do_not_depend_on_the_seed() -> None:
    """They are declared constants, not draws, so the seed must not touch them."""
    pd.testing.assert_frame_equal(
        generate_dataset().specifications, generate_dataset(seed=7).specifications
    )


def test_specifications_cover_every_gage_and_bracket_the_nominal() -> None:
    data = generate_dataset()
    specs = data.specifications
    assert set(specs["gage"]) == {profile.gage for profile in GAGES}
    assert bool((specs["lsl"] < specs["nominal"]).all())
    assert bool((specs["nominal"] < specs["usl"]).all())
    assert bool((specs["tolerance"] == specs["usl"] - specs["lsl"]).all())


def test_the_trials_are_the_size_their_designs_declare() -> None:
    data = generate_dataset()
    assert tuple(data.improvement_trials.columns) == TRIAL_COLUMNS
    expected = sum(profile.n_per_arm * len(ARMS) for profile in TRIALS)
    assert len(data.improvement_trials) == expected == 470
    counts = data.improvement_trials.groupby(["trial", "arm"], observed=True).size()
    for profile in TRIALS:
        for arm in ARMS:
            assert counts[(profile.trial, arm)] == profile.n_per_arm


def test_the_binary_trial_is_actually_binary() -> None:
    data = generate_dataset()
    binary = [p.trial for p in TRIALS if p.kind == "binary"]
    values = data.improvement_trials.loc[data.improvement_trials["trial"].isin(binary), "value"]
    assert set(values.unique()) <= {0.0, 1.0}


def test_the_designs_declare_the_effect_that_was_planted() -> None:
    """The column a real project never has, which is what makes the type II errors checkable."""
    designs = generate_dataset().trial_designs.set_index("trial")
    assert set(designs.index) == {profile.trial for profile in TRIALS}
    for profile in TRIALS:
        assert designs.loc[profile.trial, "true_effect"] == profile.true_effect
        # Every measurand here is something you want less of, so every effect is negative.
        assert profile.true_effect < 0


def test_adding_wave_two_left_wave_one_byte_identical() -> None:
    """The stream-order contract. Without it, wave 1's published figures would have moved.

    The gage study is drawn first and the trials are appended after it, so the trial draws cannot
    reach back into the gage tables. This pins the first reading, which is quoted nowhere but is
    the cheapest possible tripwire on the ordering.
    """
    data = generate_dataset()
    assert len(data.gage_studies) == 270
    assert float(data.gage_studies.iloc[0]["value"]) == pytest.approx(502.971792, abs=5e-7)

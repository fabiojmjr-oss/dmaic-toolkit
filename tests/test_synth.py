"""The generator is the foundation every figure rests on, so its contract is tested."""

from __future__ import annotations

import pandas as pd

from dmaic.synth import GAGE_COLUMNS, GAGES, OPERATORS, PARTS, REPLICATES, generate_dataset


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

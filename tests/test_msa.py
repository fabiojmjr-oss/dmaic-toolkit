"""The gage ANOVA, checked against hand arithmetic and against its own invariants.

A decomposition tested only against its own output tests nothing. The 2x2x2 fixture has integer
sums of squares that can be worked out on paper, and the property tests pin behaviour that has to
hold for any input rather than for one dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dmaic.measure import ANOVA_COLUMNS, anova, gage_rr
from dmaic.synth import Dataset


def test_the_sums_of_squares_match_hand_arithmetic(balanced: pd.DataFrame) -> None:
    table = anova(balanced).set_index("source")
    assert tuple(anova(balanced).columns) == ANOVA_COLUMNS
    assert table.loc["part", "ss"] == pytest.approx(242.0)
    assert table.loc["operator", "ss"] == pytest.approx(50.0)
    assert table.loc["part * operator", "ss"] == pytest.approx(2.0)
    assert table.loc["repeatability", "ss"] == pytest.approx(8.0)
    assert table.loc["total", "ss"] == pytest.approx(302.0)


def test_the_decomposition_is_complete(balanced: pd.DataFrame) -> None:
    """The parts have to add to the whole, or variation has gone missing."""
    table = anova(balanced).set_index("source")
    parts = ["part", "operator", "part * operator", "repeatability"]
    assert table.loc[parts, "ss"].sum() == pytest.approx(table.loc["total", "ss"])
    assert table.loc[parts, "df"].sum() == table.loc["total", "df"]


def test_the_f_tests_use_random_effects_denominators(balanced: pd.DataFrame) -> None:
    """Main effects against the interaction, interaction against error.

    Testing the main effects against error is what a fixed-effects routine does, and it inflates
    both F statistics - here it would report F=121 for operator instead of 25.
    """
    table = anova(balanced).set_index("source")
    ms = table["ms"]
    assert table.loc["part", "f"] == pytest.approx(ms["part"] / ms["part * operator"])
    assert table.loc["operator", "f"] == pytest.approx(ms["operator"] / ms["part * operator"])
    assert table.loc["part * operator", "f"] == pytest.approx(
        ms["part * operator"] / ms["repeatability"]
    )
    assert table.loc["part", "f"] == pytest.approx(121.0)
    assert table.loc["operator", "f"] == pytest.approx(25.0)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unbalanced", "unbalanced"),
        ("single_replicate", "single measurement"),
        ("one_operator", "at least two"),
    ],
)
def test_it_refuses_designs_it_cannot_decompose(
    balanced: pd.DataFrame, mutation: str, message: str
) -> None:
    """A number computed on a design the arithmetic does not fit is worse than an exception."""
    if mutation == "unbalanced":
        data = pd.concat([balanced, balanced.iloc[[0]]], ignore_index=True)
    elif mutation == "single_replicate":
        data = balanced.loc[balanced["replicate"] == 1]
    else:
        data = balanced.loc[balanced["operator"] == "A"]

    with pytest.raises(ValueError, match=message):
        anova(data)


def test_identical_replicates_give_exactly_zero_repeatability() -> None:
    """Repeatability is within-cell spread, so no within-cell spread means none of it."""
    rows = [
        {"part": part, "operator": operator, "replicate": index, "value": 10.0 * part + operator}
        for part in range(4)
        for operator in range(3)
        for index in range(1, 4)
    ]
    fitted = gage_rr(pd.DataFrame(rows))
    assert fitted.ev == 0.0
    assert fitted.repeatability_var == 0.0


def test_identical_operators_give_almost_no_reproducibility() -> None:
    """With no operator effect in the data, both reproducibility components collapse."""
    rng = np.random.default_rng(1)
    truth = rng.normal(100.0, 5.0, size=8)
    rows = [
        {
            "part": part,
            "operator": operator,
            "replicate": index,
            "value": truth[part] + rng.normal(0.0, 0.3),
        }
        for part in range(8)
        for operator in "ABC"
        for index in range(1, 4)
    ]
    fitted = gage_rr(pd.DataFrame(rows))
    assert fitted.av < 0.15
    assert fitted.dominant_source == "repeatability"


def test_contribution_is_study_variation_squared(full: Dataset) -> None:
    """The confusion this module exists to prevent, pinned as the identity it is."""
    for gage, group in full.gage_studies.groupby("gage", observed=True):
        fitted = gage_rr(group, gage=str(gage))
        assert fitted.pct_contribution == pytest.approx(fitted.pct_study**2 / 100.0, abs=1e-9)
        assert fitted.pct_contribution < fitted.pct_study


def test_the_sigma_multiplier_moves_tolerance_and_not_study_variation(full: Dataset) -> None:
    """Percent study variation is a ratio and cancels the multiplier; percent tolerance does not.

    A study quoting percent tolerance without its multiplier is unreproducible, and this is the
    size of the gap it leaves.
    """
    group = full.gage_studies[full.gage_studies["gage"] == "PAQUIMETRO-02"]
    modern = gage_rr(group, tolerance=1.0, sigma_multiplier=6.0)
    legacy = gage_rr(group, tolerance=1.0, sigma_multiplier=5.15)
    assert modern.pct_study == legacy.pct_study
    assert modern.pct_tolerance / legacy.pct_tolerance == pytest.approx(6.0 / 5.15, abs=1e-12)


def test_no_tolerance_means_no_tolerance_figure(full: Dataset) -> None:
    """Rather than a percentage against an invented specification, which reads like evidence."""
    group = full.gage_studies[full.gage_studies["gage"] == "BALANCA-01"]
    fitted = gage_rr(group)
    assert np.isnan(fitted.pct_tolerance)
    assert np.isnan(fitted.summary()["pct_tolerance"]).all()
    # And the verdict then rests on study variation alone.
    assert fitted.verdict() == "acceptable"


def test_pooling_is_controlled_by_the_alpha_the_docstring_describes(full: Dataset) -> None:
    """The comparison is ``p_value > alpha``, so 0.0 always pools and 1.0 never does.

    This reads backwards from how a significance level usually works, and an earlier version of
    the docstring had the two inverted.
    """
    group = full.gage_studies[full.gage_studies["gage"] == "PAQUIMETRO-02"]
    assert gage_rr(group, interaction_alpha=0.0).interaction_pooled is True
    assert gage_rr(group, interaction_alpha=1.0).interaction_pooled is False


def test_pooling_moves_reproducibility_into_repeatability(full: Dataset) -> None:
    """Which is the whole reason the branch is reported rather than hidden."""
    group = full.gage_studies[full.gage_studies["gage"] == "INSPECAO-03"]
    retained = gage_rr(group, interaction_alpha=1.0)
    pooled = gage_rr(group, interaction_alpha=0.0)
    assert pooled.interaction_var == 0.0
    assert pooled.ev > retained.ev
    assert pooled.av < retained.av
    # The diagnosis flips, which is the expensive part.
    assert retained.dominant_source == "reproducibility"
    assert pooled.dominant_source == "repeatability"


def test_negative_components_are_clamped_and_reported(full: Dataset) -> None:
    """A negative variance estimate is an admission that the study is too small, not a quantity."""
    group = full.gage_studies[full.gage_studies["gage"] == "PAQUIMETRO-02"]
    fitted = gage_rr(group)
    assert "operator" in fitted.clamped
    assert fitted.operator_var == 0.0
    # Every reported component stays non-negative, whatever the estimate was.
    assert fitted.repeatability_var >= 0.0
    assert fitted.interaction_var >= 0.0
    assert fitted.part_var >= 0.0


def test_the_summary_table_is_internally_consistent(full: Dataset) -> None:
    group = full.gage_studies[full.gage_studies["gage"] == "BALANCA-01"]
    fitted = gage_rr(group, tolerance=50.0)
    table = fitted.summary().set_index("source")
    assert table.loc["gage R&R", "std_dev"] == pytest.approx(fitted.grr)
    assert table.loc["total variation (TV)", "pct_study_variation"] == pytest.approx(100.0)
    # EV and AV combine in quadrature, not additively - the commonest arithmetic slip here.
    assert table.loc["gage R&R", "std_dev"] == pytest.approx(
        np.hypot(
            table.loc["repeatability (EV)", "std_dev"], table.loc["reproducibility (AV)", "std_dev"]
        )
    )
    assert table.loc["total variation (TV)", "std_dev"] == pytest.approx(
        np.hypot(fitted.grr, fitted.pv)
    )


def test_ndc_is_truncated_not_rounded(full: Dataset) -> None:
    """AIAG truncates, and rounding up would claim a category the gage cannot resolve."""
    for gage, group in full.gage_studies.groupby("gage", observed=True):
        fitted = gage_rr(group, gage=str(gage))
        assert fitted.ndc == int(1.41 * fitted.pv / fitted.grr)
        assert fitted.ndc <= 1.41 * fitted.pv / fitted.grr

"""Every figure quoted in a README, re-derived.

Marked slow because they run the full studies and every example script. The point is not
coverage: it is that a change which moves a published number breaks the build instead of leaving
the text quietly wrong.
"""

from __future__ import annotations

import pytest

from dmaic.measure import gage_rr
from dmaic.synth import Dataset


@pytest.mark.slow
def test_the_gage_table_reproduces(full: Dataset) -> None:
    """The three-gage table in the module README and both root READMEs."""
    specs = full.specifications.set_index("gage")
    expected = {
        # gage: (EV, AV, GRR, PV, %contribution, %study, %tolerance, ndc, verdict, dominant)
        "BALANCA-01": (
            0.3956,
            0.2616,
            0.4743,
            7.5277,
            0.40,
            6.29,
            5.69,
            22,
            "acceptable",
            "repeatability",
        ),
        "PAQUIMETRO-02": (
            0.0659,
            0.0830,
            0.1060,
            0.6439,
            2.64,
            16.24,
            63.58,
            8,
            "unacceptable",
            "reproducibility",
        ),
        "INSPECAO-03": (
            1.2467,
            3.9790,
            4.1698,
            5.0036,
            40.99,
            64.02,
            62.55,
            1,
            "unacceptable",
            "reproducibility",
        ),
    }
    for gage, row in expected.items():
        ev, av, grr, pv, contribution, study, tolerance, ndc, verdict, dominant = row
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        fitted = gage_rr(group, tolerance=float(specs.loc[gage, "tolerance"]), gage=gage)
        assert fitted.ev == pytest.approx(ev, abs=5e-5), gage
        assert fitted.av == pytest.approx(av, abs=5e-5), gage
        assert fitted.grr == pytest.approx(grr, abs=5e-5), gage
        assert fitted.pv == pytest.approx(pv, abs=5e-5), gage
        assert fitted.pct_contribution == pytest.approx(contribution, abs=5e-3), gage
        assert fitted.pct_study == pytest.approx(study, abs=5e-3), gage
        assert fitted.pct_tolerance == pytest.approx(tolerance, abs=5e-3), gage
        assert fitted.ndc == ndc, gage
        assert fitted.verdict() == verdict, gage
        assert fitted.dominant_source == dominant, gage


@pytest.mark.slow
def test_the_three_ways_of_reading_one_gage(full: Dataset) -> None:
    """The headline claim: 2.64, 16.24 and 63.58 are the same measurement system."""
    group = full.gage_studies[full.gage_studies["gage"] == "PAQUIMETRO-02"]
    fitted = gage_rr(group, tolerance=1.0)

    # Contribution reads as excellent, study variation as conditional, tolerance as hopeless.
    assert fitted.pct_contribution < 10.0
    assert 10.0 < fitted.pct_study < 30.0
    assert fitted.pct_tolerance > 30.0
    # The first is the second squared, which is why the confusion is so expensive.
    assert fitted.pct_contribution == pytest.approx(fitted.pct_study**2 / 100.0, abs=1e-9)
    # And the tolerance criterion is nearly four times the study criterion here.
    assert fitted.pct_tolerance / fitted.pct_study == pytest.approx(3.915, abs=5e-3)

    # INSPECAO-03's reproducibility is 3.2x its repeatability, so the instrument is not at fault.
    coating = gage_rr(full.gage_studies[full.gage_studies["gage"] == "INSPECAO-03"], tolerance=40.0)
    assert coating.av / coating.ev == pytest.approx(3.19, abs=5e-3)


@pytest.mark.slow
def test_pooling_the_interaction_flips_the_diagnosis(full: Dataset) -> None:
    """The pooling table in the module README, and the interaction p-values quoted beside it."""
    expected_p = {"BALANCA-01": 0.0357, "PAQUIMETRO-02": 0.0, "INSPECAO-03": 0.0}
    for gage, p_value in expected_p.items():
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        assert gage_rr(group).interaction_p_value == pytest.approx(p_value, abs=5e-5), gage
        # AIAG's rule retains the interaction for all three, which is the rule working.
        assert gage_rr(group).interaction_pooled is False, gage

    pooling = {
        # gage: ((EV, AV, GRR, %study) retained, (EV, AV, GRR, %study) pooled)
        "PAQUIMETRO-02": (
            (0.0659, 0.0830, 0.1060, 16.24),
            (0.0954, 0.0000, 0.0954, 14.63),
        ),
        "INSPECAO-03": (
            (1.2467, 3.9790, 4.1698, 64.02),
            (2.9918, 2.4435, 3.8628, 59.12),
        ),
    }
    for gage, (retained_row, pooled_row) in pooling.items():
        group = full.gage_studies[full.gage_studies["gage"] == gage]
        retained = gage_rr(group, interaction_alpha=1.0)
        pooled = gage_rr(group, interaction_alpha=0.0)
        for fitted, (ev, av, grr, study) in ((retained, retained_row), (pooled, pooled_row)):
            assert fitted.ev == pytest.approx(ev, abs=5e-5), gage
            assert fitted.av == pytest.approx(av, abs=5e-5), gage
            assert fitted.grr == pytest.approx(grr, abs=5e-5), gage
            assert fitted.pct_study == pytest.approx(study, abs=5e-3), gage
        # The GRR barely moves and the diagnosis inverts, which is the finding.
        assert retained.dominant_source == "reproducibility", gage
        assert pooled.dominant_source == "repeatability", gage
        assert pooled.av == 0.0 or pooled.av < retained.av


@pytest.mark.slow
def test_the_hand_computed_anova_quoted_in_the_readme(balanced) -> None:
    """The root READMEs quote 242, 50, 2 and 8 adding to 302."""
    from dmaic.measure import anova

    table = anova(balanced).set_index("source")
    assert [
        table.loc["part", "ss"],
        table.loc["operator", "ss"],
        table.loc["part * operator", "ss"],
        table.loc["repeatability", "ss"],
    ] == [242.0, 50.0, 2.0, 8.0]
    assert table.loc["total", "ss"] == 302.0

    # And the multiplier claim: exactly 1.1650x on percent tolerance, nothing on percent study.
    from dmaic.synth import generate_dataset

    group = generate_dataset().gage_studies
    group = group[group["gage"] == "PAQUIMETRO-02"]
    modern = gage_rr(group, tolerance=1.0, sigma_multiplier=6.0)
    legacy = gage_rr(group, tolerance=1.0, sigma_multiplier=5.15)
    assert modern.pct_tolerance / legacy.pct_tolerance == pytest.approx(1.1650, abs=5e-5)
    assert modern.pct_study == legacy.pct_study


@pytest.mark.slow
def test_every_example_runs_and_prints_something() -> None:
    """A broken example is a broken README."""
    import runpy
    import sys
    from io import StringIO
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scripts = sorted((root / "examples").glob("*.py"))
    assert len(scripts) == 1

    for script in scripts:
        captured, sys.stdout = sys.stdout, StringIO()
        try:
            runpy.run_path(str(script), run_name="__main__")
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = captured
        assert output.strip(), f"{script.name} printed nothing"

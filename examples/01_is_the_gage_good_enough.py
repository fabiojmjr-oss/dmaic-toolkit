"""Three gages, three verdicts, and one of them where the two criteria disagree.

Run:
    python examples/01_is_the_gage_good_enough.py

The point of the example is not that two gages fail. It is that the number you quote decides the
verdict you reach, on data that has not changed - and that the acceptance bands everybody
remembers are written for exactly one of the three percentages a gage study produces.
"""

from __future__ import annotations

import pandas as pd

from dmaic.measure import ACCEPTABLE, MARGINAL, gage_rr
from dmaic.synth import generate_dataset


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    data = generate_dataset()
    specs = data.specifications.set_index("gage")

    print("THREE MEASUREMENT SYSTEMS, ONE STUDY DESIGN")
    print("   10 parts x 3 operators x 3 replicates, crossed, decomposed by random-effects ANOVA.")
    print(f"   Acceptance bands on percent study variation: under {ACCEPTABLE:.0f}% acceptable,")
    print(f"   under {MARGINAL:.0f}% conditional, above that unacceptable. And ndc at least 5.")

    rows = []
    fitted = {}
    for gage in specs.index:
        study = data.gage_studies[data.gage_studies["gage"] == gage]
        result = gage_rr(study, tolerance=float(specs.loc[gage, "tolerance"]), gage=str(gage))
        fitted[gage] = result
        rows.append(
            {
                "gage": gage,
                "measurand": specs.loc[gage, "measurand"],
                "unit": specs.loc[gage, "unit"],
                "pct_contribution": result.pct_contribution,
                "pct_study_variation": result.pct_study,
                "pct_tolerance": result.pct_tolerance,
                "ndc": result.ndc,
                "dominant": result.dominant_source,
                "verdict": result.verdict(),
            }
        )
    print()
    print(pd.DataFrame(rows).round(2).to_string(index=False))

    print("\n" + "=" * 96)
    print("ONE GAGE, THREE NUMBERS")
    print("=" * 96)
    caliper = fitted["PAQUIMETRO-02"]
    print(
        f"   PAQUIMETRO-02 is {caliper.pct_contribution:.2f}% of variance,"
        f" {caliper.pct_study:.2f}% of study variation"
    )
    print(f"   and {caliper.pct_tolerance:.2f}% of the tolerance. Same gage, same 90 readings.")
    print(
        f"\n   Contribution is study variation squared -"
        f" {caliper.pct_study:.2f}^2 / 100 = {caliper.pct_study**2 / 100:.2f} - so quoting it"
    )
    print("   against bands written for study variation moves an unacceptable gage into the")
    print("   excellent column by arithmetic alone.")
    print(
        f"\n   And the tolerance criterion is the one that fails hardest:"
        f" {caliper.pct_tolerance:.2f}% against a"
    )
    print("   specification band this gage is used to accept and reject parts with. The parts")
    print("   vary more than the specification allows, so a gage that can just about tell these")
    print("   parts apart cannot tell a conforming one from a non-conforming one. Both figures")
    print("   are true; they answer different questions.")

    print("\n" + "=" * 96)
    print("WHAT WOULD FIX THE ONES THAT FAILED")
    print("=" * 96)
    print(
        pd.DataFrame(
            [
                {
                    "gage": gage,
                    "EV (instrument)": result.ev,
                    "AV (method)": result.av,
                    "AV / EV": result.av / result.ev if result.ev > 0 else float("nan"),
                    "points at": "the instrument"
                    if result.dominant_source == "repeatability"
                    else "training and method",
                }
                for gage, result in fitted.items()
            ]
        )
        .round(4)
        .to_string(index=False)
    )
    coating = fitted["INSPECAO-03"]
    print(
        f"\n   INSPECAO-03 fails at {coating.pct_study:.2f}% with reproducibility"
        f" {coating.av / coating.ev:.1f}x its repeatability."
    )
    print("   Buying a better instrument is the commonest response to a failed study and the one")
    print("   with an invoice attached. Here it would change almost nothing: the variation is in")
    print("   three operators taking the same reading differently.")

    print("\n" + "=" * 96)
    print("AND WHAT POOLING THE INTERACTION WOULD DO TO THAT CONCLUSION")
    print("=" * 96)
    comparison = []
    for gage in ("PAQUIMETRO-02", "INSPECAO-03"):
        study = data.gage_studies[data.gage_studies["gage"] == gage]
        tolerance = float(specs.loc[gage, "tolerance"])
        for label, alpha in (("interaction retained", 1.0), ("interaction pooled", 0.0)):
            result = gage_rr(study, tolerance=tolerance, interaction_alpha=alpha)
            comparison.append(
                {
                    "gage": gage,
                    "treatment": label,
                    "EV": result.ev,
                    "AV": result.av,
                    "GRR": result.grr,
                    "pct_study_variation": result.pct_study,
                    "dominant": result.dominant_source,
                }
            )
    print(pd.DataFrame(comparison).round(4).to_string(index=False))
    print("\n   The GRR barely moves. The diagnosis inverts. On PAQUIMETRO-02 reproducibility")
    print("   goes to exactly zero, and a report built on that would send the project to buy an")
    print("   instrument when the finding was that operators diverge on particular parts.")
    print(
        f"\n   AIAG's rule retains the interaction here in all three cases"
        f" (p = {fitted['BALANCA-01'].interaction_p_value:.4f},"
    )
    print(
        f"   {fitted['PAQUIMETRO-02'].interaction_p_value:.4f} and"
        f" {fitted['INSPECAO-03'].interaction_p_value:.4f}), which is the rule doing its job."
        " The pooled columns above"
    )
    print("   are what it is protecting against, produced by overriding it on purpose.")


if __name__ == "__main__":
    main()

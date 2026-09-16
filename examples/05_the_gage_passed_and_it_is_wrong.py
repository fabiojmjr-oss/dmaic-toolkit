"""The study that passed a gage reading 4 g heavy, and what the bias costs in parts.

Run:
    python examples/05_the_gage_passed_and_it_is_wrong.py

Three gages, already judged in example 01 by a crossed study. Here they are measured against
calibrated masters, and all three verdicts change - one gage that passed is badly biased, one
that reads perfectly at nominal is wrong at both ends, and the one that failed is accurate.
"""

from __future__ import annotations

import pandas as pd

from dmaic.measure import (
    bias_significance_tradeoff,
    bias_study,
    gage_rr,
    guard_band,
    linearity_study,
    misclassification,
)
from dmaic.synth import GAGES, generate_dataset

TRADEOFF_SDS = (0.2, 0.56, 1.5, 4.0)
IMMATERIAL_BIAS = 0.5


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    designs = data.reference_designs.set_index("gage")
    readings = data.reference_studies

    print("WHAT A CROSSED STUDY CANNOT SEE")
    print("   Every AIAG figure is computed from differences between readings, so adding a")
    print("   constant to all of them changes nothing. Measured, not asserted:")
    for gage in designs.index:
        crossed = data.gage_studies[data.gage_studies["gage"] == gage]
        tolerance = float(designs.loc[gage, "tolerance"])
        base = gage_rr(crossed, tolerance=tolerance, gage=gage)
        shifted = crossed.copy()
        shifted["value"] = shifted["value"] + 1000.0
        offset = gage_rr(shifted, tolerance=tolerance, gage=gage)
        worst = max(
            abs(getattr(base, field) - getattr(offset, field))
            for field in ("grr", "pct_study", "pct_contribution", "pct_tolerance", "ndc")
        )
        print(
            f"   {gage:14s} %tolerance {base.pct_tolerance:6.2f}  verdict {base.verdict():12s} "
            f"| shifted by 1000 units: largest change {worst:.2e}"
        )

    print("\nWHAT THE MASTERS SAY")
    rows = []
    for gage, group in readings.groupby("gage", observed=True):
        tolerance = float(designs.loc[gage, "tolerance"])
        nominal = float(designs.loc[gage, "nominal"])
        at_nominal = group[group["reference"] == nominal]
        bias = bias_study(at_nominal["value"], nominal, tolerance=tolerance, gage=gage)
        linearity = linearity_study(group, tolerance=tolerance, gage=gage)
        rows.append(
            {
                "gage": gage,
                "bias at nominal": bias.bias,
                "p": bias.p_value,
                "% tol": bias.pct_tolerance,
                "detectable": bias.detectable_bias,
                "slope": linearity.slope,
                "span": linearity.span,
                "span % tol": linearity.pct_tolerance_span,
                "slope p": linearity.p_value,
            }
        )
    table = pd.DataFrame(rows)
    print(
        table.to_string(
            index=False,
            formatters={column: "{:.4f}".format for column in table.columns if column != "gage"},
        )
    )
    print("   The one-point check passes PAQUIMETRO-02 and the range does not.")

    print("\nWHAT THE BIAS COSTS, IN PARTS")
    gage = "BALANCA-01"
    profile = next(item for item in GAGES if item.gage == gage)
    crossed = gage_rr(
        data.gage_studies[data.gage_studies["gage"] == gage],
        tolerance=profile.tolerance,
        gage=gage,
    )
    at_nominal = readings[(readings["gage"] == gage) & (readings["reference"] == profile.nominal)]
    found = bias_study(at_nominal["value"], profile.nominal, tolerance=profile.tolerance)
    limits = {
        "gage_sd": crossed.grr,
        "part_sd": profile.part_sd,
        "nominal": profile.nominal,
        "lsl": profile.lsl,
        "usl": profile.usl,
    }
    calibrated = misclassification(0.0, **limits)
    band = guard_band(calibrated.false_accept, found.bias, **limits)
    cases = (
        ("calibrated", 0.0, 0.0),
        ("as found", found.bias, 0.0),
        (f"as found, guard band {band:.4f}", found.bias, band),
    )
    cost = pd.DataFrame(
        [
            {
                "case": label,
                "bias": bias,
                "guard": guard,
                "scrap ppm": misclassification(bias, guard=guard, **limits).scrap_ppm,
                "escape ppm": misclassification(bias, guard=guard, **limits).escape_ppm,
            }
            for label, bias, guard in cases
        ]
    )
    print(
        f"   {gage}: process sd {profile.part_sd}, gage sd {crossed.grr:.4f}, "
        f"{calibrated.conforming:.4%} of production conforming"
    )
    print(
        cost.to_string(
            index=False,
            formatters={
                "bias": "{:.4f}".format,
                "guard": "{:.4f}".format,
                "scrap ppm": "{:,.0f}".format,
                "escape ppm": "{:,.0f}".format,
            },
        )
    )
    print("   The guard band buys the escape rate back by throwing away conforming parts.")
    print("   A calibration removes the bias and costs neither.")

    print("\nWHY 'THE INTERVAL CONTAINS ZERO' IS NOT AN ACCEPTANCE RULE")
    print(f"   The same {IMMATERIAL_BIAS} g offset in every row - 1% of a 50 g tolerance, below")
    print("   any materiality convention - judged by gages of different precision.")
    tradeoff = bias_significance_tradeoff(
        TRADEOFF_SDS, bias=IMMATERIAL_BIAS, tolerance=profile.tolerance, n=12
    )
    print(
        tradeoff.to_string(
            index=False,
            formatters={
                "repeat_sd": "{:.2f}".format,
                "pct_tolerance_precision": "{:.2f}".format,
                "bias_to_sd": "{:.4f}".format,
                "flagged": "{:.4f}".format,
            },
        )
    )
    print("   The better the gage, the more certainly it is rejected for an offset that does")
    print("   not matter. The verdict tracks the gage's precision, not the consequence.")


if __name__ == "__main__":
    main()

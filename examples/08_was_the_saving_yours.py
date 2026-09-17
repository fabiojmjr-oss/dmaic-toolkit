"""A project that delivered 5.00 per order and reported 10.06, and the money that follows.

Run:
    python examples/08_was_the_saving_yours.py

Twenty sites over twenty-four months, five of them improved from month thirteen. The generator
declares the effect it applied and the trend that was already running, which is the pair a real
project never has.
"""

from __future__ import annotations

import pandas as pd

from dmaic.improve import (
    BenefitCase,
    before_after,
    difference_in_differences,
    regression_to_the_mean,
)
from dmaic.synth import PANELS, generate_dataset

BASELINES = (1, 3, 6, 12, 24)
PROFILE = PANELS[0]


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    panel = data.site_performance
    design = data.improvement_designs.iloc[0]
    follow = int(design["periods"]) - int(design["split"])
    truth = float(design["true_effect"])
    trend = float(design["trend"])

    print("WHAT IS ACTUALLY IN THE PANEL")
    print(
        f"   {int(design['sites'])} sites, {int(design['periods'])} periods, "
        f"{int(design['treated'])} treated from period {int(design['split']) + 1}"
    )
    print(f"   measurand: {design['stream']} in {design['unit']}")
    print(f"   true effect {truth:+.2f} per order, and a trend of {trend:+.2f} per period")
    print(f"   the trend alone moves the measurand {trend * follow:+.2f} over the {follow} periods")
    print("   after the split, in treated and untreated sites alike.")

    print("\nWHAT THE PROJECT WOULD REPORT, AND WHAT IT CAN CLAIM")
    naive = before_after(panel, split=int(design["split"]))
    did = difference_in_differences(panel, split=int(design["split"]))
    low, high = did.comparison.confidence_interval if did.comparison else (float("nan"),) * 2
    rows = [
        {
            "basis": naive.method,
            "estimate": naive.effect,
            "controls": naive.controls,
            "attributable": naive.attributable,
            "times the truth": naive.effect / truth,
        },
        {
            "basis": did.method,
            "estimate": did.effect,
            "controls": did.controls,
            "attributable": did.attributable,
            "times the truth": did.effect / truth,
        },
        {
            "basis": "the truth",
            "estimate": truth,
            "controls": 0,
            "attributable": True,
            "times the truth": 1.0,
        },
    ]
    table = pd.DataFrame(rows)
    print(
        table.to_string(
            index=False,
            formatters={
                "estimate": "{:+.4f}".format,
                "times the truth": "{:.2f}x".format,
            },
        )
    )
    print(f"   before and after: {naive.verdict()}")
    print(f"   difference in differences: {did.verdict()}")
    print(f"   its interval runs {low:+.4f} to {high:+.4f}, which contains the truth. The estimate")
    print("   is off by chance rather than by construction, and the interval says by how much.")

    print("\nWHAT A PROJECT SHOWS WHEN IT DOES NOTHING AT ALL")
    print("   No effect and no trend in any of these rows. The only thing happening is the")
    print("   choice of which sites to charter, and how long a baseline that choice was made on.")
    artefact = regression_to_the_mean(
        BASELINES,
        sites=int(design["sites"]),
        selected=int(design["treated"]),
        site_sd=PROFILE.site_sd,
        noise=PROFILE.noise,
        follow_periods=follow,
    )
    print(
        artefact.to_string(
            index=False,
            formatters={
                "worst_selected": "{:+.4f}".format,
                "random_selected": "{:+.4f}".format,
            },
        )
    )
    print("   Selecting on a single period manufactures most of a real improvement out of")
    print("   nothing. Random selection returns zero, which is the control: the artefact is in")
    print("   the selection rule, not in the arithmetic. The remedy is a longer baseline and it")
    print("   is free.")

    print("\nAND THEN THE MONEY")
    volume = float(design["units_per_period"]) * int(design["treated"])
    cases = {
        "booked on before and after": naive.effect,
        "difference in differences": did.effect,
        "the truth": truth,
    }
    money = []
    for label, effect in cases.items():
        case = BenefitCase(
            effect=effect,
            units_per_period=volume,
            periods=follow,
            variable_share=float(design["variable_share"]),
            project_cost=float(design["project_cost"]),
        )
        money.append(
            {
                "basis": label,
                "effect": effect,
                "gross": case.gross,
                "cash": case.cash,
                "capacity": case.capacity,
                "net": case.net,
                "payback": case.payback_periods,
            }
        )
    frame = pd.DataFrame(money)
    print(
        f"   {volume:,.0f} orders per period across the treated sites, {follow} periods, "
        f"{float(design['variable_share']):.0%} of the unit cost avoidable as cash"
    )
    print(
        frame.to_string(
            index=False,
            formatters={
                "effect": "{:+.2f}".format,
                "gross": "{:,.0f}".format,
                "cash": "{:,.0f}".format,
                "capacity": "{:,.0f}".format,
                "net": "{:,.0f}".format,
                "payback": "{:.2f}".format,
            },
        )
    )
    booked, real = money[0]["gross"], money[2]["cash"]
    attribution = naive.effect / truth
    conversion = 1.0 / float(design["variable_share"])
    print(
        f"   The charter books {booked:,.0f} and the project produced {real:,.0f} of cash: "
        f"{booked / real:.2f}x."
    )
    print(f"   That gap is the product of two factors nobody writes down - {attribution:.2f}x for")
    print(f"   attribution and {conversion:.2f}x for the share that is cash rather than capacity,")
    print(f"   and {attribution:.2f} x {conversion:.2f} = {attribution * conversion:.2f}.")


if __name__ == "__main__":
    main()

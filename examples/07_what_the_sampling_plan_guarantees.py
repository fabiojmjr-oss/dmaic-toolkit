"""Three sampling plans, the same two hundred lots, and what each one actually bought.

Run:
    python examples/07_what_the_sampling_plan_guarantees.py

One in ten lots is an excursion at eight times the ordinary defect rate. The plans are the ones
industry actually writes: a share of the lot, a published acceptance quality level, and a zero
acceptance number.
"""

from __future__ import annotations

import pandas as pd

from dmaic.control import (
    SamplingPlan,
    inspect_lots,
    matched_plan,
    oc_curve,
    percentage_plan,
    plan_for,
)
from dmaic.synth import generate_dataset

AQL = 0.01
RQL = 0.04
LOT_SIZES = (100, 500, 1000, 5000, 20000)
FIXED_N = 80
SEED = 6


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    lots = data.inspection_lots
    design = data.lot_designs.set_index("stream").iloc[0]
    in_control = float(design["in_control_fraction"])
    excursion = float(design["excursion_fraction"])

    print("WHAT 'INSPECT TEN PERCENT' DECIDES, AND WHO DECIDED IT")
    print("   The rule is one sentence and the same everywhere. The protection it delivers is")
    print("   set by the lot size, which is a shipping decision.")
    rows = []
    for lot_size in LOT_SIZES:
        share = percentage_plan(lot_size)
        fixed = SamplingPlan(FIXED_N, 0, lot_size)
        rows.append(
            {
                "lot size": lot_size,
                "10% rule n": share.n,
                "accepts good lots": share.accept_probability(in_control),
                "accepts excursions": share.accept_probability(excursion),
                f"n={FIXED_N} accepts good": fixed.accept_probability(in_control),
                f"n={FIXED_N} accepts excursions": fixed.accept_probability(excursion),
            }
        )
    table = pd.DataFrame(rows)
    print(
        table.to_string(
            index=False,
            formatters={
                column: "{:.6f}".format
                for column in table.columns
                if column.startswith(("accept", "n="))
            },
        )
    )
    print(f"   Good lots here are {in_control:.1%} defective and excursions {excursion:.1%}.")
    print("   The same written rule runs from accepting two excursions in three to rejecting")
    print("   essentially every lot, good ones included. A fixed sample holds both numbers.")

    print("\nWHAT AN ACCEPTANCE QUALITY LEVEL SAYS, AND WHAT IT DOES NOT")
    published = SamplingPlan(125, 3, 1000)
    curve = oc_curve(published, (0.005, 0.01, 0.02, 0.03, 0.04, 0.05))
    print(f"   {published.verdict(AQL, 0.03)}")
    print(
        curve.to_string(
            index=False,
            formatters={
                "fraction_defective": "{:.3%}".format,
                "accept_probability": "{:.4f}".format,
                "average_outgoing_quality": "{:.5f}".format,
            },
        )
    )
    print(f"   At the quoted {AQL:.0%} the plan does what its name says. At three times that it")
    print("   is a coin toss. The number names the producer's risk, not the customer's.")

    print("\nWHY A ZERO ACCEPTANCE NUMBER IS NOT THE STRICT OPTION")
    matched = matched_plan(published, 0, AQL)
    same_sample = SamplingPlan(published.n, 0, published.lot_size)
    print(
        f"   matched at the {AQL:.0%} level: {matched.verdict(AQL, 0.03)} - a sample of "
        f"{matched.n}, and it accepts {matched.accept_probability(RQL):.1%} of {RQL:.0%} lots"
    )
    print(
        f"   at the same sample size: {same_sample.verdict(AQL, 0.03)} - which rejects "
        f"{same_sample.producer_risk(AQL):.1%} of good lots"
    )
    print("   There is no c=0 plan that is both tolerable to the producer at the acceptance")
    print("   level and discriminating above it. The acceptance number is not a strictness dial;")
    print("   the discrimination comes from the sample size.")

    print("\nWHAT EACH PLAN BOUGHT, ON THE SAME TWO HUNDRED LOTS")
    designed = plan_for(AQL, RQL, lot_size=1000)
    plans = {
        "10% of the lot, c=0": percentage_plan(1000),
        f"n={published.n} c={published.c} (AQL {AQL:.1%})": published,
        f"n={same_sample.n} c=0 (same sample)": same_sample,
        f"n={matched.n} c=0 (matched risk)": matched,
        f"designed for {AQL:.0%} vs {RQL:.0%}": designed,
    }
    total_defectives = int(lots["defectives"].sum())
    excursions = int((lots["state"] == "excursion").sum())
    outcome = []
    for label, plan in plans.items():
        decided = inspect_lots(plan, lots, seed=SEED)
        bad = decided[decided["state"] == "excursion"]
        good = decided[decided["state"] == "in control"]
        outcome.append(
            {
                "plan": label,
                "units inspected": plan.n * len(decided),
                "excursions caught": f"{int((~bad['accepted']).sum())}/{excursions}",
                "good lots rejected": int((~good["accepted"]).sum()),
                "defective units shipped": int(
                    decided.loc[decided["accepted"], "defectives"].sum()
                ),
            }
        )
    outcome.append(
        {
            "plan": "no inspection",
            "units inspected": 0,
            "excursions caught": f"0/{excursions}",
            "good lots rejected": 0,
            "defective units shipped": total_defectives,
        }
    )
    print(
        f"   {len(lots)} lots of {int(design['lot_size'])}, {excursions} of them excursions, "
        f"{total_defectives} defective units in total."
    )
    print(pd.DataFrame(outcome).to_string(index=False))
    print("   The published plan inspects 25,000 units and ships three quarters of the defects.")
    print("   The plan that catches every excursion does it by quarantining more than a third of")
    print("   good production - it is not discriminating, it is harsh. Designing to both quality")
    print("   levels is the only row that is good at both, and it costs the most inspection.")
    print("   Sampling sorts lots. It does not change what is in them.")


if __name__ == "__main__":
    main()

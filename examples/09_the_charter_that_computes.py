"""A charter measured from the wrong end of its baseline, towards the wrong end of its target.

Run:
    python examples/09_the_charter_that_computes.py

Both ends of a charter's gap are the most inflated estimate available: the recent bad baseline came
back up on its own, and the best site's observed performance goes back down. The two errors add.
"""

from __future__ import annotations

import pandas as pd

from dmaic.define import (
    Charter,
    Ctq,
    ctq_table,
    entitlement,
    entitlement_inflation,
    gap_by_window,
    overattribution,
)
from dmaic.synth import PANELS, generate_dataset

WINDOWS = (1, 3, 6, 12)
INFLATION_WINDOWS = (1, 3, 6, 12, 24)
PROFILE = PANELS[0]

# A decomposition of the gap as a project team would present it: three branches, two of whose
# leaves nobody has said how to measure.
TREE = Ctq(
    name="gap por pedido",
    children=(
        Ctq(
            name="separacao",
            children=(
                Ctq("caminhamento", measurand="metros por linha", contribution=5.2),
                Ctq("conferencia", measurand="segundos por linha", contribution=3.1),
            ),
        ),
        Ctq(
            name="embalagem",
            children=(
                Ctq("material", measurand="BRL por caixa", contribution=2.4),
                Ctq("retrabalho", contribution=1.8),
            ),
        ),
        Ctq(
            name="transporte",
            children=(
                Ctq("ocupacao", measurand="m3 por veiculo", contribution=4.5),
                Ctq("cultura de servico", contribution=2.6),
            ),
        ),
    ),
)


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    panel = data.site_performance
    design = data.improvement_designs.iloc[0]
    split = int(design["split"])

    print("THE SAME DATA, READ AS FOUR BASELINES")
    windows = gap_by_window(panel, last_period=split, windows=WINDOWS)
    print(
        windows.to_string(
            index=False,
            formatters=dict.fromkeys(
                ("mean", "best", "worst", "gap_to_best", "worst_to_best"), "{:.4f}".format
            ),
        )
    )
    one, twelve = windows.iloc[0], windows.iloc[-1]
    print(
        f"   A charter can quote a gap to the best site of {one['gap_to_best']:.2f} or "
        f"{twelve['gap_to_best']:.2f} from the same"
    )
    print("   twelve months, depending on a window nobody records. And the spread between sites,")
    print(
        f"   which is what justifies a harmonisation programme, reads "
        f"{one['worst_to_best']:.2f} on one period against"
    )
    print(
        f"   {twelve['worst_to_best']:.2f} on twelve - "
        f"{one['worst_to_best'] / twelve['worst_to_best'] - 1:.0%} larger, from the window alone."
    )

    print("\nHOW MUCH OF AN ENTITLEMENT GAP IS THE BEST SITE HAVING A GOOD RUN")
    print("   Simulated, because the true level of each site is exactly what a charter lacks.")
    inflation = entitlement_inflation(
        INFLATION_WINDOWS,
        units=int(design["sites"]),
        site_sd=PROFILE.site_sd,
        noise_sd=PROFILE.noise,
    )
    print(
        inflation.to_string(
            index=False,
            formatters=dict.fromkeys(
                ("charter_gap", "true_gap", "shrunk_gap", "inflation"), "{:.4f}".format
            ),
        )
    )
    first = inflation.iloc[0]
    print(
        f"   On a one-period baseline the charter claims {first['charter_gap']:.2f} where "
        f"{first['true_gap']:.2f} is there: {first['inflation'] / first['true_gap']:.0%} of the"
    )
    print("   gap does not exist. Shrinking the best site toward the average errs the other way,")
    print("   and the truth sits between the two in every window. Quote one and you have chosen a")
    print("   direction; quote both and you have stated a range.")

    print("\nTHE CHARTER THIS PANEL WOULD PRODUCE")
    baseline_window = int(design["split"])
    recent = panel[(panel["period"] > split - baseline_window) & (panel["period"] <= split)]
    averages = recent.groupby("site", observed=True)["value"].mean()
    reference = entitlement(averages, noise_sd=PROFILE.noise, window=baseline_window)
    charter = Charter(
        measurand=str(design["stream"]),
        unit=str(design["unit"]),
        baseline=reference.grand_mean,
        baseline_window=baseline_window,
        target=reference.observed_best,
        target_basis="entitlement",
        volume_per_period=float(design["units_per_period"]) * int(design["sites"]),
        periods=int(design["periods"]) - split,
        variable_share=float(design["variable_share"]),
        project_cost=float(design["project_cost"]),
    )
    case = charter.benefit_case()
    print(f"   {charter.verdict()}")
    print(f"   {reference.verdict()}")
    print(
        f"   gross {case.gross:,.0f}, cash {case.cash:,.0f}, capacity {case.capacity:,.0f}, "
        f"net {case.net:,.0f}"
    )
    print("   The benefit is computed by the same class the Improve phase audits it with, so the")
    print("   promise and the verification cannot disagree about arithmetic - only about reality.")

    print("\nAND THE TREE THAT EXPLAINS THE GAP")
    claimed = TREE.claimed
    multiple = overattribution(TREE, charter.gap)
    print(
        f"   The leaves claim {claimed:.2f} against a gap of {abs(charter.gap):.2f}: "
        f"{multiple:.2f}x."
    )
    print(
        f"   And {TREE.unmeasurable_claim:.2f} of the claim - "
        f"{100 * TREE.unmeasurable_claim / claimed:.1f}% of the tree - sits under leaves that"
    )
    print("   name no measurand, so that share cannot be verified after the project closes.")
    print(ctq_table(TREE, charter.gap).to_string(index=False))


if __name__ == "__main__":
    main()

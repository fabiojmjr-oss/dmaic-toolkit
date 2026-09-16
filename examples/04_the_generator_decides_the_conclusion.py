"""One experiment, three designs, and a factor that does nothing reported as the second largest.

Run:
    python examples/04_the_generator_decides_the_conclusion.py

The sixteen runs are measured once. Each design below then reads the rows it would have run, so
nothing varies between the three except which eight of the same sixteen were kept - and for the
two half fractions, not even the count. The truth is on the record: temperature and pressure
matter, their interaction matters more than pressure alone, and cure time and resin batch do
nothing whatsoever.
"""

from __future__ import annotations

import pandas as pd

from dmaic.analyze import (
    alias_structure,
    detectable_effect,
    effects,
    fractional_factorial,
    full_factorial,
)
from dmaic.synth import FACTORIALS, generate_dataset

PROFILE = FACTORIALS[0]

DESIGNS = (
    ("full 2^4, 16 runs", ()),
    ("half fraction, D=ABC", ("D=ABC",)),
    ("half fraction, D=AB", ("D=AB",)),
)


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    runs = data.factorial_runs
    coded = runs[list(PROFILE.factors)].to_numpy()
    response = runs["response"].to_numpy()
    truth = data.factorial_effects.set_index("effect")["true_effect"]

    print("WHAT IS ACTUALLY IN THE PROCESS")
    print(
        f"   {PROFILE.process}: {PROFILE.response} in {PROFILE.unit}, run-to-run sd "
        f"{PROFILE.noise_sd}"
    )
    for index, setting in enumerate(PROFILE.settings):
        letter = "ABCD"[index]
        planted = truth[letter]
        print(
            f"   {letter}  {setting.name:16s} {setting.low:>6.1f} to {setting.high:>6.1f} "
            f"{setting.unit:5s} true effect {planted:+6.2f}"
        )
    print(f"   AB {'temperatura x pressao':16s} {'':20s} true effect {truth['AB']:+6.2f}")
    print("   Every other term is exactly zero, so an estimate for one is an artefact and not")
    print("   a small real effect measured badly.")

    print("\nWHAT EACH DESIGN REPORTS, FROM THE SAME MEASURED RUNS")
    for label, generators in DESIGNS:
        design = (
            full_factorial(PROFILE.factors)
            if not generators
            else fractional_factorial(PROFILE.factors, generators)
        )
        rows = design.rows_of(coded)
        table = effects(design, response[rows])
        table = table[table["order"] <= 2].copy()
        table["true"] = table["effect"].map(truth)
        table["error"] = table["estimate"] - table["true"]
        print(f"\n   {label} - {design.verdict()}")
        print(f"   runs kept: {[index + 1 for index in rows.tolist()]}")
        print(
            f"   smallest effect {design.n_runs} runs could see at 80% power: "
            f"{detectable_effect(design.n_runs, PROFILE.noise_sd):.4f} {PROFILE.unit}"
        )
        print(
            table.to_string(
                index=False,
                formatters={
                    "estimate": "{:.4f}".format,
                    "true": "{:.4f}".format,
                    "error": "{:+.4f}".format,
                },
            )
        )

    print("\nTHE RANKING A PROJECT WOULD ACT ON")
    print("   Same sixteen runs, same eight-run budget, and the two fractions disagree about")
    print("   which factors matter - because one generator hands the interaction to a factor.")
    for label, generators in DESIGNS[1:]:
        design = fractional_factorial(PROFILE.factors, generators)
        table = effects(design, response[design.rows_of(coded)])
        mains = table[table["order"] == 1].copy()
        mains = mains.reindex(mains["estimate"].abs().sort_values(ascending=False).index)
        ranked = ", ".join(
            f"{effect} {estimate:+.2f}"
            for effect, estimate in zip(mains["effect"], mains["estimate"], strict=True)
        )
        print(f"   {label:24s} {ranked}")

    print("\nWHY, WITHOUT LOOKING AT THE DATA")
    bad = fractional_factorial(PROFILE.factors, ("D=AB",))
    print(f"   defining relation: I = {' = '.join(bad.defining_relation)}")
    print(alias_structure(bad).to_string(index=False))
    print("   D and AB are one column. The design does not know which of them it measured, and")
    print("   neither does anyone reading its output.")


if __name__ == "__main__":
    main()

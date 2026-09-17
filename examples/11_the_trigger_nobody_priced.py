"""Three reaction rules from a control plan, priced as the tests they are.

Run:
    python examples/11_the_trigger_nobody_priced.py

A control plan is a table of triggers, each of them a hypothesis test run every day. The plan
records who reacts and how, and not the two numbers that decide whether reacting is worth anything:
how often the trigger fires when nothing is wrong, and how long it takes when something is.
"""

from __future__ import annotations

import pandas as pd

from dmaic.control import (
    alarms_against_delay,
    capability,
    compare_gages,
    rule_from_spread,
    spec_trigger,
)

NOMINAL, LSL, USL = 500.0, 475.0, 525.0
TOLERANCE = USL - LSL
PROCESS_SD = 8.0
WITHIN_SD = 2.0
SUBGROUP = 20
TRIGGER = 1.0
SHIFT = 1.0

# The three gages of examples 01 and 05, as the spread each adds to a reading.
GAGES = (
    ("no gage error", 0.0),
    ("BALANCA-01, 5.7% of tolerance", 0.4743),
    ("PAQUIMETRO-02 pooled, 16.2%", 0.162 * TOLERANCE / 6),
    ("PAQUIMETRO-02 on tolerance, 63.6%", 0.636 * TOLERANCE / 6),
)


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    print("AN ABSOLUTE TRIGGER, AND THE GAGE THAT SETS ITS FALSE-ALARM RATE")
    print(f"   'react if the daily average moves more than {TRIGGER:.2f}', {SUBGROUP} units a day,")
    print(f"   a process whose within-day spread is {WITHIN_SD:.2f}.")
    absolute = compare_gages(
        GAGES, limit=TRIGGER, subgroup=SUBGROUP, process_sd=WITHIN_SD, shift=SHIFT
    )
    print(
        absolute.to_string(
            index=False,
            formatters={
                "gage_sd": "{:.4f}".format,
                "total_sd": "{:.4f}".format,
                "limit": "{:.4f}".format,
                "false_alarm_rate": "{:.4f}".format,
                "periods_to_alarm": "{:.2f}".format,
                "gage_share": "{:.2%}".format,
                "delay": "{:.4f}".format,
            },
        )
    )
    worst = absolute.iloc[-1]
    best = absolute.iloc[0]
    print(
        f"   From a false alarm every {best['periods_to_alarm']:.2f} days to every "
        f"{worst['periods_to_alarm']:.2f}, and {worst['gage_share']:.0%} of the reactions on the"
    )
    print(
        f"   last row are the instrument. The detection of a real {SHIFT:.2f} shift barely moves "
        f"({best['delay']:.2f} to {worst['delay']:.2f} days),"
    )
    print("   so the bad gage buys no speed and costs five times the reaction workload.")

    print("\nA RELATIVE TRIGGER, WHICH HIDES THE GAGE INSTEAD")
    print("   'react if the move exceeds three sigma of the observed spread' - the limit now comes")
    print("   from the data, so a worse gage widens it.")
    rows = []
    for label, gage_sd in GAGES:
        rule = rule_from_spread(subgroup=SUBGROUP, process_sd=WITHIN_SD, gage_sd=gage_sd)
        rows.append(
            {
                "gage": label,
                "limit": rule.limit,
                "false alarm rate": rule.false_alarm_rate,
                "caught in 2 days": rule.shift_caught_within(2),
                f"days to catch {SHIFT:.2f}": rule.delay(SHIFT),
            }
        )
    relative = pd.DataFrame(rows)
    print(
        relative.to_string(
            index=False,
            formatters={
                "limit": "{:.4f}".format,
                "false alarm rate": "{:.4f}".format,
                "caught in 2 days": "{:.4f}".format,
                f"days to catch {SHIFT:.2f}": "{:.2f}".format,
            },
        )
    )
    slow, fast = relative.iloc[-1], relative.iloc[0]
    column = f"days to catch {SHIFT:.2f}"
    print(
        f"   The false-alarm rate is {fast['false alarm rate']:.4f} in every row - identical to "
        "four decimals, whatever the"
    )
    print(
        f"   gage. What changes is the reaction: {fast[column]:.2f} days against "
        f"{slow[column]:.2f}, {slow[column] / fast[column]:.1f} times slower."
    )
    print("   The gage is invisible in the figure anybody checks and fully present in the one")
    print("   nobody does. Choosing this form of trigger does not escape it; it moves where it")
    print("   hides.")

    print("\nA SPECIFICATION TRIGGER, WHICH IS SLOW AND NOT SILENT")
    print(
        f"   'react when any unit of the day is outside {LSL:.0f}-{USL:.0f}', process spread "
        f"{PROCESS_SD:.2f}, so a capability index of {capability(PROCESS_SD, LSL, USL):.4f}."
    )
    spec = spec_trigger(
        (0.0, 0.5, 1.0, 2.0),
        (5, SUBGROUP),
        process_sd=PROCESS_SD,
        nominal=NOMINAL,
        lsl=LSL,
        usl=USL,
    )
    print(
        spec.to_string(
            index=False,
            formatters={
                "shift_sigmas": "{:.1f}".format,
                "rate_per_period": "{:.6f}".format,
                "periods_to_react": "{:.2f}".format,
            },
        )
    )
    on_target = spec[(spec["shift_sigmas"] == 0.0) & (spec["subgroup"] == SUBGROUP)].iloc[0]
    shifted = spec[(spec["shift_sigmas"] == 1.0) & (spec["subgroup"] == SUBGROUP)].iloc[0]
    quarter = 63.0
    print(
        f"   With nothing wrong at all it fires every {on_target['periods_to_react']:.1f} days - "
        f"about {quarter / on_target['periods_to_react']:.1f} reactions a quarter on a process"
    )
    print("   that is exactly on target, which is not a rate anybody would defend out loud.")
    print(
        f"   And a one-sigma shift takes {shifted['periods_to_react']:.2f} days to surface at "
        f"{SUBGROUP} pieces a day - 12.30 at five."
    )

    print("\nTHE TRADE THE PLAN IS MAKING WITHOUT SAYING SO")
    trade = alarms_against_delay(
        (0.5, 1.0, 1.5, 2.0, 3.0), subgroup=SUBGROUP, process_sd=WITHIN_SD, shift=SHIFT
    )
    print(
        trade.to_string(
            index=False,
            formatters={
                "limit": "{:.4f}".format,
                "false_alarm_rate": "{:.4f}".format,
                "alarms_per_year": "{:.4f}".format,
                "delay": "{:.4f}".format,
            },
        )
    )
    print("   From 107 false alarms a year with a 1.26-day reaction, to one every two thousand")
    print("   years with a reaction measured in five years. Somebody chose a row of this table")
    print("   when they wrote the plan, and the plan does not say which row or why.")
    print("   A control chart is the instrument that makes this trade explicit and tunable. It")
    print("   lives in the sibling oplab.spc package; what is priced here are the triggers people")
    print("   write instead of one, which is most of them.")


if __name__ == "__main__":
    main()

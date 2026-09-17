"""A gain that halved, reported as a gain that grew, and an audit that cannot tell either way.

Run:
    python examples/10_did_the_gain_hold.py

Three years of twenty-four sites, twelve improved from month thirteen with an effect that decays
with a one-year half-life. The trend keeps running the whole time, which is what lets a sustain
report get better every quarter while the gain gets smaller.
"""

from __future__ import annotations

import pandas as pd

from dmaic.control import decay_detection, reported_gain, retention_path, sustain_audit
from dmaic.synth import SUSTAINS, generate_dataset, mean_true_effect

PROFILE = SUSTAINS[0]
CLOSE = (13, 24)
AUDIT = (25, 36)
QUARTERS = ((13, 18), (19, 24), (25, 30), (31, 36))
DECAYS = (0.5, 1.0, 1.856, 3.0, 5.0)


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    panel = data.sustain_panel
    design = data.sustain_designs.iloc[0]
    split = int(design["split"])

    print("WHAT IS ACTUALLY IN THE PANEL")
    print(
        f"   {int(design['sites'])} sites over {int(design['periods'])} periods, "
        f"{int(design['treated'])} improved from period {split + 1}"
    )
    print(
        f"   effect at closure {float(design['effect_at_close']):+.2f} {design['unit']}, "
        f"half-life {float(design['half_life']):.0f} periods, "
        f"trend {float(design['trend']):+.2f} per period"
    )
    print(
        f"   so the true effect averages {mean_true_effect(PROFILE, *CLOSE):+.4f} over "
        f"{CLOSE[0]}-{CLOSE[1]} and {mean_true_effect(PROFILE, *AUDIT):+.4f} over "
        f"{AUDIT[0]}-{AUDIT[1]}:"
    )
    print("   exactly half, by construction. A control plan is the thing that is supposed to make")
    print("   the half-life infinite.")

    print("\nWHAT THE SUSTAIN REPORT SHOWS")
    reported = reported_gain(panel, split=split, windows=QUARTERS)
    print(reported.to_string(index=False, formatters={"reported_gain": "{:+.4f}".format}))
    first, last = reported.iloc[0], reported.iloc[-1]
    print(
        f"   The reported gain grows from {first['reported_gain']:+.4f} to "
        f"{last['reported_gain']:+.4f} while the real effect falls from "
        f"{mean_true_effect(PROFILE, *QUARTERS[0]):+.4f}"
    )
    print(f"   to {mean_true_effect(PROFILE, *QUARTERS[-1]):+.4f}. Both numbers are arithmetically")
    print("   correct. They point in opposite directions, and the flattering one is the one that")
    print("   gets into the pack, because it is the one the original baseline produces.")

    print("\nWHAT AN AUDIT WITH A COMPARISON GROUP SHOWS")
    path = retention_path(panel, split=split, windows=(CLOSE, AUDIT))
    path["true_effect"] = [mean_true_effect(PROFILE, *CLOSE), mean_true_effect(PROFILE, *AUDIT)]
    print(
        path.to_string(
            index=False,
            formatters=dict.fromkeys(("true_effect", "estimate", "low", "high"), "{:+.4f}".format),
        )
    )
    print("   The direction is right and both intervals contain the effect that was there.")

    print("\nAND WHAT IT CAN ESTABLISH, WHICH IS LESS")
    audit = sustain_audit(panel, split=split, close=CLOSE, audit=AUDIT)
    true_close = mean_true_effect(PROFILE, *CLOSE)
    true_audit = mean_true_effect(PROFILE, *AUDIT)
    print(
        f"   retention measured {audit.retention:.2%} against a true {true_audit / true_close:.2%}"
    )
    print(
        f"   decay measured {audit.decay:.4f} against a true "
        f"{abs(true_close) - abs(true_audit):.4f}"
    )
    print(
        f"   smallest decay this audit could resolve: {audit.detectable_decay:.4f}, on a "
        f"site-level change spread of {audit.change_sd:.4f}"
    )
    print(f"   intervals overlap: {audit.intervals_overlap}")
    print(f"   verdict: {audit.verdict()}")

    print("\nWHAT THE AUDIT WOULD HAVE NEEDED")
    detection = decay_detection(DECAYS, units=int(design["treated"]), change_sd=audit.change_sd)
    print(
        detection.to_string(
            index=False,
            formatters=dict.fromkeys(("decay", "detectable", "power"), "{:.4f}".format),
        )
    )
    print("   Against the decay that actually happened the audit has about a coin flip. That is")
    print("   not an argument against auditing; it is an argument for sizing the audit when the")
    print("   project closes, while there is still somebody to argue with about how many sites it")
    print("   gets, rather than a year later when the answer is due.")


if __name__ == "__main__":
    main()

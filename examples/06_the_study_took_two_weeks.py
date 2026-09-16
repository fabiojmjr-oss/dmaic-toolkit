"""The same readings, the same days, and the study blames the operators for the calendar.

Run:
    python examples/06_the_study_took_two_weeks.py

A gage drifting a tenth of a gram a day, watched two ways. Periodic checks against a master turn
the drift into a calibration interval. A crossed study spread over two weeks turns it into
whichever ANOVA term the schedule aligned it with - and the schedule is not on the form.
"""

from __future__ import annotations

import pandas as pd

from dmaic.measure import calibration_interval, gage_rr, stability_study
from dmaic.synth import generate_dataset

WAVE_FIVE_BIAS = 4.0
DRIFT_BUDGET = 5.0


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    design = data.drift_designs.set_index("gage").loc["BALANCA-01"]
    tolerance = float(design["tolerance"])
    declared = float(design["drift_per_day"])

    print("HOW LONG THE CALIBRATION LASTS")
    study = stability_study(data.stability_checks, tolerance=tolerance, gage="BALANCA-01")
    print(
        f"   {study.n} readings over {study.last_day} days, {len(data.stability_checks) // 4} "
        f"checks against the master"
    )
    print(
        f"   drift {study.drift_per_day:+.6f} per day (declared {declared:+.2f}), "
        f"p = {study.p_value:.3e}, r squared {study.r_squared:.4f}"
    )
    print(
        f"   offset left behind on day 0: {study.intercept:+.4f} - the calibration itself was fine"
    )
    print(
        f"   offset on day {study.last_day}: {study.offset_at(study.last_day):+.4f}, "
        f"{study.pct_tolerance_at(study.last_day):.2f}% of tolerance"
    )
    print(f"   verdict: {study.verdict()}")
    print(
        f"   planned from the declared rate instead of measured: "
        f"{calibration_interval(declared, tolerance, DRIFT_BUDGET):.1f} days"
    )
    print(
        f"   the {WAVE_FIVE_BIAS:.1f} g offset example 05 found arrives on day "
        f"{WAVE_FIVE_BIAS / study.drift_per_day:.1f} at this rate. A constant bias and a drift "
        "measured late"
    )
    print("   are the same reading. They are not the same problem: one is removed once, the")
    print("   other buys an interval.")
    print(
        f"   residual spread around the line: {study.residual_sd:.4f}, against the gage's own "
        f"repeatability of {float(design['repeat_sd']):.2f}"
    )

    print("\nWHERE THE DRIFT GOES IN A CROSSED STUDY")
    print("   Identical readings and identical days in both schedules. The only difference is")
    print("   which day each reading falls on: one operator per day, or every operator every day.")
    rows = []
    for schedule, group in data.drift_studies.groupby("schedule", observed=True):
        result = gage_rr(group, tolerance=tolerance, gage=str(schedule))
        rows.append(
            {
                "schedule": schedule,
                "EV": result.ev,
                "AV": result.av,
                "GRR": result.grr,
                "% study": result.pct_study,
                "% tol": result.pct_tolerance,
                "ndc": result.ndc,
                "dominant": result.dominant_source,
                "verdict": result.verdict(),
            }
        )
    # The same study with the drift subtracted, which is the instrument on any one day and the
    # only row of the three that is a property of the gage rather than of the schedule.
    without = data.drift_studies[data.drift_studies["schedule"] == "sequential"].copy()
    without["value"] = without["value"] - declared * without["day"]
    truth = gage_rr(without, tolerance=tolerance, gage="drift removed")
    rows.append(
        {
            "schedule": "drift removed",
            "EV": truth.ev,
            "AV": truth.av,
            "GRR": truth.grr,
            "% study": truth.pct_study,
            "% tol": truth.pct_tolerance,
            "ndc": truth.ndc,
            "dominant": truth.dominant_source,
            "verdict": truth.verdict(),
        }
    )
    table = pd.DataFrame(rows)
    print(
        table.to_string(
            index=False,
            formatters=dict.fromkeys(("EV", "AV", "GRR", "% study", "% tol"), "{:.4f}".format),
        )
    )

    sequential = next(row for row in rows if row["schedule"] == "sequential")
    interleaved = next(row for row in rows if row["schedule"] == "interleaved")
    print(
        f"   One operator per day inflates reproducibility {sequential['AV'] / truth.av:.2f}x and "
        f"leaves repeatability at {sequential['EV']:.4f} against {truth.ev:.4f} - the calendar,"
    )
    print("   reported as the people. A project reading it would go and retrain the operators.")
    print(
        f"   Interleaving puts the same drift in repeatability instead "
        f"({interleaved['EV'] / truth.ev:.2f}x) and leaves the"
    )
    print(
        f"   operator estimate almost intact ({interleaved['AV']:.4f} against {truth.av:.4f}). "
        "That is the right place for it,"
    )
    print("   and it is still not a repeatability: it is two weeks of drift inside a term whose")
    print("   name says one session.")
    print(
        f"   Both drifted schedules come back '{sequential['verdict']}' where the instrument on "
        f"any single day is '{truth.verdict()}'. The study's own"
    )
    print("   conclusion depends on how long it took, and no field on the form records that.")


if __name__ == "__main__":
    main()

"""The taught flowchart, measured against always using Welch. It loses.

Run:
    python examples/03_which_test_and_can_it_be_trusted.py

Two groups drawn with the same mean, so every rejection is a type I error and the nominal rate is
5% by construction. What comes out is what the procedures really do - and the procedure every
Six Sigma course teaches is not the one that holds its level.
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from dmaic.analyze import (
    DEFAULT_ALPHA,
    PROCEDURES,
    compare_means,
    type_one_error_rates,
)
from dmaic.analyze.compare import normality_test_tradeoff
from dmaic.synth import generate_dataset

SCENARIOS = (
    ("normal, equal spread, n 20/20", {"n_first": 20, "n_second": 20}),
    ("normal, spread 1:3, n 20/20", {"n_first": 20, "n_second": 20, "sd_second": 3.0}),
    ("normal, spread 1:3, n 10/30", {"n_first": 10, "n_second": 30, "sd_second": 3.0}),
    ("normal, spread 3:1, n 10/30", {"n_first": 10, "n_second": 30, "sd_first": 3.0}),
    ("skewed, equal spread, n 20/20", {"n_first": 20, "n_second": 20, "shape": "skewed"}),
    (
        "skewed, spread 3:1, n 10/30",
        {"n_first": 10, "n_second": 30, "sd_first": 3.0, "shape": "skewed"},
    ),
)


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    print("WHAT EACH PROCEDURE'S FALSE-POSITIVE RATE ACTUALLY IS")
    print(f"   Both groups drawn with the same mean, so the nominal rate is {DEFAULT_ALPHA:.0%}")
    print("   by construction and every rejection below is a type I error. 20,000 replications.")
    rows = []
    for label, keywords in SCENARIOS:
        rates = type_one_error_rates(**keywords)
        rows.append({"scenario": label, **rates})
    table = pd.DataFrame(rows)
    print()
    # Formatted rather than rounded: pandas and f-strings break ties differently, and several of
    # these rates land exactly on one. A reader comparing this output against the module README
    # should not have to wonder which of 0.0479 and 0.0480 is the real number.
    print(table.to_string(index=False, formatters=dict.fromkeys(PROCEDURES, "{:.4f}".format)))

    indexed = table.set_index("scenario")
    wide_on_small = indexed.loc["normal, spread 3:1, n 10/30"]
    wide_on_large = indexed.loc["normal, spread 1:3, n 10/30"]
    print("\n" + "=" * 96)
    print("THE POOLED TEST IS WRONG IN BOTH DIRECTIONS")
    print("=" * 96)
    print(
        f"   Wider spread on the smaller group: {wide_on_small['pooled t']:.2%} against a nominal"
        f" {DEFAULT_ALPHA:.0%}."
    )
    print(
        f"   Reverse which group is which - same violated assumption, same ratio -"
        f" and it collapses to {wide_on_large['pooled t']:.2%},"
    )
    print("   throwing away almost all its power. Nothing about the process changed; only which")
    print("   group happened to be larger. A test whose error rate depends on that is not a test")
    print("   with a caveat, it is bookkeeping with a p-value attached.")
    print(
        f"\n   Welch across the same two: {wide_on_small['Welch']:.2%} and"
        f" {wide_on_large['Welch']:.2%}. And under equal spread it costs"
    )
    print(
        f"   nothing: {indexed.loc['normal, equal spread, n 20/20', 'Welch']:.2%} against the"
        f" pooled test's"
        f" {indexed.loc['normal, equal spread, n 20/20', 'pooled t']:.2%}."
    )

    print("\n" + "=" * 96)
    print("AND THE FLOWCHART IS WORSE THAN NOT CHOOSING AT ALL")
    print("=" * 96)
    print(
        f"   {wide_on_small['flowchart']:.2%} against Welch's {wide_on_small['Welch']:.2%} in the"
        " case that matters. The flowchart"
    )
    print("   inherits the pooled test's inflation whenever the variance pre-test happens not to")
    print("   fire, which is often. **A pre-test does not protect a procedure, it launders it.**")
    print(
        f"\n   Reaching for a rank test makes it worse, not better:"
        f" {wide_on_small['Mann-Whitney']:.2%} here, and"
    )
    print(
        f"   {indexed.loc['normal, spread 1:3, n 20/20', 'Mann-Whitney']:.2%} even with balanced"
        " groups. Mann-Whitney is not a distribution-free"
    )
    print("   t-test; it tests a different hypothesis, and unequal spread breaks it too. The")
    print("   reflex 'not normal, so use the non-parametric test' treats the assumption that was")
    print("   not the problem.")
    worst = indexed.loc["skewed, spread 3:1, n 10/30"]
    print(
        "\n   And in the last row nothing holds: "
        + ", ".join(f"{worst[p]:.2%}" for p in PROCEDURES)
        + "."
    )
    print("   Picking the least bad of those is not a solution. The fix is a different design.")

    print("\n" + "=" * 96)
    print("THE NORMALITY TEST IS LEAST INFORMATIVE WHERE IT MATTERS MOST")
    print("=" * 96)
    tradeoff = pd.DataFrame(
        [{"n_per_group": n, **normality_test_tradeoff(n)} for n in (5, 10, 20, 50, 100, 300)]
    )
    print(
        tradeoff.to_string(
            index=False,
            formatters={
                "detection_rate": "{:.4f}".format,
                "welch_type_one_error": "{:.4f}".format,
            },
        )
    )
    small = tradeoff.iloc[0]
    large = tradeoff.iloc[-1]
    print(
        f"\n   At {int(small['n_per_group'])} per group the check passes"
        f" {1 - small['detection_rate']:.0%} of the time - and that is where the"
    )
    print(
        f"   test is most distorted, at {small['welch_type_one_error']:.2%} against a nominal"
        f" {DEFAULT_ALPHA:.0%}. At {int(large['n_per_group'])} it fails every"
    )
    print(
        f"   single time and sends the project to a rank test - and there the t-test is already"
        f"\n   fine, at {large['welch_type_one_error']:.2%}."
        " **The verdict is anti-correlated with the need for it.**"
    )
    control = normality_test_tradeoff(30, shape="normal")
    print(
        f"\n   On genuinely normal data the detection rate comes out at"
        f" {control['detection_rate']:.2%}, which is the"
    )
    print("   control: the instrument is calibrated. The problem is the question asked of it.")

    print("\n" + "=" * 96)
    print("FOUR COMPARISONS, AND THE TWO THE DIAGNOSTIC GETS WRONG")
    print("=" * 96)
    data = generate_dataset()
    designs = data.comparison_designs.set_index("comparison")
    rows = []
    for name in designs.index:
        frame = data.group_comparisons[data.group_comparisons["comparison"] == name]
        names = list(dict.fromkeys(frame["group"].tolist()))
        first = frame.loc[frame["group"] == names[0], "value"].to_numpy()
        second = frame.loc[frame["group"] == names[1], "value"].to_numpy()
        result = compare_means(first, second)
        pooled = float(stats.ttest_ind(second, first, equal_var=True).pvalue)
        rows.append(
            {
                "comparison": name,
                "true_difference": float(designs.loc[name, "true_difference"]),
                "sd_ratio": result.variance.sd_ratio,
                "pooled_p": pooled,
                "welch_p": result.p_value,
                "ratio": result.p_value / pooled,
                "diagnosis": result.diagnosis(),
            }
        )
    numeric = ["true_difference", "sd_ratio", "pooled_p", "welch_p", "ratio"]
    print(
        pd.DataFrame(rows).to_string(
            index=False, formatters=dict.fromkeys(numeric, "{:.4f}".format)
        )
    )

    supplier = next(row for row in rows if row["comparison"] == "FORN-X vs FORN-Y")
    print(
        f"\n   FORN-X vs FORN-Y is the case to sit with. The pooled test returns"
        f" p = {supplier['pooled_p']:.4f} and"
    )
    print(
        f"   Welch returns p = {supplier['welch_p']:.4f} on the same forty observations - a factor"
        f" of {supplier['ratio']:.1f}. One"
    )
    print(
        f"   declares a highly significant result; the other declines to reject at"
        f" {DEFAULT_ALPHA:.0%}. And there is a"
    )
    print(
        f"   real difference of {supplier['true_difference']:+.1f} days, so the pooled test"
        " reached the right answer."
    )
    print(
        f"\n   It did not earn it. The simulation puts that procedure at"
        f" {worst['pooled t']:.2%} false positives in this"
    )
    print("   exact regime, so it would have been just as confident with no difference at all. A")
    print("   single sample cannot tell a test that is right from a test that is loud, which is")
    print("   the whole reason the error rates are measured rather than reasoned about.")


if __name__ == "__main__":
    main()

"""Three pilots, three non-significant results, three real effects.

Run:
    python examples/02_could_the_pilot_have_found_it.py

The generator declares the effect it put into each trial, which is the advantage of synthetic
data here: a real project that finds nothing cannot tell a missed effect from an absent one. With
the truth on the record, "the test found nothing" and "the test missed something" become different
statements - and all three of these pilots are the second one.
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from dmaic.analyze import (
    DEFAULT_POWER,
    detectable_difference,
    observed_power_is_circular,
    power_two_means,
    power_two_proportions,
    sample_size_normal_approximation,
    sample_size_two_means,
    sample_size_two_proportions,
)
from dmaic.synth import generate_dataset


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    data = generate_dataset()
    designs = data.trial_designs.set_index("trial")

    print("THREE PILOTS, AS THEY WOULD BE WRITTEN UP")
    print("   Each sized the way projects are actually sized: from what was convenient to")
    print("   collect. Every one of them returns a non-significant result.")

    rows = []
    for trial in designs.index:
        group = data.improvement_trials[data.improvement_trials["trial"] == trial]
        baseline = group.loc[group["arm"] == "baseline", "value"].to_numpy()
        improved = group.loc[group["arm"] == "improved", "value"].to_numpy()
        n = int(designs.loc[trial, "n_per_arm"])
        truth = float(designs.loc[trial, "true_effect"])
        observed = float(improved.mean() - baseline.mean())

        if designs.loc[trial, "kind"] == "binary":
            table = [
                [baseline.sum(), n - baseline.sum()],
                [improved.sum(), n - improved.sum()],
            ]
            p_value = float(stats.chi2_contingency(table).pvalue)
            control = float(designs.loc[trial, "baseline"])
            power = power_two_proportions(n, control, control + truth)
            needed = sample_size_two_proportions(control, control + truth).n_per_group
        else:
            sd = float(designs.loc[trial, "sd"])
            p_value = float(stats.ttest_ind(improved, baseline).pvalue)
            power = power_two_means(n, truth, sd)
            needed = sample_size_two_means(abs(truth), sd).n_per_group

        rows.append(
            {
                "trial": trial,
                "measurand": designs.loc[trial, "measurand"],
                "observed": observed,
                "true_effect": truth,
                "p_value": p_value,
                "power_for_truth": power,
                "n_run": n,
                "n_needed": needed,
                "conclusion drawn": "no improvement",
                "conclusion warranted": "cannot tell",
            }
        )
    table = pd.DataFrame(rows)
    print()
    print(
        table[
            [
                "trial",
                "observed",
                "true_effect",
                "p_value",
                "power_for_truth",
                "n_run",
                "n_needed",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    print(
        "\n   All three non-significant. All three had a real effect. Every one would be filed"
        "\n   as 'no improvement demonstrated', and each fails for a different reason."
    )

    print("\n" + "=" * 96)
    print("WHY EACH ONE FAILED")
    print("=" * 96)
    cycle = designs.loc["PILOTO-CICLO"]
    reach = detectable_difference(int(cycle["n_per_arm"]), float(cycle["sd"]))
    print(
        f"   PILOTO-CICLO was underpowered and then unlucky. At {int(cycle['n_per_arm'])} per arm"
        f" it had a"
    )
    cycle_power = power_two_means(
        int(cycle["n_per_arm"]), float(cycle["true_effect"]), float(cycle["sd"])
    )
    print(
        f"   {cycle_power:.1%} chance of finding its own"
        f" {abs(float(cycle['true_effect'])):.0f}-minute effect, and it"
        f" observed {table.loc[0, 'observed']:+.2f}."
    )
    print(
        f"   Its detectable difference was {reach:.2f} minutes, so a"
        f" {abs(float(cycle['true_effect'])):.0f}-minute improvement was out of"
    )
    print("   reach from the moment the sample size was fixed. p = 0.92 reads as overwhelming")
    print("   evidence of no effect and is a statement about the study, not the process.")

    setup = designs.loc["PILOTO-SETUP"]
    setup_power = power_two_means(
        int(setup["n_per_arm"]), float(setup["true_effect"]), float(setup["sd"])
    )
    print(
        f"\n   PILOTO-SETUP was almost properly designed: {setup_power:.1%} power, near enough to"
        f" the conventional"
    )
    print(
        f"   {DEFAULT_POWER:.0%} that nobody would object. It missed anyway. **That is what"
        f" {DEFAULT_POWER:.0%} power means** - a"
    )
    print("   well-designed study fails to detect a real effect one time in five, by")
    print("   construction. Treating one non-significant pilot as settled misreads the")
    print("   guarantee that was bought.")

    scrap = designs.loc["PILOTO-REFUGO"]
    print(
        f"\n   PILOTO-REFUGO observed a *larger* improvement than the one that existed"
        f" ({table.loc[2, 'observed'] * 100:+.2f} points"
    )
    print(
        f"   against a true {float(scrap['true_effect']) * 100:+.2f}) and still could not prove"
        f" it. A proportion near"
        f" {float(scrap['baseline']):.0%} carries so"
    )
    print(
        f"   little information that detecting {abs(float(scrap['true_effect'])) * 100:.1f} points"
        f" needs {table.loc[2, 'n_needed']:,} units per arm against the"
    )
    print(
        f"   {int(scrap['n_per_arm'])} collected. This is the case that kills the intuition that a"
        " non-significant"
    )
    print("   result implies a small effect: the measured effect was bigger than the truth.")

    print("\n" + "=" * 96)
    print("THE FORMULA ON THE WALL, AND WHEN ITS SHORTCUT COSTS SOMETHING")
    print("=" * 96)
    comparison = []
    for effect in (2.0, 1.5, 1.0, 0.5, 0.33, 0.1):
        exact = sample_size_two_means(effect, 1.0)
        approximate = sample_size_normal_approximation(effect, 1.0)
        comparison.append(
            {
                "cohens_d": effect,
                "exact_n": exact.n_per_group,
                "formula_n": approximate,
                "power_delivered": power_two_means(approximate, effect, 1.0),
            }
        )
    print(pd.DataFrame(comparison).round(4).to_string(index=False))
    print("\n   Across the practical range the shortcut is off by one observation per group and")
    print("   the power it delivers rounds to the power asked for. **It is harmless for most")
    print("   studies**, and saying otherwise would overstate a real but small effect.")
    print("\n   Where it bites is the small confirmation run. At two standard deviations it asks")
    print("   for 4 per group against the 6 required and delivers 66% power - which is exactly")
    print("   PILOTO-SETUP's situation, and not 'almost right' for a study with one shot.")

    print("\n" + "=" * 96)
    print("AND WHY POST-HOC POWER CANNOT EXPLAIN ANY OF IT")
    print("=" * 96)
    circular = []
    for observed in (2.0, 4.0, 6.0, 6.2, 8.0, 12.0):
        power, p_value = observed_power_is_circular(30, observed, 12.0)
        circular.append({"observed_effect": observed, "p_value": p_value, "observed_power": power})
    print(pd.DataFrame(circular).round(4).to_string(index=False))
    print("\n   Observed power is a strictly monotone function of the p-value, so it carries no")
    print("   information the p-value did not. At p = 0.05 the observed power is almost exactly")
    print("   one half, and it converges there as the study grows:")
    for n in (10, 30, 100, 500):
        boundary = _effect_at_p(n, 0.05)
        power, _ = observed_power_is_circular(n, boundary, 12.0)
        print(f"     n = {n:4d}: effect at p = 0.05 is {boundary:7.4f}, observed power {power:.4f}")
    print("\n   So 'we only had 48% power' is another way of writing 'p was just above 0.05'. It")
    print("   is the same finding in different units, and citing one to explain the other is")
    print("   circular. The detectable difference uses the sample size and the spread but not")
    print("   the observed effect, which is why it says something the p-value does not.")


def _effect_at_p(n_per_group: int, target_p: float) -> float:
    """The observed effect that would have produced exactly this p-value."""
    from scipy import optimize

    def gap(delta: float) -> float:
        return observed_power_is_circular(n_per_group, delta, 12.0)[1] - target_p

    return float(optimize.brentq(gap, 1e-9, 200.0))


if __name__ == "__main__":
    main()

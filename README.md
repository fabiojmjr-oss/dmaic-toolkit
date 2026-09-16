# dmaic-toolkit

*[Português](README.pt-BR.md)*

A DMAIC toolkit, one module per phase. Not a library of statistical formulas with Six Sigma
vocabulary attached — a set of tools that each answer a decision a project has to take, and that
**refuse to return a number when the assumptions behind it do not hold.**

Every figure quoted in any README here is re-derived by the test suite. A change that moves a
published number breaks the build rather than leaving the text quietly wrong.

**No data from any employer, client or third party is used anywhere in this repository.** Every
table is produced by a seeded generator whose parameters are written down. See
[`DISCLAIMER.md`](DISCLAIMER.md).

## Phases

| Module | Phase | Decision it enables |
| --- | --- | --- |
| [`dmaic.measure`](src/dmaic/measure/README.md) | Measure | Can this measurement system be used, what would fix it, and can it support the specification? |
| [`dmaic.analyze`](src/dmaic/analyze/README.md) | Analyze | How much data does this test need, and what did a non-significant result actually rule out? |

[`docs/ROADMAP.md`](docs/ROADMAP.md) lists the phases not yet built, and says why the Control
phase is deliberately narrower than it looks.

## Install

```bash
make install     # editable install with the dev tools
make check       # lint, format, types and the fast suite - what gates a push
make claims      # re-derive every number quoted in a README
```

## What the waves found

### Wave 1 — measurement system analysis

A measurement system analysis on three synthetic gages, each a 10-part × 3-operator × 3-replicate
crossed study, decomposed by two-factor random-effects ANOVA.

| Gage | % contribution | % study variation | % tolerance | ndc | verdict |
| --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | 0.40 | 6.29 | 5.69 | 22 | acceptable |
| `PAQUIMETRO-02` | **2.64** | **16.24** | **63.58** | 8 | unacceptable |
| `INSPECAO-03` | 40.99 | 64.02 | 62.55 | 1 | unacceptable |

**`PAQUIMETRO-02` is one gage read three ways.** 2.64, 16.24 and 63.58 are the same measurement
system. Percent contribution is a ratio of variances, percent study variation a ratio of standard
deviations, and percent tolerance compares the gage to the specification rather than to the parts.
The 10% / 30% acceptance bands are written for the middle one — so reading contribution against
them turns an unacceptable gage into an excellent one, because contribution is study variation
squared and squaring a fraction moves it toward zero.

**Pooling the part-by-operator interaction flips the diagnosis.** AIAG's rule drops the term when
p > 0.25. Forcing the pool on `PAQUIMETRO-02` moves the GRR barely at all — 16.24 to 14.63 — while
sending reproducibility to exactly zero and flipping the dominant source from the people to the
instrument. The expensive consequence is not the 1.6 points of GRR; it is the capital expenditure
the number justifies.

**Splitting GRR is what makes a failed study actionable.** `INSPECAO-03` fails at 64%, with
reproducibility 3.2× repeatability. The instrument is not the problem, and replacing it — the
commonest response to a failed study, and the one with an invoice attached — would change almost
nothing.

### Wave 2 — power and sample size

Three pilots, each sized the way projects are actually sized: from what was convenient to collect.
The generator declares the effect it planted, which is the advantage of synthetic data here — a
real project cannot tell a missed effect from an absent one.

| Trial | Observed effect | True effect | p-value | Power for the true effect | n run | n needed |
| --- | --- | --- | --- | --- | --- | --- |
| `PILOTO-CICLO` | −0.29 min | −4.00 min | 0.9234 | **0.2456** | 30 | 143 |
| `PILOTO-SETUP` | −2.77 min | −6.00 min | 0.2345 | 0.7905 | 5 | 6 |
| `PILOTO-REFUGO` | −3.50 pts | −2.50 pts | 0.2152 | **0.1702** | 200 | **1,568** |

**All three are non-significant. All three had a real effect.** Three type II errors, each failing
for a different reason. `PILOTO-CICLO` had a 24.6% chance of finding its own effect and a
detectable difference of 8.83 minutes against a 4-minute truth. `PILOTO-SETUP` was properly
designed at 79.1% power and missed anyway — which is what 80% power *means*, one failure in five
by construction. And `PILOTO-REFUGO` observed a **larger** improvement than the one that existed
and still could not prove it, because detecting 2.5 points off an 8% scrap rate needs 1,568 units
per arm.

**The textbook sample-size formula is harmless for most studies.** Measured against the exact
noncentral-t calculation it is off by one observation per group across the practical range. Where
it bites is the small confirmation run: at an effect of two standard deviations it asks for 4 per
group against the 6 required and delivers 66% power.

**Post-hoc power is arithmetic on the p-value.** Observed power is a strictly monotone function of
it, and at `p = α = 0.05` the observed power is 0.5035 — converging on one half as the study grows
(0.5114 at n=10, 0.5002 at n=500). So "we only had 48% power" is another way of writing "p was
just above 0.05", and citing one to explain the other is circular.

## Examples

| Script | What it shows |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Three gages, three verdicts, and the two acceptance criteria disagreeing on one of them |
| [`02_could_the_pilot_have_found_it.py`](examples/02_could_the_pilot_have_found_it.py) | Three pilots, three non-significant results, three real effects |

## Verification

**74 tests, 93% statement coverage, split by cost.** 66 of them run in about four and a half
seconds, and the whole `make check` sequence — linters, type check, coverage and all — in under
six. That is what a push is gated on. The remaining 8 re-derive every figure quoted in a README
and run every example script, in under two seconds.

The gage ANOVA is verified against a 2×2×2 design whose sums of squares are integers (242, 50, 2
and 8, adding to 302), not only against its own output. Independent property checks confirm that
identical replicates give exactly zero repeatability, that identical operators give zero
reproducibility, that percent contribution is exactly percent study variation squared, and that
changing the sigma multiplier from 5.15 to 6.0 scales percent tolerance by exactly 1.1650 while
leaving percent study variation untouched.

The power arithmetic is anchored the same way: power at a zero effect equals the significance
level exactly, the detectable difference round-trips back to the power it was solved for, and the
noncentral-t result is checked against a recomputation from scipy primitives rather than against
the wrapper's own output. Every generator table is pinned too — adding wave 2 left wave 1's gage
study byte-identical, which is what the stream-order discipline is for.

## Related

Statistical process control — control charts, Nelson run rules, capability against
within-subgroup sigma — lives in a sibling repository rather than here. Two repositories holding
the same code under one name would read as padding.

## License

MIT. See [`LICENSE`](LICENSE).

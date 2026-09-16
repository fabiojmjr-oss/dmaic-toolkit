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

[`docs/ROADMAP.md`](docs/ROADMAP.md) lists the phases not yet built, and says why the Control
phase is deliberately narrower than it looks.

## Install

```bash
make install     # editable install with the dev tools
make check       # lint, format, types and the fast suite - what gates a push
make claims      # re-derive every number quoted in a README
```

## What wave 1 found

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

## Examples

| Script | What it shows |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Three gages, three verdicts, and the two acceptance criteria disagreeing on one of them |

## Verification

**33 tests, 95% statement coverage, split by cost.** 28 of them run in about five seconds — and
that, with the linters and the type check, is what a push is gated on. The remaining 5 re-derive
every figure quoted in a README and run every example script.

The gage ANOVA is verified against a 2×2×2 design whose sums of squares are integers (242, 50, 2
and 8, adding to 302), not only against its own output. Independent property checks confirm that
identical replicates give exactly zero repeatability, that identical operators give zero
reproducibility, that percent contribution is exactly percent study variation squared, and that
changing the sigma multiplier from 5.15 to 6.0 scales percent tolerance by exactly 1.1650 while
leaving percent study variation untouched.

## Related

Statistical process control — control charts, Nelson run rules, capability against
within-subgroup sigma — lives in a sibling repository rather than here. Two repositories holding
the same code under one name would read as padding.

## License

MIT. See [`LICENSE`](LICENSE).

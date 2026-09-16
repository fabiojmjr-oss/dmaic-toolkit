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
| [`dmaic.measure`](src/dmaic/measure/README.md) | Measure | Can this measurement system tell the parts apart, is it right, how long does that last, and what does being wrong cost? |
| [`dmaic.analyze`](src/dmaic/analyze/README.md) | Analyze | How much data does this test need, does it hold the error rate it claims, and can the experiment separate the effects it is being asked about? |
| [`dmaic.control`](src/dmaic/control/README.md) | Control | What does this sampling plan actually catch, what does it let through, and what did the inspection buy? |

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

### Wave 3 — the assumptions behind the p-value

Two groups drawn with the same mean, so **every rejection below is a type I error** and the
nominal rate is 5% by construction. 20,000 replications.

| Scenario | pooled t | Welch | flowchart | Mann-Whitney |
| --- | --- | --- | --- | --- |
| normal, equal spread, n 20 / 20 | 0.0479 | 0.0477 | 0.0478 | 0.0481 |
| normal, spread 1:3, n 10 / 30 | **0.0038** | 0.0478 | 0.0432 | 0.0150 |
| normal, spread 3:1, n 10 / 30 | **0.2130** | 0.0507 | **0.0628** | **0.1270** |
| skewed, spread 3:1, n 10 / 30 | **0.2331** | **0.1112** | **0.1454** | **0.2850** |

**The taught flowchart — check normality, check variance, choose accordingly — is measurably
worse than skipping the checks and using Welch.** 6.28% against 5.07% in the case that matters,
because it inherits the pooled test's inflation whenever the variance pre-test happens not to
fire. A pre-test does not protect a procedure, it launders it.

**The pooled t-test is wrong in both directions and which one depends on bookkeeping.** 21.30%
with the wider spread on the smaller group; 0.38% when the same inequality sits the other way
round. Nothing about the process changes — only which group happened to be larger. Welch holds
4.77% to 5.07% across every normal scenario and costs nothing under equality.

**Reaching for a rank test makes it worse.** Mann-Whitney runs at 12.70% here and 6.63% even with
balanced groups: it is not a distribution-free t-test, it tests a different hypothesis, and
unequal spread breaks it too.

**And the normality check is least informative exactly where it matters most.** At five per group
a real skew is detected 16.3% of the time, so the check passes — and that is where the test is
most distorted, at 2.40%. At three hundred it is detected every time, so the check fails and sends
the project to a rank test — and there the test is already fine, at 5.22%. The verdict is
anti-correlated with the need for it, because both facts are consequences of small n.

**The diagnostic cannot see what breaks the test.** The population skewness is 3.2629; at ten
observations the algebraic ceiling on a sample skewness is 2.667, so the estimator cannot report
the truth even in principle, and the flag fires 39.8% of the time. The spread diagnostic fails the
same way: drawn from a true ratio of exactly 3.00, the sample ratio's middle 90% runs from 1.152
to 6.762. Taken together the regime flag catches the bad case **75.0% of the time** — one miss in
four, which is why `compare_means` uses Welch unconditionally and returns the checks as evidence
rather than as a gate.

### Wave 4 — design of experiments

One synthetic curing-oven experiment: four factors, sixteen runs, shear strength in MPa. The
generator declares what is in the process, and **two of the four factors are exactly zero** —
cure time and resin batch. The sixteen runs are measured once; each design below reads the rows
it would have run, so nothing varies between them but which of the same runs were kept.

| Term | True | full 2⁴, 16 runs | 2^(4-1) `D=ABC`, 8 runs | 2^(4-1) `D=AB`, 8 runs |
| --- | --- | --- | --- | --- |
| A temperatura | +12.00 | 12.5810 | 11.8174 | 13.1256 |
| B pressao | +5.00 | 4.9727 | 4.5785 | 5.8547 |
| C tempo de cura | 0.00 | 0.2853 | −0.3577 | −0.4082 |
| D lote de resina | 0.00 | 1.5494 | 0.5307 | **9.4067** |
| AB | +8.00 | 7.8573 | **7.7678** | 9.4067 |
| Resolution | | full | IV | **III** |

**A resolution III design does not lose an interaction, it awards it to a factor that does
nothing.** Resin batch has an effect of exactly zero and comes back at 9.4067 — the second largest
figure in the study, 1.88 times the real pressure effect, and 2.63 times the smallest effect eight
runs could have detected. It is not marginal and it does not look like noise. The two fractions
cost the same eight runs, read the same experiment, and rank the factors differently: `D=ABC`
gives A, B, D, C and `D=AB` gives A, **D**, B, C. Only the generator differs, and it is free.

**Aliasing is an exact addition, not extra noise.** The fraction's estimate is the arithmetic sum
of the full design's estimates of the aliased terms — `D + AB` is 1.5494 + 7.8573 = 9.4067,
reproducing to 5.3e-15 across every alias pair of both fractions. That is why `D=ABC` works: it
also adds two numbers, and one of them happens to be zero. It recovers the interaction at 7.7678
against the full design's 7.8573, a gap of 0.0895 MPa on an effect of 8, for half the runs.

**A detection limit protects against noise and says nothing about bias.** At this process's
run-to-run spread of 1.5 MPa, eight runs can see 3.5711 MPa and sixteen can see 2.2600. The
largest purely spurious estimate in the full design is 1.5494, below the limit, so a project would
correctly leave it alone. The false 9.4067 sits at 2.63 times the limit, because it is a real
effect in the wrong column and a detection limit has no opinion about columns.

**And the resolution comes from the defining relation, not from the generators.** `D=ABC` and
`E=BCD` are both four-letter generators; their words multiply to `AE`, so two factors share one
column and the design is resolution II. `fractional_factorial` refuses to build it instead of
returning a run sheet that looks fine.

### Wave 5 — accuracy: the study passed and the gage is wrong

The same three gages, now measured against five calibrated masters each, twelve readings per
master. The crossed study of wave 1 **cannot see any of this**: every AIAG figure is computed
from differences between readings, so adding a constant to all of them changes nothing. Shifting
all three gages by 1000 units moves the largest of `grr`, `pct_study`, `pct_contribution`,
`pct_tolerance` and `ndc` by at most **9.2e-12** — invariant, not insensitive.

| Gage | Crossed study | Bias at nominal | p | % of tolerance | Linearity slope | Bias span | Span % of tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | **acceptable**, 5.69% tol | **3.9076 g** | 0.0000 | **7.82** | 0.0011 | 0.0456 | 0.09 |
| `PAQUIMETRO-02` | unacceptable, 63.58% tol | 0.0058 mm | 0.7113 | 0.58 | **−0.2205** | **0.1764 mm** | **17.64** |
| `INSPECAO-03` | unacceptable, 62.55% tol | −0.0521 µm | 0.8721 | 0.13 | −0.0132 | 0.4231 | 1.06 |

**Precision and accuracy are independent, and each gage proves a different corner of it.**
`BALANCA-01` passed the crossed study on both criteria and is the worst gage of the three: its
bias is 7.82% of the tolerance against the 5.69% the entire GRR study measured, so the error
nobody looked for is larger than the error everybody computed. `PAQUIMETRO-02` has **no bias at
nominal at all** — p = 0.71 — and the one-point check every procedure prescribes passes a gage
whose offset swings 17.64% of the tolerance across the range, in opposite directions at the two
specification limits. `INSPECAO-03` fails on precision and is accurate, so "recalibrate it" would
change nothing.

**The bias converts into parts.** With a process standard deviation of 8.0 g against a 50 g
tolerance, 99.8222% of production conforms and the gage's own sigma is 0.4743:

| Case | Bias | Guard band | Good parts scrapped | Bad parts shipped |
| --- | --- | --- | --- | --- |
| Calibrated | 0.0000 | — | 161 ppm | 128 ppm |
| **As found** | 3.9076 | — | **3,356 ppm** | **734 ppm** |
| As found, guard banded | 3.9076 | 3.5890 | **13,618 ppm** | 128 ppm |

Scrap multiplied by 20.8 and escapes by 5.7, on a gage whose study said *acceptable*. And the
workaround is worse than the fix: tightening acceptance by 3.5890 g brings escapes exactly back
to the calibrated rate and pays for it with 13,618 ppm of conforming parts — **84.5 times** the
calibrated scrap, 1.36% of everything produced. A calibration costs neither number.

**"The interval contains zero" is not an acceptance rule.** Hold the bias at 0.5 g — 1% of the
tolerance, immaterial — and vary only the gage's precision, over 4,000 simulated twelve-reading
studies per row:

| Gage repeatability | 6σ as % of tolerance | Bias ÷ sd | Called significant |
| --- | --- | --- | --- |
| 0.20 | 2.40 | 2.5000 | **1.0000** |
| 0.56 | 6.72 | 0.8929 | 0.7983 |
| 1.50 | 18.00 | 0.3333 | 0.1893 |
| 4.00 | 48.00 | 0.1250 | **0.0717** |

The better the gage, the more certainly it is rejected for an offset that does not matter — and
the worse the gage, the more easily it passes. The verdict tracks the gage's precision rather than
the consequence, the same anti-correlation with usefulness wave 3 found in the normality
pre-test, which is why `BiasStudy` reports significance and materiality as two separate findings.

### Wave 6 — the window the study was run in, and the plan that follows it

Two questions nobody writes down: **how long does a measurement answer last**, and **what does a
sampling plan actually guarantee**. Both turn out to be answered by a number the form has no field
for.

**A gage study is a snapshot and nothing records the date.** `BALANCA-01`, watched from the day it
was calibrated — four readings on a master every five days for sixty days:

| Figure | Value |
| --- | --- |
| Drift recovered | **+0.105428 g/day** (built in: +0.10) |
| Offset left behind on day 0 | −0.0932 g — the calibration itself was fine |
| Offset on day 60 | **+6.2325 g**, 12.47% of tolerance |
| Interval to 5% of tolerance | **22.8 days** |
| Residual spread around the line | 0.5894 g, against the gage's own 0.56 |

The 4 g offset wave 5 found arrives on **day 37.9** at this rate. A constant bias and a drift
measured late are the same reading and not the same problem: a tare is removed once, a drift buys
an interval.

**And the schedule of a crossed study decides which term the drift lands in.** The same 10 × 3 × 3
study, spread over two weeks, with **identical readings and identical days** — only the day mapping
differs:

| Schedule | EV | AV | GRR | % study | ndc | Dominant source | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| One operator per day | **0.6430** | **1.0081** | 1.1957 | 12.68 | 11 | **reproducibility** | conditional |
| Every operator every day | 0.9161 | 0.3829 | 0.9929 | 10.56 | 13 | repeatability | conditional |
| Drift removed | 0.6430 | 0.4010 | 0.7578 | 8.08 | 17 | repeatability | **acceptable** |

Giving each operator their own day inflates reproducibility **2.51×** and leaves repeatability
untouched to four decimals. The calendar, reported as the people — and a project reading that study
would retrain three operators who did nothing wrong. Interleaving puts the same drift in
repeatability (1.42×) and leaves the operator estimate intact, which is the right place for it and
still not a repeatability. Both drifted schedules come back *conditional* where the instrument on
any single day is *acceptable*: the study's own verdict depends on how long it took to run.

**A sampling plan is a curve, and "inspect ten percent" is the plan whose sample size a shipping
decision chose.** Good lots 0.5% defective, excursions 4.0%:

| Lot size | 10% rule, n | Accepts good lots | Accepts excursions | n=80 good | n=80 excursions |
| --- | --- | --- | --- | --- | --- |
| 100 | 10 | 1.000000 | **0.651631** | 1.000000 | 0.001236 |
| 1,000 | 100 | 0.589832 | 0.013520 | 0.658507 | 0.033206 |
| 20,000 | 2,000 | **0.000026** | ~0 | 0.669115 | 0.037917 |

The same written rule runs from accepting two excursions in three to rejecting 99.997% of
material that is perfectly fine. A fixed sample of eighty holds both numbers steady.

**An acceptance quality level is a producer's risk.** `n=125, c=3` quoted at AQL 1.0% rejects 2.7%
of lots at 1% defective — exactly as advertised — and accepts **47.1%** of lots at 3%. And a zero
acceptance number is not the strict option: matched to the same producer's risk it takes a sample of
**three** and accepts 88.5% of 4% lots, while at the same sample size it rejects **73.9%** of good
production. Discrimination comes from the sample size, not from the acceptance number.

**What each plan bought**, on the same 200 lots (1,478 defective units in total):

| Plan | Units inspected | Excursions caught | Good lots rejected | Defective units shipped |
| --- | --- | --- | --- | --- |
| 10% of the lot, c=0 | 20,000 | **12/12** | **70** | 543 |
| n=125 c=3 (AQL 1.0%) | 25,000 | 9/12 | 0 | **1,098** |
| Designed for 1% vs 4% | 37,800 | **10/12** | **1** | 1,066 |
| No inspection | 0 | 0/12 | 0 | 1,478 |

The published plan inspects 25,000 units and ships three quarters of the defects. The plan that
catches every excursion does it by quarantining more than a third of good production — it is not
discriminating, it is harsh. Sampling sorts lots; it does not change what is in them.

## Examples

| Script | What it shows |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Three gages, three verdicts, and the two acceptance criteria disagreeing on one of them |
| [`02_could_the_pilot_have_found_it.py`](examples/02_could_the_pilot_have_found_it.py) | Three pilots, three non-significant results, three real effects |
| [`03_which_test_and_can_it_be_trusted.py`](examples/03_which_test_and_can_it_be_trusted.py) | The taught flowchart, measured against always using Welch. It loses |
| [`04_the_generator_decides_the_conclusion.py`](examples/04_the_generator_decides_the_conclusion.py) | One experiment, three designs, and a factor that does nothing reported as the second largest |
| [`05_the_gage_passed_and_it_is_wrong.py`](examples/05_the_gage_passed_and_it_is_wrong.py) | The gage the study approved, measured against masters, and what its bias costs in parts |
| [`06_the_study_took_two_weeks.py`](examples/06_the_study_took_two_weeks.py) | A drifting gage: the calibration interval, and the schedule that blames the operators for the calendar |
| [`07_what_the_sampling_plan_guarantees.py`](examples/07_what_the_sampling_plan_guarantees.py) | Five sampling plans on the same two hundred lots, and what each one actually bought |

## Verification

**189 tests, 96% statement coverage, split by cost.** 162 of them run in about ten seconds,
and the whole `make check` sequence — linters, type check, coverage and all — in about eleven. That
is what a push is gated on. The remaining 27 re-derive every figure quoted in a README and run
every example script, in about twelve seconds.

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

The accuracy arithmetic is anchored the same way. The invariance claim is asserted as equality
within floating point rather than within a tolerance, because it is algebra rather than a
measurement. A line fitted to points that lie on a line has to come back exact, a perfect gage has
to misjudge nothing, a centred process has to misjudge symmetrically in both bias directions, and
the guard band has to round-trip to the escape rate it was solved for. The significance simulation
is anchored on its own control: at a bias of zero the t statistic does not depend on the standard
deviation at all, so all four rows have to return the *identical* rejection rate — four merely
similar numbers would mean the rows are not comparable.

The design arithmetic is checked against a 2² whose effects can be read straight off four
numbers (responses 10, 20, 30, 60 give A = 30, B = 20, AB = 10), against the orthogonality of
every column up to five factors, and against the exact-sum identity: a fraction's estimate has to
equal the sum of the full design's estimates of the aliased terms, and it does to 5.3e-15 rather
than to a tolerance. An aliased pair's two estimates are asserted **identical** rather than close,
because they are the same column and any difference at all would mean the contrast is wrong.

The simulations are anchored on their own control cases, which is the only way to test a Monte
Carlo result: where every assumption holds, each of the four procedures has to return the nominal
5%, and the normality check on genuinely normal data has to fire at exactly its own alpha. If
either control drifts, every other figure in that table is wrong in the same direction and none of
them detectably so.

## Related

Statistical process control — control charts, Nelson run rules, capability against
within-subgroup sigma — lives in a sibling repository rather than here. Two repositories holding
the same code under one name would read as padding.

## License

MIT. See [`LICENSE`](LICENSE).

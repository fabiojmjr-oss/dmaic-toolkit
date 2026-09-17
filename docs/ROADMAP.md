# Roadmap

One module per DMAIC phase, so the package reads the way a project runs. A phase is listed here
whether or not it is built; what is *not* built is as much a part of the map as what is.

## Wave 1 — Measure: the gate before every other number

**Measurement system analysis** *(complete — [`dmaic.measure`](../src/dmaic/measure/README.md))*.
A crossed gage study decomposed by two-factor random-effects ANOVA: repeatability,
reproducibility split into operator bias and part-by-operator interaction, part variation, and
the acceptance criteria that follow.

This is first because it is the gate every later number depends on. A capability index, a
before-and-after test and a factorial effect are all computed on readings, and a measurement
system that cannot resolve the parts it measures makes all three noise with a decimal point on.

Three findings the module is built to make visible, all measured on the synthetic dataset:

- **The same gage reads 2.64, 16.24 and 63.58.** Percent contribution, percent study variation and
  percent tolerance are three different ratios, and only the middle one is what the 10% / 30%
  acceptance bands are written for. Reading contribution against those bands turns an unacceptable
  gage into an excellent one, because contribution is study variation squared and squaring a
  fraction moves it toward zero.
- **Pooling the part-by-operator interaction flips the diagnosis.** On `PAQUIMETRO-02` the GRR
  barely moves — 16.24 to 14.63 — while reproducibility goes to exactly zero and the dominant
  source flips from the people to the instrument. The expensive consequence is not the 1.6 points
  of GRR; it is the capital expenditure the number justifies.
- **Splitting GRR is what makes a failed study actionable.** `INSPECAO-03` fails at 64%, with
  reproducibility 3.2× repeatability. Replacing the instrument would change almost nothing.

**One defect of my own, recorded where it happened.** The `interaction_alpha` docstring had its
two override values inverted — it said 0.0 keeps the interaction and 1.0 pools it, when the
comparison is `p_value > alpha` and it is the other way round. The arithmetic was right and the
documentation would have sent a caller to the wrong branch. It was found by using the parameter,
not by reading it, which is the argument for writing the example before publishing the module.

## Wave 2 — Analyze: the test before the test

**Power and sample size** *(complete — [`dmaic.analyze`](../src/dmaic/analyze/README.md))*. Power
from the noncentral t, sample size solved rather than approximated, and the detectable difference
as a first-class output.

This is second because it is the other gate that decides a conclusion before any data is
collected. The commonest failure in an improvement project is not a wrong conclusion, it is a test
with no power concluding "no significant difference" and the project being closed on it — and that
failure is invisible from the output while being entirely predictable beforehand.

Three pilots in the generator, each sized from what was convenient to collect, and the generator
declares the effect it planted. That last part is the whole advantage of synthetic data here: a
real project that finds nothing cannot tell a missed effect from an absent one.

- **All three pilots are non-significant and all three had a real effect**, each failing for a
  different reason. `PILOTO-CICLO` had a 24.6% chance of finding its own 4-minute effect and a
  detectable difference of 8.83 minutes, so `p = 0.9234` is a statement about the study rather
  than the process. `PILOTO-SETUP` was properly designed at 79.1% power and missed anyway, which
  is what 80% power *means* — one failure in five, by construction, and a project treating a
  single non-significant pilot as settled has misread the guarantee it bought. `PILOTO-REFUGO`
  observed a **larger** improvement than the one that existed (3.5 points against a true 2.5) and
  still could not prove it, because detecting 2.5 points off an 8% scrap rate needs **1,568 units
  per arm** against the 200 collected. That last case kills the intuition that a non-significant
  result implies a small effect.
- **Post-hoc power is arithmetic on the p-value.** Observed power is a strictly monotone function
  of it, and at `p = α` the observed power is 0.5035, converging on one half as the study grows
  (0.5114 at n=10, 0.5002 at n=500). "We only had 48% power" is another way of writing "p was just
  above 0.05". `observed_power_is_circular` returns both figures together, and only together, for
  that reason — while the detectable difference uses the sample size and the spread but *not* the
  observed effect, and therefore says something the p-value does not.

**A claim of mine was too strong and the measurement corrected it.** The module docstring first
said the textbook formula `n = 2(z+z)²s²/d²` understates sample size "the more so the smaller the
study", implying a general concern. Measured across the range, it is off by **exactly one
observation per group** from d = 0.1 to d = 1.2, and the power it delivers rounds to the power
asked for. The direction was right and the magnitude was overstated. The honest version, now
published, names where it actually bites: the small confirmation run, where at two standard
deviations the formula asks for 4 per group against the 6 required and delivers 66% power — which
is `PILOTO-SETUP`'s exact situation.

Two test expectations of mine were also wrong rather than the code. I assumed the detectable
difference falls as one over the square root of n; it falls faster (6.68 against √40 = 6.32),
because a small study is penalised twice — fewer observations *and* a wider t quantile. And I
guessed at n = 70 to land in the "marginal" power band, which came out at 0.49938, just
underneath; the verdict bands are now tested on the boundaries themselves rather than on my
arithmetic about where a sample size falls.

**Still to build in this phase:** unequal group sizes in the power calculation, which is a
different calculation rather than a refinement of this one. And multiplicity, which nothing in
the package corrects for.

## Wave 3 — Analyze: the assumptions behind the p-value

**Comparing two groups** *(complete —
[`dmaic.analyze.compare`](../src/dmaic/analyze/README-compare.md))*. Welch's test as the default
rather than the fallback, the assumption checks returned as evidence rather than consulted as a
gate, and a simulator so a project can measure the procedure it intends to standardise on.

The wave exists because the taught flowchart — check normality, check variance, choose
accordingly — is measurably worse than skipping it, and the sample sizes where it is worst are the
ones improvement projects actually collect. Every figure below comes from `type_one_error_rates`
or `normality_test_tradeoff`, under the null, where the nominal rate is 5% by construction.

- **The pooled t-test is wrong in both directions and which one depends on bookkeeping.** 21.30%
  actual type I error with the wider spread on the smaller group; 0.38% when the same inequality
  sits the other way round. Nothing about the process changes — only which group happened to be
  larger. Welch holds 4.77% to 5.07% across every normal scenario and costs nothing under equality
  (4.77% against the pooled test's 4.79%).
- **The flowchart is strictly worse than always using Welch**, at 6.28% against 5.07%, because it
  inherits the pooled test's inflation whenever the variance pre-test happens not to fire. A
  pre-test does not protect a procedure, it launders it.
- **Reaching for a rank test makes it worse.** Mann-Whitney runs at 12.70% with unbalanced groups
  and 6.63% even balanced. It is not a distribution-free t-test; it tests a different hypothesis,
  and unequal spread breaks it too. It is measured here and deliberately *not* wrapped as an API,
  because offering it next to `compare_means` would invite the substitution the simulation argues
  against.
- **The normality check is least informative exactly where it matters most.** Detection of a real
  skew and the cost of that skew move in opposite directions: 16.3% detected at five per group
  where the test runs at 2.40%, and 100% detected at three hundred where the test is already at
  5.22%. Both facts are consequences of small n, which is why they are anti-correlated.
- **The diagnostic cannot see what breaks the test.** Population skewness 3.2629; the algebraic
  ceiling on a sample skewness at ten observations is 2.667, so the estimator cannot report the
  truth even in principle, and the flag fires 39.8% of the time. The spread diagnostic fails the
  same way — drawn from a true ratio of exactly 3.00, the sample ratio's middle 90% runs 1.152 to
  6.762 — and the combined regime flag catches the bad case 75.0% of the time. One miss in four,
  documented as a limitation rather than sold as a safeguard.
- **Two of the four synthetic comparisons are the ones the diagnostic gets wrong.** `LINHA-2` is
  drawn normal and its sample skewness came out at −1.267 on 36 observations, flagging skew that is
  not there; `FORN-X` is drawn from skewness 3.26 and came out at 1.075 on 10, missing the real
  thing. And on `FORN-X vs FORN-Y` the pooled test returns p = 0.0019 against Welch's p = 0.0657 on
  the same forty observations — a factor of **34.6**, with the pooled test reaching the right
  answer for a reason the simulation shows it did not earn.

**I reproduced the bug I was writing about, and the measurement caught it.** The
`materially_skewed` flag first used a bare `abs(skewness) >= 1.0`. On genuinely normal data that
fires at a rate depending entirely on n — 14.21% at ten observations, 1.38% at thirty-six — which
is the same anti-correlation with usefulness the module criticises the normality test for.
Requiring the estimate to clear two of its own standard errors as well caps the small-n end near
alpha; above about twenty the absolute threshold binds again and the rate falls on its own, which
is intended rather than a gap.

**Three test expectations of mine were wrong rather than the code.** I asserted the exact skewness
standard error exceeds the `sqrt(6/n)` approximation; it is the other way round, and by 12.7% at
ten observations, so a criterion built on the approximation is stricter than intended rather than
looser. I asserted the tradeoff's error column is monotone across all six sample sizes; above
fifty it has arrived at alpha and only Monte Carlo noise separates the rows, so asserting
monotonicity there was asserting that noise has a direction. And two draws I picked to demonstrate
the unreliable regime landed on seeds where the diagnostic missed it — which is the 25% miss rate,
met in practice before it was measured.

**One reproducibility defect, twice.** Figures measured by iterating sample sizes from one shared
generator move when the list of sizes changes; dropping `n=50` from a list silently moved every
other row. Both affected tables now use a generator per sample size, so each figure depends only
on `(n, seed)`.

**Still to build in this phase:** more than two groups, where multiplicity stops being a footnote.
Paired and blocked comparisons. And the regimes the simulation does not cover — heavy tails
without skew, bimodality, and measurements rounded to a coarse gauge.

## Wave 4 — Analyze: the design decides the conclusion

**Full and fractional factorials** *(complete —
[`dmaic.analyze.factorial`](../src/dmaic/analyze/README-factorial.md))*. Designs built from
generators that have to be written down, the defining relation closed rather than assumed, the
alias structure as a first-class output, and effects returned with what each one is a sum of.

The wave exists because the taught summary of a fraction understates it. "A resolution III design
confounds main effects with two-factor interactions" is true and sounds statistical, as though the
estimate came back with extra uncertainty on it. It does not. It comes back as the **exact
arithmetic sum** of the two, so a factor with no effect at all reports the interaction's as its
own — a large, clean-looking, entirely fictitious main effect, with nothing in the output to say
so.

One synthetic experiment carries the argument: a curing oven, four factors, sixteen runs, and two
of the four factors set to exactly zero. The fractions select rows of those sixteen runs rather
than being generated separately, so the comparison holds the data fixed and varies only the
generator.

- **The resolution III half fraction reports 9.4067 for a factor whose effect is exactly zero.**
  Resin batch comes back as the second largest figure in the study, 1.88 times the real pressure
  effect and 2.63 times the smallest effect eight runs could have detected. The two fractions cost
  the same eight runs and read the same experiment, and they rank the factors differently: `D=ABC`
  gives A, B, D, C and `D=AB` gives A, **D**, B, C. Only the generator differs, and choosing it is
  free.
- **The aliasing is an addition, verified as one.** `D + AB` is 1.5494 + 7.8573 = 9.4067, and every
  alias pair of both fractions reproduces the full design's sum to 5.3e-15 — floating-point noise,
  not statistical agreement. That is also why the good fraction is nearly free: `D=ABC` adds two
  numbers too, and one of them is zero. It recovers the interaction at 7.7678 against the full
  sixteen runs' 7.8573.
- **A detection limit protects against noise and has no opinion about bias.** Eight runs can see
  3.5711 MPa at this process's spread, sixteen can see 2.2600, and the largest purely spurious
  estimate in the full design is 1.5494 — correctly below the limit, so a project would leave it
  alone. The false 9.4067 is at 2.63 times the limit, because it is a real effect in the wrong
  column.
- **The resolution comes from the defining relation, not from the shortest generator.** `D=ABC`
  and `E=BCD` are both four-letter generators; their words multiply to `AE`, two factors on one
  column, resolution II. `fractional_factorial` refuses to build it rather than returning a run
  sheet that looks like resolution IV.

**A defect of my own, of exactly the kind this module is about.** A word of the defining relation
has a constant contrast column, so the contrast computed on it is twice the grand mean rather than
an effect of anything. The first version filtered the identity out of the alias list, which made
`ABD` look like the one clean, estimable term in the resolution III design and gave it an
"estimate" of 79.93 — a number that is not what its label says, which is the module's own
accusation turned on itself. It was found by printing the alias table in the example, not by
reading the code. The identity is now a first-class alias and such an effect returns `nan`.

**And a gap in the earlier waves, closed here.** Wave 3's comparison table had no reproducibility
pin of its own, so the stream-order tripwire was covering three of the four generator tables. All
four first values are now pinned in one test.

**Still to build in this phase:** centre points, so curvature is not invisible. Randomisation and
blocking, which the module documents as the caller's problem rather than solving. Replication and
the error estimate it buys. And the normal plot of effects, which is the conventional answer to an
unreplicated design and deserves measuring rather than adopting.

## Wave 5 — Measure: what a gage study cannot tell you

**Accuracy against a reference** *(complete —
[`dmaic.measure.accuracy`](../src/dmaic/measure/README-accuracy.md))*. Bias and linearity against
calibrated masters, the significance and the materiality of an offset reported as two separate
findings, and the consequence converted into conforming parts scrapped and nonconforming parts
shipped.

The wave exists because a crossed gage study is not a weak test of accuracy, it is **invariant**
to it. Repeatability, reproducibility and part variation are all computed from differences between
readings, so adding a constant to every reading in a study leaves every AIAG figure exactly
unchanged — shifting all three synthetic gages by 1000 units moves the largest of them by 9.2e-12,
which is floating point rather than sensitivity. Accuracy needs a value from outside the study,
and that is what this wave puts into the generator.

The same three gages are now measured against five masters each, twelve readings per master, with
the offset the generator built in declared.

- **`BALANCA-01` passed wave 1 on both criteria and is the worst gage of the three.** Its bias is
  3.9076 g, **7.82% of the tolerance**, against the 5.69% that the entire GRR study measured. The
  error nobody looked for is larger than the error everybody computed.
- **`PAQUIMETRO-02` has no bias at nominal at all** — 0.58% of tolerance, p = 0.7113 — so the
  one-point check every procedure prescribes passes it. Across its range the offset swings 0.1764
  mm, **17.64% of the tolerance**, in opposite directions at the two specification limits.
  Averaging bias over a range is how a gage with two large errors reports none.
- **`INSPECAO-03` fails on precision and is accurate.** No bias, no slope. "Recalibrate it" would
  change nothing, which is wave 1's split of GRR into repeatability and reproducibility arriving
  at the same place in different units.
- **The bias converts into parts, and the workaround costs more than the fix.** 3,356 ppm of
  conforming parts scrapped against 161 ppm calibrated, and 734 ppm of nonconforming parts shipped
  against 128. A guard band of 3.5890 g brings escapes exactly back to the calibrated rate and
  pays for it with 13,618 ppm of scrap — **84.5 times** the calibrated rate, 1.36% of everything
  produced. A calibration costs neither number, and without measuring the bias the guard band
  looks like diligence.
- **"The confidence interval contains zero" is not an acceptance rule.** Holding a 0.5 g offset
  fixed — 1% of tolerance, immaterial — and varying only the gage's precision, the rule flags it
  100% of the time on a precise gage and 7.17% on a sloppy one. The verdict is driven by the
  gage's repeatability rather than by the consequence, which is the same anti-correlation with
  usefulness wave 3 measured in the normality pre-test. `BiasStudy` therefore reports
  `significant` and `material` separately, including the uncomfortable combination.

**Three defects of my own, all in the same place, all found by the noiseless control cases.** A
gage that reads the master identically every time has zero standard error, which is not a
pathological input — a digital indicator displaying the same digit does it routinely. The first
version divided by it. The same limit had to be taken twice more: a line fitted through points
that lie exactly on a line has a slope standard error of zero, and returning `nan` there made
`significant` false and produced the verdict "no linearity error detected" next to a slope of 0.5
— a number contradicting its own label, which is precisely what this module accuses a passed GRR
study of. And `detectable_bias` refused the zero standard deviation that `verdict()` then asked it
for. All three limits are well defined and all three are now taken explicitly. Tests with
realistic noise would never have found any of them.

**One piece of dead code, removed rather than covered.** `guard_band` raised when no guard band
could reach the target escape rate. Closing the acceptance window drives escapes to zero, so that
branch is unreachable for any representable target: a width always exists, and feasibility is
never the question. Cost always is, which is the more useful thing to say.

**The one-sample case needed no new arithmetic.** A one-sample t-test has the same degrees of
freedom and the same noncentrality as the paired test wave 2 already built, so `detectable_bias`
solves `power_paired` rather than reimplementing the noncentral t.

**Stability was the declared gap here and wave 6 closed it**, including the part that was not
anticipated: the duration of a study is a parameter of its answer, and so is the *order* the
sessions were run in. What remains in this phase is nested designs, for destructive testing where
no two operators can measure the same part, and attribute agreement, where the measurement is a
judgement rather than a number.

## Wave 6 — the window a study was run in, and the plan that follows it

**Stability** *(complete —
[`dmaic.measure.stability`](../src/dmaic/measure/README-stability.md))* and **acceptance
sampling** *(complete — [`dmaic.control`](../src/dmaic/control/README.md))*. Two questions nobody
writes down, and both turn out to be answered by a field no form has.

Stability closes the gap wave 5 declared. A gage study and a bias study are snapshots, and nothing
on either form records how far the day of the readings sits from the last calibration.

- **`BALANCA-01` drifts 0.105428 g a day** (0.10 built in), so five percent of its tolerance is
  spent in **22.8 days** and the offset reaches 12.47% of tolerance by day 60. The offset left
  behind on day zero is −0.0932 g: the calibration was fine, and the instrument does not stay
  where it was put. The residual spread around the fitted line, 0.5894, lands on the gage's own
  repeatability of 0.56, which is the check that this is a drift rather than scatter given a slope.
- **The 4 g offset of wave 5 arrives on day 37.9 at this rate.** That is a construction of the
  generator rather than a discovery — 4.0 ÷ 0.10 is exactly 40 — and it is the point worth
  carrying out of both waves. A constant bias and a drift measured late are the same reading and
  not the same problem: a tare is removed once, a drift buys an interval.
- **The schedule of a crossed study decides which ANOVA term the drift lands in.** Identical
  readings, identical days, and only the day mapping differs. Give each operator their own day and
  reproducibility inflates **2.51×** while repeatability does not move at all to four decimals: the
  calendar, reported as the people, and a project reading it would retrain three operators who did
  nothing wrong. Interleave and the same drift goes into repeatability (1.42×) with the operator
  estimate almost intact — the right place for it, and still not a repeatability, since the term is
  now carrying two weeks. Both drifted schedules come back *conditional* where the instrument on
  any single day is *acceptable*.
- **That second finding needed no new function**, which is its point: the evidence is in a study
  the project has already run, as long as somebody wrote down the date.

Acceptance sampling opens the Control phase, and the phase is narrower than it looks for the reason
set out below: charts are not here.

- **"Inspect ten percent" controls nothing.** The only number in the rule that matters is the
  sample size, and it is set by the lot size — a shipping decision. The same written rule accepts
  **65.2%** of excursion lots on a lot of a hundred and rejects **99.997%** of perfectly good
  material on a lot of twenty thousand. A fixed sample of eighty holds both figures steady across
  every lot size above five hundred, which is the property the percentage rule is assumed to have.
- **An acceptance quality level is a producer's risk, not a promise.** `n=125, c=3` quoted at AQL
  1.0% rejects 2.7% of lots at 1% defective, exactly as advertised, and accepts **47.1%** of lots at
  three times that level. The average outgoing quality column says the rest: it has a maximum, so a
  plan bounds outgoing quality above zero rather than improving it.
- **A zero acceptance number is not the strict option.** Matched to the same producer's risk it
  takes a sample of **three** and accepts 88.5% of 4% lots; held at the same sample size it rejects
  **73.9%** of good production. Discrimination comes from the sample size, and the acceptance number
  is not a strictness dial.
- **What the inspection bought, on 200 real lots.** The published plan inspects 25,000 units and
  ships 1,098 of 1,478 defectives. The plan that catches every excursion quarantines 70 good lots
  out of 188 — not discriminating, just harsh. Designing to both quality levels catches 10 of 12
  excursions while rejecting one good lot, and costs 37,800 units inspected. That is the trade,
  priced.

**A fourth instance of a defect I had already fixed twice.** Wave 5 handled a fitted standard error
of exactly zero. `scipy` returns **`nan`** when the response is constant, which is what a perfectly
stable gage and a perfectly flat linearity line both produce — so the guard missed both, and
`accuracy.linearity_study` was still returning `nan` for a p-value after its fix was published. The
wave-5 test hid it by asserting the verdict string rather than the p-value. The limit now lives in
one place, `dmaic._limits.slope_p_value`, and both modules take it there.

**And one `assert` removed from library code.** `matched_plan` searched for the best sample size
with the result starting as ``None`` and an assertion that the loop had run. The assertion was true
and it was also the wrong shape: an assert is compiled out under optimisation, so a guarantee that
matters cannot live in one. The search now starts from the smallest valid plan and the impossible
case — an acceptance number larger than the lot — raises with a message that names it.

**A test expectation of mine was wrong rather than the code.** I asserted the average outgoing
quality reaches zero at a high incoming defective level. It does not: a 12% lot is still accepted
about once in two thousand times, so the figure falls away without arriving.

**Still to build in this phase:** double and sequential sampling plans, which reach the same two
risk points with a smaller average sample. Switching rules, which is where most of a published
scheme's protection actually comes from. And attribute agreement, where the measurement is a
judgement rather than a number — the gap that makes every sampling figure conditional on an
inspector nobody studied.

## Wave 7 — Improve: was the saving yours, and is it cash?

**Benefit realisation** *(complete — [`dmaic.improve`](../src/dmaic/improve/README.md))*. The
before-and-after comparison a project reports, the difference in differences that removes the trend
from it, the selection artefact priced against baseline length, and a benefit case that keeps cash
and capacity apart.

The wave exists because a project's reported saving is the sum of three things and only one of them
is the project. Twenty sites over twenty-four months, five improved from month thirteen, with the
effect and the trend both declared.

- **The project reports twice what it delivered.** −10.0637 against a true −5.00, and the surplus
  is the trend of −0.40 a period that the untreated sites also enjoyed. This is not imprecision: a
  before-and-after number contains the trend in full, no amount of data narrows it away, and the
  error is always in the flattering direction.
- **A comparison group removes it without modelling it.** The difference in differences lands at
  −4.2241 with an interval of −5.2545 to −3.1938, which contains the effect that was applied. Off
  by chance rather than by construction — the only kind of wrong more sites fix.
- **The unit of analysis is the site, not the site-period.** Twenty sites over twenty-four months
  is twenty observations of a change, not four hundred and eighty, and the test behind the estimate
  is Welch's on site-level changes. Treating site-periods as independent is how this estimator
  arrives at a p-value three orders of magnitude too small.
- **Chartering on the worst performer manufactures an improvement from nothing.** With no effect and
  no trend at all, taking the worst five of twenty sites on a one-period baseline shows −4.3401 —
  **87% of a real five-unit improvement**, in sites where nothing was done. Random selection returns
  zero at every baseline length, which is the control. And the remedy is free: twelve periods of
  baseline bring the artefact to −0.4562 and twenty-four to −0.2294.
- **The money gap is a product of two factors nobody writes down.** The charter books 7,245,895
  gross; the project produced 1,260,000 of cash. 5.75×, which is exactly 2.01× for attribution times
  2.86× for the share of a modelled cost that is avoidable rather than freed capacity.
  `BenefitCase` reports gross and cash separately and declines to add them up: a project that books
  capacity as cash is not wrong about the process, it is wrong about the bank account.

**A defect of my own, and it is wave 3's own argument turned on me.** `difference_in_differences`
gets its p-value from `compare_means`, whose assumption checks *raise* on a group with no spread or
with fewer than three observations. So a noiseless panel, or a project with two treated sites,
crashed instead of returning an estimate — and the estimate is a difference of two averages that
depends on no diagnostic at all. Wave 3's thesis is that the checks are evidence rather than a gate;
a check that raises is a gate by another name. The estimate now comes back either way, with
`untested_because` saying why no test came with it.

**Still to build in this phase:** staggered adoption, where sites start at different times and a
two-by-two is the wrong shape. An effect that grows or decays after the change rather than stepping.
And the parallel-trends check itself, which is computable from the same panel and is the assumption
the whole estimator rests on.

## Wave 8 — Define: the charter, as arithmetic

**A computable charter** *(complete — [`dmaic.define`](../src/dmaic/define/README.md))*. The problem
statement's baseline window as the free parameter it is, the entitlement read twice, a CTQ tree whose
arithmetic is checked against the gap it decomposes, and a benefit case built by the same class the
Improve phase audits it with.

The wave is the mirror image of wave 7. A project is chartered *from* a recent baseline and *towards*
the best site's observed performance. The worst performer of a short window was partly unlucky and
comes back up on its own; the best performer of the same window was partly lucky and goes back down.
A charter therefore takes the most inflated estimate available at **both** ends of its gap, and the
two errors add rather than cancel.

- **The same twelve months support a gap of 18.79 or 13.87**, depending on a baseline window that no
  charter template has a field for. And the spread between sites — the figure a harmonisation
  programme is justified with — reads **46% larger on one period than on twelve**.
- **A quarter of a one-period entitlement gap does not exist.** 18.63 claimed against 14.86 there,
  because the minimum of twenty noisy averages sits below the minimum of twenty true levels always,
  and by a predictable amount. The arithmetic is right; the estimator is the problem.
- **Shrinking the best site toward the average errs the other way**, at 11.92, and that is the useful
  result rather than a failed fix: the truth sits between the two in every window tried. Quote one
  and you have chosen a direction; quote both and you have stated a range, which narrows from
  11.92–18.63 on one period to 14.89–15.23 on twenty-four.
- **The CTQ tree over-attributes by 1.12×** — the same saving under more than one name — and **22% of
  its claim sits under leaves that name no measurand**, which is the share nobody will be able to
  verify after the project closes. It will be claimed anyway, because by then the only figure
  available is the total.
- **The promise and the audit share one class.** `Charter.benefit_case()` returns wave 7's
  `BenefitCase`, so a charter cannot compute its benefit differently from the way it will be
  verified.

**A defect of my own, and an embarrassing one.** `entitlement` shipped a ternary whose two branches
were identical — leftover drafting, selecting the minimum either way — which meant the function
silently assumed lower is better and would have named the *worst* site as the entitlement for a
yield, an on-time rate or any measurand that runs upwards. It is now a stated parameter with a test
on both directions, and the same parameter was missing from `gap_by_window`.

**And a lesson about patching rather than reading.** The fix above failed to apply the first time
because a formatter had already rewrapped the line I was matching on, and the failed patch was in a
script whose later steps ran anyway. The measurement that followed looked correct because it used the
defaults. Verifying the patch rather than the output is what caught it.

**Still to build in this phase:** a parallel-trends check on the baseline window, which is computable
from the same panel and is the assumption wave 7's estimator rests on. Disjointness in a CTQ tree,
which `overattribution` only catches when the double counting pushes the total past the gap. And the
stakeholder side of Define, which is not arithmetic and is not pretended to be here.

## Wave 9 — Control: the rest of the plan

*Not built.* Control plans as documents that carry arithmetic, and sustaining verification —
whether the gain held, measured against a counterfactual rather than against last quarter.

**Control charts remain out of scope.** Charts, Nelson run rules and capability against
within-subgroup sigma already exist in the sibling `oplab.spc` package. Reimplementing them here
would put the same code in two repositories under one name, which reads as padding to anyone who
opens both. This toolkit references it instead, and wave 6's sampling module says explicitly that
acceptance sampling is not a substitute for it.

## Cross-cutting

These are not tools and they matter more than an extra one:

- **One seeded generator** feeding every module, so examples compose and no test needs its own
  fixture. In place.
- **Stream-order discipline** in the generator: new tables are appended, never inserted, so a
  figure published in an earlier wave keeps reproducing byte-for-byte.
- **Every figure quoted in any README is asserted in `tests/test_readme_claims.py`.** A change
  that moves a published number breaks the build instead of leaving the text quietly wrong.
- **Repo-level claims are asserted too**, in `tests/test_readme_meta.py`: test counts, module
  tables, bilingual coverage, no placeholder tokens left in any Markdown.
- **CI split by cost**: a fast gate on a version matrix, and the figure verification once.

## Conventions

- Code, docstrings and commits in English; README in English and Portuguese.
- Public functions are typed and have a docstring that states what the function decides on the
  caller's behalf.
- No tool ships without tests against hand-computed values, not only against its own output. The
  gage ANOVA is verified against a 2×2×2 design whose sums of squares are integers.
- A function refuses rather than returns a number when its assumptions do not hold. An unbalanced
  design raises; it does not get silently decomposed.
- No real operational data, ever. See [`../DISCLAIMER.md`](../DISCLAIMER.md).
- **One branch and one pull request per wave**, titled for the decision it delivers rather than
  for its first commit.

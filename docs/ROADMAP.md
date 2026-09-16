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

## Wave 2 — Measure: what a gage study cannot tell you

*Not built.* GRR measures precision, not accuracy: a gage can be perfectly repeatable and
consistently wrong. Bias, linearity and stability studies need a reference standard, which means
the generator needs one too. Also nested designs, for destructive testing where no two operators
can measure the same part.

## Wave 3 — Analyze: the test before the test

*Not built.* Sample size and power. The commonest failure in improvement projects is not a wrong
conclusion, it is a test with no power concluding "no significant difference" and the project
being closed on it. A toolkit that computes the power of a comparison *before* it is run answers
a question most of them only answer afterwards.

Then hypothesis tests with their assumptions checked rather than assumed: normality, equal
variance, and what to do when they fail.

## Wave 4 — Analyze: design of experiments

*Not built.* Full and fractional factorials, aliasing and resolution, main effects and
interactions. The point of interest is the same as wave 1's: a resolution-III design cannot
separate a main effect from a two-factor interaction, and a run sheet that does not say so is
selling a conclusion it cannot support.

## Wave 5 — Define and Improve

*Not built.* Define artifacts that carry arithmetic rather than formatting — a charter whose
benefit case is computable, CTQ trees with measurable leaves. Improve: pilot design, and
benefit realisation measured against a counterfactual rather than against last quarter.

## Wave 6 — Control: the plan, not the chart

*Not built, and deliberately narrower than it looks.* Control plans, sampling plan design and
sustaining verification — whether the gain held, measured.

**Control charts are not in scope.** Charts, Nelson run rules and capability against
within-subgroup sigma already exist in the sibling `oplab.spc` package. Reimplementing them here
would put the same code in two repositories under one name, which reads as padding to anyone who
opens both. This toolkit references it instead.

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

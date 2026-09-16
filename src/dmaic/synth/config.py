"""Every number the generator uses, in one place.

The values are invented. No operation's data is used anywhere in this repository - see
``DISCLAIMER.md`` - and the gage names, operator names and part numbers are labels, not
references to anything real.

Two conventions matter for reproducibility:

**Stream order is part of the contract.** Each table draws from the shared generator in a fixed
order, so appending a new table at the end of :func:`dmaic.synth.generate_dataset` leaves every
earlier table byte-identical. A figure published against an earlier wave keeps reproducing.

**The three gages are chosen to disagree.** A measurement system is judged against the process
spread and against the specification, and those two verdicts are not the same verdict.
``PAQUIMETRO-02`` is deliberately built so that they part company: marginal against the process,
hopeless against the tolerance. A generator where every gage is uniformly good or uniformly bad
would let a wrong reading of the acceptance rules pass unnoticed.
"""

from __future__ import annotations

from dataclasses import dataclass

SEED = 42

PARTS = 10
OPERATORS = ("OP-A", "OP-B", "OP-C")
REPLICATES = 3


@dataclass(frozen=True)
class GageProfile:
    """One measurement system, described by the variation it is built to contain.

    Attributes:
        gage: Label for the measurement system.
        measurand: What it measures, for the axis label of any chart.
        unit: Unit of measure.
        nominal: Centre of the part population.
        part_sd: Standard deviation of the true part values, which is the process variation the
            gage has to resolve.
        repeat_sd: Repeatability - the spread of one operator measuring one part twice.
        operator_sd: Reproducibility from operator bias - a constant offset per operator.
        interaction_sd: Reproducibility from the part-by-operator interaction - an offset that
            depends on which operator measures which part. Kept separate from ``operator_sd``
            because the two have different fixes: a bias is a calibration or a habit, while an
            interaction means operators diverge on some parts and not others.
        lsl: Lower specification limit.
        usl: Upper specification limit.
    """

    gage: str
    measurand: str
    unit: str
    nominal: float
    part_sd: float
    repeat_sd: float
    operator_sd: float
    interaction_sd: float
    lsl: float
    usl: float

    @property
    def tolerance(self) -> float:
        """Width of the specification band."""
        return self.usl - self.lsl


# Targets, not outcomes: these are the population parameters, and the realised study statistics
# differ from them by sampling error. The tests pin the realised values.
GAGES = (
    # Adequate on both criteria. Repeatability dominates, which is the instrument rather than
    # the people, and there is little left to win.
    GageProfile(
        gage="BALANCA-01",
        measurand="peso liquido",
        unit="g",
        nominal=500.0,
        part_sd=8.0,
        repeat_sd=0.56,
        operator_sd=0.28,
        interaction_sd=0.14,
        lsl=475.0,
        usl=525.0,
    ),
    # The instructive one. Marginal against the process spread and unacceptable against the
    # tolerance, because the specification is tight relative to how the parts actually vary.
    # Its reproducibility is mostly interaction rather than bias, so a study that pools the
    # interaction into repeatability reports a smaller number than the gage deserves.
    GageProfile(
        gage="PAQUIMETRO-02",
        measurand="diametro externo",
        unit="mm",
        nominal=25.0,
        part_sd=0.40,
        repeat_sd=0.060,
        operator_sd=0.030,
        interaction_sd=0.089,
        lsl=24.5,
        usl=25.5,
    ),
    # Unacceptable, and diagnosably so: reproducibility is three times repeatability, so the
    # instrument is not the problem and buying a better one would change nothing.
    GageProfile(
        gage="INSPECAO-03",
        measurand="espessura de camada",
        unit="um",
        nominal=80.0,
        part_sd=6.0,
        repeat_sd=1.20,
        operator_sd=2.60,
        interaction_sd=2.70,
        lsl=60.0,
        usl=100.0,
    ),
)


@dataclass(frozen=True)
class TrialProfile:
    """One two-arm improvement trial.

    Attributes:
        trial: Label for the pilot.
        measurand: What was measured.
        unit: Unit of measure, or ``"proportion"`` for a pass/fail count.
        kind: ``"continuous"`` or ``"binary"``.
        n_per_arm: Observations collected in each arm - the sample size the project actually ran,
            not the one it should have run.
        baseline: Mean, or probability, of the baseline arm.
        true_effect: The effect put into the improved arm, signed. Negative is an improvement for
            every measurand here, because all three are things you want less of.
        sd: Within-arm standard deviation for a continuous trial; ``nan`` for a binary one, where
            the spread is determined by the probability.
    """

    trial: str
    measurand: str
    unit: str
    kind: str
    n_per_arm: int
    baseline: float
    true_effect: float
    sd: float


# Each trial is sized the way projects are actually sized - from what was convenient to collect -
# and each lands in a different place once the power is computed. That spread is the point: a
# generator where every study was underpowered would make the finding look like a property of the
# data rather than of the sample sizes.
TRIALS = (
    # Sized by the month it was convenient to run. A real 4% improvement, and a study that will
    # miss it three times in four.
    TrialProfile(
        trial="PILOTO-CICLO",
        measurand="tempo de ciclo",
        unit="min",
        kind="continuous",
        n_per_arm=30,
        baseline=100.0,
        true_effect=-4.0,
        sd=12.0,
    ),
    # The confirmation run: five parts per arm, because the expected effect is large. Almost
    # adequate, and the case where the textbook shortcut would have under-sized it materially.
    TrialProfile(
        trial="PILOTO-SETUP",
        measurand="tempo de setup",
        unit="min",
        kind="continuous",
        n_per_arm=5,
        baseline=45.0,
        true_effect=-6.0,
        sd=3.0,
    ),
    # Scrap from 8% to 5.5% - an ordinary project target on an extraordinary sample requirement,
    # because the information in a proportion is thin when the proportion is small.
    TrialProfile(
        trial="PILOTO-REFUGO",
        measurand="taxa de refugo",
        unit="proportion",
        kind="binary",
        n_per_arm=200,
        baseline=0.08,
        true_effect=-0.025,
        sd=float("nan"),
    ),
)


@dataclass(frozen=True)
class ComparisonProfile:
    """Two groups someone wants compared, and the regime the comparison falls into.

    Attributes:
        comparison: Label for the question being asked.
        question: What the comparison is for, in words.
        unit: Unit of measure.
        first: Name of the first group.
        second: Name of the second group.
        n_first: Observations in the first group.
        n_second: Observations in the second group.
        mean_first: Population mean of the first group.
        mean_second: Population mean of the second group. Equal to ``mean_first`` where the
            comparison is drawn under the null, so that a rejection is a known false positive.
        sd_first: Population spread of the first group.
        sd_second: Population spread of the second group.
        shape: ``"normal"`` or ``"skewed"``.
        regime: What makes this comparison instructive - recorded so the example does not have
            to rediscover it, and so a change to the parameters that moves a comparison out of
            its regime shows up as a broken test rather than as quieter prose.
    """

    comparison: str
    question: str
    unit: str
    first: str
    second: str
    n_first: int
    n_second: int
    mean_first: float
    mean_second: float
    sd_first: float
    sd_second: float
    shape: str
    regime: str


# Four comparisons, chosen so the taught flowchart and Welch's test disagree in different ways.
# Two are drawn under the null - the group means are identical - so any significant result is a
# false positive that can be named as one rather than argued about.
COMPARISONS = (
    # The clean case. Everything agrees, which is what makes it the control: a module that
    # disagreed with the flowchart everywhere would be suspect.
    ComparisonProfile(
        comparison="TURNO-A vs TURNO-B",
        question="os dois turnos produzem no mesmo tempo de ciclo?",
        unit="min",
        first="TURNO-A",
        second="TURNO-B",
        n_first=25,
        n_second=25,
        mean_first=100.0,
        mean_second=100.0,
        sd_first=6.0,
        sd_second=6.0,
        shape="normal",
        regime="balanced and normal - every procedure holds its level",
    ),
    # Unequal spread on unequal sizes, with the wider spread on the smaller group: the case
    # where the pooled test's false-positive rate is four times its nominal level.
    ComparisonProfile(
        comparison="LINHA-1 vs LINHA-2",
        question="a linha nova reduziu o tempo de ciclo?",
        unit="min",
        first="LINHA-1",
        second="LINHA-2",
        n_first=12,
        n_second=36,
        mean_first=100.0,
        mean_second=100.0,
        sd_first=9.0,
        sd_second=3.0,
        shape="normal",
        regime="wider spread on the smaller group - the pooled test inflates",
    ),
    # The mirror image: the wider spread on the larger group, where the pooled test becomes
    # absurdly conservative instead. Same violated assumption, opposite consequence.
    ComparisonProfile(
        comparison="CELULA-X vs CELULA-Y",
        question="a celula reformada mudou o tempo de ciclo?",
        unit="min",
        first="CELULA-X",
        second="CELULA-Y",
        n_first=12,
        n_second=36,
        mean_first=100.0,
        mean_second=100.0,
        sd_first=3.0,
        sd_second=9.0,
        shape="normal",
        regime="wider spread on the larger group - the pooled test goes conservative",
    ),
    # Skew, unequal spread and unequal sizes together, with a real difference in the means. The
    # regime where no standard procedure holds its level, so the p-value cannot carry the claim
    # whichever test produces it.
    ComparisonProfile(
        comparison="FORN-X vs FORN-Y",
        question="o fornecedor alternativo entrega mais rapido?",
        unit="dias",
        first="FORN-X",
        second="FORN-Y",
        n_first=10,
        n_second=30,
        mean_first=14.0,
        mean_second=12.0,
        sd_first=6.0,
        sd_second=2.0,
        shape="skewed",
        regime="skew, unequal spread and unequal sizes - nothing holds its level",
    ),
)

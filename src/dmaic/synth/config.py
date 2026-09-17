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


@dataclass(frozen=True)
class FactorSetting:
    """One factor of a designed experiment, and the two levels it was run at.

    Attributes:
        name: Factor name, as it appears in the run sheet.
        unit: Unit of the factor's own setting, not of the response.
        low: The low level, coded -1.
        high: The high level, coded +1.
    """

    name: str
    unit: str
    low: float
    high: float


@dataclass(frozen=True)
class FactorialProfile:
    """One designed experiment, with the effects that are actually in the process declared.

    Attributes:
        process: Label for the experiment.
        response: What was measured.
        unit: Unit of the response.
        settings: The factors, in the order the design's letters refer to them.
        baseline: Mean response at the centre of the design.
        true_effects: Effect of each term, keyed by the design's letters - ``"A"`` for a main
            effect, ``"AB"`` for a two-factor interaction. An effect is the change in the
            response from the low level to the high level, so the coefficient is half of it.
            Terms left out are exactly zero.
        noise_sd: Run-to-run standard deviation of the response.
    """

    process: str
    response: str
    unit: str
    settings: tuple[FactorSetting, ...]
    baseline: float
    true_effects: tuple[tuple[str, float], ...]
    noise_sd: float

    @property
    def factors(self) -> tuple[str, ...]:
        """Factor names in letter order, for handing straight to a design constructor."""
        return tuple(setting.name for setting in self.settings)


# One experiment, four factors, and a truth chosen so the generator choice is what decides the
# conclusion. Two factors do nothing at all: the cure time because the oven is already past the
# point where longer helps, and the resin batch because it was only in the experiment to answer a
# suspicion. Their being exactly zero is what makes a fraction's arithmetic visible - an effect
# reported for either of them is entirely an artefact of the design, not a small real effect
# mixed with noise.
#
# The interaction is the large one on purpose. Temperature and pressure together are worth more
# than pressure alone, which is the ordinary situation a one-factor-at-a-time study cannot see,
# and it is also exactly the term a resolution III half fraction hands to whichever factor its
# generator happens to alias it with.
FACTORIALS = (
    FactorialProfile(
        process="FORNO-CURA",
        response="resistencia ao cisalhamento",
        unit="MPa",
        settings=(
            FactorSetting(name="temperatura", unit="degC", low=150.0, high=180.0),
            FactorSetting(name="pressao", unit="bar", low=2.0, high=4.0),
            FactorSetting(name="tempo de cura", unit="min", low=20.0, high=40.0),
            FactorSetting(name="lote de resina", unit="lote", low=1.0, high=2.0),
        ),
        baseline=40.0,
        true_effects=(
            ("A", 12.0),
            ("B", 5.0),
            ("C", 0.0),
            ("D", 0.0),
            ("AB", 8.0),
        ),
        noise_sd=1.5,
    ),
)


@dataclass(frozen=True)
class ReferenceProfile:
    """One gage measured against calibrated masters, so its accuracy can be talked about.

    The gage is one of :data:`GAGES` rather than a new instrument, which is the point: the
    crossed study and the reference study are two properties of the same measurement system, and
    the interesting cases are where the two verdicts disagree.

    Attributes:
        gage: Must name a profile in :data:`GAGES`, whose nominal and repeatability are reused.
        references: The accepted values of the masters, spanning the specification.
        repeats: Readings taken on each master.
        bias_at_nominal: Systematic offset at the centre of the range, signed.
        bias_slope: Change in bias per unit of reference away from nominal. Non-zero means the
            gage is non-linear: the offset it adds depends on what it is measuring, so a bias
            study at one point cannot stand in for the range.
    """

    gage: str
    references: tuple[float, ...]
    repeats: int
    bias_at_nominal: float
    bias_slope: float


# Three reference studies, chosen so that precision and accuracy come apart in all three
# directions. The crossed study of wave 1 is invariant to every one of these biases - adding a
# constant to every reading leaves each AIAG figure unchanged - so nothing below is visible from
# the study that already passed or failed these gages.
REFERENCES = (
    # The uncomfortable one. BALANCA-01 passed wave 1 on both criteria, and it weighs 4 g heavy
    # at every point in its range: a tare left in, which is the commonest bias there is. The
    # offset is 8% of the tolerance, larger than the entire 5.69% the GRR study measured.
    ReferenceProfile(
        gage="BALANCA-01",
        references=(480.0, 490.0, 500.0, 510.0, 520.0),
        repeats=12,
        bias_at_nominal=4.0,
        bias_slope=0.0,
    ),
    # Zero bias at nominal and unusable anyway. The offset runs from +0.08 mm at the bottom of
    # the range to -0.08 mm at the top, so the one-point check every procedure prescribes - take
    # a master near nominal, ten readings, test the mean - passes a gage that misjudges parts at
    # both specification limits, in opposite directions.
    ReferenceProfile(
        gage="PAQUIMETRO-02",
        references=(24.6, 24.8, 25.0, 25.2, 25.4),
        repeats=12,
        bias_at_nominal=0.0,
        bias_slope=-0.20,
    ),
    # The control, and the other disagreement: accurate and imprecise. It failed wave 1 at 64%
    # study variation with no bias and no linearity error at all, which is why "the gage is bad"
    # is not a diagnosis and "recalibrate it" would change nothing here.
    ReferenceProfile(
        gage="INSPECAO-03",
        references=(64.0, 72.0, 80.0, 88.0, 96.0),
        repeats=12,
        bias_at_nominal=0.0,
        bias_slope=0.0,
    ),
)


@dataclass(frozen=True)
class DriftProfile:
    """One gage that does not stay where it was calibrated, measured two ways.

    The same instrument is described twice here because a drift produces two entirely separate
    problems. Periodic checks against a master say *how long a calibration lasts*. A crossed study
    whose sessions fall on different days says something else: the drift lands in whichever term
    of the ANOVA the **schedule** happens to align it with, and the schedule is not recorded on
    any gage study form.

    Attributes:
        gage: Must name a profile in :data:`GAGES`, whose part, operator and repeatability spreads
            are reused, so the drift is the only thing added.
        drift_per_day: How far the gage moves per day since its last calibration, signed.
        session_gap_days: Days between sessions of the crossed study. Operators are rarely
            available on the same day, so a study spread over weeks is the normal case rather
            than the awkward one.
        schedules: The day mappings compared. ``"sequential"`` gives each operator their own day,
            which is how a study gets scheduled when people are busy. ``"interleaved"`` has every
            operator measure on every day.
        check_every_days: Interval between periodic checks against the master.
        check_span_days: How long the periodic checking runs for.
        readings_per_check: Readings taken at each check.
    """

    gage: str
    drift_per_day: float
    session_gap_days: int
    schedules: tuple[str, ...]
    check_every_days: int
    check_span_days: int
    readings_per_check: int


# One drifting gage, and the rate is chosen to make a point that is arithmetic rather than
# empirical: 0.10 g per day is exactly the rate at which wave 5's 4.0 g offset appears 40 days
# after a calibration. The constant bias that study found and the drift this one measures are the
# same instrument seen twice, and they need different answers - a tare is removed once, a drift
# buys an interval.
DRIFTS = (
    DriftProfile(
        gage="BALANCA-01",
        drift_per_day=0.10,
        session_gap_days=7,
        schedules=("sequential", "interleaved"),
        check_every_days=5,
        check_span_days=60,
        readings_per_check=4,
    ),
)


@dataclass(frozen=True)
class LotProfile:
    """Lots arriving for acceptance inspection, most of them fine and a few not.

    A process that fails gradually is not what acceptance sampling is for. What it is for is the
    excursion: a run of material that came out much worse than usual, mixed in with lots that are
    fine. The two states are declared so that an accepted lot can be named as an escape.

    Attributes:
        stream: Label for the incoming material.
        lots: How many lots arrive.
        lot_size: Units per lot.
        excursion_share: Probability that a lot is an excursion rather than in control.
        in_control_fraction: True defective fraction of an in-control lot.
        excursion_fraction: True defective fraction of an excursion lot.
    """

    stream: str
    lots: int
    lot_size: int
    excursion_share: float
    in_control_fraction: float
    excursion_fraction: float


# Two hundred lots of a thousand units. One in ten is an excursion at eight times the ordinary
# defect rate, which is the case every sampling plan is bought to catch and the case its published
# acceptance quality level says nothing about.
LOTS = (
    LotProfile(
        stream="COMPONENTE-X",
        lots=200,
        lot_size=1000,
        excursion_share=0.10,
        in_control_fraction=0.005,
        excursion_fraction=0.040,
    ),
)


@dataclass(frozen=True)
class PanelProfile:
    """Many sites measured over many periods, with a real improvement in some of them.

    The table exists to make one question checkable: of the improvement a project would report,
    how much is the project's? Three things move a before-and-after number and only one of them
    is the project - the improvement itself, a trend that was already running, and the selection
    that put these sites in the charter rather than others.

    Attributes:
        stream: Label for the measurand.
        unit: Unit of measure.
        sites: How many sites are measured.
        periods: How many periods each site is measured for.
        split: Last period before the improvement. Periods after it carry the effect in the
            treated sites.
        level: Mean performance across sites.
        site_sd: Spread between sites, which is real and permanent.
        trend: Change per period common to every site, treated or not. Negative is an improvement
            that was already happening and that a before-and-after comparison will credit to
            whoever happened to be running a project at the time.
        noise: Period-to-period spread within a site.
        true_effect: The effect applied to the treated sites after ``split``, signed.
        treated: How many sites are treated. They are chosen at random rather than by
            performance, which is what makes the true effect recoverable - selection by
            performance is simulated separately, because mixing the two would leave no way to
            say which error produced which part of the answer.
        units_per_period: Transactions per site per period, for turning an effect into money.
        variable_share: Share of a modelled unit saving that is avoidable cash within the year.
            The rest is capacity: real, and not a number that appears in a bank account.
        project_cost: One-off cost of running the project.
    """

    stream: str
    unit: str
    sites: int
    periods: int
    split: int
    level: float
    site_sd: float
    trend: float
    noise: float
    true_effect: float
    treated: int
    units_per_period: float
    variable_share: float
    project_cost: float


# One panel. The numbers are chosen so that the three contributions to a before-and-after
# difference are of comparable size - the trend over the measured window is about as large as the
# improvement itself - because that is the situation where the arithmetic decides the conclusion
# and the rhetoric cannot.
PANELS = (
    PanelProfile(
        stream="custo de processamento por pedido",
        unit="BRL",
        sites=20,
        periods=24,
        split=12,
        level=100.0,
        site_sd=8.0,
        trend=-0.40,
        noise=6.0,
        true_effect=-5.00,
        treated=5,
        units_per_period=12000.0,
        variable_share=0.35,
        project_cost=250000.0,
    ),
)

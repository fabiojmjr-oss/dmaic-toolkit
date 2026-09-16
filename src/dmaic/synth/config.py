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

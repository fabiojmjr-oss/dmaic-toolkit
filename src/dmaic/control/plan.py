"""A reaction rule is a hypothesis test, and almost no control plan says what its error rates are.

A control plan is a table of triggers: *react if the daily average moves more than a unit*, *react
if any piece falls outside specification*, *react if the figure moves three sigma*. Each of those is
a test, run every day, with a false-alarm rate and a detection delay. The plan records neither, and
the two things it does record - who reacts and how - are the cheap part.

Three things this module measures, and the first two fail in opposite directions:

**An absolute trigger has a false-alarm rate the measurement system controls.** "React if the daily
average moves more than one unit" fires every 8.78 days on a stable process measured perfectly, and
every **1.73 days** through a gage at 63.6% of tolerance - **80% of those reactions are the gage**.
The detection of a real shift barely changes, so the bad gage buys nothing and costs five times the
reaction workload.

**A relative trigger has a detection limit the measurement system controls.** "React if the move
exceeds three sigma of the observed spread" holds its false-alarm rate at 0.0027 a day *whatever the
gage* - identical to four decimals - while the limit widens from 1.8974 to 5.3741. The gage is
invisible in the figure everybody checks and fully present in the one nobody does. Choosing the
other form of trigger does not escape it; it moves where it hides.

**And a specification-based trigger is both a false-alarm source and a slow detector.** On a process
with a capability index of 1.04 and nothing wrong at all, "react when any unit is out of
specification" fires every 28.6 days at twenty pieces a day - so a third of the reactions in a
quarter are on a process that is exactly on target - while a one-sigma shift takes 3.48 days to
surface at the same sampling, and 12.30 days at five pieces.

Everything here is a standard normal-theory calculation, and none of it is a control chart. A chart
is the instrument that makes this trade explicit and tunable, and it lives in the sibling
``oplab.spc`` package. What this module does is price the triggers people write *instead* of a
chart, which is most of them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
from scipy import stats

#: Periods in a working year, for turning a rate per period into a workload.
PERIODS_PER_YEAR = 250.0

#: Sigma multiple a trigger derived from observed spread conventionally uses.
DEFAULT_SIGMAS = 3.0

RULE_COLUMNS = (
    "label",
    "gage_sd",
    "total_sd",
    "limit",
    "false_alarm_rate",
    "periods_to_alarm",
    "gage_share",
    "delay",
)
SPEC_COLUMNS = ("shift_sigmas", "subgroup", "rate_per_period", "periods_to_react")


@dataclass(frozen=True)
class ReactionRule:
    """A trigger on the period-to-period move of a subgroup average.

    Attributes:
        limit: The move that trips a reaction, in the measurand's units.
        subgroup: Units measured per period.
        process_sd: Within-period spread of the process itself.
        gage_sd: Measurement spread added on top of it. Zero is a perfect gage, which is the
            comparison the plan is implicitly written against.
        periods_per_year: Periods in a year, for the workload figure.
    """

    limit: float
    subgroup: int
    process_sd: float
    gage_sd: float = 0.0
    periods_per_year: float = PERIODS_PER_YEAR

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError(f"a trigger needs a positive limit, got {self.limit}")
        if self.subgroup < 1:
            raise ValueError(f"a subgroup needs at least one unit, got {self.subgroup}")
        if self.process_sd <= 0:
            raise ValueError(f"process_sd must be positive, got {self.process_sd}")
        if self.gage_sd < 0:
            raise ValueError(f"gage_sd cannot be negative, got {self.gage_sd}")
        if self.periods_per_year <= 0:
            raise ValueError(f"periods_per_year must be positive, got {self.periods_per_year}")

    @property
    def total_sd(self) -> float:
        """What a single reading actually varies by: the process and the gage together."""
        return math.sqrt(self.process_sd**2 + self.gage_sd**2)

    @property
    def move_sd(self) -> float:
        """Spread of the period-to-period move of the average, which is what the trigger sees.

        Two averages of ``subgroup`` readings, so the move varies by ``sqrt(2)`` times the standard
        error. Comparing consecutive figures doubles the variance a single figure has, which is the
        first thing a plan written on "the move" gets wrong about its own sensitivity.
        """
        return self.total_sd / math.sqrt(self.subgroup) * math.sqrt(2.0)

    @property
    def false_alarm_rate(self) -> float:
        """How often the trigger fires on a process where nothing has changed."""
        return float(2.0 * stats.norm.sf(self.limit / self.move_sd))

    @property
    def periods_to_alarm(self) -> float:
        """Expected periods between false alarms, or ``inf`` when the rate underflows."""
        rate = self.false_alarm_rate
        return 1.0 / rate if rate > 0 else float("inf")

    @property
    def alarms_per_year(self) -> float:
        """False alarms a year, which is the figure a plan is defended or attacked with."""
        return self.false_alarm_rate * self.periods_per_year

    @property
    def gage_share(self) -> float:
        """Share of the false alarms that would not happen through a perfect gage.

        The comparison is the same rule, the same process, and a measurement system with no spread
        of its own. It is the workload the plan spends chasing its own instrument.
        """
        rate = self.false_alarm_rate
        if rate <= 0:
            return 0.0
        clean = ReactionRule(
            limit=self.limit,
            subgroup=self.subgroup,
            process_sd=self.process_sd,
            gage_sd=0.0,
            periods_per_year=self.periods_per_year,
        ).false_alarm_rate
        return (rate - clean) / rate

    def delay(self, shift: float) -> float:
        """Expected periods until a sustained shift of this size trips the trigger.

        Args:
            shift: Size of the shift, in the measurand's units.

        Returns:
            Expected periods, or ``inf`` when the shift can never trip it.

        Raises:
            ValueError: If the shift is zero, which is the false-alarm case and has its own
                property rather than being folded into this one.
        """
        if shift == 0:
            raise ValueError(
                "a shift of zero is the false-alarm case; read false_alarm_rate instead"
            )
        probability = float(
            stats.norm.sf(self.limit, shift, self.move_sd)
            + stats.norm.cdf(-self.limit, shift, self.move_sd)
        )
        return 1.0 / probability if probability > 0 else float("inf")

    def shift_caught_within(self, periods: float) -> float:
        """The smallest sustained shift this rule catches within so many periods, on average.

        The inverse of :meth:`delay`, and the figure a plan should be written with: a trigger is a
        promise about how fast something is noticed, not about a threshold.

        Args:
            periods: Periods the shift has to be caught within.

        Returns:
            The shift, in the measurand's units.

        Raises:
            ValueError: If ``periods`` is below one.
        """
        if periods < 1:
            raise ValueError(f"a shift cannot be caught in less than one period, got {periods}")
        # Detecting within n periods on average means a per-period probability of 1/n. Solving the
        # upper tail alone is enough: the far tail contributes nothing once the shift is material,
        # and ignoring it makes the answer conservative rather than optimistic.
        return float(self.limit + self.move_sd * stats.norm.ppf(1.0 / periods))

    def verdict(self) -> str:
        """The rule as the two promises it actually makes."""
        return (
            f"limit {self.limit:.4f} on {self.subgroup} units: a false alarm every "
            f"{self.periods_to_alarm:.2f} periods ({self.alarms_per_year:.1f} a year), "
            f"{self.gage_share:.0%} of them from the gage"
        )


def rule_from_spread(
    subgroup: int,
    process_sd: float,
    gage_sd: float = 0.0,
    sigmas: float = DEFAULT_SIGMAS,
    periods_per_year: float = PERIODS_PER_YEAR,
) -> ReactionRule:
    """The trigger a plan sets from what it observed: so many sigma of the observed move.

    This is the form that hides the measurement system. The limit is computed from the *total*
    spread, so a worse gage widens it, and the false-alarm rate comes out the same whatever the
    gage - which is the figure anybody checks. What changes is the shift the rule will tolerate
    before reacting, and nothing in the plan records it.

    Args:
        subgroup: Units measured per period.
        process_sd: Within-period spread of the process.
        gage_sd: Measurement spread.
        sigmas: Sigma multiple of the move's own spread.
        periods_per_year: Periods in a year.

    Returns:
        A :class:`ReactionRule` whose limit came from the data rather than from a decision.

    Raises:
        ValueError: If ``sigmas`` is not positive.
    """
    if sigmas <= 0:
        raise ValueError(f"sigmas must be positive, got {sigmas}")
    reference = ReactionRule(
        limit=1.0,
        subgroup=subgroup,
        process_sd=process_sd,
        gage_sd=gage_sd,
        periods_per_year=periods_per_year,
    )
    return ReactionRule(
        limit=sigmas * reference.move_sd,
        subgroup=subgroup,
        process_sd=process_sd,
        gage_sd=gage_sd,
        periods_per_year=periods_per_year,
    )


def compare_gages(
    gages: tuple[tuple[str, float], ...],
    limit: float,
    subgroup: int,
    process_sd: float,
    shift: float,
    periods_per_year: float = PERIODS_PER_YEAR,
) -> pd.DataFrame:
    """One trigger, several measurement systems, and what each does to the plan.

    Args:
        gages: ``(label, gage standard deviation)`` pairs.
        limit: The trigger, held fixed across the rows.
        subgroup: Units per period.
        process_sd: Within-period spread of the process.
        shift: Sustained shift whose detection delay is reported.
        periods_per_year: Periods in a year.

    Returns:
        A frame with the columns in :data:`RULE_COLUMNS`.

    Raises:
        ValueError: If no gage is supplied.
    """
    if not gages:
        raise ValueError("there is nothing to compare")
    rows = []
    for label, gage_sd in gages:
        rule = ReactionRule(
            limit=limit,
            subgroup=subgroup,
            process_sd=process_sd,
            gage_sd=gage_sd,
            periods_per_year=periods_per_year,
        )
        rows.append(
            {
                "label": label,
                "gage_sd": gage_sd,
                "total_sd": rule.total_sd,
                "limit": rule.limit,
                "false_alarm_rate": rule.false_alarm_rate,
                "periods_to_alarm": rule.periods_to_alarm,
                "gage_share": rule.gage_share,
                "delay": rule.delay(shift),
            }
        )
    return pd.DataFrame(rows)[list(RULE_COLUMNS)]


def spec_trigger(
    shifts: tuple[float, ...],
    subgroups: tuple[int, ...],
    process_sd: float,
    nominal: float,
    lsl: float,
    usl: float,
) -> pd.DataFrame:
    """React when any unit of the period falls outside specification. How long does that take?

    The commonest trigger in a control plan, and the one whose arithmetic is never shown. Its
    false-alarm rate is not zero - a process with a finite capability index produces out-of-spec
    units while perfectly on target - and its detection delay is long, because a shift has to move
    enough of the distribution past a limit to be likely to show up in a day's pieces.

    Args:
        shifts: Shifts to evaluate, in process standard deviations. Zero is the on-target case.
        subgroups: Units inspected per period.
        process_sd: Process spread.
        nominal: Process centre when nothing has shifted.
        lsl: Lower specification limit.
        usl: Upper specification limit.

    Returns:
        A frame with the columns in :data:`SPEC_COLUMNS`.

    Raises:
        ValueError: If the limits are not ordered, the spread is not positive, or a subgroup is
            empty.
    """
    if usl <= lsl:
        raise ValueError(f"usl must exceed lsl, got {lsl} and {usl}")
    if process_sd <= 0:
        raise ValueError(f"process_sd must be positive, got {process_sd}")
    if any(size < 1 for size in subgroups):
        raise ValueError("a subgroup needs at least one unit")

    rows = []
    for shift in shifts:
        centre = nominal + shift * process_sd
        outside = float(
            stats.norm.sf(usl, centre, process_sd) + stats.norm.cdf(lsl, centre, process_sd)
        )
        for size in subgroups:
            per_period = float(1.0 - (1.0 - outside) ** size)
            rows.append(
                {
                    "shift_sigmas": shift,
                    "subgroup": size,
                    "rate_per_period": per_period,
                    "periods_to_react": 1.0 / per_period if per_period > 0 else float("inf"),
                }
            )
    return pd.DataFrame(rows)[list(SPEC_COLUMNS)]


def capability(process_sd: float, lsl: float, usl: float) -> float:
    """The capability index the specification and the spread imply.

    Here only to label the specification-trigger table honestly: the false-alarm rate of a
    specification trigger is a consequence of this number, and quoting the first without the second
    makes the trigger look arbitrary when it is not.

    Args:
        process_sd: Process spread.
        lsl: Lower specification limit.
        usl: Upper specification limit.

    Returns:
        ``(usl - lsl) / (6 * process_sd)``.

    Raises:
        ValueError: If the limits are not ordered or the spread is not positive.
    """
    if usl <= lsl:
        raise ValueError(f"usl must exceed lsl, got {lsl} and {usl}")
    if process_sd <= 0:
        raise ValueError(f"process_sd must be positive, got {process_sd}")
    return float((usl - lsl) / (6.0 * process_sd))


def alarms_against_delay(
    limits: tuple[float, ...],
    subgroup: int,
    process_sd: float,
    shift: float,
    gage_sd: float = 0.0,
) -> pd.DataFrame:
    """The trade a plan is making without saying so: false alarms against detection delay.

    Args:
        limits: Triggers to walk through.
        subgroup: Units per period.
        process_sd: Within-period spread.
        shift: Sustained shift whose delay is reported.
        gage_sd: Measurement spread.

    Returns:
        A frame with ``limit``, ``false_alarm_rate``, ``alarms_per_year`` and ``delay``.
    """
    rows = []
    for limit in limits:
        rule = ReactionRule(limit=limit, subgroup=subgroup, process_sd=process_sd, gage_sd=gage_sd)
        rows.append(
            {
                "limit": limit,
                "false_alarm_rate": rule.false_alarm_rate,
                "alarms_per_year": rule.alarms_per_year,
                "delay": rule.delay(shift),
            }
        )
    return pd.DataFrame(rows)

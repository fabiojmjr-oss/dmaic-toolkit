"""Acceptance sampling: what a plan actually guarantees, which is not what its name says.

A sampling plan is two numbers - how many units to draw and how many defectives to tolerate - and
those two numbers fix a curve, not a threshold. The curve says, for every possible incoming quality
level, how often a lot at that level is accepted. Almost every argument about sampling is an
argument about one point on a curve nobody drew.

Three things this module exists to measure:

**"Inspect ten percent" controls nothing.** It is the commonest rule in industry and the only
number in it that matters - the sample size - is set by the lot size, which is a shipping decision.
The same written rule protects a small lot barely at all and a large one absurdly hard, and nobody
chose either level. A fixed sample size gives the same protection whatever the lot size, which is
the property the percentage rule is usually assumed to have.

**An acceptance quality level is a producer's risk, not a promise to the customer.** A plan quoted
at "AQL 1.0%" accepts a lot at 1% defective almost always, by construction - that is what the
number means. What it says about a lot three times worse is a separate point on the same curve, and
it is usually much less comforting than the name suggests.

**A zero acceptance number is not a strict plan.** "Reject on a single defective" sounds like the
tightest rule available, and at the same sample size it is. But plans are chosen to accept good
material, so a ``c = 0`` plan is matched to the same producer's risk with a far smaller sample -
and the discrimination of a plan comes from its sample size. Matched at the acceptance quality
level, the zero acceptance plan is markedly worse at catching the lots it exists to catch.

Nothing here improves outgoing quality. Sampling sorts lots; it does not change what is in them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

#: Conventional risks the standard plans are built around: the producer accepts a 5% chance of a
#: good lot being rejected, the consumer a 10% chance of a bad lot being accepted. They are
#: conventions, exposed as arguments for that reason.
DEFAULT_PRODUCER_RISK = 0.05
DEFAULT_CONSUMER_RISK = 0.10

#: Largest sample size :func:`plan_for` will search up to before giving up.
MAX_SAMPLE = 5000

OC_COLUMNS = ("fraction_defective", "accept_probability", "average_outgoing_quality")
DECISION_COLUMNS = ("lot", "lot_size", "state", "defectives", "fraction", "found", "accepted")


@dataclass(frozen=True)
class SamplingPlan:
    """A single sampling plan: draw ``n``, accept on at most ``c`` defectives.

    Attributes:
        n: Units drawn from the lot.
        c: Largest number of defectives that still accepts the lot.
        lot_size: Units in the lot. Supplied means the sample is drawn without replacement and the
            hypergeometric distribution applies; ``None`` uses the binomial, which is the usual
            published approximation and is optimistic exactly when the sample is a material share
            of the lot.
    """

    n: int
    c: int
    lot_size: int | None = None

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError(f"the sample must hold at least one unit, got {self.n}")
        if self.c < 0:
            raise ValueError(f"the acceptance number cannot be negative, got {self.c}")
        if self.c >= self.n:
            raise ValueError(
                f"an acceptance number of {self.c} on a sample of {self.n} accepts every lot"
            )
        if self.lot_size is not None and self.lot_size < self.n:
            raise ValueError(
                f"cannot draw {self.n} units from a lot of {self.lot_size}; that is a full "
                "inspection, not a sampling plan"
            )

    @property
    def sampled_share(self) -> float:
        """Share of the lot inspected, or ``nan`` when the lot size is not known."""
        if self.lot_size is None:
            return float("nan")
        return self.n / self.lot_size

    def accept_probability(self, fraction_defective: float) -> float:
        """How often a lot at this quality level is accepted.

        Args:
            fraction_defective: True defective fraction of the lot.

        Returns:
            The acceptance probability.

        Raises:
            ValueError: If the fraction is not in ``[0, 1]``.
        """
        if not 0.0 <= fraction_defective <= 1.0:
            raise ValueError(f"a fraction must be in [0, 1], got {fraction_defective}")
        if self.lot_size is None:
            return float(stats.binom.cdf(self.c, self.n, fraction_defective))
        # A lot holds a whole number of defectives, so the fraction is rounded to one. This is the
        # honest version: the binomial treats the lot as an infinite stream, which it is not.
        defectives = int(round(self.lot_size * fraction_defective))
        return float(stats.hypergeom.cdf(self.c, self.lot_size, defectives, self.n))

    def producer_risk(self, aql: float) -> float:
        """How often a lot at the acceptance quality level is rejected anyway."""
        return 1.0 - self.accept_probability(aql)

    def consumer_risk(self, rql: float) -> float:
        """How often a lot at the rejectable quality level is accepted anyway."""
        return self.accept_probability(rql)

    def average_outgoing_quality(self, fraction_defective: float) -> float:
        """Defective fraction shipped, assuming rejected lots are sorted and made good.

        The assumption is worth stating because it is usually left implicit and it is often false:
        this is the figure for *rectifying* inspection, where a rejected lot is screened
        completely. Where rejected lots are returned to the supplier instead, the outgoing quality
        of what is shipped is the accepted lots' own level and this number does not describe it.

        Args:
            fraction_defective: True defective fraction of the incoming lot.

        Returns:
            Expected defective fraction after inspection.
        """
        accepted = self.accept_probability(fraction_defective)
        if self.lot_size is None:
            return fraction_defective * accepted
        remaining = (self.lot_size - self.n) / self.lot_size
        return fraction_defective * accepted * remaining

    def verdict(self, aql: float, rql: float) -> str:
        """The two risks in one line, which is the only honest summary of a plan."""
        return (
            f"n={self.n} c={self.c}: rejects {self.producer_risk(aql):.1%} of lots at "
            f"{aql:.1%} defective, accepts {self.consumer_risk(rql):.1%} of lots at {rql:.1%}"
        )


def percentage_plan(lot_size: int, share: float = 0.10, c: int = 0) -> SamplingPlan:
    """The "inspect ten percent" rule, as the plan it actually is.

    Args:
        lot_size: Units in the lot.
        share: Share of the lot to inspect.
        c: Acceptance number.

    Returns:
        A :class:`SamplingPlan` whose sample size is a consequence of the lot size.

    Raises:
        ValueError: If the share is not in ``(0, 1]``.
    """
    if not 0.0 < share <= 1.0:
        raise ValueError(f"the share must be in (0, 1], got {share}")
    return SamplingPlan(n=max(1, round(lot_size * share)), c=c, lot_size=lot_size)


def plan_for(
    aql: float,
    rql: float,
    producer_risk: float = DEFAULT_PRODUCER_RISK,
    consumer_risk: float = DEFAULT_CONSUMER_RISK,
    lot_size: int | None = None,
    max_sample: int = MAX_SAMPLE,
) -> SamplingPlan:
    """The smallest plan that holds both risks, searched rather than looked up in a table.

    Both risks have to be named, which is the point of asking for them: a plan derived from one
    quality level is not a plan, it is half of one.

    Args:
        aql: Quality level a lot should pass at.
        rql: Quality level a lot should fail at.
        producer_risk: Acceptable chance of rejecting a lot at the ``aql``.
        consumer_risk: Acceptable chance of accepting a lot at the ``rql``.
        lot_size: Lot size, for a hypergeometric plan.
        max_sample: Largest sample searched.

    Returns:
        The plan with the smallest ``n``, and the smallest ``c`` at that ``n``.

    Raises:
        ValueError: If the quality levels are not ordered, the risks are not probabilities, or no
            plan up to ``max_sample`` holds both risks.
    """
    if not 0.0 < aql < rql < 1.0:
        raise ValueError(f"need 0 < aql < rql < 1, got aql={aql} and rql={rql}")
    for name, risk in (("producer_risk", producer_risk), ("consumer_risk", consumer_risk)):
        if not 0.0 < risk < 1.0:
            raise ValueError(f"{name} must be strictly between 0 and 1, got {risk}")
    ceiling = max_sample if lot_size is None else min(max_sample, lot_size)
    for n in range(2, ceiling + 1):
        for c in range(0, n):
            candidate = SamplingPlan(n=n, c=c, lot_size=lot_size)
            if candidate.producer_risk(aql) > producer_risk:
                # Raising c only ever accepts more, so a plan too harsh at the aql stays too harsh
                # for every smaller c and the remaining ones are worth trying.
                continue
            if candidate.consumer_risk(rql) <= consumer_risk:
                return candidate
            # Any larger c accepts even more at the rql, so this n is exhausted.
            break
    raise ValueError(
        f"no plan up to n={ceiling} separates {aql:.2%} from {rql:.2%} at those risks; the two "
        "quality levels are too close to be told apart by sampling"
    )


def matched_plan(
    reference: SamplingPlan,
    c: int,
    aql: float,
    lot_size: int | None = None,
) -> SamplingPlan:
    """The plan with a given acceptance number that matches a reference plan's producer's risk.

    This is how two plans are compared honestly. A plan is chosen so that good material passes, so
    holding the producer's risk fixed is what "the same plan, stricter rule" actually means - and
    it is where the intuition about a zero acceptance number falls apart.

    Args:
        reference: The plan to match at the acceptance quality level.
        c: Acceptance number the matched plan must use.
        aql: Quality level the two plans are matched at.
        lot_size: Lot size for the matched plan, defaulting to the reference plan's.

    Returns:
        The plan with acceptance number ``c`` whose acceptance probability at ``aql`` is closest to
        the reference plan's.

    Raises:
        ValueError: If ``c`` is negative.
    """
    if c < 0:
        raise ValueError(f"the acceptance number cannot be negative, got {c}")
    size = reference.lot_size if lot_size is None else lot_size
    target = reference.accept_probability(aql)
    ceiling = MAX_SAMPLE if size is None else size
    if ceiling <= c:
        raise ValueError(
            f"an acceptance number of {c} needs a sample of at least {c + 1}, and the lot holds "
            f"{ceiling}"
        )
    best = SamplingPlan(n=c + 1, c=c, lot_size=size)
    best_gap = abs(best.accept_probability(aql) - target)
    for n in range(c + 2, ceiling + 1):
        candidate = SamplingPlan(n=n, c=c, lot_size=size)
        gap = abs(candidate.accept_probability(aql) - target)
        if gap >= best_gap:
            # Acceptance falls monotonically as the sample grows, so once the gap stops closing it
            # never closes again and the best n is behind us.
            break
        best, best_gap = candidate, gap
    return best


def oc_curve(plan: SamplingPlan, fractions: tuple[float, ...] | np.ndarray) -> pd.DataFrame:
    """The operating characteristic curve: the plan, as the thing it really is.

    Args:
        plan: The plan to describe.
        fractions: Incoming defective fractions to evaluate.

    Returns:
        A frame with the columns in :data:`OC_COLUMNS`.
    """
    return pd.DataFrame(
        [
            {
                "fraction_defective": float(fraction),
                "accept_probability": plan.accept_probability(float(fraction)),
                "average_outgoing_quality": plan.average_outgoing_quality(float(fraction)),
            }
            for fraction in fractions
        ]
    )[list(OC_COLUMNS)]


def inspect_lots(
    plan: SamplingPlan,
    lots: pd.DataFrame,
    seed: int = 0,
    defectives: str = "defectives",
    lot_size: str = "lot_size",
) -> pd.DataFrame:
    """Apply a plan to real lots and record what it decided about each one.

    The sample is drawn hypergeometrically from the defectives the lot actually contains, so a lot
    that happens to hold none cannot fail and a plan's luck on a particular set of lots is visible
    rather than averaged away.

    Args:
        plan: The plan to apply.
        lots: One row per lot, with a defective count and a lot size.
        seed: Seed for the draws.
        defectives: Column holding the number of defective units in the lot.
        lot_size: Column holding the lot size.

    Returns:
        A copy of ``lots`` with ``found`` and ``accepted`` columns added, in the order given by
        :data:`DECISION_COLUMNS` for the columns it recognises.

    Raises:
        ValueError: If a lot is smaller than the plan's sample.
    """
    rng = np.random.default_rng(seed)
    frame = lots.copy()
    sizes = np.asarray(frame[lot_size], dtype=int)
    if np.any(sizes < plan.n):
        raise ValueError(f"at least one lot holds fewer than the {plan.n} units the plan draws")
    found = rng.hypergeometric(
        ngood=np.asarray(frame[defectives], dtype=int),
        nbad=sizes - np.asarray(frame[defectives], dtype=int),
        nsample=plan.n,
    )
    frame["found"] = found
    frame["accepted"] = found <= plan.c
    ordered = [column for column in DECISION_COLUMNS if column in frame.columns]
    return frame[ordered + [column for column in frame.columns if column not in ordered]]

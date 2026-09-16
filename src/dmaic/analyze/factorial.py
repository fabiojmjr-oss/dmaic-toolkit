"""Full and fractional two-level factorials, and what a fraction costs.

The arithmetic here is not the interesting part. A two-level factorial is orthogonal by
construction, so every effect is a difference of two averages and the estimates do not depend on
each other - which is the whole reason the design is worth running instead of changing one factor
at a time.

What is interesting is the fraction. Halving the runs does not lose information evenly; it makes
pairs of effects arithmetically identical, so the design returns one number where the process has
two. The taught summary of that is "a resolution III design confounds main effects with two-factor
interactions", which is true and understates it. The estimate it returns is the *sum* of the two,
so a factor that does nothing at all reports the interaction's effect as its own - a large,
clean-looking, entirely fictitious main effect. Nothing in the output says so. The run sheet looks
the same as a good one, the analysis is not wrong, and the conclusion is a factor the process does
not have.

The choice of generator is what decides this, and it is free. Two half fractions of the same four
factors cost the same eight runs and draw from the same experiment; one resolves the interaction
and the other invents a factor. That is why :func:`fractional_factorial` requires the generators to
be written down and why :meth:`Design.aliases` is not an optional diagnostic.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .power import DEFAULT_ALPHA, DEFAULT_POWER, detectable_difference

# One letter per factor, in the order the factors are given. Seven is not a limit of the
# arithmetic; it is where a written alias structure stops being readable, and a design past it
# wants a different tool than a printed table.
LETTERS = "ABCDEFG"
MAX_FACTORS = len(LETTERS)

#: Resolutions with a standard meaning, as roman numerals, up to the longest word :data:`LETTERS`
#: allows. Resolution II aliases one main effect with another, which is two factors sharing a
#: column rather than a design, so it is rejected rather than labelled.
ROMAN = {2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}

GENERATOR_PATTERN = re.compile(r"^([A-G])\s*=\s*([A-G]+)$")

#: The identity. An effect aliased with it is not an effect: its contrast column is constant, so
#: the design measures the grand mean on that column and has no degree of freedom left for a term.
IDENTITY = "I"

EFFECT_COLUMNS = ("effect", "order", "estimate", "aliased_with")


def _word(letters: str) -> str:
    """Canonical form of an effect word: unique letters, alphabetical."""
    return "".join(sorted(set(letters)))


def _multiply(left: str, right: str) -> str:
    """Product of two words in the group where every letter squares to the identity.

    Two equal words multiply to ``I``, the identity, and that case is not a curiosity to be
    filtered out: a word of the defining relation has a constant contrast column, so what it
    estimates is the grand mean rather than any effect. Returning ``"I"`` is what lets
    :meth:`Design.aliases` say so instead of reporting the term as clean.
    """
    product = "".join(sorted(set(left) ^ set(right)))
    return product or IDENTITY


def _all_words(k: int) -> tuple[str, ...]:
    """Every effect of a full 2^k, in order of increasing interaction order."""
    return tuple(
        "".join(combination)
        for size in range(1, k + 1)
        for combination in itertools.combinations(LETTERS[:k], size)
    )


def _column(runs: np.ndarray, word: str) -> np.ndarray:
    """The contrast column of an effect: the elementwise product of its factor columns."""
    # Annotated because the numpy stubs shipped for older interpreters give np.ones a
    # one-dimensional shape type, which the elementwise product then widens.
    column: np.ndarray = np.ones(len(runs), dtype=int)
    for letter in word:
        column = column * runs[:, LETTERS.index(letter)]
    return column


@dataclass(frozen=True)
class Design:
    """A two-level design, with its aliasing written down rather than implied.

    Attributes:
        factors: Factor names, in the order the letters ``A``, ``B``, ... refer to them.
        runs: The coded design matrix, ``n_runs`` by ``n_factors``, entries -1 and +1.
        generators: The generators used to build a fraction, as ``"D=ABC"``. Empty for a full
            factorial.
        defining_relation: The words equal to the identity, excluding ``I`` itself. Empty for a
            full factorial, which has no aliasing to define.
    """

    factors: tuple[str, ...]
    runs: np.ndarray
    generators: tuple[str, ...]
    defining_relation: tuple[str, ...]

    @property
    def n_factors(self) -> int:
        """How many factors the design carries."""
        return len(self.factors)

    @property
    def n_runs(self) -> int:
        """How many runs it takes."""
        return int(self.runs.shape[0])

    @property
    def fraction(self) -> str:
        """The design in the usual notation, as ``2^4`` or ``2^(4-1)``."""
        if not self.generators:
            return f"2^{self.n_factors}"
        return f"2^({self.n_factors}-{len(self.generators)})"

    @property
    def resolution(self) -> int | None:
        """Length of the shortest word in the defining relation.

        ``None`` for a full factorial, where the defining relation is empty. That is not a very
        large resolution dressed up as a missing value: a full factorial has no aliasing at all,
        and giving it a number invites it to be compared against a fraction's on the same scale.
        """
        if not self.defining_relation:
            return None
        return min(len(word) for word in self.defining_relation)

    @property
    def resolution_label(self) -> str:
        """The resolution as it is written on a run sheet, or ``"full"``."""
        resolution = self.resolution
        if resolution is None:
            return "full"
        # A word cannot be longer than the number of factors, so ROMAN covers every reachable
        # resolution and a missing key would be a bug rather than an input to fall back on.
        return ROMAN[resolution]

    def letter(self, factor: str) -> str:
        """The letter standing for a named factor.

        Raises:
            KeyError: If the factor is not in this design.
        """
        if factor not in self.factors:
            raise KeyError(f"{factor!r} is not a factor of this design: {self.factors}")
        return LETTERS[self.factors.index(factor)]

    def aliases(self) -> dict[str, tuple[str, ...]]:
        """Every effect, mapped to the effects it cannot be told apart from.

        Returns:
            A dict from effect word to the other words sharing its contrast column, in order of
            increasing interaction order. The effect itself is not repeated in its own tuple, and
            a full factorial returns an empty tuple for every effect.
        """
        aliased: dict[str, tuple[str, ...]] = {}
        for effect in _all_words(self.n_factors):
            partners = {_multiply(effect, word) for word in self.defining_relation} - {effect}
            # The identity sorts first rather than among the main effects, which it would
            # otherwise do on length alone while meaning something entirely different.
            ordered = ([IDENTITY] if IDENTITY in partners else []) + sorted(
                partners - {IDENTITY}, key=lambda word: (len(word), word)
            )
            aliased[effect] = tuple(ordered)
        return aliased

    def estimable(self) -> tuple[str, ...]:
        """The effects this design can report on their own, main effects and interactions alike.

        An effect is estimable when nothing else shares its column. In a full factorial that is
        every effect; in a fraction it is only the ones whose aliases all lie outside the design,
        which for a half fraction of four factors is none of them. A word of the defining relation
        is not estimable either - it is aliased with the identity, which is a different way of
        being unusable and an easy one to report as clean by accident.
        """
        return tuple(effect for effect, partners in self.aliases().items() if not partners)

    def confounded_main_effects(self) -> dict[str, tuple[str, ...]]:
        """Main effects aliased with a two-factor interaction, which is the expensive case.

        This is the resolution III failure, listed rather than summarised. A main effect here does
        not come back with extra uncertainty attached; it comes back as the sum of itself and an
        interaction, with no way to tell how much of the number belongs to which.
        """
        return {
            effect: tuple(word for word in partners if len(word) == 2)
            for effect, partners in self.aliases().items()
            if len(effect) == 1 and any(len(word) == 2 for word in partners)
        }

    def verdict(self) -> str:
        """One line on what this design can be trusted to say."""
        resolution = self.resolution
        if resolution is None:
            return f"{self.fraction}: every effect estimable, no aliasing"
        confounded = self.confounded_main_effects()
        if confounded:
            listed = ", ".join(f"{effect}+{partners[0]}" for effect, partners in confounded.items())
            return (
                f"{self.fraction} resolution {self.resolution_label}: main effects carry "
                f"two-factor interactions ({listed})"
            )
        if resolution == 4:
            return (
                f"{self.fraction} resolution {self.resolution_label}: main effects clear, "
                "two-factor interactions aliased with each other"
            )
        return (
            f"{self.fraction} resolution {self.resolution_label}: main effects and two-factor "
            "interactions clear"
        )

    def rows_of(self, runs: np.ndarray) -> np.ndarray:
        """Which rows of a larger design matrix this design's runs are.

        A fraction is not a different experiment from the full factorial it comes out of; it is a
        subset of the same runs. Locating them makes that checkable rather than asserted: two
        fractions of the same factors can be read off one measured experiment, so the comparison
        between them holds the data fixed and varies only the generator.

        Args:
            runs: A coded design matrix over the same factors in the same order.

        Returns:
            One row index into ``runs`` per run of this design, in this design's order.

        Raises:
            ValueError: If ``runs`` has a different number of factors, or if any run of this
                design does not appear in it exactly once.
        """
        if runs.shape[1] != self.n_factors:
            raise ValueError(
                f"design has {self.n_factors} factors, matrix has {runs.shape[1]} columns"
            )
        located = []
        for row in self.runs:
            matches = np.flatnonzero((runs == row).all(axis=1))
            if matches.size != 1:
                raise ValueError(f"run {row.tolist()} appears {matches.size} times, expected once")
            located.append(int(matches[0]))
        return np.array(located, dtype=int)


def full_factorial(factors: tuple[str, ...] | list[str]) -> Design:
    """Every combination of the factors, in standard order.

    Args:
        factors: Factor names. Their order fixes which letter refers to which.

    Returns:
        A :class:`Design` of ``2 ** len(factors)`` runs with an empty defining relation.

    Raises:
        ValueError: If there are fewer than two factors, more than :data:`MAX_FACTORS`, or a
            repeated name.
    """
    named = tuple(factors)
    if len(named) < 2:
        raise ValueError("a factorial needs at least two factors")
    if len(named) > MAX_FACTORS:
        raise ValueError(f"at most {MAX_FACTORS} factors are supported, got {len(named)}")
    if len(set(named)) != len(named):
        raise ValueError(f"factor names must be unique, got {named}")
    runs = np.array(list(itertools.product(*[(-1, 1)] * len(named))), dtype=int)
    return Design(factors=named, runs=runs, generators=(), defining_relation=())


def fractional_factorial(
    factors: tuple[str, ...] | list[str],
    generators: tuple[str, ...] | list[str],
) -> Design:
    """A fraction of a full factorial, built from generators that have to be stated.

    Each generator assigns one factor to the contrast column of the others, as ``"D=ABC"``. The
    assignment is what creates the aliasing, and it is the only choice in the design that is both
    free and consequential: two generators over the same factors cost the same runs and give
    designs of different resolution.

    Args:
        factors: Factor names, in letter order.
        generators: One generator per factor being generated, as ``"D=ABC"``. The generated
            letters must be the last factors, which is the usual convention and keeps the basis
            columns a plain full factorial.

    Returns:
        A :class:`Design` of ``2 ** (k - p)`` runs whose defining relation lists every word equal
        to the identity.

    Raises:
        ValueError: If a generator is malformed, names a letter outside the design, generates a
            letter that is not one of the last factors, or produces a design of resolution II -
            two factors on one column, which is not a design of those factors at all.
    """
    named = tuple(factors)
    stated = tuple(generators)
    if not stated:
        raise ValueError("a fraction needs at least one generator; use full_factorial otherwise")
    base = full_factorial(named)
    k = base.n_factors
    p = len(stated)
    if p >= k - 1:
        raise ValueError(f"{p} generators over {k} factors leaves no factorial to fraction")

    available = LETTERS[:k]
    generated = available[k - p :]
    words: list[str] = []
    assignments: dict[str, str] = {}
    for generator in stated:
        match = GENERATOR_PATTERN.match(generator)
        if match is None:
            raise ValueError(f"generator {generator!r} is not of the form 'D=ABC'")
        target, source = match.group(1), _word(match.group(2))
        if target not in generated:
            raise ValueError(
                f"generator {generator!r} generates {target}, but the generated factors are "
                f"{tuple(generated)} - list the generated factors last"
            )
        if target in assignments:
            raise ValueError(f"factor {target} is generated twice")
        if any(letter not in available for letter in source):
            raise ValueError(f"generator {generator!r} names a factor outside {tuple(available)}")
        if target in source:
            raise ValueError(f"generator {generator!r} defines {target} in terms of itself")
        assignments[target] = source
        words.append(_multiply(target, source))

    # The defining relation is closed under multiplication: with p generators there are 2^p - 1
    # words, and the shortest of them - not the shortest generator - sets the resolution.
    relation: set[str] = set()
    for size in range(1, p + 1):
        for chosen in itertools.combinations(words, size):
            product = chosen[0]
            for word in chosen[1:]:
                product = _multiply(product, word)
            if product:
                relation.add(product)
    defining = tuple(sorted(relation, key=lambda word: (len(word), word)))

    basis = full_factorial(tuple(named[: k - p])) if k - p > 1 else None
    if basis is None:  # pragma: no cover - blocked by the p >= k - 1 check above
        raise ValueError("a fraction needs at least two basis factors")
    runs = np.empty((basis.n_runs, k), dtype=int)
    runs[:, : k - p] = basis.runs
    for target, source in assignments.items():
        runs[:, LETTERS.index(target)] = _column(runs, source)

    design = Design(factors=named, runs=runs, generators=stated, defining_relation=defining)
    if design.resolution == 2:
        raise ValueError(
            f"generators {stated} give resolution II: {defining[0]} makes two factors share a "
            "column, so the design cannot separate them at all"
        )
    return design


def alias_structure(design: Design) -> pd.DataFrame:
    """The alias structure as a table, one row per effect.

    Args:
        design: The design to describe.

    Returns:
        A frame with ``effect``, ``order``, ``aliased_with`` and ``estimable``.
    """
    aliased = design.aliases()
    return pd.DataFrame(
        [
            {
                "effect": effect,
                "order": len(effect),
                "aliased_with": " = ".join(partners),
                "estimable": not partners,
            }
            for effect, partners in aliased.items()
        ]
    )


def effects(design: Design, response: np.ndarray | pd.Series) -> pd.DataFrame:
    """Every effect the design can compute, with what each estimate is a sum of.

    The estimate is the usual contrast, ``(sum of x_i * y_i) / (n / 2)``: the difference between
    the average response at the high level and at the low level. Because the columns are
    orthogonal, adding or dropping a term changes nothing about the others.

    An effect aliased with the identity gets ``nan`` rather than a number, because its column
    is constant and the contrast on it is twice the grand mean rather than an effect of anything.

    No p-value is returned, and that is deliberate rather than unfinished. An unreplicated
    factorial has no degrees of freedom left for error, so a significance test on it is a test
    against an error estimate borrowed from whichever high-order interactions the analyst decided
    to call noise. :func:`detectable_effect` answers the question that can be answered from the
    design alone: how large an effect this many runs could have seen.

    Args:
        design: The design the response was measured on.
        response: One measurement per run, in the design's run order.

    Returns:
        A frame with the columns in :data:`EFFECT_COLUMNS`, in order of increasing interaction
        order. ``aliased_with`` is empty for an effect nothing shares a column with, and reads
        ``I`` for a word of the defining relation, whose estimate is ``nan``.

    Raises:
        ValueError: If the response length does not match the number of runs.
    """
    values = np.asarray(response, dtype=float)
    if values.shape != (design.n_runs,):
        raise ValueError(f"expected {design.n_runs} responses, got {values.shape}")
    aliased = design.aliases()
    divisor = design.n_runs / 2.0
    rows = []
    for effect, partners in aliased.items():
        # A word of the defining relation has a constant column, so the contrast returns twice
        # the grand mean. That is a number, and publishing it next to the effects would be this
        # module's own version of the mistake it is about.
        estimate = (
            float("nan")
            if IDENTITY in partners
            else float(_column(design.runs, effect) @ values) / divisor
        )
        rows.append(
            {
                "effect": effect,
                "order": len(effect),
                "estimate": estimate,
                "aliased_with": " = ".join(partners),
            }
        )
    return pd.DataFrame(rows)[list(EFFECT_COLUMNS)]


def detectable_effect(
    n_runs: int,
    sd: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
) -> float:
    """The smallest effect a design of this many runs could have found.

    Every effect in a two-level design is a comparison of two halves of the runs, so the question
    is the two-sample one :mod:`dmaic.analyze.power` already answers, with ``n_runs / 2``
    observations on each side. Screening designs are routinely sized by what the schedule allowed,
    and this is the figure that says what that bought: an effect below it was out of reach before
    the first run, and a design's silence about it is not evidence of its absence.

    Args:
        n_runs: Total runs in the design, including replicates.
        sd: Run-to-run standard deviation of the response.
        power: Power the effect has to be detectable at.
        alpha: Significance level.

    Returns:
        The smallest detectable effect, in the units of the response.

    Raises:
        ValueError: If ``n_runs`` is below four or odd.
    """
    if n_runs < 4:
        raise ValueError(f"an effect needs at least two runs per level, got {n_runs} in total")
    if n_runs % 2:
        raise ValueError(f"a two-level design has an even number of runs, got {n_runs}")
    return detectable_difference(n_runs // 2, sd, power=power, alpha=alpha)

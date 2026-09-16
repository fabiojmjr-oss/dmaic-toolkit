"""One designed experiment, run at every combination of its factors.

The full factorial is generated rather than the fractions, and this is the point of the table. A
half fraction is not a different experiment; it is eight of these sixteen runs. Generating the
full set and letting each design select its own rows holds the data fixed and varies only the
generator, so a comparison between two fractions cannot be explained by one of them having had
luckier noise.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .config import FACTORIALS, FactorialProfile

RUN_COLUMNS = ("process", "run")
EFFECT_COLUMNS = ("process", "effect", "order", "true_effect")
LETTERS = "ABCDEFG"


def _coded_runs(k: int) -> np.ndarray:
    """The full 2^k design matrix in standard order, which is the order the runs are numbered in."""
    return np.array(list(itertools.product(*[(-1, 1)] * k)), dtype=int)


def _column(runs: np.ndarray, word: str) -> np.ndarray:
    # Annotated because the numpy stubs shipped for older interpreters give np.ones a
    # one-dimensional shape type, which the elementwise product then widens.
    column: np.ndarray = np.ones(len(runs), dtype=int)
    for letter in word:
        column = column * runs[:, LETTERS.index(letter)]
    return column


def _one_factorial(profile: FactorialProfile, rng: np.random.Generator) -> pd.DataFrame:
    runs = _coded_runs(len(profile.settings))
    # The coefficient is half the effect, because an effect is the move across two coded units.
    response: np.ndarray = np.full(len(runs), profile.baseline)
    for word, effect in profile.true_effects:
        response = response + (effect / 2.0) * _column(runs, word)
    response = response + rng.normal(0.0, profile.noise_sd, size=len(runs))
    frame = pd.DataFrame(
        {
            "process": profile.process,
            "run": np.arange(1, len(runs) + 1),
        }
    )
    for index, setting in enumerate(profile.settings):
        frame[setting.name] = runs[:, index]
    frame["response"] = response
    return frame


def factorial_runs(rng: np.random.Generator) -> pd.DataFrame:
    """Every run of every experiment, one row each, factors coded -1 and +1.

    Args:
        rng: The shared generator, consumed in a fixed order.

    Returns:
        A frame with :data:`RUN_COLUMNS`, one column per factor, and ``response``.
    """
    frame = pd.concat([_one_factorial(profile, rng) for profile in FACTORIALS], ignore_index=True)
    frame["process"] = frame["process"].astype("category")
    return frame


def factorial_effects() -> pd.DataFrame:
    """What is actually in each process, one row per effect, including the zeros.

    Every term of the full factorial is listed, not only the ones that were planted. The zeros are
    the load-bearing rows: a design that reports an effect for a term listed here at 0.0 has not
    measured a small effect badly, it has reported an effect the process does not have.
    """
    rows: list[dict[str, object]] = []
    for profile in FACTORIALS:
        planted = dict(profile.true_effects)
        letters = LETTERS[: len(profile.settings)]
        for size in range(1, len(letters) + 1):
            for combination in itertools.combinations(letters, size):
                word = "".join(combination)
                rows.append(
                    {
                        "process": profile.process,
                        "effect": word,
                        "order": size,
                        "true_effect": float(planted.get(word, 0.0)),
                    }
                )
    return pd.DataFrame(rows)[list(EFFECT_COLUMNS)]

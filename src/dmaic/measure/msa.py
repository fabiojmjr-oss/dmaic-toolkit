"""Measurement system analysis: how much of the variation you see is the act of measuring.

A crossed gage study has every operator measure every part several times, which lets the total
variation be split into the part-to-part variation you want and the measurement variation you do
not. The arithmetic is a two-factor random-effects ANOVA, and three parts of it are routinely
got wrong.

**The F tests need the right denominator.** In a random-effects model with an interaction, the
part and operator effects are tested against the *interaction* mean square, not the error mean
square. Testing them against error - which is what a fixed-effects routine does - inflates both
F statistics and declares operator effects significant that are not.

**Pooling the interaction is a decision, not a default.** AIAG drops the part-by-operator term
when it is not significant at 0.25 and pools it into repeatability. That is a reasonable rule and
it is not free: pooling a real interaction moves variation out of reproducibility, where it would
have pointed at method and training, into repeatability, where it points at the instrument. This
module applies the rule, reports which branch it took, and lets the caller override it.

**Percent contribution and percent study variation are not interchangeable.** Contribution is a
ratio of variances and the components sum to 100. Study variation is a ratio of standard
deviations and they do not. A gage at 30% of study variation is 9% of contribution, so quoting
contribution against the 10%/30% acceptance bands - which are written for study variation -
turns an unacceptable gage into an excellent one by squaring. Both are reported here, and
:meth:`GageStudy.verdict` reads the one the bands are for.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .._pandas import as_float, as_int

# AIAG's rule for retaining the part-by-operator term. Deliberately generous - 0.25 rather than
# 0.05 - because dropping a real interaction is the more expensive error here.
INTERACTION_ALPHA = 0.25

# Study variation bands for the gage repeatability and reproducibility share. These are written
# for percent study variation, never for percent contribution.
ACCEPTABLE = 10.0
MARGINAL = 30.0

# Spread of a normal distribution the study is scaled to. AIAG moved from 5.15 (99% of a normal)
# to 6.0 (99.73%), and the two give percent-tolerance figures 17% apart on identical data, so a
# study that quotes percent tolerance without stating its multiplier cannot be reproduced.
SIGMA_MULTIPLIER = 6.0

# Number of distinct categories, AIAG's constant. ndc is truncated rather than rounded.
NDC_CONSTANT = 1.41
NDC_ADEQUATE = 5

ANOVA_COLUMNS = ("source", "df", "ss", "ms", "f", "p_value")


@dataclass(frozen=True)
class GageStudy:
    """The outcome of one crossed gage study.

    Variance components are variances, not standard deviations. The standard deviations the
    acceptance rules are written in are the properties below.

    Attributes:
        gage: Label for the measurement system, carried through for reporting.
        anova: The ANOVA table, one row per source.
        parts: Number of parts in the study.
        operators: Number of operators.
        replicates: Measurements per part-operator cell.
        repeatability_var: Equipment variation, as a variance.
        operator_var: Operator bias, as a variance.
        interaction_var: Part-by-operator interaction, as a variance. Zero when pooled.
        part_var: Part-to-part variation, as a variance.
        interaction_pooled: Whether the interaction term was pooled into repeatability.
        interaction_p_value: The interaction's p-value, whatever was done with it.
        clamped: Components that came out negative and were set to zero. A negative variance
            component is an estimate, not a quantity, and it means the study is too small to
            resolve that effect - which is worth reporting rather than hiding behind a zero.
        tolerance: Specification width, when one was supplied.
        sigma_multiplier: The multiplier percent tolerance was computed with.
    """

    gage: str
    anova: pd.DataFrame
    parts: int
    operators: int
    replicates: int
    repeatability_var: float
    operator_var: float
    interaction_var: float
    part_var: float
    interaction_pooled: bool
    interaction_p_value: float
    clamped: tuple[str, ...]
    tolerance: float | None
    sigma_multiplier: float

    @property
    def ev(self) -> float:
        """Equipment variation: repeatability, as a standard deviation."""
        return float(np.sqrt(self.repeatability_var))

    @property
    def av(self) -> float:
        """Appraiser variation: reproducibility, as a standard deviation.

        Operator bias and the part-by-operator interaction together, because both are variation
        the measurement system contributes through the people using it.
        """
        return float(np.sqrt(self.operator_var + self.interaction_var))

    @property
    def grr(self) -> float:
        """Gage repeatability and reproducibility, as a standard deviation."""
        return float(np.sqrt(self.repeatability_var + self.operator_var + self.interaction_var))

    @property
    def pv(self) -> float:
        """Part variation, as a standard deviation."""
        return float(np.sqrt(self.part_var))

    @property
    def tv(self) -> float:
        """Total variation, as a standard deviation."""
        return float(np.sqrt(self.grr**2 + self.part_var))

    @property
    def pct_study(self) -> float:
        """GRR as a percentage of total study variation - the figure the bands are written for."""
        return 100.0 * self.grr / self.tv if self.tv > 0 else float("nan")

    @property
    def pct_contribution(self) -> float:
        """GRR as a percentage of total variance.

        The square of :attr:`pct_study`, and not comparable to the 10%/30% bands.
        """
        return 100.0 * self.grr**2 / self.tv**2 if self.tv > 0 else float("nan")

    @property
    def pct_tolerance(self) -> float:
        """GRR as a percentage of the specification width, or ``nan`` without a tolerance.

        This is the criterion that asks whether the gage can support the specification, which is
        a different question from whether it can resolve the parts actually being made. A
        capable process measured against a tight specification fails here while passing
        :attr:`pct_study`, and the gage is unusable for disposition either way.
        """
        if self.tolerance is None or self.tolerance <= 0:
            return float("nan")
        return 100.0 * self.sigma_multiplier * self.grr / self.tolerance

    @property
    def ndc(self) -> int:
        """Number of distinct categories the gage can tell apart, truncated.

        Below five the gage cannot support anything finer than a sorting decision, whatever the
        percentages say.
        """
        if self.grr <= 0:
            return 0
        return int(NDC_CONSTANT * self.pv / self.grr)

    @property
    def dominant_source(self) -> str:
        """Whether repeatability or reproducibility is the larger half of GRR.

        This is the whole diagnostic value of splitting them. Repeatability is the instrument:
        resolution, fixturing, wear. Reproducibility is the method: how operators are trained,
        how the reading is taken, whether the procedure is ambiguous. Buying a better instrument
        against a reproducibility problem changes nothing and is the commonest response to a
        failed study.
        """
        return "repeatability" if self.ev >= self.av else "reproducibility"

    def verdict(self) -> str:
        """The acceptance call, on the worst of the criteria that apply.

        Percent study variation always applies. Percent tolerance applies when a tolerance was
        supplied, and a gage has to pass both: one says it can see the process, the other says
        it can support the specification.
        """
        worst = self.pct_study
        if not np.isnan(self.pct_tolerance):
            worst = max(worst, self.pct_tolerance)
        if worst < ACCEPTABLE and self.ndc >= NDC_ADEQUATE:
            return "acceptable"
        if worst < MARGINAL and self.ndc >= NDC_ADEQUATE:
            return "conditional"
        return "unacceptable"

    def summary(self) -> pd.DataFrame:
        """The variation table a gage report is read from.

        One row per source, with the standard deviation and both percentages, so the difference
        between them is visible rather than a footnote.
        """
        sources = [
            ("repeatability (EV)", self.ev),
            ("reproducibility (AV)", self.av),
            ("gage R&R", self.grr),
            ("part variation (PV)", self.pv),
            ("total variation (TV)", self.tv),
        ]
        rows = []
        for name, sd in sources:
            rows.append(
                {
                    "source": name,
                    "std_dev": sd,
                    "pct_study_variation": 100.0 * sd / self.tv if self.tv > 0 else float("nan"),
                    "pct_contribution": 100.0 * sd**2 / self.tv**2 if self.tv > 0 else float("nan"),
                    "pct_tolerance": 100.0 * self.sigma_multiplier * sd / self.tolerance
                    if self.tolerance
                    else float("nan"),
                }
            )
        return pd.DataFrame(rows)


def anova(
    data: pd.DataFrame,
    value: str = "value",
    part: str = "part",
    operator: str = "operator",
) -> pd.DataFrame:
    """Two-factor ANOVA table for a balanced crossed gage study.

    Args:
        data: Tidy measurements, one row per reading.
        value: Column holding the measurement.
        part: Column identifying the part.
        operator: Column identifying the operator.

    Returns:
        A frame with the columns in :data:`ANOVA_COLUMNS`. The part and operator rows are tested
        against the interaction mean square, which is the correct denominator for a
        random-effects model; the interaction row is tested against error.

    Raises:
        ValueError: If the design is unbalanced, has fewer than two parts or operators, or has
            only one replicate per cell. A single replicate leaves no degrees of freedom for
            repeatability, so there is nothing to separate the interaction from.
    """
    frame = data[[part, operator, value]].dropna()
    counts = frame.groupby([part, operator], observed=True).size()
    if counts.empty:
        raise ValueError("no measurements to fit")
    replicates = int(counts.iloc[0])
    if not bool((counts == replicates).all()):
        raise ValueError(
            "the design is unbalanced: every part-operator cell needs the same number of "
            "measurements for this decomposition to hold"
        )
    n_parts = int(frame[part].nunique())
    n_operators = int(frame[operator].nunique())
    if n_parts < 2 or n_operators < 2:
        raise ValueError("a crossed study needs at least two parts and two operators")
    if replicates < 2:
        raise ValueError(
            "a single measurement per cell leaves no degrees of freedom for repeatability; "
            "the interaction and the error term cannot be separated"
        )
    if counts.size != n_parts * n_operators:
        raise ValueError("the design is not crossed: some operators did not measure some parts")

    grand = float(frame[value].mean())
    part_means = frame.groupby(part, observed=True)[value].mean()
    operator_means = frame.groupby(operator, observed=True)[value].mean()
    cell_means = frame.groupby([part, operator], observed=True)[value].mean()

    ss_part = n_operators * replicates * float(((part_means - grand) ** 2).sum())
    ss_operator = n_parts * replicates * float(((operator_means - grand) ** 2).sum())
    # The interaction is what is left of the cell means once both main effects are removed.
    cell_frame = cell_means.rename("cell").reset_index()
    cell_frame["residual"] = (
        cell_frame["cell"]
        - cell_frame[part].map(part_means).astype(float)
        - cell_frame[operator].map(operator_means).astype(float)
        + grand
    )
    ss_interaction = replicates * float((cell_frame["residual"] ** 2).sum())
    joined = frame.merge(cell_means.rename("cell"), on=[part, operator], how="left")
    ss_error = float(((joined[value] - joined["cell"]) ** 2).sum())
    ss_total = float(((frame[value] - grand) ** 2).sum())

    df_part = n_parts - 1
    df_operator = n_operators - 1
    df_interaction = df_part * df_operator
    df_error = n_parts * n_operators * (replicates - 1)

    ms_part = ss_part / df_part
    ms_operator = ss_operator / df_operator
    ms_interaction = ss_interaction / df_interaction
    ms_error = ss_error / df_error

    # Random-effects denominators: main effects against the interaction, interaction against
    # error. Using error for the main effects is the common mistake and inflates both F values.
    f_part = ms_part / ms_interaction if ms_interaction > 0 else float("nan")
    f_operator = ms_operator / ms_interaction if ms_interaction > 0 else float("nan")
    f_interaction = ms_interaction / ms_error if ms_error > 0 else float("nan")

    def survival(f: float, numerator_df: int, denominator_df: int) -> float:
        if not np.isfinite(f) or f <= 0:
            return float("nan")
        return float(stats.f.sf(f, numerator_df, denominator_df))

    return pd.DataFrame(
        [
            {
                "source": "part",
                "df": df_part,
                "ss": ss_part,
                "ms": ms_part,
                "f": f_part,
                "p_value": survival(f_part, df_part, df_interaction),
            },
            {
                "source": "operator",
                "df": df_operator,
                "ss": ss_operator,
                "ms": ms_operator,
                "f": f_operator,
                "p_value": survival(f_operator, df_operator, df_interaction),
            },
            {
                "source": "part * operator",
                "df": df_interaction,
                "ss": ss_interaction,
                "ms": ms_interaction,
                "f": f_interaction,
                "p_value": survival(f_interaction, df_interaction, df_error),
            },
            {
                "source": "repeatability",
                "df": df_error,
                "ss": ss_error,
                "ms": ms_error,
                "f": float("nan"),
                "p_value": float("nan"),
            },
            {
                "source": "total",
                "df": n_parts * n_operators * replicates - 1,
                "ss": ss_total,
                "ms": float("nan"),
                "f": float("nan"),
                "p_value": float("nan"),
            },
        ]
    )[list(ANOVA_COLUMNS)]


def gage_rr(
    data: pd.DataFrame,
    value: str = "value",
    part: str = "part",
    operator: str = "operator",
    tolerance: float | None = None,
    interaction_alpha: float = INTERACTION_ALPHA,
    sigma_multiplier: float = SIGMA_MULTIPLIER,
    gage: str = "",
) -> GageStudy:
    """Fit a crossed gage study and decide whether the measurement system is good enough.

    Args:
        data: Tidy measurements, one row per reading.
        value: Column holding the measurement.
        part: Column identifying the part.
        operator: Column identifying the operator.
        tolerance: Specification width. Omitted rather than guessed when unknown, because a
            percent-tolerance figure computed against an invented specification is worse than no
            figure: it reads like evidence.
        interaction_alpha: Significance above which the part-by-operator term is pooled into
            repeatability, following AIAG's rule of pooling what is not significant. The
            comparison is ``p_value > interaction_alpha``, so ``0.0`` pools the interaction
            unconditionally and ``1.0`` keeps it unconditionally - the opposite way round from
            how a significance level usually reads, which is why it is spelled out here.
        sigma_multiplier: Normal spread the study is scaled to, for percent tolerance only.
            Percent study variation is a ratio and does not depend on it.
        gage: Label carried into the result for reporting.

    Returns:
        A :class:`GageStudy`.
    """
    table = anova(data, value=value, part=part, operator=operator)
    indexed = table.set_index("source")
    frame = data[[part, operator, value]].dropna()
    n_parts = int(frame[part].nunique())
    n_operators = int(frame[operator].nunique())
    replicates = int(frame.groupby([part, operator], observed=True).size().iloc[0])

    ms_part = as_float(indexed.loc["part", "ms"])
    ms_operator = as_float(indexed.loc["operator", "ms"])
    ms_interaction = as_float(indexed.loc["part * operator", "ms"])
    ms_error = as_float(indexed.loc["repeatability", "ms"])
    interaction_p = as_float(indexed.loc["part * operator", "p_value"])

    pooled = bool(np.isnan(interaction_p) or interaction_p > interaction_alpha)
    if pooled:
        # Pooling folds the interaction's sum of squares and degrees of freedom back into the
        # error term, and the main effects are then tested against that pooled estimate.
        ss_pooled = as_float(indexed.loc["part * operator", "ss"]) + as_float(
            indexed.loc["repeatability", "ss"]
        )
        df_pooled = as_int(indexed.loc["part * operator", "df"]) + as_int(
            indexed.loc["repeatability", "df"]
        )
        repeatability = ss_pooled / df_pooled
        interaction_var = 0.0
        operator_var = (ms_operator - repeatability) / (n_parts * replicates)
        part_var = (ms_part - repeatability) / (n_operators * replicates)
    else:
        repeatability = ms_error
        interaction_var = (ms_interaction - ms_error) / replicates
        operator_var = (ms_operator - ms_interaction) / (n_parts * replicates)
        part_var = (ms_part - ms_interaction) / (n_operators * replicates)

    clamped = []
    for name, component in (
        ("interaction", interaction_var),
        ("operator", operator_var),
        ("part", part_var),
    ):
        if component < 0:
            clamped.append(name)
    interaction_var = max(interaction_var, 0.0)
    operator_var = max(operator_var, 0.0)
    part_var = max(part_var, 0.0)

    return GageStudy(
        gage=gage,
        anova=table,
        parts=n_parts,
        operators=n_operators,
        replicates=replicates,
        repeatability_var=repeatability,
        operator_var=operator_var,
        interaction_var=interaction_var,
        part_var=part_var,
        interaction_pooled=pooled,
        interaction_p_value=interaction_p,
        clamped=tuple(clamped),
        tolerance=tolerance,
        sigma_multiplier=sigma_multiplier,
    )

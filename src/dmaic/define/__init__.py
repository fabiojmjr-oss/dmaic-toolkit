"""Define: the decisions a charter makes before anybody looks at data.

The phase has the least arithmetic in it and the most leverage. A charter fixes the measurand, the
baseline window, the target and the benefit, and each of those moves the answer - so written as
prose they read as description, and written as arithmetic they turn out to disagree.

:mod:`~dmaic.define.charter` computes them. Its finding is the mirror image of
:mod:`dmaic.improve`'s: a project is chartered *from* a recent bad baseline and *towards* the best
site's observed performance, and both of those are the most inflated estimate available. The worst
performer of a short window was partly unlucky and comes back up; the best performer was partly
lucky and goes back down. The two errors add, and a quarter of a one-period entitlement gap turns
out not to exist.

The benefit case a charter promises is built by the same class the Improve phase audits it with,
which is deliberate: a promise computed differently from the way it will be verified has a
discrepancy built into it that somebody will later have to explain.
"""

from .charter import (
    CTQ_COLUMNS,
    ENTITLEMENT_COLUMNS,
    GAP_COLUMNS,
    TARGET_BASES,
    Charter,
    Ctq,
    Entitlement,
    ctq_table,
    entitlement,
    entitlement_inflation,
    gap_by_window,
    overattribution,
)

__all__ = [
    "CTQ_COLUMNS",
    "ENTITLEMENT_COLUMNS",
    "GAP_COLUMNS",
    "TARGET_BASES",
    "Charter",
    "Ctq",
    "Entitlement",
    "ctq_table",
    "entitlement",
    "entitlement_inflation",
    "gap_by_window",
    "overattribution",
]

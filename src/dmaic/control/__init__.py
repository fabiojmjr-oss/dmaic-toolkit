"""Control: what the plan guarantees, rather than what its name suggests.

The Control phase of a project is where a gain is supposed to be held, and the artefacts it
produces - a control plan, a sampling plan, an inspection instruction - are usually written as
thresholds. They are not thresholds. A sampling plan is a curve, and almost every argument about
one is an argument about a single point on a curve nobody drew.

:mod:`~dmaic.control.sampling` draws it. It measures the three claims a plan is usually defended
with: that inspecting a fixed share of the lot is a policy, that an acceptance quality level is a
promise about outgoing quality, and that refusing to accept any defective is the strictest rule
available. None of the three survives its own operating characteristic curve.

:mod:`~dmaic.control.sustain` asks the other Control question: did the gain hold? The check almost
always compares the current months to the original baseline, which is the before-and-after the
Improve phase already showed is inflated by the trend - except that by now the trend has had twice
as long to run, so a decaying gain reports as a growing one. A comparison group fixes the direction
and not the power, and the module prices both.

**Control charts are deliberately not here.** Charts, run rules and capability against
within-subgroup sigma live in the sibling ``oplab.spc`` package. Putting the same code in two
repositories under one name would read as padding to anyone who opens both.
"""

from .sampling import (
    DECISION_COLUMNS,
    DEFAULT_CONSUMER_RISK,
    DEFAULT_PRODUCER_RISK,
    MAX_SAMPLE,
    OC_COLUMNS,
    SamplingPlan,
    inspect_lots,
    matched_plan,
    oc_curve,
    percentage_plan,
    plan_for,
)
from .sustain import (
    DETECTION_COLUMNS,
    REPORTED_COLUMNS,
    RETENTION_COLUMNS,
    SustainAudit,
    decay_detection,
    reported_gain,
    retention_path,
    sustain_audit,
)

__all__ = [
    "DECISION_COLUMNS",
    "DETECTION_COLUMNS",
    "DEFAULT_CONSUMER_RISK",
    "DEFAULT_PRODUCER_RISK",
    "MAX_SAMPLE",
    "OC_COLUMNS",
    "REPORTED_COLUMNS",
    "RETENTION_COLUMNS",
    "SamplingPlan",
    "SustainAudit",
    "decay_detection",
    "inspect_lots",
    "matched_plan",
    "oc_curve",
    "percentage_plan",
    "plan_for",
    "reported_gain",
    "retention_path",
    "sustain_audit",
]

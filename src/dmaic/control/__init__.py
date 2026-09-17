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

:mod:`~dmaic.control.plan` asks what the plan's triggers actually promise. A reaction rule is a
test, run every period, with a false-alarm rate and a detection delay - and a plan records
neither. Worse, the two ways of writing one fail in opposite directions: an absolute trigger has a
false-alarm rate the measurement system controls, and a trigger set from observed spread has a
*detection limit* the measurement system controls while its alarm rate stays put. There is no form
of words that escapes the gage; there is only a choice about where it hides.

**Control charts are deliberately not here.** Charts, run rules and capability against
within-subgroup sigma live in the sibling ``oplab.spc`` package. Putting the same code in two
repositories under one name would read as padding to anyone who opens both.
"""

from .plan import (
    DEFAULT_SIGMAS,
    PERIODS_PER_YEAR,
    RULE_COLUMNS,
    SPEC_COLUMNS,
    ReactionRule,
    alarms_against_delay,
    capability,
    compare_gages,
    rule_from_spread,
    spec_trigger,
)
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
    "DEFAULT_SIGMAS",
    "DEFAULT_PRODUCER_RISK",
    "MAX_SAMPLE",
    "OC_COLUMNS",
    "PERIODS_PER_YEAR",
    "REPORTED_COLUMNS",
    "RETENTION_COLUMNS",
    "RULE_COLUMNS",
    "SPEC_COLUMNS",
    "ReactionRule",
    "SamplingPlan",
    "SustainAudit",
    "alarms_against_delay",
    "capability",
    "compare_gages",
    "decay_detection",
    "inspect_lots",
    "matched_plan",
    "oc_curve",
    "percentage_plan",
    "plan_for",
    "reported_gain",
    "retention_path",
    "rule_from_spread",
    "spec_trigger",
    "sustain_audit",
]

"""A DMAIC toolkit.

One module per phase, so the package reads the way an improvement project runs:

- ``dmaic.measure`` - is the measurement system good enough to detect what you are looking for?

Later phases are added as waves land; ``docs/ROADMAP.md`` says what is built and what is not.

Statistical process control - control charts, run rules, capability against within-subgroup
sigma - is deliberately *not* reimplemented here. It lives in the sibling ``oplab.spc`` package,
and duplicating it would put the same code in two repositories under one name.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]

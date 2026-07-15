"""Cypher-DDS's two brand accent colors.

These are deliberately reserved for *status meaning*, not used as the base
palette: Royal Blue marks "connected / live data" and the currently focused
panel; Cherry Red marks DTC alerts and errors. Every other widget in any
presentation layer should keep using that layer's own default theme colors
so these two stay meaningful instead of decorative.

Validated against a dark terminal surface (#1e1e1e) with the data-viz
skill's palette validator: both clear 3:1 contrast, sit inside the dark
OKLCH lightness band, and are ~110-120 dE apart (well past the CVD-safety
target), so they read as distinct to colorblind users too.

Lives above cypher_dds.tui / cypher_dds.mobile (and any future desktop GUI)
rather than inside one of them, since the brand identity is shared across
all presentation layers, not owned by any single one — same reasoning as
cypher_dds.session sitting above the presentation layers for orchestration
logic. Anything that needs one of these accents should import the constant
from here rather than hardcoding the hex, so there is exactly one place to
retune them.
"""

ROYAL_BLUE = "#4169E1"
"""Status: connected / live data. Also used for the focused-panel border."""

CHERRY_RED = "#D2042D"
"""Status: DTC alert / error."""

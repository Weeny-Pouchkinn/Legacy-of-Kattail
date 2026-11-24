# Painter UI alignment — 2026-11-24

Scope: match the EU4 painter's native light controls, compact toolbar, left
sidebar and dark map canvas. Preserve the HOI4 prototype's memory-only behavior,
source fields, state brushes and tintable flags. No game-data changes.

- [x] Compare both implementations and read project memory/instructions.
- [x] Apply the layout and styling changes in `legacy_of_kattail_painter/painter.py`.
- [x] Compile, run existing fixtures, exercise actual Tk controls with real data,
  and review the targeted diff. Update status and decisions with observed results.

The existing painter directory is untracked. Ordinary Git diffs do not include
it; review its complete source and `git diff --no-index` against `/dev/null`.
An attempted temporary baseline did not remain accessible across tool calls.
Earlier memory entries describe another branch; do not treat them as current
validation of `Legacy-of-Kattail-Main`.

Outcome: 11 fixtures and real-data UI/isolation checks passed. Geometry checks
passed at normal/minimum sizes. Existing railway and OOB errors remain unrelated.
Desktop screenshot inspection was unavailable; native Tk controls were exercised
programmatically. See CURRENT_STATUS.md for exact validation and limits.

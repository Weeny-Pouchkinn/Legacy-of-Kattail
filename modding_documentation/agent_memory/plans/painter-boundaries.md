# Species checks and paint boundaries — 2026-11-24

- [x] Inspect current model/UI, project memory and strategic-region membership.
- [x] Enforce distinct majority/minority across setters, loaded data and Save;
  repair the three existing invalid state histories with guarded backups.
- [x] Add independent 1/2/3 display-pixel province/state/strategic-region borders.
- [x] Add State/Strategic region scope for all brushes, grouped undo and drag
  deduplication. Refuse region painting across split state definitions.
- [x] Test fixtures, real-data UI, no-source-write rendering, map baseline and
  full diff; update memory and controls documentation.

Baseline: clean tree at `ee25bc98`. Equal species/minority: states 1040 (0),
447 (1), 888 (44). The map defines 413 strategic regions; no province appears
in two regions, all state provinces have regions, and no state spans regions.
Rendering and scope must use current province membership, never hard-coded IDs.
No map topology, region definitions or localisation changes are requested.

Completed: 24 tests pass and four changed Python files compile. Actual Tk checks
exercised all boundary toggles, all eight views, two window sizes, a five-state
region brush, grouped undo/redo and raw-source auto-repair. `verify_real.py`
passed 1,026 mask renders and 10,786 unchanged hashes during UI-only checks.
Map validator before/after reports the same two railway non-neighbor errors.
Only minorities in states 447, 888 and 1040 changed on disk, each to 1000;
backups: legacy_of_kattail_painter/backups/save_20261124_104605_259819/.
No game launch claimed.

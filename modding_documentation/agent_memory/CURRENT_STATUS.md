# Current status

## Painter interface alignment (2026-11-24)

Current branch verified as `Legacy-of-Kattail-Main`. The older sections below
describe work on `jublio-system-backport`; their branch/validation statements are
historical, not a verified status of the current branch.

Changed `legacy_of_kattail_painter/painter.py` to follow the EU4 painter's native
ttk light styling, compact toolbar, left sidebar and dark map canvas. State
controls moved into a scrollable sidebar tab; map/source/flag tabs remain.
Flag previews resize without changing native flag dimensions or mask tinting.
No game scripts, map data, export behavior or game identifiers changed.

Validation: Python compilation and all 11 existing fixture tests passed.
`verify_real.py` exercised real-data Tk controls, demographic drafts, undo/redo,
source filtering and flags; 1,023 renders passed and 10,786 source hashes stayed
unchanged. Additional live Tk geometry checks passed at 1500x900 and 1050x680,
including all tabs, all eight views, state scrolling and preview aspect ratio.
Native `vista` theme was retained. Screenshot inspection was unavailable because
the desktop helper required a usable `CODEX_CLI_PATH`; no screenshot review is
claimed. No game launch was performed.

`python -B tools/validate_map.py` reports railway non-neighbor links on lines
893-894 (20839/20841 and 20841/19461), matching the earlier diagnostic notes.
Map files were untouched. The real-data parser still reports excess closing
braces in EUL/GAL/KKN/KTZ OOBs, already documented in the painter README.

The painter folder was already untracked before this task. Next action: restart
the painter to load the new interface and review its appearance on the user's
display. No implementation blocker remains.

## Jublio system backport (2026-11-04)

Branch `jublio-system-backport`, based on `3abc65d2`. Installed in the working tree, not committed.

**Done:** map grown to 4096x3072 with EU4's solar system chart in rows 0..887; 12 new bodies;
18 Doughland nations at their 100 AKA borders; 11 NPC planet tags; 10 terrains; 12 continents.

**First launch (2026-11-04):** reached nation select, showed a map error warning, then crashed at
game start. Six map errors were logged; all are fixed in the current build.

**Validated (static only):** `work/legacy-kattail-hoi4-space/check_stage.py` passes, including
rules taken from that `error.log`. `tools/validate_map.py` reports the same 2 issues as before the
change, both in `railways.txt` lines 893-894.

**Not validated:** the current build has not been launched, so the crash fix is unconfirmed.
Rendering, AI behaviour and balance are unknown.

**Next action:** launch once and read `error.log`.

**Not done:** space programme decisions for the new bodies; superregion map mode entries;
per-culture state names; final flags.

Generator and full notes: `universal-modder/work/legacy-kattail-hoi4-space/` (`MODLOG.md`). It
reads a pristine export of git HEAD, so re-export it if HEAD moves.

## Conquest release fixes (2026-11-04)

Same branch, uncommitted, independent of the Jublio work. Changed `decide_fate_of_nation`,
`return_occupied_cores_to_puppet`, `lok_peace.1` and `lok_create_blank_occupation_puppet`; added
`common/scripted_triggers/lok_peace_triggers.txt`.

**Validated (static only):** braces and line endings checked, diff reviewed. Not launched.

**Next action:** in game, have two nations carve up a third and release, then check each puppet's
cores match its own land. Then puppet a nation, take more of its land, and confirm only "Return
Territories" shows.

**Unverified:** whether `FROM` keeps its value inside `create_dynamic_country`; what the engine does
when the dynamic tag pool runs out (a failure is only written to `game.log`).

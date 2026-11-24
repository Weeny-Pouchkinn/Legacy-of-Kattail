# Current status

## EU4 nations in ZZZ territory (2026-11-24)

Installed on Legacy-of-Kattail-Main: 39 countries receive 320 former ZZZ states;
84 remain ZZZ. Reused 34 identities (12 dormant), with LRN -> LAK and NOV -> NFS;
new tags ELC/HIV/INT/MAG/WMD. User explicitly retained all states and excluded
Meogartha. Added missing histories/source leaders, native-sized source flags,
source colours and country species laws. Preserved existing country history/text,
state demographics, all map data and unrelated working edits.

Validation: importer verification passes 631 game output files and 12,102 protected
files. 320 states match originals outside owner/core changes; 234 flags pass exact
pixel/dimension checks. 82 new localisation keys are unique and BOM/header pass.
Localisation analyser's pre/post missing-key sets are identical (2,285); Python
compilation and diff checks pass. Map validator still reports only the existing
railway errors at 893-894. No CWTools executable or in-game validation.

Limits: whole-state geographic approximation; WMD uses its only assigned state 331
because its source capital does not overlap eligible land. Missing histories use
an explicit small starting baseline; unrelated/missing OOBs become an empty OOB.
No force/balance or mission conversion. Existing authored country names prevail.

Exact paths, country mapping, source provenance, validation and recovery:
`eu4_zzz_import/README.md`, `files.txt` and `audit.json`. Tool:
`tools/import_zzz_from_eu4.py --verify`. Originals:
`work/zzz-eu4-import/before/`. Next action: fresh campaign/startup-log check.

## Species invariant, boundary toggles and region brushes (2026-11-24)

Completed on `Legacy-of-Kattail-Main`, based on `ee25bc98`:

- Equal majority/minority species now clears the minority to 1000 in shared
  setters, load/normalisation, raw source edits and the pre-save hook. Majority
  1000 is rejected because it denotes None, not a species. Corrected the three
  existing equal pairs: 447 (1), 888 (44), 1040 (0). Only each minority changed;
  originals are in legacy_of_kattail_painter/backups/save_20261124_104605_259819/.
- Independent boundary toggles draw province/state/strategic-region lines at
  1/2/3 screen pixels. They are off by default and cached at the current zoom.
- State/Strategic region scope applies to culture, majority/minority and owner
  brushes. Region membership comes from map/strategicregions, not country tags
  or a hard-coded state list. Each regional action is grouped for undo/redo,
  deduplicated across a drag and rolled back completely if an edit fails.
  Split states block region painting before any changes. The current 413
  regions have no split states or ambiguous province memberships.

Validation: all 24 fixture tests and four Python compile checks pass. Exact
boundary pixels and width after zoom, source/Save invariant, region membership,
owner/demographic brushes, grouped undo, exclusions, split-state rejection and
failure rollback are covered. Real-data Tk checks passed all toggles, all eight
views, normal/minimum layouts, region 1's five-state painting/undo/redo and raw
source auto-repair. `verify_real.py` passed 1,026 mask-size renders and 10,786
unchanged source hashes during UI-only checks. Existing EUL/GAL/KKN/KTZ OOB brace
errors remain. Map validator before/after has the same railway errors at 893-894;
no map files or localisation changed. Full diff and encoding reviewed.

Next action: restart the painter, select Paint scope and boundary checkboxes.
No new implementation blocker; no in-game validation or screenshot review is
claimed. Map memberships are startup snapshots; restart after topology edits.
Exact changed paths and commands are in legacy_of_kattail_painter/MODLOG.md.

## Persistent state painting and demographic migration (2026-11-24)

Completed on `Legacy-of-Kattail-Main`, based on `a8d83c64`. This supersedes the
read-only limitation in the earlier interface-alignment entry below.

- Applied initial demographics to all 1,902 state-history files and removed
  1,655 startup assignment statements from `common/on_actions/LOK_on_actions.txt`.
  All original culture order/values, majority and minority values are unchanged.
  Four three-culture states (894-897) retain all entries. Runtime `state_cultures`,
  `species`, `minority`, global culture-group catalogs, country species ideas and
  subsequent gameplay/derived-modifier effects are preserved.
- Painter now supports Save/Ctrl+S, exact-byte external-edit checks, source
  backups and rollback for write failures. Source-field drafts also save. Flags
  remain session-only. Backups/bytecode are excluded by the painter's .gitignore.
- Left palette lists named cultures/species/countries with defined-colour swatches.
  Culture has Set/Add/Remove; species has independent Majority/Minority brushes
  and No minority (1000). Species rendering overlays minority-coloured stripes.
  Shift-click picks the assignment and suppresses painting for that gesture.
- Actual map-mode definitions supply 101 culture colours and 61 species colours.
  Named culture 102 (Katzenurkisch) has no defined colour; it remains selectable
  with a labelled grey fallback. All currently assigned IDs have defined colours.

Validation: 16 fixture tests pass, covering save/reload, stale-source rejection,
rollback, BOM/newlines, migration application, exact pixels/stripes and existing
functionality. All seven changed/new Python files compile. Full live-state checks
prove one demographic block per state, exact initial-value equality, preserved
BOM/newlines and identical state text outside the inserted blocks. Surviving
startup syntax trees retain all unrelated effects and ordering.

Real-data checks exercised palettes (102 cultures, 61 majority/62 minority
choices), actual province painting, independent species fields, undo/redo,
all eight views and normal/minimum layouts. `verify_real.py` passed 1,026 mask-size
renders and 10,786 unchanged source hashes during UI-only checks. Four existing
EUL/GAL/KKN/KTZ OOB brace errors remain. `git diff --check` passed. Map validation
before and after reports the same two railway errors on lines 893-894; no map,
localisation or binary graphics files changed. No CWTools executable was found.

Original migration backups:
`legacy_of_kattail_painter/backups/migration_20261124_101441_420939/` (all 1,903
original sources). Exact changed paths are in `plans/painter-editing-files.txt`;
commands/results are in the painter MODLOG.md.

Next action: restart the painter and use Paint > select entry > click/drag > Save.
Fresh-campaign engine validation of state-history initialisation remains pending;
no game launch or screenshot inspection is claimed. Migration runs earlier than
the removed startup assignments, so static equality does not prove timing
equivalence with arbitrary earlier startup effects.

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

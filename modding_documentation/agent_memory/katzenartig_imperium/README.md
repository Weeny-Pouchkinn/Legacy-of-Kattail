# Katzenartig Imperium elements and mapmode - 2026-11-25

## Color policy update - 2026-11-26

Per user request, duplicate element colors are now allowed, including the
unassigned gray. Removed both Apply and Save uniqueness restrictions and changed
the dialog label to Map color. IDs, assignments and tooltip text remain distinct;
color is display data only. Earlier unique/reserved-color statements below are
historical and superseded by this update. No live definitions or states changed.

Changed `legacy_of_kattail_painter/imperium_model.py`, `imperium_ui.py`,
`test_imperium.py`, `README.md`, `MODLOG.md`, this report and
`modding_documentation/agent_memory/CURRENT_STATUS.md`.
Validation: the three Python files compile; `python -B -m unittest discover -s
legacy_of_kattail_painter -p 'test_imperium.py'` passes all 10 tests. Regression
checks duplicate-color creation, distinct state pointers/tooltips after
Save/reload, and editing to unassigned gray without erasing the assignment.
Scoped diff/whitespace reviewed. No engine test; no engine script change.

Implemented a reusable object catalog under States > Katzenartig Imperium,
also exposed in MAP > Definitions alongside cultures/species, and in the geography
database. Objects have stable numeric ID, name, unique RGB and independently
authored immediate/delayed tooltips. Selecting an object paints whole states;
right-drag or No element clears, Shift-click picks. Edits to an object affect all
its states. State names, overlays and PNG export use existing controls.

The user's example `[FROM.GetName] was part of the Schutzone Pegasien` works as
an immediate string; the hovered state's localized name replaces the token.
Both text fields support multiline text, native tokens and formatting. Painter
preview expands name/localization tokens and displays plain text, adding delayed
text after 650 ms; arbitrary game expressions remain literal in the preview.

Initial native definitions and assignments are empty. No historical borders,
MCF assignments, names or narrative were inferred. The disposable UI probe used
the example object only in memory and restored its drafts before exiting.

## Files changed for this task

| Path | Purpose |
| --- | --- |
| `legacy_of_kattail_painter/imperium_model.py` | Reusable objects, native color/text persistence, assignment/validation/preview |
| `legacy_of_kattail_painter/imperium_ui.py` | New/Edit object dialog and timed canvas hover |
| `legacy_of_kattail_painter/painter.py` | States category/palette, definitions database, paint/erase/pick, Save validation |
| `legacy_of_kattail_painter/geography_ui.py` | Geography database access and object editing |
| `legacy_of_kattail_painter/model.py` | State assignment colors, water/unassigned colors |
| `legacy_of_kattail_painter/map_render.py` | State-name family for the new layer |
| `legacy_of_kattail_painter/install.py` | Module/test distribution manifest |
| `legacy_of_kattail_painter/test_imperium.py` | Nine regression tests including mapped Tk forms/hover |
| `common/map_modes/LOK_katzenartig_imperium_map_mode.txt` | Empty native mapmode/catalog scaffold |
| `common/scripted_localisation/LOK_katzenartig_imperium_scripted_loc.txt` | Immediate/delayed dispatchers, unassigned fallback |
| `localisation/english/lok_katzenartig_imperium_l_english.yml` | BOM English title, description and wrappers |
| `legacy_of_kattail_painter/README.md` | User workflow |
| `legacy_of_kattail_painter/MODLOG.md` | Change/validation record |
| `modding_documentation/agent_memory/CURRENT_STATUS.md` | Current result and engine follow-up |
| `modding_documentation/agent_memory/DECISIONS.md` | Architecture/rationale |
| `modding_documentation/agent_memory/plans/katzenartig-imperium-mapmode.md` | Completed milestones |
| `modding_documentation/agent_memory/katzenartig_imperium/README.md` | This report |
| `modding_documentation/agent_memory/katzenartig_imperium/scaffold.json` | Guarded scaffold creation audit/hashes/backup |
| `modding_documentation/agent_memory/katzenartig_imperium/verification.json` | Native UI/hash-check evidence |

No state history or bitmap was written for this task. Later painting saves only
the owned assignment in each painted state's existing source, preserving dated
history, comments, other variables, ownership and buildings. All definitions,
texts and assignments use normal atomic draft/Undo/Redo/Cancel/guarded Save.

## Native identifiers and representation

- Mapmode: `LOK_katzenartig_imperium_map_mode`.
- State variable: `lok_katzenartig_imperium_element`; zero/unset is unassigned.
  Positive IDs are stable; maximum 2,147,483 for native fixed-point safety.
- Scripted-localization functions: `GetKatzenartigImperiumTooltip` and
  `GetKatzenartigImperiumTooltipDelayed`.
- Generated per-object keys: `lok_ki_element_<id>_name`,
  `lok_ki_element_<id>_tooltip`, `lok_ki_element_<id>_tooltip_delayed`.
- Native wrapper keys: `LOK_katzenartig_imperium_map_mode_tooltip` and
  `LOK_katzenartig_imperium_map_mode_tooltip_delayed`.
- Mapmode title keys: `MAPMODE_LOK_KATZENARTIG_IMPERIUM_MAP_MODE`, plus
  `_NAME` and `_DESCRIPTION`.
- Unassigned keys: `lok_ki_unassigned_tooltip` (state name),
  `lok_ki_unassigned_tooltip_delayed` (empty).
- Unassigned RGB: `(65, 69, 78)`; reserved from the element palette. Element
  colors are distinct byte RGBs saved as nearest 0.001 fractions, matching the
  demographic color writer. Color `if` branches test `FROM` (rendered state).

Uses the existing custom scripted-mapmode infrastructure; no new runtime
on-action, global iterator, sprite, GUI replacement or metadata file.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **169 tests pass**, including nine new regression tests. Covers independent
  objects/colors, shared updates, manual texts, native dispatcher output,
  source-preserving state edits, dated history, long-form variables, erase,
  Undo/Redo, atomic errors, Save/reload/BOM, real dialogs/database/selection,
  actual immediate/delayed hover and cleanup.
- `python -m py_compile` on `imperium_model.py`, `imperium_ui.py`, `painter.py`,
  `geography_ui.py`, `model.py`, `map_render.py`, `install.py`, `test_imperium.py`
  under `legacy_of_kattail_painter/`: passed. Cache redirected to system Temp.
- `python -B tools/validate_map.py`: passed; 21,515 provinces, 20,926
  state-assigned provinces, 413 strategic regions, no X crossings.
- Native mapped Tk probe with actual mod data: New/Edit via reusable definition
  catalog, exact palette/map RGB, whole-state assignment/erase/Undo, shared
  changes, overlay, state name and genuinely timed hover passed. Live Save was
  forbidden; zero callback errors; **4,321 native source hashes unchanged**.
  Zero persisted elements or state assignments. Evidence: `verification.json`.
- Localization analyzer's `parse_yml_file()` used for the new English file;
  seven keys parsed. English BOM/header, unique owners of all seven keys,
  unique definitions of both tooltip functions, native parsed blocks, installer
  file existence and new-source whitespace checked separately. Whole-project
  analyzer `main()` was not run; it rewrites an unrelated diagnostic snapshot.
- `git diff --check -- legacy_of_kattail_painter`: passed. New source files
  checked separately because untracked files are not included by Git diff.
  Whole `git diff --check` reports retained whitespace in culture mapmode,
  on-actions, culture triggers and state histories predating this task.
  `git diff --stat` and implementation diff reviewed; unrelated user/previous
  task edits retained.

## Sources and scope verification

- Installed primary documentation:
  `C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV/common/map_modes/documentation.md`,
  example opening/name keys, `type = state`, player/FROM scope comments, RGBA
  outputs, `near_text`, `update_daily` sections. Confirms mode-derived tooltip
  keys and rendered state in FROM. Optional mapmode icons follow existing mod
  practice rather than adding invented art.
- Nearby native example: `common/map_modes/LOK_superregion_map_mode.txt`.
- `common/scripted_localisation/LOK_scripted_localisation.txt`,
  `GetSubstatesTooltip` around line 985: variable-based state text dispatch.
- `localisation/english/lok_map_mode_l_english.yml` around line 104: existing
  `[FROM.GetSubstatesTooltip]` wrapper and `[FROM.GetName]` state-name convention.
- `legacy_of_kattail_painter/imperium_model.py`: authoritative implementation
  of native branch catalog, source-targeted state writes and generated keys.

## Limits, recovery and remaining work

HOI4 and CWTools were not run. Engine rendering, custom mapmode visibility and
actual immediate/delayed text scope must still be exercised in game. After
authoring an element and painting it, Save, restart HOI4 and start a fresh
campaign to load the changed state history. Inspect assigned/unassigned colors
and both tooltip stages. Do not claim historical extent until authored.

The scaffold audit contains the guarded backup location and hashes. The three
new native files were initially absent; remove/restore them only after confirming
they have not since received user definitions. Future writes use normal painter
backups and readback verification. No rollback of unrelated user edits is valid.

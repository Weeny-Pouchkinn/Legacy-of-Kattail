# State boundary editor - 2026-11-27

## Completed behavior

States > State boundaries adds a destination-state palette, province brush,
per-stroke preview/atomic application, Shift-pick and a New state dialog.
New states use a user-entered name and seed province. State IDs exceed all live
and allocated session IDs, skipping existing STATE_<id> localisation keys.
Undo/Redo/Discard/Save synchronize the state index, membership, region-state
index, inspectors, palettes and boundary/label caches. New files remain drafts
until normal conflict-checked, backed-up Save; source formatting uses the existing
tab-aware formatter. Names use the existing UTF-8-BOM state localisation file.

Only existing assigned land provinces can be brushed. Native lake memberships
remain assigned and receive no automatic building models. Donors must retain
land; every affected state stays wholly within one strategic region. The set of
assigned province IDs is invariant. Province geometry and definition IDs do not
change. New states inherit root attributes/category, ordered political setup and
dated ownership/core/claim changes, infrastructure intensity, demographics and
Imperium assignment. Existing legacy supply areas gain the new state when their
state list contains its parent. Province-addressed VP pairs/building blocks move
at base and direct dated history scopes. Province IDs and VP localisation,
railways, global supply nodes and unitstacks do not change.

## Estimates

Population/resources on; industry off by default. Each stroke snapshots its
donor and receiver profiles once, then allocates each original state's quantities
to destinations of its original provinces. It does not round after each mouse
motion. Largest remainders use state-ID ties; totals are conserved. Population
and building counts are integers, including sources written as 3310000.0.
Fractional resource precision is retained where present. Scripted/non-numeric
values require turning off the relevant estimate; invalid enabled calculations
roll back the whole operation.

- Population weight: actual pixel area × terrain density + 10 × original mean
  province pixel area × VP. Density plains 1, urban 4, forest .6, hills .65,
  jungle .4, mountain/desert .2, marsh .35, frozen/volcanic .1, lakes .02.
  Other defined terrain uses 1 / max(1, movement_cost)^2, unknown fallback .5.
- Resources: actual pixel area, independent of VP and terrain.
- Industry: shared-slot state building counts, weight 1 + 2 × VP per province.
  Coastal types allocate only to coastal receivers. Losing a state's last coast
  with industry redistribution off is blocked if coastal state buildings remain.
- Off options retain existing state quantities. New states start with zero for
  those quantities. Infrastructure is copied as an intensity; other state
  buildings, including airbases, are never duplicated by splitting.

These are explicit editing heuristics, not empirical population/resource models.
In the equal-size 50-VP fixture, the receiving state gets over 9500 of the
combined 10301 population. Both terrain and source totals still matter.

## Model placements and airbase correction

`StatePositions` reads effective common/buildings show_on_map/spawn_points,
actual province pixels, heightmap and ocean adjacency. It preserves valid state
slots where possible, rebuilds affected province/coastal slots, and fills missing
state slots. Positions spread over available interior points. Land model height
uses heightmap pixel × .1, matching existing native examples. Ports are on land
shore pixels with adjacent ocean IDs; floating harbors are in the adjacent sea
and refer back to their land province. Manual/unknown placements retain physical
positions and get their current state ID; unsafe assignments block the edit.
Native disable_auto_nudging entries are not invented or repositioned.

Each affected state has a valid land air_base model slot. The user explicitly
corrected the initial minimum-level assumption: no actual level-one airbase is
added. Existing air_base levels stay unchanged; new states get no automatic
air_base history entry. Old ordinary building slots over lakes regenerate on
land. New coordinates agree under floor and nearest-pixel sampling.

This is a deterministic painter implementation, not the proprietary Nudge
algorithm. Static tests establish membership/height/coastal references and slot
coverage. Engine rendering and visual spacing remain untested.

## Files changed

- legacy_of_kattail_painter/state_boundary_model.py (new)
- legacy_of_kattail_painter/state_positions.py (new)
- legacy_of_kattail_painter/state_boundary_ui.py (new)
- legacy_of_kattail_painter/test_state_boundaries.py (new)
- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/geography_model.py
- legacy_of_kattail_painter/model.py
- legacy_of_kattail_painter/map_render.py
- legacy_of_kattail_painter/install.py
- legacy_of_kattail_painter/README.md
- modding_documentation/agent_memory/plans/state-boundary-editor.md (new)
- modding_documentation/agent_memory/state_boundary_editor.md (this report)
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md

Identifiers: Python StateBoundaryStore, StatePositions, Recalculate,
NewStateDialog; UI category State boundaries; options Recalculate Population,
Recalculate Resources, Recalculate Industry. Runtime-created native objects use
history/states/<id>-painter.txt and STATE_<id>. No production native IDs, tags,
events, localisation keys or state boundaries were added/changed in this task.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`
  passed all 240 tests, including 10 new boundary tests and real Tk controls.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_state_boundaries.py -v`
  tests conserved integer/fractional estimates, strong VP weighting, all terrain
  fallback coverage, industry options/coastal constraints, dated payload transfer,
  source preservation, airbase model/level distinction, lake handling, rollback,
  ID/loc collisions, Save/reopen, Undo/Redo and a multi-province UI stroke.
- `python -m py_compile legacy_of_kattail_painter/state_boundary_model.py legacy_of_kattail_painter/state_boundary_ui.py legacy_of_kattail_painter/state_positions.py legacy_of_kattail_painter/test_state_boundaries.py legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/model.py legacy_of_kattail_painter/map_render.py legacy_of_kattail_painter/geography_model.py legacy_of_kattail_painter/install.py`
  passed.
- `python -B tools/validate_map.py` passed before/after: 21515 provinces,
  20926 assigned provinces, 413 strategic regions, no X crossings.
- Disposable native-map staging: split state 16, allocated temporary state 1903,
  then transferred another province. All estimates enabled. Population conserved
  as 4755 + 205245 = 210000; actual airbase levels unchanged. Formatted output was
  inspected: normal tabs, separated history/building/VP/demographic blocks.
  Wrote staged drafts only into a disposable copy with original binary geometry,
  states, regions and network files; imported tools/validate_map.py and ran its
  main() against that copy: passed. Checked SHA-256 of all 1902 original state
  files and six coupled map files: all 1908 unchanged. Temporary state 1903 was
  never created in the production mod.
- Native painter UI with actual map: category visible, 1902-state palette,
  forced province borders, correct three defaults; zero callback errors, zero
  drafts; closed the test window. Fixture UI tested real mouse/edit handlers,
  preview, Create dialog and Undo/Redo.
- Additional disposable multi-donor probe moved provinces from two states into
  a newly created state, with all estimates on: population 10321, steel 10, oil
  1.25 and industry 6 conserved. Source population written as 10001.0 was accepted
  and saved as an integer; existing/new airbase levels remained correct.
- `git diff --check`, `git diff --stat`, complete tracked diff and new source
  review performed. Existing Python line-ending styles preserved.

## Uncertainties and genuine remaining work

No game engine launch was performed. Next concrete validation is loading a
user-edited map in HOI4 and inspecting models/ports/airbase locations and supply.
The official wiki request returned 401 during source inspection; syntax and
geometry were checked against local current mod/game files instead:
common/buildings/00_buildings.txt (show_on_map header and spawn_points),
map/buildings.txt, map/heightmap.bmp, history/states and the existing geography
parser/editor. No existing production geography has been changed for testing.

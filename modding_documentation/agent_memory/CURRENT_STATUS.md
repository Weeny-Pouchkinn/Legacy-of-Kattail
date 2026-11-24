# Current status

## Native state/region editors and VP layer (2026-11-24)

On Painter-Test: MAP > States / regions / VPs, sidebar/library and map
double-click entry points now edit state names, native attributes/resources,
shared/nonshared/province buildings, ownership and demographics. Regions move
whole states, reject empty regions and split/unassigned states, and edit names,
naval terrain and weather. Vanilla weather import and 30 editable Köppen-inspired
North/South presets are available. VPs have a gradient map layer, zoomed labels,
map placement/edit/remove and alphabetical base-name localization consolidation.
All data uses existing native files; no painter metadata. No reshaping, railway
route generation or map spawn generation. Restart the painter to load the UI.

All 98 painter tests pass. Isolated model/form tests cover Save/reload,
BOM/versions/comments, unknown/dated
history, building constraints, supply nodes, whole-state transfers/Undo, presets,
vanilla import, VP sorting/conflicts/variants and nested Cancel. Native alpha-zero
mapped Tk checked the three forms, map handoff/grab, minimum-size weather controls,
252 viewport VP items, all 1,902 state rows and unchanged state/region/English-loc
source hashes. Native audit: 413 regions, 1,552 VPs and 4,791 valid weather periods.
Map validation still has only the known railway errors at lines 893–894. No live
Save, game launch or CWTools claim. Exact files/commands: painter/MODLOG (full path
`legacy_of_kattail_painter/MODLOG.md`). Next action: user authoring and game checks
after saving desired edits; no implementation blocker remains.

## Visual flag background/emblem pickers (2026-11-24)

COUNTRIES > Flags arrows, entry double-clicks and Browse buttons now open visual
thumbnail galleries with a large full-flag preview. Current colors/tint/size,
name/code/fuzzy search, source filters, keyboard controls and Cancel/accept are
supported. Rendering is lazy and batched; caches are bounded in memory. No new
assets, native game IDs, data/cache files or writer changes. Restart to load it.

83 tests pass, including three new Tk gallery tests over 1,004 choices. Native
mapped Tk verified 346 emblems (35 visible thumbnails, zero failures), all 17
backgrounds, minimum-size preview layout, arrow callbacks, selection/cancel and
parent grab restoration. Country drafts and checked native source hashes stayed
unchanged. Compilation/whitespace passed; no screenshot review or live Save.
Exact files and commands: legacy_of_kattail_painter/MODLOG.md.


## Native country editor (2026-11-24)

On Painter-Test, added COUNTRIES create/edit with seven tabs: setup and capital
map pick; live party-popularity pie; ideological name/DEF bulk copying/article
helpers; native flag import/design with all/undefined copying; linked character
leaders; starting techs; national spirits/modifiers and vanilla/mod icon library.
17 recolorable flag backgrounds, independent emblem tint, existing Stellaris/EU4
emblems and native reusable DDS mask import are available. New countries register
native definitions/history/flags; Owner palette/library entry points and a Paint
on map button work. No country/flag/spirit JSON/data sidecars are created.

Edited country species/attributes live in country history as native ideas.
Game-consumed lok_country_species_defined_in_history and
lok_country_attribute_defined_in_history flags guard original startup defaults.
Selected attributes reuse native scoped research-bonus templates; untouched tags
keep the previous defaults. No new world loops or global history migration.
Existing character roles/recruitments, dated/conditional setup, unknown fields,
localization BOM and tech/equipment ordering are preserved. Forms support grouped
Undo/Redo/Cancel and native guarded Save.

Validation: 80 tests pass; compilation and scoped whitespace checks pass. All 198
native histories load, with 273 registered tags. Native alpha-zero Tk probes
covered all country tabs, flag/name bulk actions, emblem tint, leader/spirit
creation, icon previews, capital pick/Escape, Apply/Cancel/Undo/Redo and new-country
Owner painting; all 14,521 checked native file hashes stayed unchanged. A full
20-native-file Save/reload fixture passed without a character metadata file.
Guard probe left the other 197 country law setups unchanged. Two existing railway
validator issues remain at lines 893-894. No game/CWTools/screenshot validation.

Restart the painter, open COUNTRIES, edit or create, Apply, then Save. Full source
paths, native destinations, references and limits: legacy_of_kattail_painter/MODLOG.md.
Earlier unrelated working-tree changes and the separate culture/species/wonder
catalog-authoring save/reload milestone are preserved; this does not close that
separate follow-up.


## Painting performance (2026-11-24)

Optimized the existing MAP painter using EU4's viewport rendering pattern.
Only visible pixels plus a pan margin are colored; geometry, static palettes,
country colors, validated catalog parses, Tk images and wonder icons are cached.
Brushes edit immediately; redraw/inspection/status share a 25 ms frame queue,
flushed on release. Repeated motion in painted states skips brush work. Native
catalog existence checks are no longer repeated per province. Undo remains as
before, and caches are bounded and memory-only.

Same-run warm redraw at 25% zoom: culture 170.44 -> 17.75 ms, species
281.82 -> 26.27 ms, owners 251.32 -> 25.75 ms, wonder 211.37 -> 15.64 ms.
Methodology/limits and exact changed paths are in the painter MODLOG.md.
67 fixture tests and compilation pass. Native alpha-zero Tk probes verified all
nine views, pixel-exact viewport/zoom/pan/boundary rendering and actual paint,
release flush, Undo/Redo, discard and fit. All 14,521 checked native file hashes
stayed unchanged. Map validation still reports the two existing railway links on
lines 893-894. No engine/CWTools/screenshot review or game identifiers changed.

Restart the painter to use the optimization. The separate culture/species/wonder
catalog-authoring milestone still needs its full save/reload verification; this
performance task verifies rendering and painting, not every authoring workflow.


## Trait database and commander randomizers (2026-11-24)

Added CHARACTERS / Trait database with General, Admiral, Political advisor and
Other unit views. Reads installed vanilla and mod trait folders; shows origins,
active/overridden definitions and name/ID search. Current data: 3,960 definitions,
1,695 active, 775 searchable modifiers. Native modifier docs/custom definitions
and English localization supply labels/categories. Vanilla is inspect/clone;
file constants resolve on cloning. Mod definitions edit in place. New user traits
write alphabetically to the appropriate common/unit_leader/lok_traits.txt or
common/country_leader/lok_traits.txt and BOM English strings to
localisation/english/painter/traits_l_english.yml. No live dummy traits created.

Military role dialogs roll base skills from current level with active skill
bounds/defines (vanilla 4 + 3*(level-1)), keep level, and roll a chosen count of
generic vanilla traits. Add/replace modes preserve custom/status/scripted traits
and avoid incompatible/unavailable/restricted choices. Field marshals can carry
general traits, matching 25 existing mod cases. All rolls stay local until Apply;
Cancel/Undo/Save guards hold across trait and localisation edits. Existing
character/portrait edits from save_20261124_172934_590513 are preserved.

Validation: 61 fixture tests, compilation, native hidden-Tk source/catalog/
randomizer/editor checks and read-only real verification. All 10,864 current
source hashes unchanged during checks; four pre-existing OOB brace errors remain.
Unchanged view refresh 0.1–0.2 ms, warm role 0.110 s, skills 0.024 s, traits
0.0044 s measured. Changed-code whitespace checks pass. Whole diff still flags
existing common/characters/LOK_eu4_import_characters.txt:35 whitespace.

Historical character migration audit is now stale after the existing save:
portrait GFX, character metadata and English character localisation differ.
Do not revert those authored edits or rewrite the old snapshot to claim a pass.
No live game sources/assets written by this task; future trait files are created
on user Save. No in-game/CWTools/screenshot validation. Exact files/commands and
source references: legacy_of_kattail_painter/MODLOG.md and
plans/trait-database-randomizers.md. Next: restart painter; test saved traits and
tooltips in a fresh game. No editor implementation blocker.

## Painter performance and localized selectors (2026-11-24)

Optimized character-localization prefix matching (removed the measured 87.6
million comparisons), targeted cache invalidation, per-file parsing/catalogs,
batched role edits, unchanged identity and bounded decoded/Tk portrait caches.
Profiled identity apply went from 53.463 s to about 0.52 s; save preparation
29.209 s to about 0.20 s (profiling overhead included). Actual Tk military-stat
apply 0.0256 s, refresh 0.0338 s, warm character/role dialogs 0.190/0.131 s.
First role dialog still loads native names once (1.078 s measured).

All dropdowns accept typing. Localized names precede IDs in parentheses;
alphabetic name/ID ordering, both-field matching, accent/case normalization,
fuzzy suggestions and keyboard/mouse selection share ChoiceBox. TraitChoices
supports multiple localized traits. Country/portrait galleries, nation/tag
filters and map/source/emblem lists use names/IDs consistently. Stored values
remain raw native IDs. New portrait tags can still be typed directly.

Validation: 51 tests, native hidden-Tk interactions with zero callback errors,
Python compilation, original character migration audit and real-data map/tool
checks pass; all 10,863 checked source hashes unchanged. Four pre-existing OOB
parse errors remain. No game content or assets modified for this optimization.
Exact files, commands and measurements: legacy_of_kattail_painter/MODLOG.md and
plans/character-performance-selectors.md. Reproducible read-only benchmark:
`python -B legacy_of_kattail_painter/benchmark_characters.py --profile`.
Next: restart the painter. No remaining implementation blocker; no in-game or
screenshot validation claimed. External source edits still require reload.

## Character workspace and Ministermaker (2026-11-24)

Implemented on Painter-Test: MAP retains existing painting/tools; CHARACTERS has
localised-name/nation galleries, 284 characters (12 unrecruited), native repeated
roles/traits/stats/recruitment and description/credits editing. Independent
portrait library contains 2,565 large/small pairs, arbitrary three-character
tags, additional linked variants and per-native-slot assignment; pair creation
also works inside character editing. Drafts, nested Cancel, Undo/Redo and guarded
Save cover new text/JSON/localisation and binary assets with backup/rollback.

Applied alphabetic tag/neutral-name character localisation and portrait GFX
organisation. All 51,295 English values and 284 character identities/recruitments/
roles preserved. Moved 726 large/source + 682 small original assets; every byte
hash matches. Added 42 derived small portraits, reused two authored images.
Generate small portrait exactly matches the supplied Ministermaker main script
(37x51, 5 degrees, centred 65x67, original border at 8,1), including pixel parity.
An initial overwrite of two small originals was caught/restored from backups;
the regression fix reuses existing art and guards destination collisions.

Validation: 42 fixture tests, 12 Python compilations, read-only audit of 2,869
paths/backups, repeated-Save idempotence, hidden Tk sorting/filter/layout/generator
Apply/Save/reload/Cancel checks pass. Real-data read-only checks preserve 10,863
hashes. Localisation analyser has identical pre/post 2,285 missing-key sets.
Exact paths, identifiers, backups and commands: legacy_of_kattail_painter/MODLOG.md
and plans/character-refactor-audit.json / character-workspace-files.txt.

Limits: five pre-existing generic source textures and ten character sprite
references remain unresolved in available indexes; four existing OOB parse errors
remain. No in-game/CWTools or screenshot validation. No state/map topology work
belongs to this change; concurrent duplicate-history cleanup is preserved below.
Next: restart painter; verify portraits and edited roles in a fresh game.

## State-history duplicate cleanup (2026-11-24)

Current branch verified as Painter-Test. Audited all 1,902 state files and repaired
46 duplicate-history files: removed 39 second ZZZ blocks and merged seven
same-owner blocks (151, 284, 556–559, 953), preserving unique VPs/buildings/claims
and later overlapping building values. All states now contain one history.
Existing edits, state demographics and root data are preserved. One trailing
space in state 557's province list was removed to pass diff validation.

Validation: all state files parse; 1,856 untouched hashes match; all seven merged
VP/building maps and 39 primary histories match originals. Four regression tests,
Python compilation and diff checks pass. Map validator now rejects duplicates;
its only remaining errors are the pre-existing railway links at lines 893–894.
Importer state reader now also rejects duplicate/missing histories. No game test.

Correction to the earlier EU4-import validation note below: that verifier selected
only the first history and did not prove uniqueness. Earlier hashes/counts describe
its snapshot; they are not a current validation after user edits and this cleanup.
50 files have other repeated root resources/scalars, intentionally left unchanged.
Full results/exact paths: state_history_audit/README.md, audit.json and files.txt.
Next: in-game ownership/building check; no duplicate-history implementation blocker.

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

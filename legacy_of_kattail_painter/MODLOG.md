# MODLOG — Legacy of Kattail painter

## 2026-11-24 - Character performance and searchable localized selectors

Profiled native source operations without saving drafts. The main bottleneck
was character-localization collection: 87.6 million character-prefix comparisons
in the measured sequence. Replaced that scan with longest-prefix lookup.
File inventories, parsed files, localization per file, recruitment and native
trait/ideology catalogs are cached. Derived caches invalidate by changed source
category, including Undo/Redo, Cancel, discard, creation and deletion. Role fields
are patched together and unchanged character identity is skipped. Bounded image
caches retain decoded art and Tk images across unrelated stat/credit edits.

Same cProfile instrumentation on this workstation (seconds, single runs;
profiling overhead included, not a guarantee for other machines):

| Operation | Before | After |
|---|---:|---:|
| Apply character identity | 53.463 | 0.519 |
| Prepare character save | 29.209 | 0.199 |

Actual hidden-Tk measurements, without cProfile: existing-character open 0.338 s,
warm open 0.190 s, unchanged identity 0.0012 s, first role open 1.078 s (native
translation/catalog load), warm role open 0.131 s, apply military stats 0.0256 s,
refresh after edit 0.0338 s, portrait dialog 0.0904 s, small preview 0.0053 s.
An earlier synthetic role benchmark used role zero and is not presented as a
native military-role comparison; benchmark_characters.py now selects the actual
military role. All benchmark changes remain memory-only drafts.

Added shared ChoiceIndex/ChoiceBox/TraitChoices controls. All application
dropdowns now accept typing and show localized `Name (ID)` when available, sorted
alphabetically by displayed name with ID tie-breaks. Search checks both fields,
ignores case/accents, offers fuzzy matches, and highlights the closest/exact ID
without reordering the list. Popup lists retain typing focus and support mouse,
arrow keys, Enter, Tab and Escape. All choices remain scrollable. Names that
collide require selecting their distinct IDs. Trait selection is localized
multi-select. Selected labels never become game script IDs. Country/portrait/tag
filters, roles, ideologies, gender, slots, map modes, state species/cultures,
owners and flag targets use the same control. Source/palette/emblem lists also
search both names and IDs; typing in a list transfers into its search field.
Native trait translations are read from installed English localisation only
as a fallback to mod strings. Missing localisation retains the code. No game
localisation, sprites, portraits, character IDs or map data changed in this task.

Files changed (relative to mod root):

- `legacy_of_kattail_painter/model.py`, `character_model.py`, `character_ui.py`,
  `painter.py`, `install.py`, new `select_ui.py`, `test_selectors.py` and
  `benchmark_characters.py`.
- `legacy_of_kattail_painter/README.md`, `MODLOG.md`.
- `modding_documentation/agent_memory/CURRENT_STATUS.md`, `DECISIONS.md` and
  `plans/character-performance-selectors.md`.

Identifiers: no game IDs changed. New Python controls are Choice, ChoiceIndex,
ChoiceBox and TraitChoices. Stored values retain native IDs such as `LAU` and
`harsh_leader`; visible labels are `Laurandar (LAU)` and
`Harsh Leader (harsh_leader)`. No `trait_` prefix is invented for native IDs.

Validation:

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test*.py'`:
  51 tests, including typing/code mapping, fuzzy/diacritic matching, duplicate-name
  grouping, popup keyboard/cancel, nested drafts and targeted cache invalidation.
- `python -B legacy_of_kattail_painter/benchmark_characters.py --profile`:
  memory-only timings and 2,795 loaded source snapshots unchanged.
- `python -B legacy_of_kattail_painter/verify_characters.py`: original migration
  audit still passes (2,869 paths, 1,408 original asset hashes, 51,295 authored
  English values, 284 characters, 2,565 portrait pairs).
- `python -B legacy_of_kattail_painter/verify_real.py --mod . --output
  '<temporary diagnostics directory>'`: map/state draft, Undo/Redo, flags and
  source fields pass; all 10,863 source hashes unchanged. Existing four OOB brace
  errors remain. All 1,026 emblem/size renders pass.
- Actual native Tk: country name/ID typing and nation/unrecruited filters,
  localized Harsh Leader suggestions, stat edits, parent Cancel, portrait/tag
  selection, small generation, map palette/owner/source searches, 1050x680 layout;
  no callback exceptions and no source writes.
- Python compilation of all eight changed/new Python files; Git diff/check/stat
  and new-file whitespace review. No source-data migration required.

Limits: initial native catalogs still require one read per launch. External
source changes require reload and remain guarded at Save. No in-game or screenshot
validation. Existing missing portrait references and game diagnostics are unchanged.

## 2026-11-24 - Character workspace and Ministermaker

Added MAP/CHARACTERS main tabs. Characters has a full-width, virtualised large
portrait gallery sorted by localised names, nation grouping/filter and a section
for the 12 characters without undated starting recruitment (284 total).
Character drafts edit identity/name/description/credits, starting recruitment,
repeated native roles, traits/stats and advanced role fields. Dated/conditional
history and unknown fields are preserved. Portrait definitions are independent
large/small pairs with three-character tags, credits/notes and multiple linked
variants; native civilian/army/navy slots can choose separate pairs. New portrait
pairs can be created and assigned from the character dialog. Cancel/Undo apply
to nested edits; Save guards text, new files, image imports and deletions together.

Generate small portrait reproduces the supplied external Ministermaker main
`ministermaker.py`: 37x51 resize, 5-degree rotation, centred transparent 65x67
canvas, original border at (8,1). Its exact border is bundled, SHA256
`6a505780b8c3cd758416393c4eb0d56195d697d6a877c3a8358f47f6d9dec0f2`.
Verified output pixels against the supplied script using a deterministic image;
the external directory was not modified. The separate Test/ bulk variant and
the mod's different root minister_border.png are not used by the new generator.
The preview stages on Apply; Save writes a TGA with backups.

Applied the reviewed migration: 726 large/source assets and 682 small assets
moved to leaders/large_portraits and leaders/small_portraits, respectively.
All 1,408 original byte hashes match. Grouped lok_leader_portraits.gfx by tag,
preserved animation fields, updated all moved-path references, created 42
derived small images and reused two authored small images. Consolidated native
character strings into alphabetic tag/neutral-name sections with localised-name
ordering and an UNASSIGNED section. All 51,295 English key/value pairs remain
exactly preserved, including authored descriptions/tokens. UTF-8 BOM retained.

Identifiers: no character IDs renamed or recruitment/roles changed. Fixed the
conflicting CAT Elwin small sprite by using its expected `_Small` ID. Added
large aliases `GFX_portrait_PLR_Lenagahn` and `GFX_portrait_PLR_Vesbuncchi`,
preserving legacy spellings. New authored characters use zz_painter_characters;
portrait notes/credits/tags/variant links use characters_painter_data.json v1.
No state, province, region or binary map topology edits belong to this task.

Backups: initial migration `backups/save_20261124_155821_493637/`; final derived
images `backups/save_20261124_161345_640711/`. Post-move checking caught an initial
thumbnail overwrite of two authored small files (KTZ_Kaiser_Kattail_Neither and
PLR_Vesbuncci). Both were restored byte-for-byte from backups. The refactor now
reuses existing small art before deriving, refuses original-asset hash changes,
and allocates a different destination rather than overwriting unrelated files.
This is covered by regression tests. Restore provenance is in the audit.

Files: exact source paths and before/after hashes are in
`modding_documentation/agent_memory/plans/character-refactor-audit.json`;
`character-workspace-files.txt` in that directory adds implementation/docs paths.
The two older root portrait tools received canonical-path updates only.
Concurrent state-history/importer/validator work was preserved separately.

Validation actually performed:

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test*.py'`:
  42 tests pass, including lossless grouping, repeated roles, variants, recruitment,
  exact Ministermaker pixels, Save/reload, binary rollback and absent-file Undo.
- `python -B legacy_of_kattail_painter/verify_characters.py`: passed all 2,869
  migration output paths/backups, 1,408 original hashes, 51,295 exact English
  values, 284 identities/recruitments/roles, 2,565 pairs and Save idempotence.
- `py_compile.compile(..., doraise=True)` for all 12 changed Python files:
  passed, bytecode redirected outside the workspace.
- `verify_real.py` after migration: 1,902 states, 198 histories, 4,191 scripts;
  342 flat masks/1,026 renders; 10,863 source hashes unchanged by testing.
- Actual `loc_analyzer.main()` baseline/post-migration runs with report-only
  output redirected to temporary files: identical 2,285 missing-key sets, no
  new missing keys. Root diagnostic file was not rewritten.
- Hidden native Tk: both main tabs, 284-character gallery, name/nation sorting,
  12 unrecruited, Pawtton editor, 2,565-pair gallery/tag filter, widths at 1500x900
  and 1050x680, Generate button/previews, Apply/Save/reload and Cancel passed.
- Git diff/check/stat review and per-file review; no relevant whitespace errors.
- Searched 4,231 active native script files: no stale moved-asset references.
  All 44 generated/alias sprite IDs are globally unique. Applying a character
  without changing its primary country preserves multiple native recruitments.
- `python -B tools/validate_map.py`: only the two previously documented railway
  non-neighbor links at lines 893-894. No map inputs changed by this task.

Removed trailing whitespace outside two regrouped localisation strings so the
complete diff check passes; quoted values/BOM/newline style are unchanged.
Backup: `backups/localisation_whitespace_20261124_161919_026487/`.

Uncertainties: five generic large textures and ten character large sprite
references were already unresolved in the available indexes (listed in audit).
No replacement art or lore invented. Four pre-existing EUL/GAL/KKN/KTZ OOB brace
errors remain. No game or CWTools validation, no screenshot inspection. Restart
the painter to load the new tabs. Next validation is an in-game portrait/role
check; there is no remaining editor implementation blocker.

## 2026-11-24 — Species invariant, boundaries and region scopes

Equal majority/minority species automatically clears the minority to 1000.
This includes Diverse (0), direct state forms, paint brushes, loaded source,
raw source edits and pre-save validation. Majority 1000 is rejected because
it represents None. Existing identical pairs in states 447, 888 and 1040 were
corrected with byte-preserving backups at
`backups/save_20261124_104605_259819/`; only the three minority values changed.
Runtime variables and game identifiers were retained; no new game IDs added.

Added independent boundary checkboxes for Province (1 px), State (2 px) and
Strategic region (3 px). Width is measured after zoom, not in source-map pixels.
Boundaries are display-only, cached for the current zoom and off by default.
Added State/Strategic region scope for culture, majority, minority and owner
brushes. Scope uses the clicked province's actual region. Region changes group
as one undo action, deduplicate a drag, and roll back on partial edit failure.
Split states refuse regional painting before any edits; no spillover is allowed.
The current 413 strategic regions have no split states or duplicate memberships.

Validation commands from the repository root:

```powershell
python -B -m unittest discover -s legacy_of_kattail_painter -p test_painter.py -v
# All 24 tests passed. New coverage: duplicate species (including 0), raw-source
# save repair, region membership/ownership/demographics, one-action undo/reload,
# drag exclusions, split states, batch rollback and exact 1/2/3-pixel boundaries.

python -m py_compile legacy_of_kattail_painter/model.py legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/demographics.py legacy_of_kattail_painter/test_painter.py
# Passed; PYTHONPYCACHEPREFIX redirected bytecode outside the repository.

python -B legacy_of_kattail_painter/verify_real.py --mod . --output C:\Users\elowi\AppData\Local\Temp\lok-painter-boundaries-verification
# Passed hidden Tk controls/undo/redo/fields/flags; all 1,026 mask-size renders
# succeeded and 10,786 source hashes stayed identical during these UI-only tests.
# Same four pre-existing OOB brace errors: EUL/GAL/KKN/KTZ.

python -B tools/validate_map.py
# Before and after: same non-neighbor railway errors at lines 893 and 894
# (20839/20841 and 20841/19461). Map inputs were not changed.

git -c core.fsmonitor=false diff --check
git -c core.fsmonitor=false diff --stat
git -c core.fsmonitor=false diff
# Whitespace passed; complete diff reviewed, including minority-only state edits.
```

Additional actual-data Tk checks passed all independent toggles and combinations,
all eight map views, 1500x900 and 1050x680 layouts, region 1 painting exactly its
five member states, grouped undo/redo, and raw source auto-repair. Test painting
was not saved to the live mod. Loaded state records all satisfy the invariant.
Scope/boundary membership is a startup snapshot: restart after topology edits.
No game launch or screenshot inspection is claimed.

Exact changed/new repository paths for this task:

```text
history/states/447-State_447.txt
history/states/888-Mount Lisejr.txt
history/states/1040-Timothia.txt
legacy_of_kattail_painter/demographics.py
legacy_of_kattail_painter/model.py
legacy_of_kattail_painter/painter.py
legacy_of_kattail_painter/test_painter.py
legacy_of_kattail_painter/README.md
legacy_of_kattail_painter/MODLOG.md
modding_documentation/agent_memory/CURRENT_STATUS.md
modding_documentation/agent_memory/DECISIONS.md
modding_documentation/agent_memory/plans/painter-boundaries.md
```

## 2026-11-24 — Persistent painting and applied state migration

Implemented Save/Ctrl+S for edited text sources, byte-level external-edit guards,
backups, atomic per-file replacement and rollback for write failures. Installed
source_io.py and updated the optional installer. Save includes arbitrary source
drafts; flags remain session-only. A painter .gitignore excludes backups/bytecode.

The Paint sidebar now lists named cultures/species/countries with RGB swatches.
Culture supports Set/Add/Remove; species has Majority/Minority selection plus
No minority (1000). Click/drag changes entire states. Shift-click picks without
painting the rest of the gesture. Inspection no longer replaces the paint palette
during a stroke. State parsing is cached to avoid reparsing all state histories
for every preview refresh.

Colours come from LOK_culture_map_mode.txt and LOK_species_map_mode.txt. Species
minorities render as diagonal bands; majority/minority edits preserve the other
field. Multiple cultures blend their defined colours. Culture 102 has no source
colour and is labelled with neutral grey. Current choices: 102 cultures, 61
majority species, 62 minority choices including None. All assigned IDs have RGB.

Applied 1,655 initial startup statements to 1,902 state histories. Removed those
startup statements; preserved culture-group arrays, country species ideas,
runtime containers, derived-modifier setup, later gameplay effects and all
unrelated statements. Initial demographics including ordered three-culture
states 894-897 match the pre-migration baseline exactly.

Original 1,903 sources are backed up under
`backups/migration_20261124_101441_420939/`. The delimited blocks preserve state
text outside the insertion, existing closing-line indentation, BOM and newlines.
An additional formatting backup is under `backups/save_20261124_101603_545214/`.

Commands/results from the mod root:

```powershell
python -B -m unittest discover -s legacy_of_kattail_painter -p test_painter.py -v
# Passed all 16 tests: existing parser/isolation/migration/flag checks plus
# persistent save/reload, stale-source rejection, rollback, applied migration,
# source BOM/newlines and exact defined-colour/stripe pixels.

python -m py_compile legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/model.py legacy_of_kattail_painter/demographics.py legacy_of_kattail_painter/source_io.py legacy_of_kattail_painter/migrate_state_setup.py legacy_of_kattail_painter/install.py legacy_of_kattail_painter/test_painter.py
# Passed; PYTHONPYCACHEPREFIX redirected bytecode to temporary storage.

python -B legacy_of_kattail_painter/migrate_state_setup.py --mod . --output C:\Users\elowi\AppData\Local\Temp\lok-painter-migration-20261124
# Dry run staged 1,903 files. Reviewed all state insertions mechanically and
# compared surviving startup AST/effect ordering against the originals.
python -B legacy_of_kattail_painter/migrate_state_setup.py --mod . --output C:\Users\elowi\AppData\Local\Temp\lok-painter-migration-20261124 --apply
# Applied after all source/stage hash checks. Subsequent canonical block
# formatting preserved all original state text outside the demographic section.

python -B legacy_of_kattail_painter/verify_real.py --mod . --output C:\Users\elowi\AppData\Local\Temp\lok-painter-editing-verification
# Passed actual-data demographics, undo/redo, source filters and flag controls;
# 1,026 mask-size renders and 10,786 unchanged hashes during unsaved UI tests.
# Reported the same 4 pre-existing OOB parser errors (EUL/GAL/KKN/KTZ).

python -B tools/validate_map.py
# Before and after: same 2 failures, railways.txt:893 (20839/20841) and
# :894 (20841/19461), both non-neighbor jumps. No map inputs changed.

git diff --check
git diff --stat
git diff
# Whitespace check passed; complete source/metadata diff reviewed. All 1,902
# state insertions checked against original bytes and baseline demographics.
```

Additional inline Python/Tk checks passed: palette-backed culture painting,
independent majority/minority brushes, minority clearing, Shift-pick drag
suppression, Save/reload in disposable fixtures, actual province painting and
undo/redo in real data without saving, all eight views, all workspace tabs and
scrollable forms at 1500x900 and 1050x680. All migrated state definitions were
checked for unique complete blocks and valid assigned colour IDs. No
map/localisation/graphics files changed. Exact paths: project memory's
plans/painter-editing-files.txt.

No usable CWTools executable or screenshot helper was available. State-history
syntax follows the local State modding reference (History section) and native
271-ethiopia.txt variable effects. Live wiki access failed. No in-game validation
is claimed; earlier initialisation timing needs a fresh-campaign check.

## 2026-11-24 — EU4 interface styling

Replaced the forced dark `clam` theme and banner with native ttk controls,
compact Undo/Redo/Discard, Paint/View and zoom tools. Matched the EU4 painter's
left sidebar, section typography, spacing and `#1e1e1e` map canvas. Sources and
scrollable state setup share sidebar tabs; map, source fields and flags retain
their workspace tabs. Map inspection opens state setup automatically. Flag
previews fit narrow panes while preserving aspect ratio and native image sizes.
The application still keeps all drafts in memory. No game identifiers changed.

Validation commands:

- `python -m py_compile legacy_of_kattail_painter/painter.py` — passed; bytecode
  redirected outside the repository using `PYTHONPYCACHEPREFIX`.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_painter.py -v`
  — all 11 tests passed.
- `python -B legacy_of_kattail_painter/verify_real.py --mod . --output "$env:TEMP/lok-painter-ui-verification"`
  — passed real-data UI/drafts/undo/redo/filter/flag checks, all 1,023 mask-size
  renders, and 10,786 unchanged game-source hashes. Four existing OOB brace
  errors remain, as documented below.
- Additional Python/Tk checks exercised all three workspace tabs, state/source
  navigation, all eight map views, state-form scrolling and flag-preview sizing
  at 1500x900 and 1050x680. Native `vista` theme remained selected. Preview sizes
  were 492x312 and 391x248 respectively.
- `python -B tools/validate_map.py` — failed on the two previously documented
  railway non-neighbor links at lines 893-894; map inputs were not changed.
- `git diff --check`, `git diff --stat`, `git diff` and `git diff --no-index
  --check -- /dev/null legacy_of_kattail_painter/painter.py` — reviewed; no
  whitespace errors. The painter directory was already untracked, so ordinary
  Git diff omits its files; the full painter source was separately reviewed.

Desktop screenshot inspection was unavailable (`CODEX_CLI_PATH` helper error).
Tk controls/layout were checked programmatically; no screenshot or in-game
validation is claimed. Restart the painter to load the updated interface.

## 2026-11-24

Requested: first read-only HOI4 painter, fields for mod-specific content, a flag
maker using tintable white Stellaris masks and a single-colour background, all
under `legacy_of_kattail_painter` in the mod root. User additionally authorised
experimental migration of state culture/species into state files and noted Git
version control.

Route: standalone Python/Tk with Pillow/numpy, reading source data. No source
writers in the application. A separate staging generator and hash-checked
installer handle the authorised migration experiment. No game assets bundled.

Observed source: 1,902 states, 181 country histories, 4,154 script files, 341 flat
Stellaris/Gigastructures mask choices. Dimensions from native mod TGA flags:
82×52, 41×26, 10×7. EU4's loader is not imported because it writes lazy caches.

The mod's state demographics were not native database keys: cultures use
`state_cultures`, majority species uses `species`, and minority uses `minority`
with sentinel 1000. Country species ideas are distinct and remain untouched.
Four freeport states (894–897) have cultures [17, 67, 2]; preserve all three.

Migration stage moves 1,655 initial startup statements to 1,902 state files;
1,903 source files affected including the original startup file. Runtime
variables/arrays remain compatible with consumers. No live source files edited.
Original hash checks prevent applying a stale stage. The complete diff and
per-state initial snapshot are included in `migration_patch/`.

Validation: 11 fixture tests pass, covering ordered cultures/conditions/minorities,
read-only isolation, undo/redo, arbitrary fields, repeated edits, path confinement,
unknown-effect rejection, migration preservation and tintable flat masks. Real
data verification is recorded separately in `verification/verification.json`.
Hidden Tk checks passed; all 1,023 mask/size renders succeeded and 10,786 source
file hashes remained identical. Four existing OOB files have excess closing
braces; they stay accessible through raw source. No OOB repair was attempted.
Independent staged-file checks preserve all original state content outside the
new sections and match the original evaluated demographics. Disposable install
checks verified all 1,903 backups and installed bytes, and rejected stale input
before writes. The installer uses Python because local PowerShell execution
policy rejected .ps1 execution; no policy or registry setting was changed.

Limitations: staged values use undated initial ownership/core history and observed
startup expressions, not a full HOI4 VM. Other startup files/scripted effect calls
and changed initialisation timing require engine validation. No modded launch,
game input takeover, commit, PR or publishing performed. The live mod path is
outside writable roots, so direct installation was unavailable in this session.

Next action: install the folder; optionally apply the reviewed migration using
the installer; run the painter. Validate the migration in a fresh offline game
and inspect relevant logs before accepting it.

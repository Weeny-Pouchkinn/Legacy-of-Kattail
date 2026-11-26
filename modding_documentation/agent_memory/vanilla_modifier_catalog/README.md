# Complete vanilla modifier catalog - 2026-11-26

Fixed the shared modifier catalog and national-spirit editor. Restart the painter
to load the new catalog. `army_core_defence_factor` is selectable as **Division
Defense on core territory**, and its value can be applied/saved.

## Cause and resulting behavior

The example modifier was already loaded, but the spirit editor hid and rejected
anything without the documentation category `country`. Its actual categories
are `army, defensive`. The installed modifier-definition documentation describes
categories as tooltip filters; vanilla country ideas use this exact modifier.
The spirit picker/save check now accepts normal registered modifiers regardless
of tooltip category. Synthetic military trait skill/stat-weight fields retain
their separate context, and remain excluded from spirit choices.

The old parser also ignored parameterized headings such as
`production_speed_<Building>_factor`, omitting thousands of native IDs. It now
expands only the types explicitly supplied by the installed documentation,
preserves case (including uppercase country/operation/trait tokens), isolates
each section's metadata and merges repeated template entries. No fabricated IDs
or redundant built-in game definitions are generated.

The shared registry serves traits, national spirits, species traits and wonders.
Labels use existing native/local translations, with readable ID-derived fallbacks
where no translation is found. Display precision is metadata, not a cap on saved
precision. Documented Boolean modifiers accept `yes`/`no` in spirits; numeric
values remain finite game-unit numbers. Example Boolean used in tests/probe:
`can_guarantee_other_ideologies`. Wonder help says categories rather than scopes.

## Exact files changed

| Repository path | Change |
| --- | --- |
| `legacy_of_kattail_painter/trait_model.py` | Complete documentation parser/type expansion, category/Boolean/precision metadata, definition overlays, separate spirit choices/value parser |
| `legacy_of_kattail_painter/country_model.py` | Remove false category scope gate; retain trait-stat protection and native value parsing |
| `legacy_of_kattail_painter/country_ui.py` | Full spirit picker and documented Boolean inputs/help |
| `legacy_of_kattail_painter/painter.py` | Accurate modifier-category help |
| `legacy_of_kattail_painter/test_traits.py` | Two parser/category/type/override regressions |
| `legacy_of_kattail_painter/test_countries.py` | Mapped spirit search/Add/Apply/native Save/reload regression |
| `legacy_of_kattail_painter/README.md` | User behavior and coverage |
| `legacy_of_kattail_painter/MODLOG.md` | Change record |
| `modding_documentation/agent_memory/CURRENT_STATUS.md` | Current result and limits |
| `modding_documentation/agent_memory/DECISIONS.md` | Catalog/scope rationale |
| `modding_documentation/agent_memory/plans/vanilla-modifier-catalog.md` | Completed milestones |
| `modding_documentation/agent_memory/vanilla_modifier_catalog/README.md` | This report |
| `modding_documentation/agent_memory/vanilla_modifier_catalog/coverage.json` | Independent exhaustive ID coverage and primary source hash |
| `modding_documentation/agent_memory/vanilla_modifier_catalog/verification.json` | Real-mod UI/source-hash audit |
| `modding_documentation/agent_memory/vanilla_modifier_catalog/idea_usage_scan.json` | Supplemental actual vanilla idea usage scan and parser limitations |

No live modifier definitions, ideas, traits, state/country history, localisation
or binary assets were changed by this task. Existing unrelated user edits were
retained. Actual identifiers remain the documented engine/custom identifiers;
`trait_stat` is internal Python catalog metadata, not a new game identifier.

## Coverage against the installed primary documentation

| Coverage | Count |
| --- | ---: |
| Fixed vanilla IDs | 722 |
| Parameterized vanilla IDs | 3,806 |
| Total distinct documented vanilla IDs | **4,528** |
| Parameterized documentation sections expanded | 42 |
| Full catalog, including custom definitions and trait stats | 4,581 |
| Spirit picker, excluding 12 synthetic military stat fields | 4,569 |
| Documented IDs missing from full catalog | **0** |
| Documented IDs missing from spirit picker | **0** |

The independent audit split headings/type lists separately from the implementation
and compared all resulting IDs against both full catalog and spirit choices.
The 42 sections include repeated templates for different documented type lists;
their resulting identifiers are deduplicated. Coverage JSON records each section.

Catalog sources: 4,525 entries from engine documentation, three overridden by
vanilla modifier-definition entries, 41 custom mod definitions and 12 synthetic
trait-stat/weight fields. There are 19 Boolean entries including custom definitions.
Existing translations resolve for 1,467 entries; the rest have derived labels,
not invented localisation. These counts describe the installation audited here.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_traits.py'`:
  **12 passed** in the focused run.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_countries.py'`:
  **32 passed** in the focused run.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **197 passed** on the final run. Regression coverage includes CRLF Boolean
  metadata, category isolation, template merging, case-sensitive expansion,
  custom overrides, actual picker exact-ID search, army/generated/Boolean values,
  Apply, native Save/reload, existing effect preservation and trait-stat rejection.
- `python -m py_compile` on all six changed Python files above: passed, with
  cache redirected to system Temp using `PYTHONPYCACHEPREFIX`.
- Real-mod mapped Tk probe: spirit chooser exact-ID search/selection,
  `army_core_defence_factor = 0.1`,
  `production_speed_arms_factory_factor = 0.2`, and
  `can_guarantee_other_ideologies = yes` Add/Apply/Undo passed, plus shared trait
  picker coverage/Cancel. Used `lok_tribal_economy` only in drafts. Live Save
  forbidden; no callback errors; **4,324 native source hashes unchanged**.
- Complete independent documentation coverage audit passed; primary document
  SHA256, per-template counts and examples are in `coverage.json`.
- Supplemental vanilla idea scan: 211 files parsed, all 617 canonical modifier
  IDs found in their direct modifier blocks are present. The two other scalar
  keys are `custom_modifier_tooltip` (text entry) and `army_org_Factor` (source
  case variant of already documented `army_org_factor`). Neither was invented
  as a separate engine modifier. The lightweight parser could not read three
  other vanilla idea files: persia.txt, SOV.txt and switzerland.txt, reporting
  Unclosed block. This limits the supplementary scan, not the exhaustive
  engine-documentation audit. It is not a claim those files fail in HOI4.
- Scoped `git diff --check`, implementation diff review and changed-file checks
  passed. Global working tree contains unrelated authored/native whitespace and
  content changes; they were not reformatted or rolled back.

No map/topology edit was made, so map validation was not required for this patch.
HOI4/CWTools were not run. Catalog coverage and editor persistence do not establish
that every modifier has a gameplay effect in every script context.

## Primary sources and precise locations

Installed game root:
`C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV`.

- `documentation/modifiers_documentation.md:1837`: exact
  `army_core_defence_factor`, numeric display precision and army/defensive tags.
- `common/modifier_definitions/modifier_definitions.txt:23`: categories control
  which modifiers some tooltips display, not a country-idea permission list.
- `common/ideas/afghanistan.txt:111` (also 835, 940, 976) and
  `common/ideas/argentina.txt:838`: vanilla country-idea uses of the exact modifier.
- `documentation/modifiers_documentation.md:4484`: actual parameterized
  `production_speed_<Building>_factor` with supplied building types.
- `documentation/modifiers_documentation.md:2107`: documented Boolean
  `can_guarantee_other_ideologies`.
- The documentation opening explains that listed modifiers are recognized by
  the game but not necessarily used in every context, and display precision is
  separate from supported stored precision.

The user's linked [HOI4 modifier wiki](https://hoi4.paradoxwikis.com/List_of_modifiers)
returned HTTP 401 through the browser tool; both search engines returned no
indexed result. No wiki content was assumed or cited as retrieved. The installed
engine documentation and native examples above were used as primary evidence.

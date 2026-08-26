# English localisation ownership migration

Date: 2026-08-26
Branch: `global-rework-2`

## Result

English localisation was reorganized into `lok_country_*`, `lok_system_*`,
`lok_shared_*`, and `lok_world_*` owners. Intentional vanilla replacements
remain under `localisation/english/replace/`. Localisation keys and quoted
values were not renamed or rewritten.

The reusable inventory/staging checker is
[`tools/localization_migration.py`](../tools/localization_migration.py).

## Baseline versus final

The machine-readable manifests were generated outside the repository during
the migration. The exact parsed definition comparison was:

| Metric | Before | After |
| --- | ---: | ---: |
| Parsed definitions | 59,432 | 59,432 |
| Unique parsed keys | 50,882 | 50,882 |
| Duplicate-key definitions | 8,550 | 8,550 |
| Duplicate keys with conflicting values | 3,248 | 3,248 |
| Malformed definitions | 2 | 2 |
| Missing keys from `loc_analyzer.py` | 2,287 | 2,287 |
| Potentially unused keys from `loc_analyzer.py` | 7,935 | 7,935 |

The exact key set had zero missing keys, zero additions, and zero changed
value multisets. The analyser's unused result is only a static warning and may
include indirect or dynamic references.

## New ownership families

- 279 country files: `localisation/english/lok_country_*_l_english.yml`
- 27 system files: `localisation/english/lok_system_*_l_english.yml`
- 10 shared files: `localisation/english/lok_shared_*_l_english.yml`
- 6 top-level world files plus 10 world files under `localized_state_names/`
- 20 normalized vanilla override files remain under `localisation/english/replace/`

The old catch-alls were split among food, Katzen High Command, Herzlands
Unification, peace/occupation, Space Program, economy, country intro,
notifications, map infrastructure, nuclear, state management, and other
named owners. Country files use the internal section order `CORE`, `FOCUSES`,
`IDEAS / NATIONAL SPIRITS`, `DECISIONS`, `EVENTS`, and
`TOOLTIPS AND MISC COUNTRY CONTENT` where applicable.

## Duplicate definitions

There are 8,550 duplicate-key definitions in the source set. 5,014 keys are
defined in both ordinary localisation and `replace/`, which is expected for
intentional vanilla overrides. The remaining conflicts were preserved rather
than silently discarded; 3,248 duplicate keys have differing values. No
duplicate count increased during migration.

## Malformed definitions preserved

These two source lines were preserved verbatim and intentionally not repaired:

- `parties_l_english.yml:222` → `lok_country_PAW_l_english.yml`
- `replace/lok_diplomacy_l_english.yml:3` → the normalized diplomacy override

## Empty files removed

The empty `CRA_l_english.yml`, `WUW_ideas_l_english.yml`, and
`replace/lok_core_l_english.yml` files were removed. They contained no
localisation definitions.

## Validation

- `python -m py_compile tools/localization_migration.py` — passed using the
  bundled workspace Python runtime.
- `loc_analyzer.py` — completed with unchanged missing/unused totals.
- BOM/header/suffix scan — 352 files passed; no empty generated YAML files.
- Exact baseline/final manifest comparison — passed.
- `git diff --check` — passed.

No Hearts of Iron IV session was launched, so runtime loading and effective
last-definition behavior for pre-existing conflicting duplicates remain
unverified.

## Country, character, and party ownership refinement

The follow-up extraction on 2026-08-26 consolidated the existing world-country
entries with the country-name and formable-name matrices found in the 279
`country_loc` files:

- `lok_world_countries_l_english.yml` now contains 5,150 unique country-name
  entries in alphabetical key order.
- `lok_world_characters_l_english.yml` contains 290 actual character database
  localisation entries, including coupled descriptions, grouped by country.
- `lok_shared_parties_l_english.yml` was renamed to
  `lok_world_parties_l_english.yml`, which contains 3,601 party-related entries
  grouped by country/shared ownership; `replace/lok_parties_l_english.yml` was
  left unchanged. This includes the two generic Parliament party placeholders.
- Extracted keys no longer remain in the country files, and the generated
  target files have no duplicate keys. The 12 generic role/trait labels in the
  existing shared-character file were not character-object names and remain
  there.

The exact baseline key/value audit found no missing or changed baseline pairs.
The worktree also contains 43 additional localisation entries in a concurrent
untracked `LOK_parliament_gui_l_english.yml`; those were not part of this
extraction and were left untouched. One character database reference,
`ZZZ_leader_desc`, has no localisation definition and was not fabricated.

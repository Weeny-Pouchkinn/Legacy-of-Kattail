# Architectural Decisions

## 2026-08-26 — World ownership for country names, characters, and parties

Decision: keep country and formable nation names in the alphabetically sorted
`lok_world_countries_l_english.yml`; keep character names and their descriptions
in `lok_world_characters_l_english.yml` grouped by character owner; and keep
political-party names in the renamed `lok_world_parties_l_english.yml` grouped
by country. Vanilla replacement party localisation remains under `replace/`.

Rationale: these are cross-country display databases rather than country
content, while grouping by owner makes character and party maintenance easier.
Character ownership was derived from actual `common/characters` `name`/`desc`
references; generic role/trait labels without character-object references were
left in the shared-character file.

Consequences: country files no longer duplicate the extracted name, character,
or party keys. The extraction preserves all baseline key/value pairs, but the
game still needs a runtime load check for effective duplicate-key behavior.

## 2026-08-26 — Interface ownership and explicit overrides

Decision: organize custom interface definitions into `lok_country_<TAG>_*`,
`lok_shared_*`, and `lok_system_*` files; retain vanilla-style filenames for
base interface structures; and place deliberate late replacements in
`zzz_lok_override_*` files.

Rationale: the former catch-all files obscured ownership and the
`interface/replace/` directory did not communicate which definitions were
intended overrides. Splitting active blocks by identifier and feature keeps
country content maintainable while preserving the exact GFX identifiers and
the final definition selected under lexical file ordering.

Consequences: the interface tree now has 166 GFX files and 46 GUI files. All
10,943 active GFX definition blocks and 137 pre-existing duplicate names are
preserved. The static audit passes, but the game still needs a runtime UI and
error-log check because actual file enumeration/loading is not available here.

## 2026-08-26 — Single sorted character-portrait library

Decision: keep all named character portrait definitions in
`interface/lok_leader_portraits.gfx`, with one alphabetically ordered country
section per tag and explicit generic/miscellaneous/template sections at the
end. Keep `lok_shared_species_portraits.gfx` separate.

Rationale: character portraits are maintained as one cross-country registry,
while generic species placeholders are a distinct reusable asset library.
Country comments make the registry navigable without changing any `GFX_*`
identifier or texture path.

Consequences: the country-specific portrait files are removed; the character
creator now appends to the single canonical file. The static HEAD fingerprint
and lexical final-definition audits still pass for all 10,943 active GFX
definitions.

## 2026-08-26 — One GFX file per country

Decision: merge each country's remaining ideas, focus icons, modifiers, and
estates GFX sources into `interface/lok_country_<TAG>.gfx`, separated by
uppercase section comments. Country GUI files remain separate because this
rule applies to GFX libraries only.

Rationale: one country file is easier to find and maintain than several
country-suffixed GFX files, while section comments retain the ownership
distinction inside the file.

Consequences: 28 split country GFX files became 20 country files. The updated
focus and national-spirit tools insert into their respective commented
sections, so future generated content preserves the layout.

## 2026-08-26 — Generated GFX indentation

Decision: format owned generated GFX registries by structural brace depth,
using tabs for each nesting level, while preserving all strings, identifiers,
comments, and definition order.

Rationale: the consolidation pass retained inconsistent source indentation,
which made the merged files difficult to read even though their active content
was correct.

Consequences: 54 generated GFX files now use consistent indentation. The
interface audit compares whitespace-insensitive active definitions so future
formatting does not appear as a semantic migration.

## 2026-08-26 — Canonical localisation ownership files

Decision: normal English localisation is organized as one `lok_country_<TAG>` file per country, with named `lok_system_*`, `lok_shared_*`, and `lok_world_*` owners; intentional vanilla replacement keys remain under `localisation/english/replace/`.

Rationale: source-file names were not a reliable ownership model, while the underlying script object and country/system scope provide a maintainable canonical location. A staging migration preserved all parsed key/value multisets before replacement.

Consequences: duplicate definitions, including conflicting ordinary/replace pairs, are reported and preserved rather than silently resolved. The new `tools/localization_migration.py` checker is the repeatable baseline/final audit path. Runtime loading and duplicate effective-order behavior still require an in-game check.

## 2026-07-29 — Signed-axis Great Game data model

Decision: represent every contested state with one signed `lok_gg_influence` variable, use exactly one live game per country, store iteration arrays on the host, and mirror only UI/action/reference data to participants.

Rationale: this makes positive and negative competition directly comparable, prevents ambiguous multi-game participant state, and avoids host-side parallel actor metadata arrays.

Consequences: supporters never receive states; their `lok_gg_beneficiary_ref` points to a principal. Participant decisions can read local round data without unsupported owner-variable localisation chains.

## 2026-07-29 — Event-driven bounded processing

Decision: schedule one daily event only on each active host. AI selection is recalculated per action from bounded host-state arrays; spill and settlement use snapshot phases.

Rationale: avoid global recurring scans and iteration-order-dependent outcomes.

Consequences: cost scales with configured participants, their actions, and the host's disputed states. The constants cap participants at 50, actions at 20, and rounds at 200.

## 2026-07-29 — Failed setup and landless-host handling

Decision: failed setup retains staged inputs and sets `lok_gg_setup_invalid`; successful setup clears staging. If settlement transfers every host state, the former-capital recipient annexes the now-landless host after the state split.

Rationale: retained staging is inspectable during content debugging, while post-transfer annexation provides an explicit unit/country cleanup path without letting annexation decide the multi-recipient state distribution.

Consequences: content should call `lok_begin_great_game_configuration` before retrying. Landless annexation semantics remain an explicitly documented in-game validation requirement.

## 2026-08-24 — Aggregate fiscal-capacity authority

Decision: represent the six independent government budget slots with shared `lok_fiscal_capacity_usage` modifier contributions, use `lok_base_fiscal_capacity` for the 100-point base, and keep variables as display/dynamic-effect mirrors rather than a second authority.

Rationale: this avoids six manually maintained usage variables while allowing any law add/remove to recalculate from current modifier totals. The overextension modifier reads the calculated penalty variable and applies only the requested political-power effect.

Consequences: changing a budget law triggers `LOK_update_fiscal_capacity`; the monthly fallback repairs or initializes missing slots. The first-pass system has no economy, money, debt, taxes, or prosperity layer.

## 2026-08-24 — Fiscal-capacity initialization fallback

Decision: initialize countries through the existing startup `every_possible_country` loop, known country-lifecycle hooks, and a monthly fallback because the current repository does not expose a verified generic country-created on-action.

Rationale: this covers scenario-start countries and the repository's known creation paths without inventing an unsupported on-action. The monthly pulse is explicitly requested and provides eventual coverage for other dynamically generated countries.

Consequences: a country created through an unrecognized path may lack the system until the next monthly pulse; this requires runtime testing against the declared game version.

## 2026-08-24 — Parliament uses popularity arrays for the first display pass

Decision: use the inspected ideology indices and tokens directly: `pol_party_array^0..^8` map to `communism`, `socialism`, `social_democratic`, `social_liberal`, `democratic`, `social_conservative`, `authoritarian_democratic`, `neutrality`, and `fascism`; `gestalt` is excluded completely. Treat `3` as hostile, `2` as coalition, and `1` as neutral, while detecting the ruling party through `has_government`.

Rationale: the initial seat-allocation display rendered unusable zeros and raw/missing text. The simpler first pass keeps the Parliament readable by storing popularity directly in an ideology-indexed share array, storing the relation-based approval factor in a second array, and storing their product in a third array.

Consequences: slots 0–8 map to the nine non-Gestalt ideologies. `LOK_hold_parliament_election` excludes hostile popularity before normalizing the share array, so hostile parties receive 0% and eligible parties receive the redistributed share. It refreshes the arrays yearly and at initialization; seats, population calculations, and seat-allocation variables are no longer part of the Parliament implementation. Government support is persisted in `lok_parliament_government_support` for reliable display. Party names remain dynamically resolved from canonical `TAG_ideology_party` keys, while ideology labels use dedicated Parliament scripted-localisation functions. Each ideology has one party localisation key; `LOK_GetParliamentPartyStatus` injects the relation-status line. `LOK_update_parliament_approval` runs on `on_ruling_party_change`, setting the new non-hostile ruling party's approval array slot to 1.0 without changing its popularity share.

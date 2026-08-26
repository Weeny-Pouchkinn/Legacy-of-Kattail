# Current Status

## Signed-Axis Great Game — 2026-07-29

Implemented the reusable one-game-per-country signed-axis Great Game system described in `modding_documentation/great_game_system.md`.

Completed:

- atomic staged start validation and public begin/start/abort effects;
- host-owned participant/state arrays and participant-local role/UI/action data;
- one-sided and two-sided influence, direct actions, claimant cohesion, simultaneous spill, isolation, bounded AI actions, and ten-day host scheduling;
- normal and doomed settlement snapshots, compliance, capital-last transfers, landless-host cleanup, invalidation, and idempotent cleanup;
- state-target decision UI with scripted localisation;
- `lok_debug.22`, which starts PRL (+) versus MEW (-) over WPR;
- developer documentation and ten configuration examples.

Validation performed:

- CWTools 0.10.31 language server: zero diagnostics published for all nine changed HOI4/localisation files;
- balanced-brace check: zero imbalance for every changed HOI4 script;
- `loc_analyzer.py`: no Great Game key appeared in its missing or potentially-unused results (repository-wide totals remain 2,287 missing and 7,895 potentially unused, treated as pre-existing diagnostics);
- localisation BOM/header, generated-entry marker, and duplicate-key checks passed;
- exact namespace/event collision search passed;
- verified PRL, WPR, and MEW country tags and the two selected decision sprites;
- `git diff --check` plus no-index checks for untracked files passed.

Unverified:

- no Hearts of Iron IV session was launched;
- save/reload persistence and the specification's full gameplay scenario matrix remain untested;
- landless-host annexation after a split settlement needs in-game confirmation;
- the available game install is 1.19.2 while `descriptor.mod` declares `supported_version="1.17.*"` and separately `version="1.15.*"`.

Next concrete action: launch the declared-compatible game environment, run `event lok_debug.22`, exercise at least one complete two-sided game, then test save/reload and settlement edge cases while checking a fresh `error.log`.

### English localisation ownership migration — 2026-08-26

Completed the structural English localisation migration for `global-rework-2`.

Completed:

- split country names, parties, characters, country ideas, focus/event/decision localisation, and country-specific traits into 279 `lok_country_<TAG>_l_english.yml` files;
- split catch-all content into named `lok_system_*`, `lok_shared_*`, and `lok_world_*` files;
- kept vanilla overrides under `localisation/english/replace/`, normalizing their filenames to lowercase `lok_` names where needed;
- removed empty CRA, WUW, and `replace/lok_core` localisation files;
- preserved 59,432 parsed definitions, 50,882 unique parsed keys, all duplicate definitions, and both malformed source lines;
- added `tools/localization_migration.py` and `modding_documentation/localisation_migration_report.md`;
- ran BOM/header/suffix checks, the analyser, an exact baseline/final key-value comparison, and `git diff --check`.

Unverified:

- no Hearts of Iron IV session was launched after the migration;
- pre-existing duplicate keys with conflicting values remain and their final in-game load-order behavior was not runtime-tested;
- the analyser still reports 2,287 missing and 7,935 potentially unused keys, unchanged from baseline and subject to indirect-reference false positives.

Next concrete action: launch the mod, confirm localisation loading and inspect the affected country/system UI paths, then review whether any duplicate definitions require an explicit project decision.

### Country, character, and party localisation refinement — 2026-08-26

Completed:

- extracted the existing country-name/formable-name matrices from all 279
  `localisation/english/country_loc/` files into the alphabetically sorted
  `localisation/english/lok_world_countries_l_english.yml`;
- extracted 290 localised character names/descriptions referenced by
  `common/characters/` into `lok_world_characters_l_english.yml`, grouped by
  owning country with comments;
- renamed `lok_shared_parties_l_english.yml` to
  `lok_world_parties_l_english.yml` and grouped its 3,601 party-related entries
  by country/shared ownership, including the two generic Parliament party
  placeholders; the vanilla `replace/lok_parties_l_english.yml` override
  remains separate;
- verified that no extracted keys remain in the country files and that all
  three destination files have unique, ordered keys and UTF-8 BOM headers;
- preserved every baseline key/value pair exactly. A separate concurrent
  untracked Parliament GUI localisation file contributes 43 additional pairs
  outside the extraction.

Unverified:

- no Hearts of Iron IV session was launched after this refinement;
- `common/characters` references `ZZZ_leader_desc`, but no localisation value
  exists for it; no placeholder was invented;
- effective runtime last-definition behavior for pre-existing conflicting
  duplicate keys remains untested.

Next concrete action: launch the mod and inspect country names, character
tooltips, and political-party names in-game, then review any runtime
localisation errors against a fresh `error.log`.

### Interface ownership migration — 2026-08-26

Completed:

- reorganized the interface GFX libraries into country-owned, shared, and
  system-owned files, including country splits for ideas, portraits, and
  focus icons;
- renamed custom GUI/GFX pairs to explicit `lok_system_*` or
  `lok_country_*` names while preserving all internal GUI object and sprite
  identifiers;
- moved the former replacement-folder definitions into explicit
  `zzz_lok_override_*` files and retained vanilla-style interface filenames;
- updated repository generators and wonder documentation to use the new
  ownership paths;
- consolidated all 585 named character portraits into
  `interface/lok_leader_portraits.gfx`, sorted into 93 country sections with
  comments, while leaving generic species portraits separate;
- updated `character_creator_2.py` to append to the consolidated portrait
  file;
- merged the remaining 28 split country GFX files into 20 canonical
  `lok_country_<TAG>.gfx` files with commented ideas, focus-icon, modifier,
  and estates sections;
- checked all 60 generated GFX registry files and normalized structural
  indentation to tabs in the 54 files that needed it, without changing active
  definitions;
- removed only the comment-only FRA interface files;
- added `tools/interface_reorganization.py` and
  `modding_documentation/interface_migration_report.md`;
- preserved 10,943 active named GFX blocks, 10,806 unique identifiers, and
  all 137 pre-existing duplicate identifier names;
- passed active-block fingerprint, lexical final-definition winner, brace,
  direct-rename, and `git diff --check` audits after formatting.

Unverified:

- no Hearts of Iron IV session was launched after the interface migration or
  portrait/country-GFX consolidation;
- runtime interface file enumeration and visual loading remain untested;
- `generate_lok_parliament_gui.py` remains pre-existingly uncompilable at its
  original f-string syntax error on line 1038; only its output paths changed.

Next concrete action: launch the mod, inspect the affected system/country UI
paths, and check a fresh `error.log` for interface loading errors.

### Generic Parliament — 2026-08-24

Implemented a first-pass universal informational Parliament category and reusable `LOK_hold_parliament_election = yes` effect in the current `global-rework` workspace. The requested repository branch was `great-game-test`, but this worktree was already on `global-rework`; no branch switch was performed.

Completed:

- yearly and startup election hooks, plus existing coup/civil-war/puppet lifecycle hooks;
- persistent `lok_parliament_party_share_array`, `lok_parliament_party_approval_array`, and `lok_parliament_party_gov_array` values for the nine non-Gestalt ideologies; the share array is normalized across non-hostile popularity;
- popularity display using the requested `Holds [amount]% of seats` wording, with current party status and government-contribution percentages;
- hostile-party zero approval and government contribution using the existing `pol_party_array` values;
- persistent `lok_parliament_government_support` aggregation from the government-contribution array;
- dynamic category title (`ROQ` → `Assemblée Nationale`, otherwise `Parliament`), ideology labels/colours, and existing canonical `TAG_ideology_party` lookup;
- no custom GUI or new graphical assets;
- one party localisation key per ideology, with shared `LOK_GetParliamentPartyStatus` scripted localisation injecting the hostile/ruling/coalition/neutral status line;
- `LOK_update_parliament_approval` is called by `on_ruling_party_change`, giving the new non-hostile ruling party 100% approval immediately without changing its popularity share.

Static validation passed for balanced braces, localisation BOM/header, identifier/reference audits, requested arithmetic cases, and `git diff --check`. CWTools and an actual game session were unavailable for this task. The repository has no verified localisation-key-existence trigger, so canonical party-key fallback behavior for countries relying on base-game or dynamically assigned party names remains a runtime verification item rather than an invented script construct.

### Runtime parser correction — 2026-07-29

An in-game parser run exposed trigger/effect argument forms that CWTools 0.10.31 had accepted incorrectly:

- dynamic state-owner comparisons now use `is_owned_by = event_target:<country>` instead of `owner = event_target:<country>`;
- host ownership validation now uses `is_owned_by = PREV`;
- landless-host annexation now targets an explicitly saved `event_target:lok_gg_resolved_host` instead of the malformed `PREV.PREV` argument.

Static searches confirm that the rejected dynamic `owner = ...`, `var:owner`, and `target = PREV.PREV` forms no longer occur in the Great Game files. A fresh in-game parser run is still required to confirm that no subsequent runtime-only diagnostics remain.

### Runtime array-scope correction — 2026-07-29

The first playable debug run showed PRL with round `0 / 0`, PRL duplicated as the negative claimant, no state decisions, and repeated country-scope errors for state triggers. The cause was cross-scope writes such as:

```hoi4
PREV = {
	add_to_array = { lok_gg_states = THIS }
}
```

After entering `PREV`, `THIS` referred to the host country, so host, participant, and state arrays received the wrong scope type. All affected writes now use the repository's working scoped-left-hand-side pattern:

```hoi4
add_to_array = { PREV.lok_gg_states = THIS }
```

This correction covers:

- host state and participant arrays;
- claimant references written back to the host;
- participant-local target-state arrays;
- AI priority and fallback arrays;
- invalid participant and state removal arrays.

The geographic-support scripted triggers were also stripped of an invalid `var:owner` scope chain, and decision ownership checks now use `is_owned_by = var:ROOT.lok_gg_host_ref`.

Existing saves in which the broken event already ran contain corrupted persistent arrays and a scheduled host tick. Retesting requires a save from before `lok_debug.22` was fired or a new game.

### Government Budgets + Fiscal Capacity — 2026-08-24

Implemented a first-pass six-slot Government Budgets system with seven levels per slot. Each level contributes to the aggregate `lok_fiscal_capacity_usage` modifier; `lok_base_fiscal_capacity` provides 100 capacity. `LOK_update_fiscal_capacity` mirrors authoritative modifier totals into display variables, calculates remaining capacity, overage, and the political-power penalty, and refreshes `lok_fiscal_capacity_overextension_modifier`.

Initialization is wired into the existing startup country loop, with lifecycle hooks for puppets, releases, and civil-war endings plus the requested monthly fallback. No reliable generic country-created on-action was found in the current repository, so dynamically created countries are guaranteed to converge on the next monthly pulse rather than necessarily receiving budgets immediately. Static validation passed for 6 roots, 42 levels, cost mappings, initializer coverage, localization coverage, UTF-8 BOM, braces, and `git diff --check`. A fresh game launch and runtime error-log review remain outstanding.

### Runtime decision-target and cohesion-scope correction — 2026-07-29

The next in-game run exposed two additional runtime-only scope failures:

- the state-targeted decision evaluated `event_target:lok_gg_action_state` while building decisions, before its `complete_effect` could save that target;
- the cohesion neighbor loop used `PREV.PREV` for the acting claimant, but that chain resolved to a state when `has_country_flag` required a country.

The decision now saves its action targets on click and immediately calls `lok_apply_great_game_action`, whose validation runs after those targets exist. Cohesion now saves the acting participant as `event_target:lok_gg_cohesion_actor` before entering state scopes and uses that explicit country target for claimant checks and result assignment.

Static reference, scope-pattern, brace, line-ending, and diff checks passed after this correction. A fresh game restart and clean runtime log remain necessary because no game session was launched by Codex.

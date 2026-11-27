# Country diplomacy editor - 2026-11-27

## Summary

Countries > Edit selected > Diplomacy loads incoming/outgoing starting diplomatic
declarations, with source file/line and original condition/date context. Add,
Edit, Remove, search and Show all countries cover faction leader/name/member,
war/goal, subject/autonomy/freedom, guarantee, military access, non-aggression
pact and equipment-market access. Localized pickers include landless tags.
Creating a new country uses the existing Apply-country prerequisite before
adding its diplomacy. Parent Cancel includes all nested edits. Shared Documents
drafts, grouped Undo/Redo, normal Save conflict checks/backups and tab formatting
remain authoritative. Opening the editor makes no source changes.

Discovery reads mod country/general histories and on_startup effect blocks,
literal nested country and ROOT/THIS/PREV scopes, base/dated/conditional history,
and reachable scripted effects. Shared scripted effects/dynamic unresolved
targets are visible but require source editing, since editing a shared function
for one country would affect other callers. Runtime event chains and arbitrary
trigger execution are not simulated.

Static faction membership expands every_country/every_possible_country loops;
exists/tag/is_in_faction_with and simple boolean limits are evaluated using
current draft owner histories. Editing/removing one group instance leaves the
original declaration behind a NOT-tag guard and applies any replacement only
under that country's tag inside the same original loop. Conditions, ROOT/PREV,
other members, comments and unknown relation fields are preserved. Source spans
are checked for stale records before writes. Unchanged Apply is a no-op.

New subject setup is written in the subject's own history before political
setup, using an explicit overlord scope. It sets end_wars/end_civil_wars = no
and keep_subjects = yes, avoiding accidental loss of the requested starting wars
or subordinate subjects. New faction creation precedes membership commands;
ordinary additions append to the appropriate country history. Edits patch the
original source declaration, including conditional/startup/dated declarations.
Legacy puppet blocks convert to set_autonomy when changing autonomy fields.

Validation checks tags/self-links, source immutability for existing rows,
duplicate/mutual relations, existing faction membership, subject uniqueness,
overlord cycles, same-faction/overlord-subject wars and 0-1 finite freedom values.
Autonomy/war-goal catalogs honor replace_path and same-file vanilla overrides.
Conditional existing declarations retain their conditions rather than being
treated as guaranteed active relationships. Existing unknown literal target
tags are visible and can be removed or corrected; dynamic targets remain guarded.

## Files changed in this task

- legacy_of_kattail_painter/diplomacy_model.py (new)
- legacy_of_kattail_painter/diplomacy_ui.py (new)
- legacy_of_kattail_painter/test_diplomacy.py (new)
- legacy_of_kattail_painter/country_ui.py
- legacy_of_kattail_painter/painter.py (store initialization/import only here)
- legacy_of_kattail_painter/install.py (three manifest entries)
- legacy_of_kattail_painter/README.md (Country diplomacy section)
- modding_documentation/agent_memory/plans/country-diplomacy-editor.md (new)
- modding_documentation/agent_memory/country_diplomacy_editor.md (this report)
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md

The previously completed state-boundary editor remains in the working tree.
No production country-history/diplomacy, map, faction names or geopolitical
relationships were changed for this implementation or testing.

Identifiers: Python DiplomacyStore, Relation, DiplomacyPanel, RelationDialog;
country tab key diplomacy. Native effects are existing create_faction,
add_to_faction, set_autonomy, declare_war_on, give_guarantee,
give_military_access, give_market_access and diplomatic_relation. No new native
game keys, flags, country tags, on-actions, scripted effects or localisation IDs.

## Sources inspected

- modding_documentation/wiki_doc/Country creation - Hearts of Iron 4 Wiki.md,
  lines 181-205: Diplomacy-related effects, subject setup before politics in
  the subject history, faction creation/name/localisation and membership.
  Its sample misspells autonomous_state; use autonomy_state, verified in the
  engine reference and all native mod subject setup.
- Installed HOI4 documentation/effects_documentation.md: add_to_faction 2294,
  create_faction 3101, declare_war_on 3468, diplomatic_relation 3565,
  give_guarantee 4566, give_market_access 4575, give_military_access 4588,
  puppet 5195, set_autonomy 6587, remove_from_faction 6032 and white_peace 8600.
  The installed game deprecates create_faction for a newer template API; retain
  the mod's existing syntax for its declared 1.17 compatibility target.
- history/countries/ACR - Amphibious Confederal Republic.txt, lines 13-26:
  faction/member setup, faction-filtered war loop and EUL puppet declaration.
- history/countries/PGN - Piertuguese.txt, lines 13-21: exists-guarded KOA war.
- history/countries/FLM - Mercurian Forces in Fleather.txt, lines 111-120:
  nested MER market access and non-aggression pact.
- history/countries/PLR - Paluushian Realms.txt, lines 11-12:
  autonomy_outer_mayorland; common/autonomous_states/outer_mayorland.txt.
- Existing country_ui.py, character_ui.DraftDialog, model.Documents,
  country_model.CountryStore and source formatter for draft/Cancel/Save behavior.

## Validation

- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_diplomacy.py -v`
  passes 9 tests: source/conditional/dated/startup/shared detection, group-instance
  isolation, source preservation, Save/reload, Undo, custom autonomy/extra fields,
  new subject placement, duplicate/cycle/reference checks, catalog overrides,
  unregistered targets, legacy puppet migration, escaped-name/no-op behavior,
  live draft ownership and real country-tab/Apply/parent-Cancel controls.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`
  passes 249 tests, including the existing state-boundary feature tests.
- `python -m py_compile legacy_of_kattail_painter/diplomacy_model.py legacy_of_kattail_painter/diplomacy_ui.py legacy_of_kattail_painter/test_diplomacy.py legacy_of_kattail_painter/country_ui.py legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/install.py`
  passes, with PYTHONPYCACHEPREFIX isolated in a disposable temporary directory.
- Native inventory: 77 declarations: 7 faction leaders, 21 member declarations,
  17 subjects, 18 wars (including 12 expanded faction-loop instances), 10
  guarantees, 2 market-access and 2 non-aggression declarations. Catalogs show
  16 effective autonomy levels and 10 war-goal types. ACR's literal MSN member
  target is currently unregistered; it is displayed as such, not silently fixed.
- Native staged probe: removed DAW->FOD war only, verified ACR/EUL->FOD retained,
  Undo restored inventory; added CAT->ANS subject, verified setup precedes ANS
  politics; Undo cleared drafts. Native Painter/real EUL country dialog showed
  all six applicable declarations, including ACR faction, subject and wars;
  zero callback errors. No Save. SHA-256 of all 212 native country histories
  before/after matches exactly. Test windows were closed.
- `git diff --check`, `git diff --stat` and complete relevant diff/new source
  review pass; installer files verified present. Existing pending boundary
  implementation retained. No tracked caches or generated diagnostics added.

## Uncertainties / remaining work

No game engine launch: actual fresh-game execution and tooltips are untested.
Next concrete validation is saving a chosen diplomacy edit and inspecting that
fresh campaign's diplomacy. This editor exposes source declarations; it cannot
guarantee the net result of future events, DLC branches, runtime faction changes,
scripted calls or engine load ordering. It makes no automatic geopolitical edits.

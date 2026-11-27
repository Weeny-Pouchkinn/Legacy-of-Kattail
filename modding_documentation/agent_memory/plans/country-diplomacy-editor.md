# Country diplomacy editor - 2026-11-27

- [x] Inspect instructions/memory, country editors, native relations and local
  game/wiki documentation. Existing direct/nested subjects/factions/wars,
  PGN conditional war and ACR faction-member war loop must be recognized.
- [x] Add source-aware relation discovery over country/general histories and
  startup effects, retaining dates/conditions and editable physical sources.
- [x] Implement native add/edit/remove, faction membership, custom autonomy,
  war-goal and bilateral relation validation; shared-loop instance isolation.
- [x] Add Countries > Diplomacy tab with existing relations/source/context,
  localized country pickers and complete relation dialogs; preserve draft Undo,
  Cancel and Save behavior, including new countries.
- [x] Exercise disposable regression/UI fixtures, native inventory/draft probes,
  Python compilation, full suite and diff review. Do not save native relations.
- [x] Update documentation/status/decisions with actual validation and limits.

Existing boundary-editor changes are pending in the working tree; retain them.
No engine simulation is claimed: conditional/dynamic/delayed scripts are labeled.
No global recurring work or automatic starting-geopolitics changes are authorized.

Completed: 9 new diplomacy tests, full suite 249 passing; six Python files
compile. Native inventory 77 declarations/16 autonomy levels/10 war goals;
staged DAW war isolation, CAT->ANS subject placement, Undo and real EUL tab pass.
All 212 country-history hashes unchanged, no real Save or engine launch.
Report: ../country_diplomacy_editor.md. Next concrete engine check: save a chosen
relation in painter, start a fresh campaign and inspect its diplomatic setup.

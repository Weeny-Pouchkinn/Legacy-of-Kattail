# Core audit and Owners painter - 2026-11-27

Completed the additive core audit and implemented ownership/core transfer,
independent core/claim painting and nominal-capital saves.

## Native audit

Out of 1,902 owned base-history states, **167** lacked the owner's core outside
the specified exceptions. Added those cores across **38 countries**. All 1,898
non-excluded states now have their owner's core. Audit source and proof:
[tools/audit_owner_cores.py](../../../tools/audit_owner_cores.py),
[dry_run.json](dry_run.json), [repair.json](repair.json) and
[post_repair_check.json](post_repair_check.json). Second run proposes zero changes.

The four verified exceptions are:

| State | Name | Owner | Retained core |
| --- | --- | --- | --- |
| 34 | Nord-Katown | SIL | KTW |
| 36 | Westen-Katown | SIL | KTW |
| 44 | Ost-Katown | SIL | KTW |
| 45 | Sud-Katown (native name: SÃƒÂ¼d-Katown) | SIL | KTW |

Each has `set_demilitarized_zone = yes` in its immediate history. All four source
files remain byte-identical, verified by SHA-256. Other DMZ states were not
excluded: the request concerned these four SIL Katown states specifically.

Exact backup directory:

`legacy_of_kattail_painter/backups/owner_core_audit_20261127_164250_453011`

All other countries' cores and every claim are retained. Ownership, province
membership, dated history, localisation and other gameplay fields are unchanged.
For every changed file, deleting just that owner's immediate add/remove core
operations produces an identical ordered lexer token stream, including exact
comments. The resulting core set equals the old set plus the owner; owner and
claim sets match exactly. Changed scopes use the shared tab formatter; encoding,
BOM and newline handling use the normal source writer. Native writes are guarded
against concurrent changes, backed up and checked by exact readback. Final backup
and native hashes still match the repair manifest. Only state-history files were
written; binary map assets and province geometry were not changed.

## Painter behavior

Owners contains Ownership and Cores/Claims categories. Transfer Cores defaults
on. Giving a state to a different country adds that country's core and removes
only the prior owner's core, leaving third-party cores and all claims intact.
Painting its existing owner is a no-op, preserving deliberate non-core land
and the four exceptions.
Off leaves memberships unchanged. The same flag governs map painting, inspector
owner changes, state-dialog owner changes and native field/source owner edits.
The state dialog exposes the shared checkbox too. If a state edit changes both
owner and explicit membership lists, transfer reconciliation runs last; disable
Transfer Cores when authoring a deliberately non-core owner assignment.

In Cores/Claims, every registered country appears, including landless tags and
tags with no country history yet. Selected-country cores are green, claims yellow,
and ownership blue-striped. A core takes base-color priority if both memberships
exist; the claim is still retained and editable. An owned state without either
membership shows blue over gray. No selection/other membership is gray; seas
retain the existing water color. Stripes use map coordinates, so viewport crops
and exports agree. MapConfig stores the selected country: saved overlays keep
their country's view while live state data continues updating.

| Gesture | Operation |
| --- | --- |
| Left-click/drag | Add core |
| Shift-left-click/drag | Add claim |
| Right-click/drag | Remove core |
| Shift-right-click/drag | Remove claim |

Middle-drag pans. These edits do not transfer ownership. State/strategic-region
brush scopes and once-per-stroke filtering use existing paint targets. Selected
tag validation, grouped rollback, Undo/Redo, guarded Save, overlays and viewport
PNG rendering share the existing native editor paths. Cores/claims are read in
immediate-source order, including removals; dated blocks remain separate.

The user's nominal-capital request explicitly supersedes the earlier capital-
ownership save guard. Country UI/model already offered all defined states; the
Save hook now permits any defined nominal capital, even when the country owns
other territory. Undefined newly edited IDs remain invalid. No capital state is
automatically assigned, transferred or relocated.

## Files changed and identifiers

Implementation/test/tool files:

- `legacy_of_kattail_painter/model.py`
- `legacy_of_kattail_painter/painter.py`
- `legacy_of_kattail_painter/map_render.py`
- `legacy_of_kattail_painter/geography_model.py`
- `legacy_of_kattail_painter/geography_ui.py`
- `legacy_of_kattail_painter/install.py`
- `legacy_of_kattail_painter/test_cores.py`
- `legacy_of_kattail_painter/test_painter.py`
- `legacy_of_kattail_painter/test_startup_safety.py`
- `tools/audit_owner_cores.py`

All **167 exact state paths** are listed in [repair.json](repair.json), with
before/after hashes and the complete exception records. The complete file list,
including documentation, is [files_changed.txt](files_changed.txt).
Documentation: painter README/MODLOG, agent_memory CURRENT_STATUS/DECISIONS,
[plan](../plans/core-audit-and-painter.md), this report and JSON proof records.
Existing unrelated AI, country, spirit, EaW and localisation edits were preserved.

No game IDs, flags, namespaces, sprites or localisation keys were added/renamed.
Native operations use existing `add_core_of`, `remove_core_of`, `add_claim_by`
and `remove_claim_by`. The new map view is within the painter. Python interfaces
added: World.state_relations/set_relation_draft/transfer_owner_cores;
transfer_cores on owner/state edit APIs; country_tag in MapConfig/rendering.

## Validation actually performed

- `python -B tools/validate_map.py`, before and after applying the audit: passed;
  21,515 provinces, 20,926 assigned, 413 strategic regions, no X crossings.
- `python -B tools/audit_owner_cores.py --help`: inspected the actual interface.
- `python -B tools/audit_owner_cores.py --report
  modding_documentation/agent_memory/core_audit/dry_run.json`: 167 candidates.
- `python -B tools/audit_owner_cores.py --apply`: 167 guarded writes with backups,
  token/core-set proofs and exact readback. All four exception hashes retained.
- `python -B tools/audit_owner_cores.py --report
  modding_documentation/agent_memory/core_audit/post_repair_check.json`: zero changes.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_cores.py`:
  seven integration tests pass. Covers transfer on/off, third-party cores/claims,
  atomic Undo, repeated add/remove order, comments/dates, no-op repaint, actual
  landless country editing and Save/reload, invalid tags, state-editor owner
  changes, exact color/stripe/crop samples, overlay country retention, audit
  exceptions/idempotence and real Tk gestures/checkbox/field/source editing.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **224 tests passed** in 41.124 seconds. Earlier ownership-capital regressions
  were updated to the explicitly requested nominal-capital policy while retaining
  undefined-ID rejection and Save/Undo coverage.
- Python `py_compile.compile(..., doraise=True)` for all 10 implementation/test/
  tool files listed above, with temporary cache destinations: passed.
- Actual native Painter/World probe: Owners categories, landless palette tag,
  all four membership operations, same-owner exception no-ops, overlay country
  snapshot, ownership transfer,
  nominal foreign capital, full Undo and exact native-source hashes: passed.
  Production Save forbidden, zero callbacks, **4,225 native sources unchanged**.
  See [verification.json](verification.json). KTW was initially assumed landless;
  ownership inspection disproved that, so the successful probe used verified
  landless AAA. No test changes were written to real game sources.
- `git -c core.fsmonitor=false diff --check`, `git diff --stat`, source/diff review,
  native before/after backup hashes, exception hashes, documentation paths and
  installer references: passed. All non-core native changes are layout-only,
  proven by the token comparisons above.

No game launch/CWTools execution was performed. This audit targets immediate
state-history setup, not runtime conquests, scripted future transfers or dated
bookmarks. The painter does not promise how the engine treats a foreign nominal
capital; the requested save freedom is implemented and fixture/native-model
checks pass. Restart the painter to load the new controls; inspect state-history
changes in a fresh campaign for engine verification.

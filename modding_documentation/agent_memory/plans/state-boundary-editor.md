# State boundaries and new-state authoring - 2026-11-27

- [x] Read instructions, memory and existing ownership/geography/save/render code.
  Inspect map files and native building/spawn definitions; baseline map check passes.
  Official wiki fetch is 401; primary local game/mod data is authoritative.
- [x] Add state index/cache synchronization for new/deleted draft states and Undo.
- [x] Implement atomic whole-province moves/new states, single-region/nonempty
  constraints, base/dated province buildings/VP relocation and inherited setup.
- [x] Add conservative integer population, area resources and optional VP/count
  industry redistribution with deterministic rounding and per-stroke baselines.
- [x] Regenerate affected building/spawn placements from actual definitions and
  province/height geometry, retaining valid coastal access and manual landmarks.
- [x] Add States > State boundaries, new-state seed selection, recalculation flags,
  painting/picking, operation status, Undo/Redo/Save and map/cache refresh.
- [x] Verify fixtures for all coupled files/flags/rounding/rollback; full suite,
  compile/map checks, staged native-map exercise and native UI without real Save.
- [x] Update documentation/decisions/status with actual results and engine limits.

No existing state boundaries are to be changed in production by this feature task.
Use disposable/staged native probes. Source/target nonempty, land-only, exactly one
strategic region. New ID exceeds existing maximum and never collides. New names
are entered by the user. New states inherit source politics/category/demographics;
each affected state has a valid airbase model placement. Existing levels stay
unchanged; new states get no automatic airbase building (explicit user correction).
Recalculation preserves totals; placements never create gameplay buildings.
Population weights use actual province area/terrain and strong VP urban weighting;
resources area; industrial shared-slot buildings VP plus province count. Industry
is off by default; population/resources on. Province geometry/IDs, rail paths,
supply node IDs, VP IDs/localisation and province unit positions remain intact.

Implementation: `legacy_of_kattail_painter/state_boundary_model.py`,
`state_positions.py`, `state_boundary_ui.py` plus painter/render/save integration.
Ten new tests, full suite 240 passing; native UI 1902 states/no callback errors,
no drafts. Disposable native split of state 16 into temporary state 1903 and a
second transfer passed `tools/validate_map.py`; population 210000 conserved as
4755 + 205245. All 1908 checked production file hashes stayed unchanged.
Production map validator and Python compilation pass. Final review also added
explicit repair/rejection of ordinary building models on lake pixels.
Exact commands, files, semantics and engine limitation: `../state_boundary_editor.md`.

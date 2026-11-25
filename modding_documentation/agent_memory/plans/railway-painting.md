# Province railway painting — 2026-11-25

- [x] Inspect native route format, level define, map adjacency and supply hub sprite.
- [x] Add native graph editing/compaction with bounds and topology checks; preserve
  pre-existing invalid links and introduce no new ones. Keep edits inside drawn
  provinces, without pathing through unpainted land.
- [x] Add railway map layer, exact/add-remove brushes, amount, existing-only guard,
  province-level strokes and native supply hub icon toggle with overlay parity.
- [x] Verify graphs/branches/loops/wrap, topology, Undo/Redo/guarded Save/reload,
  actual UI, native source hashes and performance. Run full suite, compile and
  map validator. Document limits and update durable status/decisions.

Design: native railway levels belong to connections. Province clicks change
incident connections; map labels report the highest touching level. Isolated
first points are stroke anchors until a neighboring province is painted. Save
compacts equal-level links into native paths, retaining the same links/levels.
No new game data sidecars, new hubs, global routing or game-time script.

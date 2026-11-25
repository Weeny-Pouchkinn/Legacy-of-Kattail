# Species/culture map colours and optional groups - 2026-11-25

- [x] Inspect native scripts, painter readers/writer, installed mapmode docs and
  latest log. User identifies Altarian (species 61), intended #9DFFFF but white
  in game. Source contains correct intended fraction; engine rendering not yet
  reproduced. Preserve recent user edits to species 61 and new culture 103.
- [x] Confirm culture writer overwrites division operands as well as literals;
  live culture 103 has three corrupt divisors. Minority IDs 20-23 have duplicate
  branches, and writer changes only the first while readers use the last.
- [x] Correct targeted colour writes, duplicate handling and native precision;
  repair confirmed affected native data and audit actual calculation paths.
- [x] Support ungrouped cultures in UI/model/native arrays/triggers/localisation.
- [x] Add meaningful native-operation regression tests, Save/reload/Undo and UI
  coverage; run full checks and record remaining engine-rendering uncertainty.

Installed common/map_modes/documentation.md defines top/bottom order, player
scope/FROM state, and RGB/alpha temp values. Installed modifiers documentation
states numbers support up to three decimals. The existing culture calculation
also includes a gray seed in every average, unlike the painter; verify intended
averages and retain a gray fallback for uncultured states.

Implementation/static/UI milestones complete. The in-game Altarian white symptom
remains unconfirmed after repair; see ../demographic_map_colors/README.md.

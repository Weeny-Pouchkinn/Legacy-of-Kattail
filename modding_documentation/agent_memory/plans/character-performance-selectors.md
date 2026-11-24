# Character performance and searchable selectors — 2026-11-24

- [x] Inspect current cache/edit/gallery and all selection controls; profile real data without writing game sources.
- [x] Cache file inventories, parsed files and derived catalogs by relevant draft changes; avoid redundant identity and localisation work.
- [x] Add shared searchable selectors, localized-name (ID) labels, dual-name matching, typo suggestions and alphabetic ordering throughout the painter.
- [x] Exercise real-data timings and Tk typing/selection/save/undo/cancel; run fixtures/compiler/diff checks and update memory.

Preserve all native IDs, source strings, portraits, map data and existing external edits. No subagents. No in-game validation claimed.

Completed: 51 regression tests, original character migration audit, read-only
real-data source/map/flag checks and native Tk interactions pass. All 10,863
verified native source hashes remain unchanged. Four pre-existing OOB syntax
errors remain. No game/source assets written by the optimization or benchmarks.

Profiled identity apply 53.463 -> 0.519 s; save preparation 29.209 -> 0.199 s.
Actual Tk military stats apply 0.0256 s, refresh 0.0338 s; warm character/role
dialogs 0.1904/0.1312 s. First role open 1.0783 s includes native name loading.
Before/after profiler overhead is included and timings vary by machine/load.
Benchmark source uses an actual military role; the initial synthetic role-zero
timing is not claimed as an in-game valid military-role comparison.

Exact changed files relative to the mod root:

- legacy_of_kattail_painter/model.py
- legacy_of_kattail_painter/character_model.py
- legacy_of_kattail_painter/character_ui.py
- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/install.py
- legacy_of_kattail_painter/select_ui.py
- legacy_of_kattail_painter/test_selectors.py
- legacy_of_kattail_painter/benchmark_characters.py
- legacy_of_kattail_painter/README.md
- legacy_of_kattail_painter/MODLOG.md
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md
- modding_documentation/agent_memory/plans/character-performance-selectors.md

New Python identifiers: Choice, ChoiceIndex, ChoiceBox, TraitChoices, matching_base,
inherited_localisations and benchmark. Game IDs/localisation unchanged. Commands
and detailed results are recorded in legacy_of_kattail_painter/MODLOG.md.

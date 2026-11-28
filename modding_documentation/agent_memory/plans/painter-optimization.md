# Painter optimization - 2026-11-27

- [x] Read current memory and inspect painting/rendering, caches, selectors and
  icon/bonus catalogs. Preserve current user changes to Imperium/state/loc data.
- [x] Establish repeatable native-data timings/profiles for painting, map frames,
  spirit/icon/bonus selection and broader UI/read/refresh workloads; no Save.
- [x] Optimize measured repeated work with dependency-aware invalidation and
  bounded caches, keeping Undo/Redo/Cancel/Save and imported assets correct.
- [x] Exercise changed paths/regressions and compare the same native workloads.
- [x] Full tests/compile/diff review; document actual speedups and remaining costs.

No geopolitical, map, existing spirit/asset or localisation content changes.
Benchmarks operate in drafts and close their own windows; never save native data.
Do not weaken external-change detection to improve timings.

Completed: 258 tests, compile on 11 Python files, 58-file manifest and map check
pass. Native benchmark: mean paint .605 -> .046 s, search .394 -> .007 s, first
catalog 10.64 -> 5.47 s profiled; final unprofiled 29-38 ms strokes, 5 ms search,
3.55 s first catalog. Same 4429 icons, no source writes. Full report/timing
caveats: ../painter_optimization.md. New user request adds a Land OOB editor;
continue that task after recording this completed milestone.

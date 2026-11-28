# Painter optimization - 2026-11-27

## Completed changes

- State/region parsing is reused from initial World loading. State-boundary
  synchronization reparses only changed source files while still validating
  unique IDs/membership, land, topology and current ownership. Geography avoids
  duplicating the boundary store's validation and owner/name updates.
- Imperium element definitions depend on their own source/localisation rather
  than every unrelated document revision. Assignment extraction is incremental
  per state, retaining Undo/Redo/Cancel and strict value checks.
- EaW enumeration uses scandir metadata and resolves directories rather than
  every asset/root repeatedly. Escaping directory links and symlink files are
  skipped. Texture dimensions use fixed DDS/TGA headers, with Pillow fallback
  for other formats; minister filtering and custom-icon exceptions remain.
- Native sprite lookup can request only GFX_idea_ entries, skipping unrelated
  file parsing. General sprite callers retain the full registry.
- Thumbnail previews use a 256-entry LRU, including image bytes, texture,
  frame count, size and game root in dependencies. Native image bytes are read
  only on cache miss; imported mod overrides and Undo switch correctly.
- Icon search indexes survive query changes and rebuild for source filters or
  catalog changes. Typing debounces at 80 ms; visible thumbnails stay lazy.
- Shared selector normalization uses a bounded 32768-entry cache. Fuzzy search
  prunes only with SequenceMatcher upper bounds below the existing 0.45 cutoff,
  retaining the same results/ranking and Unicode resolution.
- Equipment/research bonus catalogs reuse unchanged installed-game source text
  across selections, while mod overrides/replace_path/Undo remain live.
- Cache signatures retain real dependencies instead of relying on disposable
  object IDs for element/asset catalogs; a new regression caught a stale-label
  case after a localisation edit and now passes.

No native content was modified by this task. User state/Imperium/localisation
edits were already present and continued during profiling; preserve all of them.
Save conflict checks, backup behavior and source formatting remain unchanged.

## Timings

Commands: `python -B legacy_of_kattail_painter/benchmark_painter.py --profile`
before/after. Both catalog runs contain 4429 selectable icons. Seconds below:

| Workload | Before | After |
| --- | ---: | ---: |
| World load | 4.239046 | 4.293655 |
| Painter initialization after World | 3.498774 | 1.942880 |
| Imperium stroke 1 | .615280 | .049865 |
| Imperium stroke 2 | .602207 | .044003 |
| Imperium stroke 3 | .598322 | .043007 |
| Warm map frame | .019389 | .020294 |
| First idea catalog in process | 10.640864 | 5.470211 |
| Warm catalog lookup | .000069 | .000061 |
| Picker open after catalog | .438793 | .266810 |
| Idea search | .393551 | .007194 |
| New spirit editor | 1.182375 | .770261 |
| UI sync after Cancel | 1.142773 | .474533 |

Mean Imperium stroke .605270 -> .045625 (about 13x faster), search about 55x,
first catalog about 2x. Whole profiled workload calls 52.69 million -> 27.92
million. World load and already-fast warm frames did not materially improve.

An additional non-profiled final run reported World 2.639935 s, painter
initialization 1.349749 s, strokes .037936/.036633/.029373 s, map frame .016004 s,
first catalog 3.546597 s, picker .112050 s, search .005388 s, new spirit .331466 s
and Cancel sync .246197 s. This final run checked 3042 source snapshots, observed
zero external changes and performed zero source writes.

Timings are local examples, not latency guarantees. The first exploratory scan
was 25.66 s with colder OS caches; ratios use the second baseline above. User
editing changed 51 observed sources during that baseline, so the native state
inputs are not byte-identical across runs. No checks competed for CPU during
the final recorded benchmark. An earlier intermediate after-run overlapped
tests and is deliberately excluded from these comparisons.

## Files and identifiers

- legacy_of_kattail_painter/character_model.py
- legacy_of_kattail_painter/country_model.py
- legacy_of_kattail_painter/country_ui.py
- legacy_of_kattail_painter/geography_model.py
- legacy_of_kattail_painter/imperium_model.py
- legacy_of_kattail_painter/install.py
- legacy_of_kattail_painter/model.py
- legacy_of_kattail_painter/select_ui.py
- legacy_of_kattail_painter/state_boundary_model.py
- legacy_of_kattail_painter/benchmark_painter.py (new)
- legacy_of_kattail_painter/test_performance.py (new)
- legacy_of_kattail_painter/README.md
- modding_documentation/agent_memory/plans/painter-optimization.md (new)
- modding_documentation/agent_memory/painter_optimization.md (this report)
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md

Python additions: asset_files, image_dimensions, _normalized, benchmark_painter.
inherited_sprites accepts an optional prefix; old callers remain compatible.
No native script IDs, effects, flags, localisation keys or asset paths changed.

## Validation and remaining limits

- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_performance.py -v`:
  9 new tests pass, including parse reuse without bypassing membership checks,
  localization/Undo invalidation, header dimensions, minister filtering, native
  thumbnail read/decode reuse and mod override/Undo, bounded LRU, prefix/full
  sprite equivalence, bonus override/Undo, exact fuzzy results and real picker
  filter/search/Cancel timer cleanup.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  all 258 tests pass, including prior country/diplomacy/boundary/import suites.
- `python -m py_compile` on all eleven changed/new Python files passes with
  PYTHONPYCACHEPREFIX redirected to a disposable temporary directory. No tracked
  bytecode changes. All 58 installer manifest files exist.
- Profiled and non-profiled native Tk benchmarks pass, close their own windows
  and never call Save; current input has 4429 selectable icons.
- `python -B tools/validate_map.py` passes (21515 provinces, 20926 assigned,
  413 regions, no X crossings). No binary map assets changed.
- `git diff --check`, scoped `git diff --stat`, complete relevant code diff and
  new-file whitespace/source review performed. Do not include or revert the
  unrelated live user data changes in this optimization patch.

The first asset enumeration still performs filesystem work (3.55 s in the final
unprofiled example); subsequent catalog lookups/searches are cached. Installed
game databases are session snapshots, consistent with existing sprite/loc caches:
restart after changing installed vanilla files or adding external assets. Normal
in-painter imports and edits invalidate correctly. Save current progress and
restart the painter to use these code changes. No engine launch was needed or
performed for this UI optimization.

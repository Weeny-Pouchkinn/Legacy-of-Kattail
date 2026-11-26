# Painter script formatting audit and repair - 2026-11-26

Implemented native tab indentation for generated/edited script and repaired
proven historical painter output. No identifiers, values, operators, statement
order, quoted strings or comment text changed in the 180-file repair.

## Sources and behavior

The screenshot examples are repaired in
[common/ideas/lok_misc_ideas.txt](../../../common/ideas/lok_misc_ideas.txt), including
`KTN_Never_Invaded`, `MCF_The_Loose_Realms` and `MCF_Grand_Airforce`.
Each object now has separate picture/allowed/removal/modifier lines; research and
equipment blocks use the same nesting depth as nearby handwritten objects.
Identifiers, equipment targets and values are retained exactly.

Root causes: compact generator templates and the shared missing-field writer's
one-tab fallback when a parent started in the middle of a line. The latter now
uses parsed brace depth. New shared layout uses one tab per actual syntax level,
expands complex definitions/bodies, retains short inline parameter blocks and
wraps long atom lists. Comments and blank separation are retained within edited
containers; exact physical whitespace inside those containers can change.

The [writer inventory](writer_inventory.json) audits 41 painter Python files,
including verification/tests, and identifies all detected write calls and direct
CLI boundaries. Runtime writer families include states/demographics, countries,
characters/portraits/traits/spirits, geography/climate and Imperium definitions.
All shared Documents Save operations are covered, including staged script bytes.
Direct state migration, character refactor and Koppen reapply format before audit
hashes/output collection. Character verification compares script tokens rather
than raw layout. The installer includes the formatter and regressions.

Formatting deliberately runs at final Save/CLI boundaries, after span-based
primitive edits: formatting earlier would invalidate their AST offsets. Only
changed containers are selected, expanding inline ancestors when necessary.
Unedited handwritten neighbors are excluded. Lexer tokens including comments
must match exactly; the result must parse. Safe native writes still use the
existing conflict guards/backups. Non-Clausewitz formats (railway/supply/building
line records, CSV, Lua, JSON, localisation, bitmaps and images) retain their own
writers; these do not share Clausewitz brace indentation rules.

## Existing-output repair

`tools/format_painter_output.py` defaults to dry-run. It identifies edited scopes
from exact before/after SHA-256 witnesses in 63 native Save manifests, rather than
formatting the repository wholesale. There are 3,307 structured records; 3,269
resolve across 1,869 files. The remaining 38 records cannot establish both byte
witnesses and are excluded from scope ownership. Other proven records for the
same file remain usable. Deleted/renamed historical addresses are skipped.
No current-source parse failures or unsupported-source skips occurred.

The guarded repair changed **180 files**:

| Family | Files |
| --- | ---: |
| State history | 166 |
| Characters | 3 |
| Country colors | 1 |
| Leader traits | 1 |
| Ideas | 1 |
| Map modes | 2 |
| On-actions | 1 |
| Scripted localisation | 2 |
| Scripted triggers | 1 |
| Portrait sprites | 1 |
| Portrait pools | 1 |

Each repair independently checks exact token/comment equality and ordered parsed
structure, preserves encoding/BOM, and retains the existing newline family.
Sources must still match the read hashes before any native write. Exact backup
bytes and before/after hashes are retained under:

`legacy_of_kattail_painter/backups/painter_script_formatting_20261126_172635_615366`

See [repair.json](repair.json) for all 180 paths/hashes and provenance counters,
[dry_run.json](dry_run.json) for the preview and
[post_repair_check.json](post_repair_check.json) for the second dry run, which
proposes **zero further changes**. Previous repair backups are only byte witnesses
for original Save records, never additional ownership authorization.

## Files changed

Implementation, integration and regression files:

- `legacy_of_kattail_painter/script_format.py`
- `legacy_of_kattail_painter/model.py`
- `legacy_of_kattail_painter/character_model.py`
- `legacy_of_kattail_painter/migrate_state_setup.py`
- `legacy_of_kattail_painter/refactor_characters.py`
- `legacy_of_kattail_painter/verify_characters.py`
- `legacy_of_kattail_painter/install.py`
- `legacy_of_kattail_painter/test_script_format.py`
- `legacy_of_kattail_painter/test_spirit_bonuses.py`
- `tools/format_painter_output.py`
- `tools/reapply_koppen_latitude.py`

The complete exact list, including all 180 native files and documentation, is
[files_changed.txt](files_changed.txt). Unrelated existing working-tree changes
were preserved. No public identifiers, localisation keys, namespaces, flags,
variables or sprites were added, removed or renamed by this task.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **211 passed**. Seven new formatter regressions cover screenshot layout,
  comments/quoted syntax/operators/duplicates, unchanged neighbors, missing-field
  depth, list wrapping, Save integration/BOM/CRLF and excluded formats. Existing
  demographic no-op repaint and spirit bonus preservation regressions also pass.
- Python `py_compile.compile(..., doraise=True)` for the 11 implementation/test/
  tool files listed above: **passed**, cache output directed to temporary files.
- `python -B tools/validate_map.py`, before and after repair: **passed**;
  21,515 provinces, 20,926 state-assigned, 413 strategic regions, no X crossings.
- Native Tk existing `MCF_Grand_Airforce` edit and temporary new-spirit Apply,
  final-boundary formatting, exact draft token checks and Undo: **passed**.
  Production Save forbidden; no callback errors; 4,325 native source hashes
  unchanged by the probe. Details: [verification.json](verification.json).
- `python -B tools/format_painter_output.py --apply`: **180 guarded writes**;
  exact post-write readback, token/comment/structure/BOM checks passed.
- `python -B tools/format_painter_output.py --report
  modding_documentation/agent_memory/painter_script_formatting/post_repair_check.json`:
  **0 changes**.
- Full native repair diff and implementation diff reviewed; scoped
  `git -c core.fsmonitor=false diff --check -- <implementation/docs/native paths
  except portraits/LOK_portraits.txt>` passes. Global `git diff --check` reports
  **933 inherited carriage-return warnings in portraits/LOK_portraits.txt**.
  Untouched source contains CRCRLF; 440 malformed double-CR sequences inside
  proven edited scopes were fixed. Remaining untouched portrait areas were
  deliberately not normalized. No other whitespace-check failures remain.

No game launch or CWTools execution was performed. Structural/token proof covers
this whitespace-only repair, not unrelated existing gameplay behavior. Some old
unproven painter output may remain; the report lists the unresolved sources.
Restart the painter to load the updated Save formatter.

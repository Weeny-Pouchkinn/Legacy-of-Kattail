# Painter-generated script formatting audit - 2026-11-26

- [x] Read current instructions/memory and compare screenshot ideas with nearby
  human style; identify shared patch_field indentation fallback and compact
  generator templates as root causes. Preserve all current user edits.
- [x] Inventory all painter source writers and native save-backup provenance.
- [x] Add token/comment-preserving, depth-aware script formatting for changed
  structured blocks; integrate at final Save/CLI boundaries and field insertion.
- [x] Verify new/edited output across every writer family with focused and full
  tests; profile large edits and avoid modifying unrelated handwritten blocks.
- [x] Dry-run provenance-based repair of existing painter output, inspect native
  examples/diff, apply guarded backups and verify token/AST equivalence/encoding.
- [x] Run required validators and update memory/report with exact sources,
  paths, counts, tests and remaining uncertainty.

User explicitly authorizes formatting painter-generated content, including
existing output. Tabs reflect actual syntax nesting. Expand complex definitions
and nested bodies; retain readable native small inline parameter/list blocks.
Never change identifiers, values, operators, order, quoted strings or comments.
Use backup provenance to select prior output, not a repository-wide reformatter.

Completed: 211 tests; 11 Python compile checks; map validation before/after;
native spirit UI probe; 180 guarded repairs; second dry run zero changes.
38 unresolved provenance records excluded; inherited portrait CR warnings remain.
Exact evidence and files: ../painter_script_formatting/README.md.

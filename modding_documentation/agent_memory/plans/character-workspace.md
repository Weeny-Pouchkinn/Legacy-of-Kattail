# Character and portrait workspace — 2026-11-24

Requested: MAP and CHARACTERS top-level tabs; full-width, localised-name-sorted
character gallery with nation/unrecruited grouping; character/role/recruitment/
traits/stat editing; independent tagged large/small portrait pairs; description
and art credits; dynamically grouped character localisation and portrait GFX;
move portrait assets into leaders/large_portraits and leaders/small_portraits.

- [x] Read project rules/memory, native character documentation, nearby role,
  recruitment, localisation, GFX and EU4 metadata examples; inspect data hazards.
- [x] Extend guarded drafts/saves to coordinated text, new files, binary assets
  and moves; keep all existing map features and undo/redo behavior.
- [x] Implement native character/role/recruitment models, portrait registry and
  deterministic localisation/GFX grouping without losing authored strings.
- [x] Implement top-level workspace, character gallery/dialog and independent
  portrait library/dialog, including optional pair creation during character edit.
- [x] Dry-run/refactor current localisation and portrait assets; inspect complete
  path/reference/value changes; apply reviewed migration with backups.
- [x] Run fixtures, compiler/localisation checks, real-data Tk/save/reload and
  full-diff checks; update durable status/decisions and exact changed paths.

Baseline: clean tree at `5b1dc2ee` (includes the EU4/ZZZ country import).
Preserve repeated roles, conditional/dated history, country membership, animated
sprites, generic portraits, source encodings/BOM and existing public IDs. Keep
description and art-source metadata separate from engine-unsupported fields.
Live wiki read failed; installed common/characters/_documentation.md and native
effects_documentation.md establish the character database/recruitment syntax.

Completed on Painter-Test (branch changed externally during work). No branch
switch or commit made. See character-refactor-audit.json for all 2,869 source
paths and hashes; character-workspace-files.txt includes the implementation/docs.
All 1,408 moved original assets match their original hashes, all 51,295 English
values are preserved, and all 284 identities/recruitments/roles are unchanged.
42 newly derived small images use the supplied Ministermaker main script's
37x51 / 5 degrees / 65x67 / border at (8,1) algorithm; exact pixel parity passed.
Two existing small artworks were reused. Initial thumbnail overwrite of those
two originals was detected by hash checking, restored from backups and covered
by a regression test; no original artwork remains replaced.
42 fixture tests and native hidden-Tk gallery/generator/Save/reload checks pass.
No game launch or screenshot validation. Five generic source textures and ten
character sprite references remain unresolved in available indexes, pre-existing.
Concurrent state-history/importer/validator work was preserved separately.

# Flat EaW runtime icon paths - 2026-11-27

- [x] Verify current writer/provenance/credits and existing saves. One imported
  texture and one sprite reference use a hash/CTL hierarchy. Source library has
  no duplicate filenames. User explicitly supersedes the old hash-path decision.
- [x] Change imports to eaw/<filename>; preserve existing different art with a
  readable _2 suffix only if needed. Keep original EaW credit paths and badges.
- [x] Add guarded dry-run migration of native textures, active literal references
  and credit destination paths; remove only superseded files/empty directories.
- [x] Test Save/reload, missing library, collisions, migration proof/idempotence,
  exact image bytes and rollback; apply migration, inspect complete diff.
- [x] Run focused/full tests and compile checks, update current memory/report.

Keep sprite IDs, spirit values, original source art and original EaW credit
paths unchanged. Do not edit old backups or historical reports as game sources.

Additional user request: import own national-spirit icons. Added Import icon
actions in spirit form and gallery; fit to transparent 60x68 DDS under the flat
custom/ directory, preserve aspect/source and support draft/Undo/Cancel/Save.

Completed: two saved textures migrated (the second was saved while work was in
progress), six native file operations, guarded backup, second pass zero changes;
230 tests, six compiles, native UI import/Cancel with 4,226 unchanged hashes.
Details: ../eaw_flat_paths/README.md. No game launch.

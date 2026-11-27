# EaW national-spirit asset library - 2026-11-27

- [x] Inspect native catalogs, picker, draft/save/import patterns, instructions,
  and the supplied EaW folder/badge. User authorizes asset use.
- [x] Add recursive DDS/TGA catalog, safe native imports, origin preservation
  and existing minister-portrait exclusions.
- [x] Add source filter checkboxes and a separate UI-only lower-left sun badge;
  ship the badge and library with painter installs.
- [x] Exercise imports, duplicate names, filter combinations, badge isolation,
  Undo/Cancel/Save/reload and missing-source handling in fixtures/native catalog.
- [x] Compile changed Python, run regression suite/diff checks, inspect UI,
  update durable memory and report actual validation/limitations.

Never bake the attribution mark into imported game textures. Copy only selected
assets into a native gfx path as part of the normal guarded draft/save operation.
Preserve unrelated working-tree changes and keep the user's source art intact.

Credits requirement added: append asset filename, original EaW path with
eaw_ideas replaced by gfx\interface\ideas, national spirit ID/name and native
texture path to credits/EaW Credits.txt as part of the atomic Apply/Save draft.

Completed: 217 tests, four compile checks, 3,398 image decodes, actual-data Tk
probe with 4,226 unchanged native hashes, exact badge copy and diff review.
No engine launch. Detailed evidence: ../eaw_spirit_assets/README.md.

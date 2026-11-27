# Flat EaW paths and own national-spirit icon import - 2026-11-27

Replaced hash/source-folder runtime paths with readable flat filenames, migrated
existing saves and added own-image imports in both spirit selection interfaces.

## Files and behavior

- [country_model.py](../../../legacy_of_kattail_painter/country_model.py): shared
  flat filename allocation, credit provenance lookup, flattened EaW imports and
  own-image conversion/registration.
- [country_ui.py](../../../legacy_of_kattail_painter/country_ui.py): Import icon
  buttons in SpiritDialog and IconPicker; file chooser, preview selection and
  automatic Mod filter activation.
- [install.py](../../../legacy_of_kattail_painter/install.py): includes the new
  own-import regression module.
- [test_eaw_icons.py](../../../legacy_of_kattail_painter/test_eaw_icons.py): updated
  flat-path expectations plus collision, provenance and migration regressions.
- [test_spirit_icon_import.py](../../../legacy_of_kattail_painter/test_spirit_icon_import.py):
  source fitting/transparency, reuse/conflicts, validation and Tk transaction tests.
- [tools/flatten_eaw_icons.py](../../../tools/flatten_eaw_icons.py): reusable
  dry-run/guarded migration, exact path-literal rewrite and empty-folder cleanup.
- [interface/lok_ideas.gfx](../../../interface/lok_ideas.gfx): two native texture
  references updated; sprite names/other fields retain their existing tokens.
- `legacy_of_kattail_painter/credits/EaW Credits.txt`: only Mod texture destination
  paths updated; original EaW paths, asset names, uses and other text retained.
- Runtime texture creations/deletions are listed exactly below and in
  [repair.json](repair.json).
- Painter README/MODLOG, agent CURRENT_STATUS/DECISIONS,
  [original report notice](../eaw_spirit_assets/README.md),
  [plan](../plans/eaw-flat-paths.md), this report and JSON records document the change.

EaW now saves to `gfx/interface/ideas/eaw/<filename>`. Identical bytes reuse an
existing destination; different art gets a readable `_2`, `_3`, etc. suffix.
There are no hash or country subdirectories in these new paths. Original catalog
IDs stay source-relative. Per-texture/per-spirit source records in the existing
credits file retain provenance after flattening/reload, including when the library
is unavailable. Unique library filenames can supply fallback provenance. Unknown
provenance is not invented; assigned icons remain editable, while a new use with
unknown origin requests the original library asset. Badges/source filters remain.

Both the spirit form and browser have **Import iconâ€¦**. PNG/JPEG/DDS/TGA/BMP/WebP
images fit without stretching on a transparent 60Ã—68 canvas and save as DDS under
`gfx/interface/ideas/custom/<readable name>.dds`. Source art is unchanged. Sanitized
source names and readable collision suffixes are used. Reusable source sprites
follow `GFX_idea_lok_custom_icon_<stem>`; actual spirits retain `GFX_idea_<ID>`.
Own imports are Mod assets and deliberately selectable even if the source name
resembles a portrait. No EaW badge/credit is attached to own art. Selecting a known EaW library
file through the file chooser retains its EaW identity and credits instead. The gallery activates
Mod automatically and selects the imported icon; both interfaces preview it.
Imported files, registrations and spirit changes share grouped Undo/Redo,
Cancel/outer Cancel, Save conflict guards and backups. No custom icon or spirit
was seeded into production by the validation probes.

## Existing-save audit and repair

The initial preview found one saved import; another was saved while work was in
progress. Apply rebuilt the audit from current files and migrated both:

| Previous path under eaw/ | Flat destination under eaw/ |
| --- | --- |
| `f49d6ff75f994b32/CTL/CTL_axes.tga` | `CTL_axes.tga` |
| `50e397cea2f12273/ZAR/deserttribes.dds` | `deserttribes.dds` |

Active path literals were searched across common, history, events, interface,
portraits, map and localisation text files. Only mapped literal values change;
comments and all other tokens remain. Credit updates target Mod texture lines,
leaving the original `gfx\interface\ideas\CTL\â€¦` / `ZAR\â€¦` source paths intact.
Nested references without a native source are rejected before writing.

The six native file operations are: create the two flat textures; update the one
GFX file and credits; delete the two obsolete nested textures. New files are exact
copies of old bytes, proven by SHA-256. Both old files and edited text are backed
up under:

`legacy_of_kattail_painter/backups/eaw_flat_paths_20261127_174759_248434`

Copies/reference edits precede deletions. The normal guarded writer validates
all original bytes, makes backups and rolls back on failure. Only empty nested
directories inside the native eaw folder are removed with nonrecursive rmdir;
source library, historical backups and unrelated files are untouched. Existing
spirit/sprite IDs and gameplay values are unchanged. Second audit: zero changes.

## Validation actually performed

- `python -B tools/flatten_eaw_icons.py --help`: inspected actual interface.
- `python -B tools/flatten_eaw_icons.py --report
  modding_documentation/agent_memory/eaw_flat_paths/dry_run.json`: initial preview.
- `python -B tools/flatten_eaw_icons.py --apply`: two images migrated, six guarded
  file operations, exact readback and empty-folder cleanup.
- `python -B tools/flatten_eaw_icons.py --report
  modding_documentation/agent_memory/eaw_flat_paths/post_repair_check.json`:
  zero changes; no remaining nested live EaW references.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_eaw_icons.py`:
  eight tests passed. Covers flat imports, readable collisions, same-art reuse,
  credits/BOM/original source paths, provenance without source library, Save/reload,
  migration literal/comment preservation, conflicting concurrent writes, missing
  legacy textures, old-file/folder removal and idempotence, plus attribution UI.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_spirit_icon_import.py`:
  three tests passed. Covers source bytes, fitting/transparent margins, own-image
  portrait names, collision preservation, same-image reuse, corrupt-image rollback,
  both Tk import buttons, cancelled file picker/dialog, filter activation, preview,
  Apply/Undo/Redo/Save/reload and exclusion from EaW credits.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **230 tests passed** in 43.379 seconds.
- `py_compile.compile(..., doraise=True)` for all six modified/new Python files:
  passed, caches written into a temporary directory.
- Native existing CAT_Drakwald_Logging dialog and gallery: flat EaW reload/preview/
  original source lookup, own icon Import in both interfaces, Mod filter activation,
  preview and Cancel passed. Production Save forbidden, no callbacks, **4,226 native
  source hashes unchanged**. [verification.json](verification.json).
- Migration images, edited native text and backup hashes rechecked; original source
  art and EaW credit paths retained. Global `git diff --check`, `git diff --stat`,
  implementation diff review, report links and installer references passed.

No game launch/CWTools execution was performed. Native runtime image paths are
validated by files/sprite definitions and unchanged bytes; own-image rendering
is tested in the painter and Save/reload fixtures. Restart the running painter
before saving further imports so it uses the new path logic.

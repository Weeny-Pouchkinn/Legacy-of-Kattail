# EaW national-spirit assets and credits - 2026-11-27

Update 2026-11-27: the hash/source-subfolder runtime layout described below is
superseded by flat `eaw/<filename>` paths. Existing imports have been migrated;
see [current path and own-import report](../eaw_flat_paths/README.md). This report
retains the original implementation evidence; original EaW credit paths remain.

Implemented the user-authorized EaW library, source filters, supplied sun badge
and per-use credits. No live spirit was assigned or changed by this task.

## Files changed

- [country_model.py](../../../legacy_of_kattail_painter/country_model.py): external
  catalog, native import, preserved origin/source identity and credit staging.
- [country_ui.py](../../../legacy_of_kattail_painter/country_ui.py): source
  checkboxes, synchronized dropdown and UI-only badge previews.
- [install.py](../../../legacy_of_kattail_painter/install.py): installs badge,
  regression module, supplied asset hierarchy and credits hierarchy.
- [test_eaw_icons.py](../../../legacy_of_kattail_painter/test_eaw_icons.py): five
  integration regressions covering the import/UI/credits/install paths.
- [assets/eaw_sun.png](../../../legacy_of_kattail_painter/assets/eaw_sun.png): exact
  copy of the user's C:/Users/elowi/Downloads/eaw sun.png, visually inspected.
- [credits/EaW Credits.txt](../../../legacy_of_kattail_painter/credits/EaW%20Credits.txt):
  initial header only; actual uses are added on Apply and written by Save.
- [README.md](../../../legacy_of_kattail_painter/README.md),
  [MODLOG.md](../../../legacy_of_kattail_painter/MODLOG.md),
  [CURRENT_STATUS.md](../CURRENT_STATUS.md), [DECISIONS.md](../DECISIONS.md),
  [plan](../plans/eaw-spirit-assets.md), this report and the two JSON validation
  records document behavior and actual checks.

The user-supplied assets/eaw_ideas tree already existed and was not modified.
Its 3,403 files comprise 3,398 DDS/TGA images and five PSD working files. Existing
unrelated AI changes and earlier minister-filter edits were preserved.

## Behavior and identifiers

`CountryStore.eaw_icon_catalog` scans the supplied library recursively, once per
store/session. Restart after adding files. Catalog IDs use `eaw:<relative path>`;
duplicate basenames in different folders stay distinct. Common minister exclusion
rules apply. Combined native catalog: 7,015 registered entries; 4,420 selectable,
of which 2,219 are EaW. The 1,179 excluded EaW entries match the current portrait
path/name/dimension rules. Five PSD files are not game textures and are ignored.

`IconPicker` offers Mod / Vanilla / EaW checkboxes. Search and filters combine,
including an empty selection; choices are remembered for the session and copied
back to the spirit dropdown. Existing icons still load and Apply regardless of
the currently visible sources. The supplied 16-pixel sun appears in a separate
left margin, aligned to the bottom of the UI preview; the icon itself starts to
its right, without overlapping the badge. Both gallery and spirit preview use
this UI presentation. `icon_image` remains an undecorated source thumbnail.

Apply copies the selected DDS/TGA bytes unchanged into:

`gfx/interface/ideas/eaw/<first 16 SHA-256 digits>/<original relative path>`

The content directory prevents different art versions from overwriting previous
uses; an existing differing target fails safely. The original subpath preserves
source identity. The normal `GFX_idea_<spirit ID>` sprite points to this native
copy, with the existing picture convention. Reloaded sprites in this import
namespace retain EaW origin and original source path. No new fixed public game
IDs, localisation keys, flags or namespaces are seeded; actual uses create the
existing dynamic spirit/sprite/localisation IDs the user supplies.

Constants added: `EAW_IDEAS`, `EAW_TEXTURES`, `EAW_CREDITS` in country_model.py.
These are relative repository paths, not machine-specific absolute paths.

## Credit records and transaction boundaries

`legacy_of_kattail_painter/credits/EaW Credits.txt` records, for example:

```text
Asset: royal_guard.dds
EaW path: gfx\interface\ideas\EQS\royal_guard.dds
Used for: National spirit AAA_eaw (Guard spirit)
Mod texture: gfx/interface/ideas/eaw/<hash>/EQS/royal_guard.dds
```

This example is from a disposable regression fixture, not an invented live use.
The original `eaw_ideas` prefix is replaced by `gfx\interface\ideas`, as requested.
Applying a spirit records its actual ID/name; merely browsing or selecting and
cancelling does not leave credits. Entries are staged with the asset, sprite,
idea and localisation as one grouped edit. Undo/Redo and enclosing Cancel include
all of them. Save uses the normal conflict guards and byte-exact backups. Plain
credit prose is staged as encoded bytes so it is not parsed as Clausewitz script.
Existing human notes, BOM and newline family are retained. Identical repeated
asset/use/destination records are deduplicated; other uses append records.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_eaw_icons.py`:
  all five integration tests passed. Covers recursive paths, DDS/TGA/PSD filtering,
  duplicate basenames, portrait exclusions, exact imported bytes, source paths,
  human credit notes/BOM, Undo/Redo, Save/reload, repeated/shared uses, missing
  sources, conflicting destinations, source checkboxes/search, UI badge pixels,
  original thumbnail pixels, nested Cancel and installer preservation.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **217 tests passed** in 37.773 seconds.
- `py_compile.compile(..., doraise=True)` for country_model.py, country_ui.py,
  install.py and test_eaw_icons.py, with temporary cache destinations: passed.
- Pillow full image decoding of every supplied DDS/TGA: **3,398 passed, zero
  failures**. Size inventory and badge hash: [asset_validation.json](asset_validation.json).
- Actual native World/CharacterStore/CountryStore + mapped Tk existing
  MCF_Grand_Airforce / gallery source-filter/search/EaW select/preview/Cancel:
  passed, production Save forbidden, zero callback errors, **4,226 native source
  hashes unchanged**. Details: [verification.json](verification.json).
- Visually inspected the supplied logo and actual Airframe_Blueprint preview:
  the sun occupies its own lower-left margin; source/game art is separate.
- `git -c core.fsmonitor=false diff --check`, `git diff --stat` and implementation
  diff review: passed. New documentation links/paths and installer file references
  checked. No unrelated working-tree edits were reverted.

No game launch or CWTools execution was performed. Native import/Save/reload and
credits were tested in disposable fixtures; native UI exploration performed no
production Apply/Save. The library supplies image files rather than animation
sprite definitions, so new raw imports use one frame; existing registered sprites
keep their native frame handling. Portrait classification retains its documented
path/name/exact-size heuristic. Source filters are session preferences, not
persistent configuration. Restart the painter to load these changes.

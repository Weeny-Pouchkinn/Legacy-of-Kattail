# National-spirit icon picker - 2026-11-27

Both icon selection controls exclude minister/character portrait art. Existing
spirit icon assignments still load, preview and Apply unchanged. No sprites,
textures, national spirits, public IDs or localisation keys were changed.

## Files and implementation sources

- [country_model.py](../../legacy_of_kattail_painter/country_model.py): new
  `CountryStore.spirit_icon_catalog` filters selection separately from the full
  `icon_catalog` used to load, preview and validate existing assignments.
- [country_ui.py](../../legacy_of_kattail_painter/country_ui.py): `IconPicker.refresh`
  and `SpiritDialog` dropdown use the same filtered catalog.
- [test_countries.py](../../legacy_of_kattail_painter/test_countries.py): new
  `test_spirit_icon_pickers_exclude_minister_images_but_preserve_existing_assignment`.
- [README.md](../../legacy_of_kattail_painter/README.md),
  [MODLOG.md](../../legacy_of_kattail_painter/MODLOG.md),
  [CURRENT_STATUS.md](CURRENT_STATUS.md) and this report document the change.

Selection checks texture paths, rather than only sprite names, because portraits
also register as GFX_idea_* and may have aliases. Normalize slash/case for folder
and name checks. Exclude leaders/ministers/portraits/small_portraits/large_portraits
folders, portrait_/idea_portrait_ and generic-political-advisor filenames, plus
standard SMALL_SIZE/LARGE_SIZE dimensions from
[character_model.py](../../legacy_of_kattail_painter/character_model.py).
[small_portrait.py](../../legacy_of_kattail_painter/small_portrait.py) documents the
65x67 Ministermaker canvas; large imports use 156x210. Read headers only and cache
per texture/draft image version; do not populate native source snapshots with
thousands of image blobs. Draft replacement and Undo refresh eligibility.

Native evidence: interface/lok_ideas.gfx registers KVK Alice Clatz and KTZ Pawllas
small icons using leaders/small_portraits and interface/ministers respectively.
Installed vanilla interface/ideas.gfx registers GFX_idea_hjalmar_schacht using
interface/ideas/idea_hjalmar_schacht.dds, whose header is 65x67. The generic
political advisor images use the same canvas. The real german_advisors spirit is
60x68 and remains selectable: non-square art alone is not a portrait rule.

## Validation

- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_countries.py`:
  33 tests passed before the final per-texture cache improvement.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  all 212 tests passed, including the cache and Tk regression.
- `py_compile.compile(..., doraise=True)` on all three modified Python files,
  output directed into a temporary directory: passed.
- Native World/CharacterStore/CountryStore catalog probe: 3,617 full entries,
  2,201 selectable, 1,416 excluded. Confirmed KVK/KTZ, Hjalmar Schacht and generic
  advisor exclusions; MCF_Grand_Airforce and german_advisors retained. No native
  drafts changed. First cold metadata scan took 14.06 seconds on this machine;
  catalogs and individual texture results are cached for subsequent use.
- Real mapped Tk fixture checks: dropdown/gallery/search omit portraits, existing
  portrait icon loads/previews and Apply retains its assignment, zero callback
  errors, no unexpected sprite writes. Staging a 60x60 replacement makes that
  image selectable; Undo removes it again.
- `git -c core.fsmonitor=false diff --check`, `git diff --stat`, implementation
  diff review: passed. Existing unrelated AI changes are untouched.

Classification uses known paths/names and exact standard portrait dimensions.
Art stored under unrelated names at other dimensions may still appear; conversely
an intentionally custom spirit icon at a standard portrait size is excluded.
This avoids treating every non-square picture or advisor-themed spirit as a
portrait. No game launch was performed; this change affects painter selection
only. Restart the painter to load it.

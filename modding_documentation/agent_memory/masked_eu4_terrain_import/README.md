# Masked EU4 terrain import — 2026-11-25

**Superseded in part (2026-11-25):** this remains the first-import audit/recovery
record. The later refinement replaces its height/normal/color blend and EU4
province-override classification, and adds trees. Current results are documented
in ../terrain_refinement/README.md. Province geometry/graphical import/rivers and
the exact original selection remain as recorded here.

Completed in the public Legacy-of-Kattail DEV workspace. The EU4 source mod was
read-only. No private HOI4 mod was accessed. The separate supply-hub reader fix
was completed in the same work session; see painter MODLOG.md.

## Scope and source

The user supplied C:/Users/elowi/Downloads/mask.bmp: 4096x3072 RGB, 93,809 exact
black pixels, bbox (3212,1718) to (3675,2068), exclusive far edge. Its source hash
and all input hashes are in audit.json. selection.png is an exact binary copy of
the geographic selection, with black selected pixels and white elsewhere.

EU4 source: C:/Users/elowi/Documents/Paradox Interactive/Europa Universalis IV/
mod/LegacyOfKattailEU4. Current source/target rasters are aligned 4096x3072 maps.
The importer explicitly checks dimensions, province colors, native terrain tables,
river palettes and input hashes, and applies an inspected dry run only.

## Changes

| Native file | Change |
| --- | --- |
| map/terrain.bmp | 50,211 graphical terrain pixels; target palette/header retained |
| map/heightmap.bmp | 74,484 elevation pixels; source land heights, shoreline rim retained |
| map/terrain/colormap_rgb_cityemissivemask_a.dds | 19,280 RGB pixels; entire original city-emissivity alpha retained |
| map/world_normal.bmp | 19,262 shading pixels from corresponding EU4 normals |
| map/definition.csv | Terrain column changed for 363 existing provinces |

The exact compatibility mask contains 78,470 shared land pixels. Preserve 11,832
HOI4-water pixels and 3,507 HOI4-land pixels that are EU4 inland water. This avoids
submerging/reclassifying land or altering coastline/province geometry. Neither
province bitmap nor province membership changed. The old central unmasked hole
and all pixels outside the black selection remain unchanged.

Graphical terrain uses explicit EU4-to-HOI4 semantic index mappings, verified
against source map/terrain.txt and target common/terrain/*.txt. Province gameplay
types follow EU4 native terrain_override values, with graphical majority fallback
only where no override exists. Only provinces with at least 50% compatible-mask
coverage are candidates: 517 considered, 363 changed. Ties resolve deterministically
by type name. Changed destinations: 156 mountain, 118 forest, 30 marsh, 28 jungle,
18 desert, 7 plains, 6 hills. Source glacier maps to snowy mountain graphics and
mountain gameplay terrain; woods maps to forest, savannah/steppe to plains.

Copy land elevations with a minimum value of 96, preserving the existing shoreline
rim. Feather height, colormap and normals over at most four full-resolution pixels
inside the compatible mask. The source summer colormap supplies HOI4's single
RGB colormap. Half-resolution texture pixels require all four full-resolution
pixels to be selected, preventing exterior edits. BMP headers/palettes and the
single-mip uncompressed 32-bit BGRA DDS header/compression are retained byte-for-byte.

Rivers already match EU4 exactly inside the selected area, including indices,
start/join markers and background. map/rivers.bmp was checked and left unchanged;
no river was invented, erased, clipped or regenerated.

## Identifiers and protected data

No province, state, country, terrain-category, sprite or localisation IDs were
added or renamed. Only the terrain-name field of the 363 native province rows
changed. IDs, RGB, land/water type, coastal flags, continents, row order and line
endings are unchanged. Province geometry, buildings, supply nodes, railways,
state history and strategic regions were protected by 2,321 file hashes.
map/railways.txt had a user change before this import; it was preserved exactly.

## Files changed for this task

- map/terrain.bmp
- map/heightmap.bmp
- map/world_normal.bmp
- map/terrain/colormap_rgb_cityemissivemask_a.dds
- map/definition.csv
- tools/import_masked_eu4_terrain.py (new)
- tools/test_import_masked_eu4_terrain.py (new)
- modding_documentation/agent_memory/plans/masked-eu4-terrain-import.md (new)
- modding_documentation/agent_memory/masked_eu4_terrain_import/README.md (this file)
- modding_documentation/agent_memory/masked_eu4_terrain_import/audit.json (new)
- modding_documentation/agent_memory/masked_eu4_terrain_import/selection.png (new)
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md

## Validation actually performed

- python -B -m unittest discover -s tools -p test_import_masked_eu4_terrain.py:
  5 passed. Covers indexed/grayscale/RGB native BMP headers/palettes/orientation,
  exact exterior preservation, BGRA DDS/alpha, inward feathering/half-pixel scope,
  majority coverage and native terrain override parsing/conflicts.
- python -m py_compile tools/import_masked_eu4_terrain.py
  tools/test_import_masked_eu4_terrain.py: passed; PYTHONPYCACHEPREFIX in Temp.
- Dry run staged five files with hashes and a side-by-side preview. Inspected
  graphical terrain, elevation and colormap before applying. --apply required the
  same complete input/output hashes as the inspected stage; original bytes were
  backed up by the existing atomic, rollback-capable native writer.
- Post-apply readback: all five file hashes match the stage and all five backup
  hashes match the original inputs. Zero exterior raster pixels changed; colormap
  alpha unchanged globally; only province CSV terrain fields changed. BMP/DDS
  dimensions, headers, native indexed palettes and compression remain unchanged.
- All 2,321 protected files, EU4 inputs, mask and native river bytes are unchanged.
- python -B tools/validate_map.py before and after: the same two existing railway
  jumps remain, now railways.txt:1308 (19461–20841) and :1309 (20839–20841), following
  the user's railway Save. They are not introduced by this terrain import.
- git diff --check, git diff --stat and complete task diff inspected. No unrelated
  changes were made; the user's pre-existing railway edit remains separate.
- The related supply reader patch's full painter suite passed 145 tests; its
  native read-only probe found/rendered all 1,192 authored hubs without modifying
  any of 4,224 checked source files. See painter MODLOG for those exact files.

## Reproduction and recovery

Dry run command (then add --apply only after inspecting the stage):

```powershell
python -B tools/import_masked_eu4_terrain.py --eu4 'C:\Users\elowi\Documents\Paradox Interactive\Europa Universalis IV\mod\LegacyOfKattailEU4' --mask 'C:\Users\elowi\Downloads\mask.bmp' --stage 'legacy_of_kattail_painter\backups\masked-eu4-terrain-import'
```

The completed stage cannot be applied twice. A changed input/output requires a
new dry run. Exact before/after hashes and the retained original-file backup path
are in audit.json. Backup directory:

C:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\legacy_of_kattail_painter\backups\masked_eu4_terrain_20261125_162117_698140

The backup contains only the five map files changed here. Restore only those
files if reverting; do not restore or replace the user's railway edits. Git also
tracks the resulting native map patch. No debug/game logs were modified.

## Uncertainties / remaining verification

No game launch or CWTools check was performed. The static map validator does not
prove in-game visual terrain, elevation seams, river rendering or movement. Next:
restart the painter to load terrain definitions, then load a fresh campaign and
inspect the changed area in game. Existing railway errors remain a separate
known map-data defect. No further terrain conversion work is pending.

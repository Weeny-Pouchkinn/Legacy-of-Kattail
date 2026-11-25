# Masked EU4 terrain import — 2026-11-25

## Authorized scope

Import the black-masked area shown in the current conversation from the active
LegacyOfKattailEU4 mod into the active HOI4 DEV mod. Update graphical terrain,
heightmap, colormap, province terrain definitions and rivers. Preserve province
shapes/IDs/RGB/state membership and all data outside the selected area. Never
access or modify the private HOI4 mod.

## Milestones

- [x] Inspect existing map formats and EU4 source files, earlier alignment evidence.
- [x] Exact mask supplied: C:/Users/elowi/Downloads/mask.bmp, 4096x3072 RGB.
  Black pixels: 93,809; bbox (3212,1718)–(3675,2068), exclusive far edge. SHA256
  434c7c76bd34b3127922162bd80772d300204c3c240b87a08068daa3777270f3.
- [x] Verify source-target alignment against current coastlines/province rasters;
  define explicit EU4-to-HOI4 terrain/index conversion and safe border treatment.
- [x] Stage deterministic edits with a dry run, protected-file hashes and backups;
  inspect a side-by-side preview before applying the authorized import.
- [x] Apply inside the mask, verify formats/palettes and unchanged exterior,
  definitions/province topology and river continuity, run map validator and
  document current-data results and any engine checks not performed.

## Verified preflight facts

- Source: ../Europa Universalis IV/mod/LegacyOfKattailEU4 (active public EU4 mod).
- Both current province maps and source/target terrain/height/river rasters are
  4096x3072. Earlier country import verified identity alignment, with no crop.
  Current masked area: source ocean matches 11,832 target-water pixels. Another
  3,507 pixels are EU4 inland water but HOI4 land; preserve their target land and
  existing assets to avoid changing coastlines/province shapes.
- HOI4 terrain and rivers are indexed P bitmaps, heightmap is 8-bit grayscale.
  Preserve the target palettes; EU4 terrain index meanings differ substantially.
- Target colormap_rgb_cityemissivemask_a.dds is 2048x1536 uncompressed 32-bit BGRA
  with one mip level. Its alpha is city emissivity, so preserve existing alpha.
  EU4 has 2048x1536 master/spring/summer/autumn/winter/water colormaps.
- River palettes are identical. All current non-background river pixels and their
  index values already match EU4 exactly. Only background 254/255 differs globally.
  Determine the actual masked river delta rather than regenerating entire rivers.
- Target world_normal.bmp is a coupled height-shading asset; inspect normal
  conventions before deciding whether local normal changes are required.
- Existing map validator failures before import: two native railway jumps at
  railways.txt now at lines 1308–1309 after a user Save (earlier 893–894).
  map/railways.txt has a user change during this task;
  preserve it and do not attribute it to the terrain import or supply-hub fix.

## Implementation choices

- Preserve all target water and the 3,507 EU4-inland-water/HOI4-land pixels.
- Convert palette indices semantically; use EU4 native province terrain overrides
  for gameplay types. Change only HOI4 provinces with at least 50% mask coverage.
- Copy source height inside compatible land, feathering at most four full-size
  pixels inside the mask; retain original coastal/sea pixels.
- Use the source summer RGB for the single target colormap; preserve target
  city-emissivity alpha. Update coupled world normals from EU4 inside the mask.
- Preserve every exterior pixel and native file header/palette/compression format.
- Rivers have zero differences inside the exact mask and need no rewrite.

Inspected preview and verified staged outputs: 517 majority-covered compatible
provinces considered, 363 terrain changes; graphical terrain 50,211 pixels,
height 74,484 pixels, colormap RGB 19,280 pixels, normals 19,262 pixels. No
exterior pixels or protected CSV fields changed; 2,321 protected hashes verified.
Five format/scope unit tests pass. Applied the inspected hash-guarded stage. Post-apply exterior/alpha/CSV-field
checks passed and all 2,321 protected hashes remain unchanged. Current map
validator has only the same two user-baseline railway jumps at lines 1308–1309.
No game launch. Audit/recovery: ../masked_eu4_terrain_import/README.md.

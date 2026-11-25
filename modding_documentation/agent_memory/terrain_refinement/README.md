# Terrain refinement, province modes and popularity repair - 2026-11-25

## Result

The previous masked import's elevation contrast, four-pixel feather and source
province overrides are superseded by this refinement. Original province shapes,
coastlines, water, graphical terrain and rivers are unchanged by this pass.

Height uses EU4 relief smoothed to the surrounding native scale (gain 0.622101),
harmonic boundary correction and a 48-pixel inward quintic feather. The coastal
rim remains native. Native-style normals are regenerated from final relief;
colormap uses adjacent native biome tones with restrained EU4 texture. The
95th-percentile gradient in the same gentle boundary sample changed from 5.85235
to 1.80278; the original native sample was 2.0 (8-bit height units per map pixel).
This metric and the inspected before/after preview support the blend; neither
proves engine rendering. See preview.png and audit.json.

All 580 land provinces touched by the exact mask were audited against their
complete current graphical terrain, including minority-covered boundary
provinces. Native graphical indices vote for their semantic gameplay terrain;
dominant coverage wins and an existing tied type is retained. 160 additional
definition.csv terrain fields were corrected. Example: province 478 had forest
gameplay terrain despite 182 mountain graphic pixels and no other land type; it
now uses mountain. No IDs/RGB/type/coast/continent/membership fields changed.

Trees now use the existing native 1650x1237 indexed bitmap and models 5 (forest)
and 28 (beech blend, matching neighboring jungle). Only cells whose complete
native map footprint is inside compatible selected land can change. EU4 seeds
are restricted to final woodland graphics; deterministic density fill matches
surroundings. Selected forest cells with trees: 460 -> 2,107; jungle: 0 -> 540.
No trees are placed on nonwoodland graphics by this refinement.

VPs and Railways moved into Provinces subcategories. Existing VP dialogs/labels,
railway set/add/subtract/erase/level count/protection, supply-hub display, overlay,
Undo/Redo and guarded Save remain. Provinces > Terrain adds native gameplay
terrain painting, searchable native colors/names, per-province strokes and
Shift-click picking. Only definition.csv terrain fields are edited by that brush.

Popularity: MAJ, ANS and KHO repaired, plus PAR, SPT and CER with the identical
failure in the user's log. Six-decimal shares total 100 in Python but truncate
below 100 on the native 0.001 grid. The writer and normalization/random helpers
now use largest remainders to produce exactly 100 with at most three decimals.
Random allocation never adds Gestalt; authored positive Gestalt remains manual.
Country Apply reads back the canonical saved values into its pie/fields. Repairs
patch only popularity numeric spans. Detailed original/final shares and backup:
../popularity_precision_repair/audit.json.

## Exact files changed by this refinement/follow-up

- map/heightmap.bmp
- map/world_normal.bmp
- map/terrain/colormap_rgb_cityemissivemask_a.dds
- map/trees.bmp
- map/definition.csv
- history/countries/MAJ.txt
- history/countries/ANS.txt
- history/countries/KHO.txt
- history/countries/PAR.txt
- history/countries/SPT.txt
- history/countries/CER.txt
- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/geography_model.py
- legacy_of_kattail_painter/model.py
- legacy_of_kattail_painter/country_model.py
- legacy_of_kattail_painter/country_ui.py
- legacy_of_kattail_painter/test_geography.py
- legacy_of_kattail_painter/test_railways.py
- legacy_of_kattail_painter/test_countries.py
- legacy_of_kattail_painter/README.md
- legacy_of_kattail_painter/MODLOG.md
- tools/refine_masked_terrain.py
- tools/test_refine_masked_terrain.py
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md
- modding_documentation/agent_memory/plans/terrain-blend-province-modes.md
- modding_documentation/agent_memory/masked_eu4_terrain_import/README.md (superseded note)
- modding_documentation/agent_memory/popularity_precision_repair/audit.json
- modding_documentation/agent_memory/terrain_refinement/README.md
- modding_documentation/agent_memory/terrain_refinement/audit.json
- modding_documentation/agent_memory/terrain_refinement/verification.json
- modding_documentation/agent_memory/terrain_refinement/preview.png

The earlier supply-reader patch and first importer remain in the working tree;
their scopes are recorded separately. The user's map/railways.txt edits were
preserved byte-for-byte, including the existing invalid links.

Identifiers: existing province IDs, terrain categories, ideology IDs and
set_popularities retained. No new native IDs, sprites, localisation or scripts.

## Validation actually performed

- python -B -m unittest discover -s legacy_of_kattail_painter -p test_geography.py:
  36 passed (terrain field-only changes, native colors, Undo/Redo/Save/reload,
  actual province VP/Terrain UI gestures; existing geography coverage retained).
- python -B -m unittest discover -s legacy_of_kattail_painter -p test_railways.py:
  14 passed, including railway mouse gestures under the Provinces category.
- python -B -m unittest discover -s legacy_of_kattail_painter -p test_countries.py:
  30 passed, including fixed-point sum readback, 30 random seeds with no automatic
  Gestalt, manual Gestalt, and exact saved/reopened pie legend percentages.
- python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py':
  148 passed in 26.042 seconds.
- python -B -m unittest discover -s tools -p 'test_*masked*terrain.py': 11 passed.
  Includes six new tests for boundary continuity, harmonic offset, shoreline
  preservation, noninteger tree footprints, whole-province graphical majority,
  deterministic native models/density and woodland-only placement.
- python -m py_compile tools/import_masked_eu4_terrain.py
  tools/test_import_masked_eu4_terrain.py tools/refine_masked_terrain.py
  tools/test_refine_masked_terrain.py legacy_of_kattail_painter/painter.py
  legacy_of_kattail_painter/geography_model.py legacy_of_kattail_painter/model.py
  legacy_of_kattail_painter/country_model.py legacy_of_kattail_painter/country_ui.py
  legacy_of_kattail_painter/test_geography.py legacy_of_kattail_painter/test_railways.py
  legacy_of_kattail_painter/test_countries.py: passed; PYTHONPYCACHEPREFIX in Temp.
- Staged dry run, visual preview inspection and guarded --apply succeeded with
  identical input/output hashes. Atomic writer retained all original bytes in
  audit.json's backup path. The stage cannot be applied twice.
- python -B legacy_of_kattail_painter/backups/terrain-refinement-stage/verify_native.py:
  passed byte/pixel verification against backup and stage; 2,323 protected hashes
  unchanged; all 580 province types match the complete graphical majority. No
  exterior raster pixels, BMP headers/palettes, DDS header/compression/alpha,
  province geometry or river bytes changed. EU4 inputs stayed read-only.
  Changed pixels: height 74,250; normals 19,215; RGB 19,280; tree cells 2,715.
  Native mapped Tk: Provinces VP/Railways/Terrain modes, terrain draft/Undo/Redo,
  MAJ/ANS/KHO politics pies and random allocation passed. 1,192 hubs remain;
  zero callback errors/drafts and 4,214 native source hashes unchanged. Live Save
  was forbidden for this probe. verification.json records the results.
- python -B tools/validate_map.py: fails only the two known pre-existing jumps:
  railways.txt:1308, 19461-20841; :1309, 20839-20841. The railway file's protected
  hash matches the pre-refinement file; this is not introduced by the patch.
- git diff --check, git diff --stat, complete text diff and task-baseline diff
  reviewed. Native image changes verified by exact byte/pixel masks and hashes.

## Sources and limits

The user's live HOI4 logs/error.log lines 168-173 at 16:27:10 list the six rejected
set_popularities blocks. Stored before/after sums in the repair audit reproduce
that deficit on the fixed-point grid. The engine was not relaunched; correcting
the grid addresses this evidenced failure, but in-game pie rendering is pending.

Installed game documentation/effects_documentation.md lines 7542-7554 documents
COUNTRY set_popularities with 54.5/45.5 decimal shares. Installed documentation/
modifiers_documentation.md lines 6-7 states up to three decimals. Repository
modding_documentation/wiki_doc/Data structures - Hearts of Iron 4 Wiki.md lines
408 and 487 explains fixed-point 1/1000/truncation. These support retaining legal
fractional shares rather than restricting authors to whole percentages.

common/terrain/00_terrain.txt and other native terrain files provide gameplay
categories, graphical index/type mappings and UI colors. Installed gfx/entities/
trees.gfx lines 18-26 and 37-45 defines native models 5 and 28. Existing trees.bmp
already uses both; no new art was made. The exact source/mask/original import
paths and all content hashes are recorded in audit.json and the original import
audit. Refinement requires NumPy, Pillow and SciPy; these are tooling dependencies,
not new painter runtime requirements.

No game launch or CWTools check was performed. Next: restart the painter and
load a fresh campaign to inspect the region with trees and confirm the six
countries' popularity pies. Known railway jumps remain a separate data defect.
No further implementation is pending for these requests.

## Subsequent authorized railway repair

The user then explicitly requested fixing the two preserved railway jumps.
Removed only the impossible routes to land-isolated province 20841; all other
railway links/levels preserved. python -B tools/validate_map.py now passes.
The protected railway hash and failure output above describe the earlier
refinement snapshot, before this separate authorized change. Current evidence,
backup and exact file list: ../railway_jump_repair/README.md and audit.json.

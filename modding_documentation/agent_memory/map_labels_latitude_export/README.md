# Map names, planetary latitude and viewport export - 2026-11-25

## Implemented behavior

Display names is available beside Display numbers. It remembers separate session
choices: states off, strategic regions off, VPs on. State choices also apply to
state resources/population/buildings/category views; region choices also apply
to Koppen colors. VP names and numeric values toggle independently, while dots
remain. Overlay snapshots retain their own name setting. Other modes disable
the names control. Localized names use the existing source/draft localizer.

All manual North/South controls were removed from the painting sidebar and the
region preset dialog, following the user's clarification. Hemisphere always
comes from geographic area. Account for latitude is enabled initially and now
controls only near-equator thermal smoothing; turning it off retains automatic
hemisphere selection. Native weather fields remain directly editable.

The original planet is bottom-aligned and 2:1: for this map it occupies rows
1024..3071, with equator y=2048 (top-origin map pixels). The solar-system chart
and Firmament are excluded. This is NOT the full-map midpoint y=1536. Latitude
uses the exact area-weighted land-pixel centroid of a region; sea-only regions
use their water area. Off-world/mixed-body regions have no main-planet latitude
and require direct native weather editing; no fictitious hemisphere is assigned.

Thermal smoothing uses a signed cubic smoothstep across +/-10 degrees. It
suppresses only the annually reversing temperature component, preserves the
annual mean of the monthly cycle/even harmonics and is identical to the original hemisphere profile
outside the band. The 10-degree width is an editor design approximation, not a
calibrated physical boundary. This does not infer altitude, ocean currents or
planetary obliquity. Koppen class, rainfall wet/dry seasonality and dry-weather/
sandstorm choices remain class-led; freezing, rain/snow partition and mud weights
are recalculated using adjusted temperature. A cold highland/glacial preset can
therefore remain cold at the equator. The preset classifier recognizes these
exact generated native profiles after Save/reload without metadata. Custom
weather remains gray.

Display equator is off initially and visible in every map mode. The dashed gold
reference is drawn after overlay compositing, at the actual planet equator,
with stable map coordinates under pan/zoom. It does not alter game map assets.
Export current view as image opens a PNG destination dialog and renders exactly
the currently visible map bounds at current zoom, including names, numbers,
boundaries, supply hubs, overlay/opacity and the equator when enabled. It excludes
toolbars and the renderer's overscan margin. Cancel writes nothing.

## Existing weather reapplied

277 regions were recognizable native presets. 276 belong wholly to the main
planet. All 276 were evaluated while retaining their authored climate class;
29 native strategic-region weather blocks needed changes, including nine
hemisphere corrections. 247 profiles were already identical at native precision.
The recognized off-world EF region 282 and 136 unrecognized/custom regions were
left unchanged. 29 centroids lie within the thermal band (28 changed thermally;
one already rounds to its original temperatures). Province lists, region names,
naval terrain, other script, state history and map geometry are unchanged.

The reapplication used a staged dry run and matching input/output hashes before
a guarded atomic write with original-file backups. reapplication.json records
all 276 region IDs/classes/latitudes, changed paths, exact hashes and backup path.
Native readback confirms every class/hemisphere and complete weather signature.
Only changed blocks were written; 4,185 protected source hashes stayed unchanged.

## Files changed

- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/map_render.py
- legacy_of_kattail_painter/geography_model.py
- legacy_of_kattail_painter/geography_ui.py
- legacy_of_kattail_painter/test_geography.py
- legacy_of_kattail_painter/README.md
- legacy_of_kattail_painter/MODLOG.md
- tools/reapply_koppen_latitude.py
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md
- modding_documentation/agent_memory/plans/map-labels-latitude-export.md
- modding_documentation/agent_memory/map_labels_latitude_export/README.md
- modding_documentation/agent_memory/map_labels_latitude_export/reapplication.json
- modding_documentation/agent_memory/map_labels_latitude_export/verification.json
- modding_documentation/agent_memory/map_labels_latitude_export/preview.png

Native weather files:

- map/strategicregions/30-Itchiloo.txt
- map/strategicregions/31-Lionsburg.txt
- map/strategicregions/36-Katzen Hills.txt
- map/strategicregions/37-Eastern Katzen Moutains.txt
- map/strategicregions/38-Meownich.txt
- map/strategicregions/39-Catburg.txt
- map/strategicregions/41-Feline Frontier.txt
- map/strategicregions/42-Gruyettburg.txt
- map/strategicregions/43-Lionita.txt
- map/strategicregions/45-Struken.txt
- map/strategicregions/51-Feline Gulf.txt
- map/strategicregions/52-Low Sea.txt
- map/strategicregions/129-Sudflutstadt.txt
- map/strategicregions/132-Valaros.txt
- map/strategicregions/138-Western Sun Sea.txt
- map/strategicregions/140-Wacegia.txt
- map/strategicregions/143-Altarian Approaches.txt
- map/strategicregions/200-Sankt-Krokersburg.txt
- map/strategicregions/229-Belkansavet Approaches.txt
- map/strategicregions/231-Propanian Shores.txt
- map/strategicregions/233-Donofettian Ridge.txt
- map/strategicregions/237-Tiefland.txt
- map/strategicregions/239-Northern Altaria.txt
- map/strategicregions/286-The Dish.txt
- map/strategicregions/287-Stone Kolechia.txt
- map/strategicregions/290-Sanguine Hills.txt
- map/strategicregions/308-Yinja2.txt
- map/strategicregions/309-Yinja3.txt
- map/strategicregions/310-Yinja4.txt

Identifiers: no new native IDs, sprite or localisation keys. Existing Koppen
classes and region IDs retained; nine existing seasonal hemisphere assignments
corrected. Names/equator/export settings are session-only UI state.

## Validation actually performed

- python -B -m unittest discover -s legacy_of_kattail_painter -p test_geography.py:
  42 passed after the final hemisphere-control removal. Covers per-family names,
  independent VP numbers/dots, overlay name snapshots, exact area/planet frame,
  all 30 climates across both latitude signs, thermal continuity, nine weather
  fields, off-world rejection, native Save/reload classification, camera-aligned
  equator pixels and actual mapped Tk checkbox/painting/PNG export/cancel.
- python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py':
  154 passed in 29.055 seconds after the final feature changes.
- python -m py_compile legacy_of_kattail_painter/painter.py
  legacy_of_kattail_painter/map_render.py legacy_of_kattail_painter/geography_model.py
  legacy_of_kattail_painter/geography_ui.py legacy_of_kattail_painter/test_geography.py
  tools/reapply_koppen_latitude.py: passed, PYTHONPYCACHEPREFIX in Temp.
- python -B tools/reapply_koppen_latitude.py then the same with --apply:
  staged/inspected/applied; all native profile readbacks and protected hashes pass.
  The audit cannot be applied twice. Use a new --audit path for future runs.
- python -B legacy_of_kattail_painter/backups/map-labels-latitude-export/verify_native.py:
  passed. All 29 changes are confined to weather blocks with BOM/newline style
  preserved. Real mapped Tk confirms names defaults/snapshots, absence of both
  hemisphere selectors, geographic region presets, globally visible equator and
  pixel-exact 1055x733 viewport PNG export. Zero callback errors/drafts; live UI
  Save forbidden and 4,213 native source hashes unchanged. verification.json and
  visually inspected preview.png record the results.
- python -B tools/validate_map.py: passes, 21,515 provinces, 20,926 state-assigned
  provinces, 413 strategic regions, no X crossings.
- git diff --check, git diff --stat and full changed-code/weather diffs reviewed.

## Sources, reasoning and limits

Geometry source: EU4 mod JUBLIO_SYSTEM_README.md lines 3-6 explicitly records
4096x2048 expanded to 4096x3072, with original world in rows 1024..3071.
Current HOI4/EU4 identity-aligned rasters and original masked import confirm the
same extent. Main-world geometry derives from that bottom-aligned 2:1 extent,
not the displayed full-map center or a centroid of landmasses.

NASA, Climate and Earth's Energy Budget, Heating Imbalances section:
https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/
Explains weaker annual solar-energy variation near the equator and stronger
seasonality at higher latitudes. This supports thermal smoothing qualitatively;
it does not prescribe the editor's 10-degree width or temperatures.

NOAA JetStream, Inter-Tropical Convergence Zone, paragraphs on seasonal movement
and equatorial rainfall, including its Kano/Lagos comparison:
https://www.noaa.gov/jetstream/tropical/convergence-zone
Explains that equatorial rainfall can be strongly seasonal/bimodal and monsoon
patterns vary geographically. Latitude alone cannot infer those patterns, so
this editor preserves the chosen climate's wet/dry structure rather than
flattening rain with temperature or inventing local monsoon behavior.

No game launch/CWTools validation was performed. The weather model remains an
editor approximation, not climate simulation. Next: restart the painter for the
new controls and check the changed weather in a fresh game. No further
implementation is pending for these requests.

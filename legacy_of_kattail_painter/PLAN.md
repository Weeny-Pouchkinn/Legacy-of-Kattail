# Painter milestones

1. Read-only source/map browser and tintable native-sized flags — completed.
2. Native EU4-style desktop interface — completed.
3. Guarded Save, backed-up migration into state histories, searchable paint
   palettes, majority/minority brushes, minority stripes and defined colours —
   implemented and applied on 2026-11-24.
4. Fixture and actual-data verification — 16 tests pass; real-data Tk painting,
   undo/redo, palettes and layouts pass. Save/reload verified in a disposable
   fixture. All 1,902 migrated demographic records match the original baseline.
5. Fresh-campaign engine verification — pending. The two pre-existing railway
   errors remain unchanged; no game launch is claimed.

Current controls and limits: README.md. Exact validation: MODLOG.md. Project
milestones: ../modding_documentation/agent_memory/plans/painter-editing.md.
# 2026-11-24: Existing-source culture/species/wonder editors

- [x] Trace native catalogs, culture group arrays/triggers, species traits and
  apply/clear effects, scripted localisation, GFX and wonder scaling/placements.
- [ ] Add source-backed definitions and writers in existing tool modules only;
  all game definitions/localisation/GFX go into existing native files, with new
  imported images only in their existing native asset folders.
- [ ] Add editable definition UI, species trait editor, wonder brush/overlay and
  state/strategic-region painting with shared searchable modifier selectors.
- [ ] Exercise generated data, coupled references, icons, undo/cancel/save/reload,
  native read-only/Tk performance and validators; update existing documentation.

No painter JSON/override/source files. No live invented lore or dummy entities.
Culture groups, species majority/minority colors and wonder base values stay
native. Wonder capital/noncore scaling stays in apply_wonder_effects. Existing
unique event targets must follow a move; repeated native wonders remain supported.


# 2026-11-24: Painting performance

- [x] Profile native editing/inspection/redraw and inspect the EU4 viewport renderer.
- [x] Sample cached viewport IDs before coloring; compute colors per state; reuse
  static palettes, country colors, Tk map images and wonder icons. Batch drag frames.
- [x] Verify exact pixels/stripes/boundary halos, cache invalidation, stroke input,
  real-data Tk behavior and before/after timings; document observed results.

This optimization changes tool code only. Native definitions and maps stay untouched.

# 2026-11-24: Native country editor

- [x] Trace country registration/history, ideological names, flag assets, leader
  promotion, technologies, national spirits, laws and startup species/attributes.
- [x] Add transactional native country/idea/flag/emblem writers and country index
  refresh; preserve unrelated history and conditional/dated content.
- [x] Add country workspace, ideology popularity pie, names/flags bulk actions,
  leader links, tech/spirits/icon picker, laws and map capital selection.
- [x] Verify temp Save/reload, Cancel/Undo/Redo, native read-only UI/data, asset
  sizes, source hashes and performance; document final limits and exact files.

No country/flag/spirit painter metadata, JSON catalogs or cache files. Imported
flags/emblems and created definitions are native assets/database entries.

# 2026-11-24: Visual flag background and emblem pickers

- [x] Inspect the EU4 visual library and current HOI4 selection controls.
- [x] Add modal thumbnail galleries, current-color previews, search/source filters,
  keyboard selection, Cancel/accept and bounded lazy rendering; wire arrows/Browse.
- [x] Verify fixture/native UI, lazy loading, colors, selection/grab restoration,
  unchanged source files and documentation. No new data/cache files.

# 2026-11-24: States, strategic regions and victory points

- [x] Audit native attributes/buildings, complete state-region membership, weather,
  VP localization, game/vanilla sources and Köppen classification references.
- [x] Add native state/building, region/weather and VP writers; enforce topology
  invariants without reshaping states/provinces and preserve unrelated content.
- [x] Add state/region dialogs, vanilla weather import and hemisphere climate
  presets, plus a fast VP gradient layer with zoomed labels and map placement.
- [x] Verify isolated Save/reload, limits, transfers, weather, locale sorting,
  Undo/Cancel, native read-only UI/data and map validation; update documentation.

All definitions remain in native files. No new painter data files; no live dummy
entities, state reshaping, province geometry, adjacency or railway editing.

# 2026-11-25: Flag colors, procedural outlines/backgrounds and country overwrite

- [x] Add live swatches/typed-pasted updates, procedural sized/tinted outlines,
  eight independent draggable symbol tabs with sliders/inputs, and more
  native-rendered background patterns with gallery parity.
- [x] Replace country-create source collisions with explicit overwrite choice;
  retain transactional Cancel/Save behavior and preserve unrelated history.
- [x] Check rendering, UI updates/galleries, overwrite acceptance/refusal and
  native read-only behavior; update documentation and project memory.

# 2026-11-25: Country save fixes and building map editing

- [x] Reproduce country color/popularity save failures; synchronize native color
  sources and verify country form Apply/Save/reopen with regression fixtures.
- [x] Add state/province building heatmaps, positive count labels, localized
  palettes and add/remove gestures for all state-scope and province-scope buildings.
- [x] Add direct state/region layer editing and whole-state region assignment;
  verify Undo/Save/reload, limits, map interaction/performance and documentation.

# 2026-11-25: Categories, scalar painting, overlays and country reports

- [x] Add native category create/edit/paint, category colors, shared-slot usage
  and static category/state capacity with full/over-capacity stripes and labels.
- [x] Add session configuration overlays with live data, alpha and zoom/pan
  alignment; share annotation rendering and add a Display numbers toggle.
- [x] Add resource/population gradients and precise/arithmetic painting, requested
  resource colors and a strict positive-resource-type threshold stripe option.
- [x] Add read-only owned-state country summaries and native-weather-derived
  Koppen preset colors and hemisphere labels, without persistent metadata.
- [x] Verify native writers, warnings, snapshots/compositing, UI/save/reload,
  source hashes and performance; update documentation and project memory.

120 tests pass. Native probes left 3,229 source hashes unchanged and no drafts.
Static capacity excludes runtime country modifiers. Map validation still has
only the known unrelated railway jumps at lines 893-894. No game launch claimed.

# 2026-11-25: Precision range and building arithmetic

- [x] Add per-click nonnegative integer precision sampling for resources/population.
- [x] Share arithmetic controls with state and province buildings, retaining native limits.
- [x] Verify bounds, gestures, validation/Undo/save/reload and native controls; document.
- [x] Discover all native/mod global text colors and add searchable colored lists,
  swatches and live name previews wherever a text-color selector exists.

# Deferred proposal: railway editor (requested 2026-11-25)

Status: historical proposal, superseded in part by the implemented province brush
below. Explicit route/waypoint editing and routing over unpainted land remain
outside the current request. The user confirmed that recomputation should stay
inside painted/existing railways; current compaction preserves its link graph.

## Proposed UI and first release

- Add **Railways** to MAP, with colored route lines, level legend, province/state
  borders, supply-node/port markers and a searchable route list. It should also
  support Save for Overlay, opacity, zoom/pan and optional level labels.
- **Inspect** selects a route, highlights its ordered provinces, and shows level,
  endpoints, source line and any invalid edge. Click an overlapping segment to
  choose which source route to edit rather than silently changing every route.
- **Draw route** clicks a start province, optional waypoints and an end province.
  Preview a suggested path; dragging adds adjacent provinces. Enter/Finish stages
  the route, Backspace removes the last waypoint and Escape cancels the draft.
- **Edit route** changes level, extends/trims endpoints, inserts/removes waypoints
  and deletes the selected route. A later edge brush can upgrade/downgrade levels;
  it must preview any splitting of longer source routes before applying.
- Read the allowed level range from native building definitions/installed rules.
  Keep province buildings and railway routes separate. Reuse the existing supply
  node editor rather than implicitly creating nodes or ports.

## Native files and route generation

`map/railways.txt` is authoritative. Current lines use
`level province_count province_1 province_2 ...` (for example the second route
starts `5 17 4970 13986 ...`). Load each route with its original source line and
ordered province list. Preserve untouched lines, ordering and unrelated whitespace;
recalculate the count only for edited/new lines. Retain overlapping route records
and do not globally merge or normalize them without a separate verified need.
Use the existing Documents drafts, grouped Undo/Redo, nested Cancel and backed-up
Save. No railway JSON, painter-specific native files or disk graph caches.

Build a cached in-memory graph from actual bitmap land adjacency, including the
horizontal map wrap as in `tools/validate_map.py:122`. Check IDs and province types
against `map/definition.csv`. Imported adjacency CSVs can assist inspection but
must agree with the active bitmap. Restrict generated paths to confirmed land
neighbors; special straits/sea links need verified engine rules before support.
Route suggestions use A* between waypoints, with map-distance edge costs and an
optional preference for existing tracks. Show the path before accepting; avoid
claiming the suggested route reproduces in-game construction cost or supply flow.
Cache geometry and adjacency, draw only visible segments, and invalidate only
changed routes so ordinary map painting remains responsive.

## Validation and staged implementation

1. [ ] Read-only network layer: parse native routes, display levels/endpoints,
   resolve overlapping source routes, integrate overlays and flag existing defects.
2. [ ] Transactional authoring: draw/extend/trim/delete and change route level;
   waypoint path suggestions; native writers with precise source preservation.
3. [ ] Verify before broader brushes: ID validity, native level bounds, exact
   province counts, minimum route length, consecutive adjacency, no sea/missing/
   self-linked nodes, overlap preservation, Undo/Cancel and Temp Save/reload.
   Exercise world-wrap paths, islands with no path, disconnected endpoints and
   repeated clicks. Do not reject or rewrite disconnected authored networks merely
   because they are disconnected. Report connectivity without simulating logistics.
4. [ ] Native read-only/full-scale performance probe, validator and actual in-game
   inspection of newly authored routes in a disposable fixture/copy before shipping.

Current baseline: `python -B tools/validate_map.py` reports railway non-neighbor
jumps on lines 893-894 (20839-20841 and 20841-19461). Inspect/highlight these in the
first phase. Preserve unrelated existing routes; new edits must introduce no new
topology errors. Fixing these two live defects is a separate explicit action.

Implementation would extend existing geography model/UI and shared map rendering;
`map/supply_nodes.txt`, native naval-base histories and province topology remain
unchanged unless independently edited through their own existing controls.

# 2026-11-25: Koppen preset painting

- [x] Inspect native weather, preset matching and strategic-region gestures.
- [x] Add Paint Koppen, colored left preset list and South checkbox (off = North).
- [x] Paint complete native weather profiles per region; preserve geography;
  support Shift-pick, Undo/Redo and Save/reload, including sea-only regions.
- [x] Verify all 60 profiles include every weather field and seasonal shifts;
  run gesture/UI/model checks, compilation and map validator; document results.

# 2026-11-25: Province railway brush and supply hub display

- [x] Add native railway level palette, province heatmap, route lines and exact/
  additive left/right gestures with amount and existing-only protection.
- [x] Interpolate province strokes, permit new adjacent route anchors, implement
  graph-preserving route compaction on Save, and reuse native hub sprite display.
- [x] Verify cap/scopes, branches/cycles/wrap, impassable borders/state drafts,
  source preservation, guarded Save/reload, Undo/Redo, actual UI, overlay/crop,
  native source hashes and performance; compile and run full tests/map validator.
- [x] Document native link semantics, source limitations and existing invalid links.

141 tests passed, including 13 railway tests. Native UI: 5,595 links, 5,259 rail
provinces and 46 hub logos; 4,224 source hashes unchanged, no remaining drafts or
callback errors. Map validator retains the two known jumps; the railway layer
also identifies two original links crossing explicit impassable borders. No game
launch. Current milestone details: ../modding_documentation/agent_memory/plans/railway-painting.md.

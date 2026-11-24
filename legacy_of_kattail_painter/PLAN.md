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

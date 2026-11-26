# National-spirit research/equipment bonuses - 2026-11-26

- [x] Inspect existing native/mod ideas and installed add_equipment_bonus docs;
  trace current SpiritDialog/Save source preservation and catalog overlays.
- [x] Add research-category/equipment/stat catalogs and source-preserving bonus
  read/write with optional API inputs, duplicate blocks and unknown data retained.
- [x] Add separate spirit tabs for modifiers, research and equipment bonuses,
  including instant/default setting, Add/Update/Remove and existing value loading.
- [x] Verify native output, unknown/nested data, duplicates, Cancel/Undo/Save/reload,
  actual UI and real-mod draft-only probe; run tests/compile/diff checks.
- [x] Update documentation/memory and report exact files, sources and limits.

Research uses technology_categories from effective technology_tags. Equipment
uses active native equipment IDs/type tokens and numerical equipment attributes.
Use native fractional game units, no automatic percentage conversion. The
installed documentation explicitly says instant=yes applies immediately;
otherwise bonuses affect new equipment variant creation. Preserve optional
instant omission, existing variable values and unrelated/native nested fields.
No production spirit data or historical content is to be seeded automatically.

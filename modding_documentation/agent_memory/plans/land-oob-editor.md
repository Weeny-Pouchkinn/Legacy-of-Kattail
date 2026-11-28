# Land OOB editor - 2026-11-27

- [x] Finish optimization milestone; read native OOB/history/unit definitions
  and local Division modding documentation. Inventory base references/fields.
- [x] Source-aware template/division model, isolated writes for shared OOBs,
  template create/edit/copy/rename, valid land placements and custom names.
- [x] Add Land OOB mapmode, country/source/template palette, global totals,
  per-province gradients/counts, placement/removal and province/name list view.
- [x] Template grid/unit picker and shortened-name field; ordinal + state + short
  generated names for newly placed divisions, manual overrides preserve originals.
- [x] Meaningful fixture/model/render/UI tests, native read/draft/Undo probes,
  full suite, compile/map/diff checks. Never Save native gameplay while testing.
- [x] Update memory/report, finish with actual validation and limits.

Keep all ongoing user native data edits and completed optimization changes.
Use whole existing provinces, no map geometry changes. Existing native division
names and unfamiliar template/unit/equipment fields stay intact unless edited.
Never add unsupported native fields for painter-only shortened-name metadata.

User additionally ordered retirement of KTZ_1936. Removed its land/air family,
references in 19 country histories and generator special case; guarded 22-file
backup remove_legacy_oob_20261127_230536_514574. No other native data touched.
Completed: 9 new tests/full suite 267 pass, 9 Python files compile, map check and
61-file installer manifest pass. Native source inventory: 144 primary sources,
317 templates/1939 divisions; staged AUR->AKR copy/place/rename/Undo and native
mapmode/global UI pass with zero drafts/source writes. Full report/limitations:
../land_oob_editor.md. Engine fresh-game inspection remains outstanding.

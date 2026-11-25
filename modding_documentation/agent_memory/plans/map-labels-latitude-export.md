# Map names, planetary latitude and current-view export - 2026-11-25

- [x] Add per-family Display names defaults (states/regions off, VPs on), keeping
  names independent of numbers and preserving overlay snapshots. First complete
  suite: 150 tests pass; modified Python compilation passes.
- [x] Establish main-planet extent from EU4 JUBLIO_SYSTEM_README.md lines 3-6:
  original 4096x2048 world occupies bottom rows 1024..3071, equator y=2048.
  Verify seasonality against NASA energy-budget and NOAA ITCZ references.
- [x] Add automatic geographic hemisphere and optional thermal transition painting; use exact
  region area, reject off-world geometry, retain native preset recognition.
- [x] Add globally available map equator overlay (off initially) and PNG export
  of the current viewport, including labels/overlays/reference line.
- [x] Validate model, real Tk gestures/export/cancel, native read-only probe,
  complete painter tests, compilation/diff; document decisions and limits.

Chosen scope: latitude selects hemisphere and smooths the annual temperature
component inside 10 degrees. Preserve the selected Koppen rainfall seasonality;
recompute rain/snow/frozen weights from adjusted temperature. The 10-degree width
is an explicit editor approximation, not calibrated planet climate data. No
automatic changes to already authored weather, province geometry or map assets.

User refinements completed: all hemisphere selectors removed, automatic geographic
phase always used, thermal checkbox starts enabled, and existing recognized
main-world classes reapplied (276 checked, 29 files updated, nine hemisphere
corrections). Current full validation and exact files: ../map_labels_latitude_export/README.md.
No implementation blockers; game validation not run.

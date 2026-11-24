# EU4 nations in HOI4 ZZZ territory

Date: 2026-11-24. Branch: Legacy-of-Kattail-Main.

## Scope

Import the active LegacyOfKattailEU4 starting nations that occupy HOI4 states
currently owned by ZZZ. Reuse existing HOI4 identities wherever established.
Preserve all other owners, map geometry, state demographics and unrelated edits.
Use EU4's default 100.1.1 bookmark as the geographic source.

## Milestones

- [x] Compare province rasters, evaluate dated histories, identify state overlaps
  and tag matches; resolve ambiguous assignments before writing game content.
- [x] Apply reversible, audited country/state changes and required identity assets.
- [x] Verify references, encodings, ownership/capitals and unchanged protected data;
  run map/localisation checks and review the diff.

## Baseline

- ZZZ owns 404 states before this task. The initial text search counted 444
  matching lines because 40 are comments; parsed history is authoritative.
- Existing uncommitted painter/demographic changes must be preserved.
- `python -B tools/validate_map.py` fails before import with two railway links:
  line 893 (20839/20841), line 894 (20841/19461). These are pre-existing.
- Both province bitmaps are 4096 by 3072. Existing-owner comparisons establish
  alignment with no crop/scale; the earlier 512-row cropping note is historical.

## Validation / next action

Dry run assigns 320 states to 39 countries; 84 remain with ZZZ. Ignore EU4
sea/lake/impassable pixels when voting, but retain uncolonised habitable land as
a competing result. Reuse LRN -> LAK and NOV -> NFS based on existing names,
species, geographic histories and flags. Five genuinely new tags: ELC, HIV,
INT, MAG, WMD; reactivate 12 dormant declarations. Existing history is retained
where present. Watermasters' Domain has no capital-province overlap with eligible
land; its sole assigned state 331 is its required HOI4 capital.

User confirmed existing states must be retained and Meogartha must not be imported.
Dry-run output is in work/zzz-eu4-import/proposal.json (ignored scratch).
Installed and statically verified; all three milestones are complete. See
../eu4_zzz_import/README.md for exact results, sources, limitations and recovery.
Remaining: fresh-campaign engine validation; no game launch is claimed.

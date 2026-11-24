# Deduplicate state histories — 2026-11-24

Branch verified: Painter-Test. Preserve existing uncommitted state/painter edits.

- [x] Parse all 1,902 state files; identify duplicate root history blocks.
- [x] Remove 39 redundant second ZZZ histories; consolidate seven same-owner
  histories while preserving unique data and the later value for overlapping
  building settings. Keep unrelated state-level resource/scalar duplicates intact.
- [x] Add a duplicate-history guard to the map validator, verify exact source
  preservation and all state histories, run map checks and inspect the full diff.

Findings: 46 files have two histories, no missing histories or parse errors.
State 1124 has FRU followed by ZZZ with conflicting building values. The first
history holds its detailed provincial setup and demographics. The seven same-owner
cases are states 151, 284, 556, 557, 558, 559 and 953; four MEW states have unique
VPs and provincial buildings in both blocks, so deleting either block loses data.

Pre-existing map validator failures: railway lines 893 and 894 (20839/20841,
20841/19461). Root resource/scalar duplicates occur in 50 state files; these are
a separate issue, outside the requested history-block cleanup.

Completed: 46 repairs, all 1,902 histories unique, source preservation checks and
four regression tests pass. Map validator retains only the original two railway
errors. Full result: ../state_history_audit/README.md. No game launch claimed.

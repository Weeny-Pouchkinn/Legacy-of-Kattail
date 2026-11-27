# Core audit and owner/releasable painter - 2026-11-27

- [x] Verify instructions/current sources, baseline map validation and Elwin's
  exceptions: SIL-owned demilitarized Katown states 34, 36, 44, 45 retain KTW cores.
- [x] Add ordered state core/claim reads and targeted atomic edits. Default owner
  transfers add the new owner's core and remove only the previous owner's core.
- [x] Add Owners categories Ownership and Cores/Claims, Transfer Cores default
  on, selected-country map rendering/ownership stripes and requested gestures.
- [x] Allow nominal capitals outside ownership while retaining defined-ID checks.
- [x] Dry-run/apply a guarded owner-core audit; preserve four exception files,
  third-party cores/claims, dated history, comments and unrelated data.
- [x] Exercise model, UI gestures, dead tags, map samples/overlays/export,
  transfer toggle, Save/reload/Undo, full tests and map validator; record evidence.

Audit is additive only; generic later ownership painting follows the explicit
Transfer Cores checkbox. No automatic reassignment of nominal capitals. Existing
third-party work and user drafts are preserved. No subagents or game launch.

Completed: 167 native repairs / 38 owners; 4 unchanged exceptions; second audit
zero changes; 224 tests; 10 compiles; before/after map validation; native GUI
probe with landless AAA and 4,225 unchanged source hashes. KTW owns territory;
initial assumption that it was landless was rejected before the successful probe.
No engine launch. Exact evidence: ../core_audit/README.md.

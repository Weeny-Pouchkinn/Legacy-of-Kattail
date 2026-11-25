# Terrain refinement and province submodes — 2026-11-25

- [x] Inspect prior mask/audit, original height, current assets and existing editor.
- [x] Match imported height contrast to surrounding native relief and remove seams
  inside the original selection; update matching shading/colors and audit all
  touched land provinces against actual graphical terrain. Preserve geometry,
  coastlines, exterior pixels, alpha and unrelated user/source changes.
- [x] Move VP/Railways edit modes into Provinces subcategories, retaining all
  gestures, overlays, dialogs, save and supply-hub features. Add native gameplay
  Terrain painting under Provinces, without editing graphical terrain assets.
- [x] Verify visual before/after, seam metrics, terrain consistency, province-mode
  UI, Undo/Redo/guarded Save/reload, native hashes, tests, compilation and map
  validator. Update status/decisions and mark the earlier import choices superseded.

Known initial defects: direct EU4 height range + four-pixel inward feather leaves
an obvious tonal boundary. Earlier province classification used EU4 overrides
rather than final HOI4 graphical terrain, and excluded minority-covered boundary
provinces. User now explicitly requires every province in the area to match its
visible terrain. Existing map validator has two railway jumps; preserve unrelated
railway edits and do not repair topology as part of this task.

## Added scope: popularity persistence (user follow-up)

- [x] Read live game error log: set_popularities rejected ANS/PAR/SPT/MAJ/KHO/CER.
- [x] Quantize writer/helper outputs to the engine 0.001 fixed-point grid using
  exact apportionment; preserve total 100 and intentional manual Gestalt.
- [x] Exclude Gestalt from random remainder allocation; repair all six matching
  failed histories with targeted value edits. Verify writer/UI/readback; new engine reload remains pending.
- [x] Explicitly include trees.bmp in masked terrain refinement, mapping source
  tree indices to native models and preserving cells outside the selection.

Completed implementation/static/UI milestones. Results and remaining engine-only
checks: ../terrain_refinement/README.md. No game launch performed. Map validator
has only proven pre-existing railway jumps at lines 1308-1309.

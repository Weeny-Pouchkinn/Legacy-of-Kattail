# Katzenartig Imperium state painter and native mapmode - 2026-11-25

- [x] Inspect existing state categories, mapmode/scripted-localization tooltip
  scopes, definition forms, draft/Save semantics and native map rendering.
  Search new identifiers globally; existing country prose is unrelated.
- [x] Add native element definitions (color + editable name/immediate/delayed
  localization), state-history assignment and matching in-game mapmode/tooltips.
- [x] Add States > Katzenartig Imperium palette/New/Edit, paint/erase/Shift-pick,
  immediate/delayed hover preview, overlays/export and state-name support.
- [x] Validate native syntax/references, independent definitions/colors,
  source-preserving state painting, Undo/Redo/Cancel/guarded Save/reload,
  actual mapped Tk hover/edit workflows, full tests/compile/map validator.
- [x] Update docs/memory, report exact files and engine-verification limits.

Design: one optional historical element per state, independent of current owner.
Native state-history variable lok_katzenartig_imperium_element (0 = unassigned).
Native mapmode color branches are the authoritative element/color catalog;
English localization holds manually authored names and both tooltip texts.
Scripted localization selects those texts in the hovered state context, using
the repository's existing [FROM.GetName] convention. No metadata, runtime world
loops, ownership inference or automatically invented historical boundaries.
The user's Schutzone Pegasien / MCF scenario is an example, not an instruction
to populate its historical extent. Initial definitions/assignments stay empty.

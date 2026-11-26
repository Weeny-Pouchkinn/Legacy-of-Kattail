# Generic portrait groups - 2026-11-26

- [x] Inspect native group comments, reserved species sprites, repeated country
  pools, individual portrait uploads/small generation and country/species Apply.
- [x] Implement source-preserving group catalog, reserved slot allocation,
  pool/art editing and country reassignment across native portrait sources.
- [x] Add Characters > Generic Portrait Groups and role/gender upload editor;
  add country group picker and species creation allocation hook.
- [x] Validate independent reserved groups, shared country updates, images/small
  portraits, source preservation, Undo/Cancel/Save/reload and real Tk controls.
- [x] Repair/allocate existing Altarian slot if needed; document files/IDs,
  exact tests and engine verification limits; update durable memory.

Design: group identity follows existing Species_<id>/special section headers.
All reserved 0..100 slots remain available; species names dynamically label IDs.
Existing native country blocks are authoritative. A small draft-managed template
catalog retains editable pools for groups with no countries, because HOI4 has
no unassigned country portrait block. No fake country tags or global loops.
Native files and sprite registrations drive the game; art edits never overwrite
the shared placeholder texture. New species uses its matching reserved ID.

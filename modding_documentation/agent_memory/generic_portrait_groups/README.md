# Generic Portrait Groups - 2026-11-26

Implemented **CHARACTERS > Generic Portrait Groups**, species-slot allocation
and the country Setup portrait-group selector. Restart the painter to load it.

The database exposes all **103** existing group sections: **Species_0..100**,
**Amphibian_Species** and **Roqualian_Species**. Numeric groups display the species
name when allocated, including **Altarian (Species_61)**. No reserved group is
removed when it has no country or no species yet.

Double-click a group, choose role/ideology/gender, then add, replace or remove
portraits. Political pools are separated by ideology/gender; army, navy, operative
and scientist pools have both genders. Missing ideology pools can be populated
through the same uploader. An enabled pool must retain at least one portrait.
Large uploads fit inside **156 x 210 pixels** with alpha-preserving padding;
small **65 x 67** portraits are generated using the existing Ministermaker
routine. Both preview in the editor. New imports select their preview immediately.

Replacing shared art changes every pool/country referencing that sprite. Pool
membership changes update the same role/gender in all group countries, preserving
their other fields and comments. Removing a membership does not delete its asset.
Uploads have separate group-owned paths; shared placeholder textures are retained.
Apply keeps drafts, Cancel restores all dialog changes, and main Save uses native
guarded writes/backups. Undo/Redo includes the binary images.

New species receive their same-ID portrait group in the same draft transaction.
Already reserved sprites/art are retained. Beyond Species_100, new registrations
point at existing placeholder files. Vacant group defaults follow the existing
native pool layout, independently of later Species_0 edits.

Country Setup now selects a generic group. New-country UI suggests its national
species until manually overridden; Use national species restores that suggestion.
Existing country choices stay as authored. Apply inserts the tag in the selected
group and removes its previous country-specific pool, including pools in other
portrait files. Keep existing/native default preserves sources outside this
catalog; Default deliberately clears country-specific pools. Species and portrait
group remain independently selectable.

## Files changed

| Exact repository path | Change |
| --- | --- |
| `legacy_of_kattail_painter/generic_portrait_model.py` | Group discovery/templates, independent defaults, allocation, targeted pools, uploads, country membership |
| `legacy_of_kattail_painter/generic_portrait_ui.py` | Group database and role/gender image editor/previews |
| `legacy_of_kattail_painter/character_model.py` | Lazy shared generic portrait store |
| `legacy_of_kattail_painter/character_ui.py` | Characters subtab |
| `legacy_of_kattail_painter/demographics.py` | Species creation allocation hook in grouped draft transaction |
| `legacy_of_kattail_painter/country_model.py` | Read/write selected native country portrait group |
| `legacy_of_kattail_painter/country_ui.py` | Country selector, national-species suggestion, preserve/default choices |
| `legacy_of_kattail_painter/install.py` | Distribution manifest |
| `legacy_of_kattail_painter/test_generic_portraits.py` | Ten meaningful regression/model/mapped Tk tests |
| `portraits/LOK_portraits.txt` | Correct special-group sprite prefixes only |
| `legacy_of_kattail_painter/README.md` | User instructions |
| `legacy_of_kattail_painter/MODLOG.md` | Feature and validation record |
| `modding_documentation/agent_memory/CURRENT_STATUS.md` | Result and engine follow-up |
| `modding_documentation/agent_memory/DECISIONS.md` | Architecture and source-preservation choices |
| `modding_documentation/agent_memory/plans/generic-portrait-groups.md` | Completed milestones |
| `modding_documentation/agent_memory/generic_portrait_groups/README.md` | This report |
| `modding_documentation/agent_memory/generic_portrait_groups/native_repair.json` | Native repair hashes, backup, counts, affected tags |
| `modding_documentation/agent_memory/generic_portrait_groups/verification.json` | Real-mod UI and source-hash evidence |

Files created lazily by future user edits, not seeded as live data for this task:

- `legacy_of_kattail_painter/generic_portrait_groups.json`: sparse native-body
  templates for unassigned groups. Existing country blocks remain authoritative.
- `interface/lok_generic_portrait_groups_painter.gfx`: new portrait registrations.
- `gfx/leaders/generic_groups/<group_prefix>/large/<sprite_stem>.tga` and
  `.../small/<sprite_stem>.tga`: imported art; collisions get numeric suffixes.

Existing registered sprites are updated in their existing GFX source. No runtime
world scan, on-action, localisation, state/country history, species identity or
country membership was changed in the live mod. The native UI probe's ALT
assignment was draft-only and cancelled.

## Identifiers and representation

- Group IDs follow existing headers: `Species_<species_id>`,
  `Amphibian_Species`, `Roqualian_Species`.
- Altarian uses its existing `Species_61` section and 44 existing placeholder
  large/small registrations. It is visible without creating a fake country pool.
- Standard sprites retain `GFX_portrait_species_<id>_<kind>_<n>[_small]`.
  Reserved kinds: civilian (6), military (6), navy (3), spy (3), scientist (4).
- New uploads use `GFX_portrait_<group_prefix>_<role_ideology_gender>_<n>`
  and corresponding `_small`. Existing art replacements retain the selected ID.
- Special prefixes are `species_amphibian` and `species_roqualian`.
- Model field `Country.portrait_group`: `None` preserves existing/default native
  sources; empty string clears country-specific pools; otherwise native group ID.

The game loads country-tag blocks, not abstract group IDs. Their repeated pool
contents are updated together. Vacant groups cannot have a fake tag; the sparse
editor template catalog preserves their authored lists until a tag is assigned.
Template edits use the same Documents store, Undo/Cancel and guarded Save.

## Coupled native reference repair

Existing special pools referenced **38 undefined large sprite IDs**, although
the intended large and small sprites/art were already registered under different
names. Verified both actual images for all 19 Amphibian and 19 Roqualian pairs.

- `GFX_portrait_amphibian_species_` -> `GFX_portrait_species_amphibian_`:
  **140** occurrences across ACR and WAC.
- `GFX_portrait_roqualian_species_` -> `GFX_portrait_species_roqualian_`:
  **980** occurrences across ROQ, LMB, PER, TAK, DEM, REC, OBS, BOC, GLI, BRU,
  UCE, VEL, POI and RSA.

Guarded native write with backup and readback. Exact byte comparison against the
backup confirms these prefix substitutions are the only changes: all **151**
country blocks, comments, encoding and original line endings retained. Recovery
path and before/after SHA256 are in `native_repair.json`. Do not overwrite later
user edits by blindly restoring the backup.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **192 tests passed**, including **10 new tests**. Covers reserved/special groups,
  label allocation, above-100 placeholder generation, independent Species_0
  edits, shared pool updates and per-country fields, exact small portrait output,
  placeholder preservation, batch failure rollback, unassigned template
  Save/reload, country creation/reassignment/Undo, native tag uniqueness, actual
  species-creation hook and real mapped dialogs/database/preview/Cancel/Apply.
- `python -m py_compile` on the nine Python files in the changed-file table:
  passed. `PYTHONPYCACHEPREFIX` redirected to system Temp.
- Real-mod mapped Tk probe: actual Characters tab and all 103 database rows,
  Altarian role upload, selected large/small preview, Cancel, actual ALT country
  form Apply/country-list membership/Cancel and both special-group previews passed.
  Live UI Save forbidden; **zero callback errors**; **4,328 native source hashes
  unchanged by the probe**. No persisted template or country assignment.
- All 103 groups' large sprite references now resolve. All 38 repaired special
  large/small pairs resolve to actual readable images. Species_61 allocation is
  a no-op on the current native mod because its header and sprites already exist.
- Installer manifest file existence and new-source trailing whitespace passed.
  `git diff --check -- legacy_of_kattail_painter modding_documentation/agent_memory`
  passed; new untracked source files checked separately.
- Whole `git diff --check` reports **416 changed native portrait lines** with
  inherited CRCRLF endings. The before/after files both contain 8,305 CRCRLF
  sequences and 8,825 LF terminators. Byte-only replacement comparison proves
  no new line-ending changes; unrelated formatting was deliberately preserved.
- `git diff --stat` and implementation diff reviewed; native diff checked against
  the exact prefix-only transformation. New IDs/files checked for collisions.
  No bitmap, topology or state-history edit, so map validation was not required
  for this feature. No claim of game/CWTools testing.

## Sources and remaining check

Primary repository sources (physical LF-based locations; CRCRLF may display
additional empty lines in editors):

- `portraits/LOK_portraits.txt`: existing Species_0 role/gender/ideology layout,
  Species_61 header at LF line 7765; Amphibian at 7925; Roqualian at 8040.
- `interface/lok_generic_species_portraits.gfx`: Species_61 registrations around
  line 3851, Amphibian registrations around 6375, Roqualian around 6438. Existing
  texture files establish correct prefixes and placeholder allocation.
- `legacy_of_kattail_painter/small_portrait.py:15`: established Ministermaker
  transformation reused unchanged, pixel-checked by the tests.
- `legacy_of_kattail_painter/character_model.py`: existing image fitting,
  source-targeted sprite updates and draft/binary storage patterns.
- `legacy_of_kattail_painter/source_io.py`: guarded backup/write/readback and
  encoding/newline preservation.

**Not tested in HOI4 or CWTools.** Restart the painter, edit a group, select it
for a country, Save, then restart HOI4 and use a fresh campaign to inspect newly
generated political leaders, commanders, operatives and scientists, including
their small portraits. Existing explicitly assigned character portraits are
separate and do not automatically become generic portraits.

# Current status

## Jublio system backport (2026-11-04)

Branch `jublio-system-backport`, based on `3abc65d2`. Installed in the working tree, not committed.

**Done:** map grown to 4096x3072 with EU4's solar system chart in rows 0..887; 12 new bodies;
18 Doughland nations at their 100 AKA borders; 11 NPC planet tags; 10 terrains; 12 continents.

**First launch (2026-11-04):** reached nation select, showed a map error warning, then crashed at
game start. Six map errors were logged; all are fixed in the current build.

**Validated (static only):** `work/legacy-kattail-hoi4-space/check_stage.py` passes, including
rules taken from that `error.log`. `tools/validate_map.py` reports the same 2 issues as before the
change, both in `railways.txt` lines 893-894.

**Not validated:** the current build has not been launched, so the crash fix is unconfirmed.
Rendering, AI behaviour and balance are unknown.

**Next action:** launch once and read `error.log`.

**Not done:** space programme decisions for the new bodies; superregion map mode entries;
per-culture state names; final flags.

Generator and full notes: `universal-modder/work/legacy-kattail-hoi4-space/` (`MODLOG.md`). It
reads a pristine export of git HEAD, so re-export it if HEAD moves.

## Conquest release fixes (2026-11-04)

Same branch, uncommitted, independent of the Jublio work. Changed `decide_fate_of_nation`,
`return_occupied_cores_to_puppet`, `lok_peace.1` and `lok_create_blank_occupation_puppet`; added
`common/scripted_triggers/lok_peace_triggers.txt`.

**Validated (static only):** braces and line endings checked, diff reviewed. Not launched.

**Next action:** in game, have two nations carve up a third and release, then check each puppet's
cores match its own land. Then puppet a nation, take more of its land, and confirm only "Return
Territories" shows.

**Unverified:** whether `FROM` keeps its value inside `create_dynamic_country`; what the engine does
when the dynamic tag pool runs out (a failure is only written to `game.log`).

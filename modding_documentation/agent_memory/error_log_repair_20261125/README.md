# Startup error repairs and painter safeguards

Task started 2026-11-25, on `Painter-Test`, based on `a5958d259`.
This is the completion record for the [original repair plan](../plans/current-error-log-fix-plan.md).
Exact patch paths: [files.txt](files.txt). Frozen validation and engine evidence:
[verification.json](verification.json). Original messages, source lines and
conflicting localisation values: [baseline inventory](../error_log_audit_20261125/inventory.json).

## Result

The original engine baseline contained 1,526 records, of which 1,520 belonged
to the mod. The latest inspected fresh-run log contains only the six unchanged
Workshop descriptor warnings from other mods; `text.log` is empty. The user
performed the fresh-game/UI checks; the agent independently inspected the logs.
This is not a claim of exhaustive campaign, focus-tree or AI testing.

The first fresh run also exposed additional repair-number widgets when the
construction screen opened. Their native containers and backing sprite were
ported and added to dependency validation. Final screen-check confirmation is
recorded in verification.json rather than inferred from reaching the main menu.

## Game changes

- Restored the installed 1.20 trade automation, repair-priority windows and
  entries, volunteer recall indicators/dialog, diplomatic responses and keyboard
  shortcuts in the five existing GUI overrides. Kept custom resource/map UI.
  Added the missing repair-number containers in all relevant construction
  templates and restored the single vanilla `GFX_generic_circle_background`
  definition in `interface/core.gfx`, using the existing game texture and shader.
- Shadowed only `common/scripted_guis/ROM_diplomacy_scripted_gui.txt` with an empty
  documented override. The inherited GUI referenced a country/system excluded
  by this total conversion. No `replace_path` entries were changed.
- Repaired two horizontal-wrap X crossings with exactly two province pixels
  (six channel bytes). Province IDs/colors, bitmap header/format, states,
  strategic regions, supply and railway data remain intact. The validator now
  checks horizontal wrap; it reproduced both failures before the pixel repair.
- Relocated exactly the 64 logged enemy-territory divisions: TEM 17, KKN 24,
  FOD 23. Each moved to the nearest owned province by current bitmap centroid,
  with horizontal wrap. Kept all division names, templates and counts and left
  accepted neutral/friendly deployments alone. Corrected 16 malformed armored
  entries in EUL/GAL/KKN/KTZ and their `generate_oobs.py` writer.
- Selected owned capitals using highest existing VP, then population: TEM
  `1312 -> 1514`, FOD `1519 -> 1481`, KRO `1043 -> 1044`, NKR `1044 -> 93`.
  Borders were not changed. Moved RST's three state-215 air entries (120 aircraft)
  to existing RST air base 189. Guarded PGN's war declaration on both countries
  existing; PGN's territory and release status remain unchanged.
- Kept the startup generator's existing eight-battalion motorized/support
  template for countries with its required technologies. Other countries receive
  an eight-battalion basic infantry template using already-active equipment.
  Existing division counts/spawn scopes are unchanged; no technologies or new
  recurring scans were added. Native-data checks cover 159 modern and 49 basic
  country technology contexts.
- Added a generic random-name fallback by reusing the authored ZZZ Random Names
  pool. Added default scientist pools using four existing generic scientist
  sprites and their existing small portraits. No nation-specific names, lore,
  leaders or new placeholder image files were invented.
- Added 53 explicit shared building slots across exactly the 21 logged states.
  Every original state byte outside the inserted effect is preserved, including
  factories, resources, population, ownership and culture/species/Imperium data.
- Resolved all 3,542 English localisation collisions. VP definitions live in
  the existing `victory_points_*` files; the current Jublio names remain in their
  Jublio file. Every alternate authored line remains as a comment in its source
  file, including different spellings and BASILISK variants. No live key was
  lost or renamed. BOMs, first-line headers and authored tokens are preserved;
  intentional localisation `replace`-layer overrides remain valid.
- Converted the 198 implicated flags to 32-bit TGA, with identical decoded RGB
  pixels/dimensions and opaque alpha. Removed two copied Sabaton playlists that
  referenced unavailable optional-DLC assets. The proper DLC playlists can be
  inherited when that DLC is installed; custom music remains unchanged.

## Painter and generator changes

- Painter country/flag export and the EU4 importer now write 32-bit RGBA TGA.
- Owner painting and country/source edits cannot save a newly foreign capital
  for a country that still owns territory. Choose another owned capital in the
  same transaction; dormant countries may keep nominal capitals. The actual
  painter Save callback, direct model Save and Undo are regression-tested.
- Saves reject new cross-file localisation collisions and require the English
  header on the first line and a UTF-8 BOM. The check honors the engine's
  `replace` layer, reads untouched files freshly to catch external edits, and
  permits an undone file creation. Existing authored localisation is edited
  through its native definition rather than duplicated elsewhere.
- The armored OOB writer now emits the missing `{ name =` opening syntax.
- Added `tools/validate_startup.py` for the repaired GUI bindings and all their
  sprite dependencies, localisation uniqueness, random fallback coverage,
  capitals, OOB parsing, logged deployments, air bases, shared slots, flag
  formats, optional music references and generated equipment compatibility.

## Identifiers

No public game IDs were renamed. `Standard Infantry` retains its template
name. Added engine `default` fallback blocks and restored the existing vanilla
sprite name `GFX_generic_circle_background`. GUI binding names are enumerated
in `tools/validate_startup.py::GUI_BINDINGS`; these include
`auto_import_priority_window`, `auto_import_priority_entry`,
`repair_order_window`, `repair_order_entry`, `repair_order_number_window`,
`repair_order_number`, `response_icon` and the research/focus shortcut controls.
No new persistent flags, variables, country tags or province/state IDs.

## Validation

```text
python -B -m unittest discover -s legacy_of_kattail_painter -p "test_*.py"
python -B -m unittest discover -s tools -p "test_*.py"
python -B tools/validate_map.py
python -B tools/validate_startup.py --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"
python -m py_compile <the ten modified/new Python files listed in verification.json>
python -B legacy_of_kattail_painter/verify_real.py --mod . --output <temporary-output-folder>
git -c core.fsmonitor=false diff --check
git -c core.fsmonitor=false diff --stat
git -c core.fsmonitor=false diff
```

Compilation outputs were redirected to a temporary pycache directory. No cache
files or generated root diagnostics are part of the patch. The real-data painter
check parsed all 4,215 scripts with zero errors, exercised hidden Tk editing,
Undo/Redo, flags and source fields, rendered 1,026 masks and preserved all 11,153
checked source hashes. Exact test totals and outcomes are in verification.json.

All 198 flag RGB planes were compared to their original source bytes. All six
changed localisation files retain their BOM/header and every original text line,
either active or commented. All 21 slot-state files match their exact backups
outside the inserted effect. The bitmap differs in exactly six channel bytes.
Complete diff review confirmed the expected path set and balanced native blocks.

The actual `loc_analyzer.py` interface was run with only its output file
redirected to temporary storage. Repeating it with the pre-patch localisation
sources gives the identical set of 2,285 missing keys. These are pre-existing
content gaps, not new engine-log errors; no invented narrative was added to fill
them. The tracked old `loc_analysis_results.txt` is preserved as a historical
snapshot. Two unrelated existing English files have BOM/header issues
(`FRA_l_english.yml`, `WUW_ideas_l_english.yml`); neither was changed by this task.

## Limits and remaining work

The six `supported_version` warnings reference external Workshop descriptors
`2735339350`, `3305141798`, `3368690477`, `3446246309`, `3679587713`,
`3718330259`. They are not this mod's descriptor and remain outside the patch.
This mod's declared `1.17.*` compatibility / `1.15.*` version inconsistency was
left untouched as instructed. No Private-variant files were inspected.

No CWTools check or long campaign test is claimed. Agent-controlled game launch
was blocked by automatic approval review; the user supplied the fresh-game
checks instead. Logs prove the exercised startup/UI paths, not every gameplay
branch. Future content changes should rerun both validators and the tests.

Originals of native edits are recoverable from timestamped
`legacy_of_kattail_painter/backups/error_log_*` directories. Their exact paths
and manifest hashes are indexed in verification.json. Do not restore the whole
backup over later user edits; select the required file/version first.

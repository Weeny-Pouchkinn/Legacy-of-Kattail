# Legacy of Kattail Painter

Run `run_painter.bat` with Python 3.10+ and the packages in `requirements.txt`.
Install dependencies if necessary with `python -m pip install -r requirements.txt`.
The launcher disables bytecode generation.

## Painting

The interface follows the EU4 painter: native light controls, compact toolbar,
left palette and dark map canvas.

1. Choose **Culture**, **Species** or **Owner** in **Paint**.
2. Search the **Paint** sidebar and select a named entry with its colour swatch.
3. Choose **State** or **Strategic region** in **Paint scope**, then click or
   drag to assign that entry. State scope changes the clicked state; Strategic
   region changes all states in the clicked region. Each regional action undoes
   as one operation, and a state is painted only once per drag.
4. Use **Save** or **Ctrl+S** to write edited source files. Undo/Redo apply to
   unsaved edits; saving establishes a new baseline and clears undo history.

Culture supports **Set**, **Add** and **Remove**. Set replaces the state's culture
list; Add/Remove retain other entries and their order. Existing three-culture
states are preserved until explicitly painted or edited.

Species has **Majority** and **Minority** selectors. Each changes its own field;
if the resulting species are identical, the minority is automatically cleared.
This also repairs equal pairs loaded from source files or entered in the source
editor, including before Save. Choose **No minority** to clear the minority
(runtime value `1000`, which cannot be used as a majority species).
The **Species** view shows minority-coloured diagonal stripes over the majority
colour. Water stays water-coloured. The separate Minority view remains available.

**Shift-click** picks the current layer's assignment without painting; for a
multi-culture state it picks the first culture. The rest of that drag gesture
also remains unpainted. **Inspect** opens the state form. Right-drag pans;
the wheel and toolbar zoom; Fit frames the map. **View** changes the map overlay
independently of the paint brush.

**Province boundaries**, **State boundaries** and **Strategic region boundaries**
can be toggled independently. Their lines are 1, 2 and 3 screen pixels wide,
respectively, including after zooming. These display options are independent of
the paint scope and start switched off.

Culture, majority, minority and owner brushes all support both scopes. A region
containing a state that crosses its boundary is refused before any painting,
because state-level data cannot be split safely between regions. The current
map has no such split states. Province/region memberships are loaded when the
painter starts; restart after editing map topology externally.

The sidebar also contains **State setup** for full ordered culture lists,
majority/minority values and owner changes, and **Sources** for country/state
histories and other mod scripts. The main tabs contain Map, All source fields
and Flag maker. State forms scroll and flag previews fit narrower panes.

## Saving and source fields

All edits remain drafts until Save. Save writes changed text sources, including
edits in All source fields, after structural parsing and checking that each
changed file still matches its originally loaded bytes. External edits block
the entire save before any source write. Reload the painter to incorporate them.

Original bytes are backed up under `backups/save_<timestamp>/` in this painter
folder, preserving relative paths. Each source replacement is atomic; a write
failure restores previously written sources and keeps the drafts. This is not a
power-loss-safe transaction across multiple files. Source encoding/BOM and
newline style are preserved. Backups and bytecode are excluded from Git.

All source fields exposes nested and repeated fields with scope, occurrence and
line number, including mod-specific resources, buildings, government variables,
technologies, characters, space data, food, WMDs and arbitrary custom fields.
Whole-source editing is also available. The parser checks structure, not engine
scopes or gameplay semantics. Four pre-existing OOB files (EUL/GAL/KKN/KTZ) have
excess closing braces; raw text remains available but structured fields cannot
be displayed until corrected.

Flags remain session-only prototypes; Save does not export flag images.
Discard removes unsaved source changes and session flags. Closing warns when
unsaved changes or session flags remain.

## Defined map colours

The painter reads the actual RGB components from:

- `common/map_modes/LOK_culture_map_mode.txt`: `culture_<id>_red/green/blue`.
- `common/map_modes/LOK_species_map_mode.txt`: majority bottom and minority top
  branches, using the original numeric species IDs.

Single-culture states use their defined colour; multiple cultures use the
arithmetic mean of those colours. This represents the definitions rather than
simulating the in-game culture map shader's extra initial grey contribution.
Species stripes use the defined minority colour without shader alpha blending.
The catalogs currently contain 101 culture colours and 61 species colours.
Culture 102 (Katzenurkisch) has a name but no colour in the map-mode source;
it remains selectable and is shown in neutral grey, labelled accordingly.
No assigned migrated culture or species ID lacks a defined colour.

## State-history demographics

The initial demographic migration was applied on 2026-11-24. All 1,902 states
now define their initial demographics in their native `history` effect block:

```text
history = {
	# owner, cores, buildings and other existing history
	# LOK PAINTER DEMOGRAPHICS BEGIN
	clear_array = state_cultures
	add_to_array = { array = state_cultures value = 85 }
	set_variable = { species = 20 }
	set_variable = { minority = 19 }
	# LOK PAINTER DEMOGRAPHICS END
}
```

The 1,655 old startup assignment statements were removed. Runtime
`state_cultures`, `species` and `minority` names remain intact, as do global
culture-group catalogs, country species ideas, derived-modifier setup and later
gameplay conversions. Those are consumers/catalogs, not duplicate state setup.
All initial values were compared against the original evaluator and preserved.
Originals are under `backups/migration_20261124_101441_420939/`.

For another unmigrated checkout, generate and review a new stage **outside**
the mod, then apply it. The existing-stage apply checks all original/staged hashes
and makes backups; it refuses stale stages and reapplication:

```powershell
python -B migrate_state_setup.py --mod '<mod root>' --output '<new external staging directory>'
python -B migrate_state_setup.py --mod '<mod root>' --output '<reviewed staging directory>' --apply
```

This is initial undated setup. The painter does not simulate arbitrary events,
DLC conditions, dated bookmarks or every on_action. Moving definitions before
startup changes their availability to earlier startup scripts. Engine validation
in a fresh campaign remains required; none is claimed here. Native evidence:
`modding_documentation/wiki_doc/State modding - Hearts of Iron 4 Wiki.md`, History
section (state histories are effect blocks), and installed
`history/states/271-ethiopia.txt` (native `set_variable` effects in history).

## Flag maker

Choose one solid background and one optionally tinted flat Stellaris emblem.
Background and emblem colours are independent; Refresh colours applies entered
hex values. Only white/flat masks are read: Stellaris `flags/<category>/map/*.dds`,
Gigastructures `flags/flusionian/map/*.dds`, and existing EU4 painter
`stellaris_flags/emblems/*/*__mask.png`. Gold/gilded textures are never loaded.
No asset caches are created. Override paths with `--eu4-painter`, `--stellaris`
and `--gigastructures` if necessary.

| Size | Width × height |
|---|---|
| Large | 82 × 52 px |
| Medium | 41 × 26 px |
| Small | 10 × 7 px |

Dimensions come from the mod's actual `AAA.tga` flags. Masks retain their aspect
ratio and each native size is rendered independently. Existing external assets
remain in their local installations; none are bundled here.

## Validation

Run `python -B -m unittest discover -s . -p test_painter.py -v` from this folder.
The suite covers parser behavior, draft isolation, migration equivalence,
guarded saves, rollback, encoding, defined colours, stripes and flag masks.
`verify_real.py` checks current source data without saving its test drafts; use
`--mod '<mod root>' --output '<temporary diagnostics directory>'`.
See MODLOG.md for actual commands, results, existing map errors and UI checks.

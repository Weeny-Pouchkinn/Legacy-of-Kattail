# Legacy of Kattail Painter

Run `run_painter.bat` with Python 3.10+ and the packages in `requirements.txt`.
Install dependencies if necessary with `python -m pip install -r requirements.txt`.
The launcher disables bytecode generation.

## Painting

The interface follows the EU4 painter: native light controls, compact toolbar,
left palette and dark map canvas.

The main **MAP** tab contains these map tools. **CHARACTERS** opens the
character editor and its independent **Portrait definitions** library.

Dropdowns accept typing: search either the localized name or the internal ID.
Entries display `Name (ID)` wherever a localized name exists and sort by name.
Suggestions ignore case/accents and offer near matches for typos. Use Down/Up
and Enter, or click a suggestion; Escape closes the suggestions. Typing a full
unambiguous name or ID and pressing Tab also selects it. IDs remain the stored
values. Trait selection supports multiple traits with individual removal.
Countries, traits, ideologies, portraits, tags, species, cultures and ordinary
mode selectors use the same control. A portrait tag may still be entered as a
new three-letter value. Palette/source/emblem lists have matching search fields;
typing while a list has focus moves directly into its search field.

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
histories and other mod scripts. MAP contains Map, All source fields and Flag
maker subtabs. State forms scroll and flag previews fit narrower panes.

## Saving and source fields

All edits remain drafts until Save. Save writes changed text and portrait assets,
including edits in All source fields, after structural parsing and checking that each
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

## Characters and portrait definitions

**CHARACTERS → Characters** shows full-size portraits, sorted by localised name.
Choose **Nation** sorting for country sections, or filter a country and search
names/IDs. **Not recruited at start** includes characters with no unconditional,
undated recruitment in country history. Dated and conditional recruitment is
preserved; this editor does not simulate it. A character recruited by several
countries appears in each country's filter and sorts under its first tag.

Click a card to edit its name, description, art source, gender, starting country,
roles, traits and stats. Repeated roles remain independent. The role editor
includes the native script for conditions and fields beyond the basic controls.
Unknown existing fields are preserved. Changing the starting country changes
only undated `recruit_character` statements. Empty country means unrecruited.
New characters use `common/characters/zz_painter_characters.txt`.

**Portrait definitions** is a separate library of large/small pairs. Each has a
unique sprite ID, a three-character uppercase tag, art source and notes. The tag
can be any three letters; it need not identify a country. Tag edits change
grouping without renaming public sprites. Assign different pairs to civilian,
army and navy slots, and link additional variants for later use. **Create pair
and assign** opens the same portrait editor from a character. Multiple characters
can share a pair. Credits and extra variant links live in
`characters_painter_data.json`; descriptions use native English localisation.
Existing animated sprites retain their properties. The gallery uses their first
frame; importing a regular replacement image makes that sprite static.

Choose a large image and click **Generate small portrait** to preview the exact
Ministermaker transformation: resize to 37 × 51 px, rotate 5° counter-clockwise,
centre on a transparent 65 × 67 px canvas, then composite the supplied border at
(8, 1). The original Ministermaker border is bundled in `assets/`; its other
files are untouched. **Apply portrait pair** stages the preview; **Save** writes
it with a backup. Cancel discards the dialog's changes. You can also import a
hand-made small image. New large imports fit a transparent 156 × 210 px canvas;
small imports fit 65 × 67 px. Existing art is not resized merely by opening it.

Save dynamically organises `characters_l_english.yml` as `#TAG - neutral name`
sections sorted by tag, then by displayed character name with related strings
together. Unrecruited characters have an `UNASSIGNED` section. Existing authored
values, tokens and BOM are preserved. `lok_leader_portraits.gfx` groups native
sprite pairs by their portrait tag; simple sprites remain single-line entries.
Portrait files now use `gfx/leaders/large_portraits/` and
`gfx/leaders/small_portraits/`. All 1,408 moved originals retain their exact bytes;
42 additional small images were generated and two existing images reused.

Run both fixture suites from the mod root:

```powershell
python -B -m unittest discover -s legacy_of_kattail_painter -p 'test*.py'
python -B legacy_of_kattail_painter/verify_characters.py
```

The second command checks the migration snapshot against its original-byte
backup, all moved hashes, authored localisation, recruitment/roles and repeat
Save stability. Deliberate subsequent edits invalidate that snapshot. The exact
changed paths, hashes and pre-existing unresolved portrait references are in
`modding_documentation/agent_memory/plans/character-refactor-audit.json`.

## Character performance

Parsed files, localization, recruitment, trait/ideology catalogs and sprites
are reused until a relevant draft changes. Portrait decoding and gallery images
are bounded caches; changing stats or credits does not reload every portrait.
Unchanged identity fields are not reapplied when opening a role or assigning art.
The first role dialog loads native trait translations once (about 1 s in the
measured run); subsequent opens reuse them. Restart to incorporate external edits.

`python -B legacy_of_kattail_painter/benchmark_characters.py --profile` reproduces
the measured source operations using unsaved drafts and checks loaded source
snapshots afterward. It never saves sources. Omit `--profile` for ordinary timings.
See MODLOG.md for before/after measurements and separate actual Tk timings.

# Legacy of Kattail Painter

Run `run_painter.bat` with Python 3.10+ and the packages in `requirements.txt`.
Install dependencies if necessary with `python -m pip install -r requirements.txt`.
The launcher disables bytecode generation.

## Painting

The interface follows the EU4 painter: native light controls, compact toolbar,
left palette and dark map canvas.

The main **MAP** tab contains these map tools. **CHARACTERS** opens the
character editor and its independent **Portrait definitions** library.
**COUNTRIES** opens native country setup, ideological names/flags and starting
leaders, technologies and national spirits.

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

MAP > Flag maker sketches remain session-only. COUNTRIES > Flags drafts are
written by Save as native large/medium/small TGA assets.
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

This MAP sketchpad remains available. For persistent imports and patterned flag
editing, use **COUNTRIES > Flags** (documented below).

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

## Trait database and random commander rolls

Open **CHARACTERS → Trait database** for General, Admiral and Political advisor
traits (plus other unit traits such as operative/status definitions). The reader
loads both the installed game's and the mod's `common/unit_leader/` and
`common/country_leader/` files. Mod file replacements, including empty files,
are respected. Enable **Show overridden vanilla** to compare definitions that
the mod replaces. Names/IDs are searchable and sorted by localized name; source
files and active/overridden status remain visible.

**New trait** creates a definition with the supplied ID, name, description and
modifiers. Choose modifiers by localized name or code, enter their game-unit
value, and use **Add / update** or **Remove**. Military modifiers normally go in
`modifier`; the other native modifier blocks and direct trait stat bonuses are
also available. Political modifiers go directly on the trait. The picker shows
modifier categories; advanced nested effects, conditions, icons and special
modifier blocks remain editable in **Other fields and conditions**. Native
modifier documentation and both gameside/mod custom modifier definitions supply
the catalog. Names without a known translation use a readable ID-derived label.

Vanilla definitions are read-only. **Clone with new ID** copies one into the
mod, resolving its file-local constants first. Existing mod traits edit their
own source so existing public IDs/conditions are preserved. Added definitions go
into `common/unit_leader/lok_traits.txt` or
`common/country_leader/lok_traits.txt`, alphabetically by ID. Their names and
descriptions go into `localisation/english/painter/traits_l_english.yml` with
UTF-8 BOM and alphabetic keys. The distinct subfolder retains the requested
basename without writing over the installed file. Empty descriptions stay empty;
the editor invents no lore or traits. Files are created only when a new draft is
saved. Apply/Cancel, Undo/Redo and guarded Save work as for characters.

In a general/field-marshal/admiral role editor:

- **Randomize skills from current level** keeps the level and rolls its four
  base stats using active skill tables and level-up defines. With current
  vanilla rules the budget is `4 + 3 × (level − 1)`, each stat 1–10 and overall
  level 1–9. Land/naval fields differ. This editor policy excludes trait bonuses;
  it does not simulate all conditional game generation weights. Unsupported Lua
  expressions or incomplete skill tables produce an error instead of a guess.
- **Roll traits** selects the requested count of generic vanilla trait IDs that
  exist in the active mod setup. **Replace vanilla** replaces only eligible
  generic traits; **Add** retains them. Both retain custom traits, injuries/status
  and country-restricted/scripted traits. The roller avoids explicit
  incompatibilities, unavailable parents and restricted traits. Field marshals
  can also receive general traits. Roll results stay in the role dialog until
  Apply and are discarded by Cancel.

Fresh traits do not enter the game's automatic generation pool by default;
clones retain the source's generation rules. Assign fresh traits to a character
or explicitly edit their generation rules. Read-only
vanilla files are never written. Restart the painter to load these controls.


## Faster map painting (2026-11-24)

Restart the painter to load the optimized renderer. It now colors only the
visible viewport (with a small pan margin), samples province IDs before coloring,
and reuses geometry, static palettes, country colors, map images and wonder icons.
Painting applies each state immediately; map/inspector updates share a 25 ms
frame queue, with a final flush on mouse release. Repeated motion within an
already-painted state skips the brush. Save, state/region scope and undo retain
their existing behavior. All caches are in memory; no cache/data files are added.

In a same-run warm comparison at 25% zoom, culture redraw was 170.44 -> 17.75 ms,
species 281.82 -> 26.27 ms, owners 251.32 -> 25.75 ms and wonders
211.37 -> 15.64 ms. These are local redraw measurements, not guaranteed frame
rates or total stroke times. First loading a layer/icon can take longer.
See MODLOG.md for methodology and validation.


## Country editor

Restart the painter and open **COUNTRIES**. Select a country and choose **Edit
selected**, or use **New country**. The Owner palette's New/Edit buttons and a
double-click on a country in the source library also open this editor. **Paint on
map** selects the country for the Owner brush. Creating a country registers it;
assign its territory separately with the Owner brush.

The country form has seven tabs:

- **Setup**: tag, base name, map color, capital (search or **Pick on map**),
  stability/war support in percent, mobilization and economy laws, optional
  national economic model, national attribute and national species. New countries
  default to `volunteer_only` and `civilian_economy`. Escape cancels a map pick.
- **Parties & popularity**: ruling ideology and popularity values with a live pie
  chart in the ideology colors. Values must total exactly 100%.
- **Ideology names**: normal and DEF names for the base and each ideology. Copy to
  all or only undefined ideology fields; duplicate normal to DEF with/without
  `the`. Missing overrides inherit base names. Existing explicit empty strings
  count as defined and are preserved by the undefined-only action.
- **Flags**: import an image or use 17 editable background patterns, four colors,
  a separately tinted emblem and emblem sizing. Use the design, then copy to all
  ideologies or only those without an explicit flag. The three native sizes are
  written together: 82x52, 41x26 and 10x7, as RGB TGA. Base flags remain fallback
  flags. Saved flags are ordinary flattened images; design controls are session
  values, not separate metadata. You can remake a pattern or import its image.
- **Leaders**: recruited party leaders/candidates for every ideology. Quickly
  assign an existing character or create a native character with a name,
  description, portrait pair and subideology. Assignment explicitly promotes the
  character. Open the linked character editor for the full roles/traits/portraits
  interface. Existing other roles/recruitments remain unless edited there.
- **Starting technologies**: searchable native technology IDs with levels. Edits
  preserve original assignment positions, popup flags and conditional/dated
  scripts. New technologies join the first unconditional technology block so
  they precede equipment-variant creation.
- **National spirits**: searchable starting spirits and native create/edit with
  localized name, description, country modifiers and an icon. The icon browser
  lists both vanilla and mod sprites (including overridden vanilla alternatives),
  with lazy previews. Editing an existing spirit changes its shared definition.

The emblem selector reuses the white Stellaris masks, existing EU4 imported
emblems and emblems imported here. **Import reusable emblem** accepts alpha,
white-on-dark or dark-on-light masks. Imported masks become native DDS assets
registered in the existing miscellaneous GFX file, so they remain reusable after
restarting; flags themselves have no external image dependency.

**Apply country** stages an atomic draft. Nested leader, spirit and imported
emblem changes belong to that draft: Cancel restores them, and an accepted form
undoes as one action. **Save** writes the normal game files with guarded backups.
There are no new country/flag/spirit JSON catalogs or painter-specific game-data
files. New countries receive normal tag registrations, country definitions,
history and flags; existing countries keep their existing source filenames.

National species is stored as its native species idea in country history.
Native history flags make startup defaults respect explicit species and
attribute choices. Attribute research bonuses are copied from the existing
native templates and scoped to the edited country; unchanged countries keep
their original default setup. Unconditional starting setup is edited;
conditional/dated game scripts are preserved and are not a full campaign
simulation. No live-game validation is claimed. Exact files and checks: MODLOG.md.


### Visual flag library

In **COUNTRIES > Flags**, click the background or emblem arrow, double-click its
entry, or use **Browse backgrounds / Browse emblems**. Each opens a separate
thumbnail gallery with a larger preview of the full flag, using your current
colors, emblem tint and size. Click a tile to preview; double-click or choose
**Use selected** to apply. Cancel/Escape leaves the design unchanged.

Search matches names and codes, including near matches. The emblem window can
filter Stellaris masks, native imports, EU4 imports or No emblem. Arrow keys move
between tiles and Enter accepts. No emblem is a selectable tile. Only visible
rows are rendered, with bounded memory caches; no disk thumbnails/data files are
created. The ordinary entry fields still accept name/ID typing.

### States, strategic regions and victory points

Restart the painter. In **MAP > States / regions / VPs**, choose a database,
search its localized names/IDs, and double-click an entry. The State setup sidebar
also has **Edit state** and **Edit strategic region**. With the Inspect brush,
double-click the map to edit a state; in the **Strategic regions** view this opens
the region instead, including regions at sea. The States source library also
opens the state editor on double-click.

The state editor changes the displayed name, population, category, building-slot
multiplier, local supplies, impassability, resources, owner/controller, cores,
claims, culture/species and VPs. Buildings distinguish shared slots, nonshared
state buildings and province buildings. Choose a province by name/ID search or
on the map. Defined level limits, coastal requirements, facility groups,
exclusive buildings and required existing facility/dam map placements are checked
when applying. Supply nodes use `map/supply_nodes.txt`. Railway routes and map
building spawn positions are not generated here. State/province shapes are fixed.

Region membership moves **whole states**. Add an existing state to move all of its
provinces into the region. Removing a state requires another destination region;
an empty region or a split/unassigned state is rejected. Region indices, map
boundaries and region painting update with Apply/Undo. Sea provinces outside
states remain in their existing region. The region form also edits its localized
name, native naval terrain (for sea provinces, including mixed land/sea regions),
and weather periods, temperature ranges and phenomenon weights. Dates use the
game's zero-based `day.month` calendar. Weights need not sum to one.

**Import weather** reads a selected region from the installed vanilla game,
optionally shifting seasons by six months and importing its naval terrain. It
does not import province membership, IDs or names. There are 30
[Köppen-inspired climate classes](https://www.gloh2o.org/koppen/), each with North
and South variants. The classification reference is
[Beck et al. (2023)](https://doi.org/10.1038/s41597-023-02549-6); preset temperatures
and weather weights are editor approximations, not measured climate data or a
conversion of the published dataset. Apply a preset, then edit its monthly values.

Choose **View: VPs** (or **Paint: VPs**) and click any land province to add/edit its
VP name and positive integer value. Existing points can also be removed. The map
uses a blue-to-red gradient scaled to the largest VP, with markers and names plus
values at zoom 0.65 and above. **New VP on map** also works from the database or
state form. VP geometry is cached in memory; only nearby labels are drawn.

Names use existing native localization owners; state attributes/buildings and
VP values use their state histories, while region data uses
`map/strategicregions/*.txt`. Applying a VP consolidates exact base
`VICTORY_POINTS_<province ID>` names into the existing
`localisation/english/victory_points_l_english.yml`, sorted alphabetically by
displayed place name, then numeric province ID for ties. Original version markers
and inline comments are retained. Country-specific suffixed VP variants remain
in their original files; conflicting base names stop the operation. Removing a
point retains its authored name. Dated/conditional histories and unrelated script
fields remain intact.

Apply stages drafts; Cancel includes nested VP edits, and Undo/Redo work across
the native files. **Save** writes them with the existing guarded backups. No
painter-specific game-data files, JSON catalogs or disk thumbnail caches are
created. Validation details and limitations are in MODLOG.md.

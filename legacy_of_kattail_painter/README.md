# Legacy of Kattail Painter — first read-only prototype

Run `run_painter.bat` with Python 3.10+ and the packages in `requirements.txt`.
If needed, install them with `python -m pip install -r requirements.txt`.
The launcher disables Python bytecode generation. The painter reads the mod and
existing Stellaris/EU4-painter mask files; it writes no game data, flag files,
settings or asset caches. All UI edits are held in memory and discarded on close.

## Install in the requested folder

Extract this package outside the mod. From PowerShell in the extracted folder:

```powershell
python -B install.py --mod 'C:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
```

This creates `Legacy-of-Kattail/legacy_of_kattail_painter`. It refuses to overwrite
an existing painter folder. A session restriction prevented this installation
from being performed automatically.

To install the separately staged culture/species migration as well:

```powershell
python -B install.py --mod 'C:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail' --include-migration
```

Choose one installation command. Review `migration_patch/migration.diff` first.
All 1,903 affected original/staged file hashes are checked before copying;
originals are backed up and a failed copy restores them. Git can review/revert
the resulting changes. Installation is separate from the read-only application.
The installer does not launch the game, alter the descriptor or create a commit.

## Map and fields

The workspace follows the EU4 painter's native light interface: a compact
toolbar, left sidebar and dark map canvas. **Paint** selects the memory brush;
**View** selects the map overlay. The sidebar's **Sources** tab contains the
searchable library; **State setup** opens automatically when inspecting a state
and scrolls to keep all controls accessible. The main tabs contain the map,
all source fields and flag maker. Flag previews shrink to fit narrower panes.

- Inspect owners, states, provinces, terrain, continents, cultures, majority species
  and minority species. Click to inspect, wheel to zoom, right-drag to pan.
- Select a memory brush and click/drag over states to draft owner, culture,
  majority-species or minority-species changes. Choose the values in the state panel.
- Country/state library entries open their source fields. Select **All scripts**
  to access the mod's common, history, events, interface, map and metadata scripts.
- **All source fields** exposes nested fields and blocks with their complete scope,
  occurrence index and source line. This includes custom resources, buildings,
  ideology, coalitions, substates, colours, government variables, technologies,
  characters, special projects, space/colonisation data, food, WMDs, wonders,
  arrays, flags, diplomacy and arbitrary future custom fields defined in those files.
- Select a field, edit its value and apply to the memory draft. Edit whole blocks
  or add new custom fields without a fixed schema. Repeated effects remain separate.
  Whole-source drafts are also available; syntax checks are structural only.
- State culture lists retain their order and existing number of entries. The
  source currently has four states with three cultures; these are preserved.
- Undo/redo covers source drafts and state brushes. Session flag designs can be
  kept/restored separately using their country/ideology draft label.

The field inspector is a source editor, not a full HOI4 interpreter. Editing an
arbitrary script field does not execute its effects. Use the dedicated map forms
for demographic previews. Catalogs and initial ownership come from this mod's
files; inherited vanilla content, conditional/DLC evaluation, dated bookmarks,
event outcomes and effective runtime modifiers are not comprehensively resolved.
The painter does not edit localisation or binary topology in this prototype.

## Flag maker

One solid background colour and one optionally coloured flat emblem. Set the
background and emblem colours independently using the colour pickers or hex
values. **Refresh colours** applies manually entered hex values.

Only flat white masks are read: Stellaris `flags/<category>/map/*.dds`,
Gigastructures' `flags/flusionian/map/*.dds`, and existing EU4 painter
`stellaris_flags/emblems/*/*__mask.png` cache entries. Gilded/gold textures are
never loaded. No new asset cache is created in any source folder. Paths can be
overridden with `--eu4-painter`, `--stellaris` and `--gigastructures`.

Native preview dimensions, checked against the mod's actual `AAA.tga` images:

| Size | Width × height |
|---|---|
| Large | 82 × 52 px |
| Medium | 41 × 26 px |
| Small | 10 × 7 px |

Each size is rendered directly from the original mask without stretching it.
The small flag uses HOI4's observed dimensions even though its aspect ratio is
slightly different. White is the default emblem tint, not a fixed tint. There are
341 flat choices on the inspected installation, including Flusionian masks.
Assets remain in their existing local installations; none are bundled here.

## State-history migration experiment

`migrate_state_setup.py` stages initial definitions in each state's `history`:

```text
history = {
	# existing owner, cores, buildings, etc.
	# LOK PAINTER DEMOGRAPHICS BEGIN
	clear_array = state_cultures
	add_to_array = { array = state_cultures value = 85 }
	set_variable = { species = 20 }
	set_variable = { minority = 19 }
	# LOK PAINTER DEMOGRAPHICS END
}
```

The state files become authoritative. The old startup assignments, including
later startup overrides, are removed. `state_cultures`, `species` and `minority`
remain the runtime interface expected by existing mod scripts. The migration
does not rewrite country species ideas or gameplay conversion mechanics.

The evaluator handles the observed initial state/country scopes, owned-state
iteration, core/owner tests, nested scripted tag triggers, conditional species
tests, array membership, ordered culture additions, clears and later overrides.
Unknown constructs stop the migration rather than guessing. The staged values
are compared with the pre-migration evaluated snapshot for all 1,902 states.

This establishes static consistency, **not engine equivalence**. The evaluator
does not execute other on_action files, arbitrary scripted-effect calls or dated
ownership changes. Moving initialisation earlier may affect scripts that run
before the old startup blocks. Validate a new offline campaign and HOI4's logs
before accepting the migration; no game was launched in this session.

To regenerate a patch after source changes, use a new output directory:

```powershell
python -B migrate_state_setup.py --mod '<mod root>' --output '<new staging directory>'
```

The generator never modifies the input mod. It preserves original encodings,
BOMs, newline styles, unedited text and later gameplay on_actions.

## Sources and validation

Primary local sources inspected:

- `history/states/*.txt`, `common/country_tags/*.txt`, country histories and
  `map/definition.csv` / `map/provinces.bmp`.
- `common/on_actions/LOK_on_actions.txt`: initial culture additions starting near
  line 582; state species/minority initialisation near lines 2747–3255;
  species-dependent cultures and later demographic overrides through line 3737.
- `common/scripted_effects/LOK_culture_effects.txt`: runtime `state_cultures` readers/writers.
- `common/scripted_effects/LOK_scripted_effects.txt`: species-modifier routines
  `clear_all_state_species_modifier` / `apply_state_species_modifier`.
- `common/scripted_triggers/LOK_scripted_triggers.txt`: tag-based Herzlands triggers.
- Installed HOI4 `history/states/271-ethiopia.txt`, `history` block: native
  `set_variable` examples support placing species/minority variables in state histories.
- Existing EU4 painter `tools/culture_painter/stellaris_flags.py`, `_cached` and
  `render`: white-map alpha masks for flat emblems versus gilded textures.
- Mod `gfx/flags/AAA.tga`, `medium/AAA.tga`, `small/AAA.tga`: exact dimensions.

Run fixture checks: `python -B -m unittest discover -s . -p test_painter.py -v`.
See `verification/verification.json` for the recorded real-data UI/render/isolation
checks. No claim of in-game validation is made.

The inspected unit OOB files `EUL_1936.txt`, `GAL_1936.txt`, `KKN_1936.txt`,
and `KTZ_1936.txt` have pre-existing excess closing braces (net balances −2,
−4, −9 and −1). These four remain available as raw text; structured fields
cannot be shown until their syntax is corrected. No unit files were changed.

The fixture suite passed 11 tests. The hidden Tk check exercised current mod
data, state forms, undo/redo, source filtering and tintable flags. It rendered
1,023 mask/size combinations and verified 10,786 source-file hashes unchanged.

The staged files passed independent hash and content checks: all original state
text is preserved outside the new demographic sections. A disposable installer
fixture checked all 1,903 originals/backups and installed bytes. Stale input was
rejected before destination creation.

# National-spirit research and equipment bonuses - 2026-11-26

Added **Research bonuses** and **Equipment bonuses** tabs beside **Modifiers**
in the national-spirit editor. Restart the painter to load the updated form.

Choose a research category and enter its native bonus value, or choose equipment
and an equipment stat. Add/update and remove work independently in each tab.
Research `0.1` means a 10% bonus. Equipment values use native game units; negative
`build_cost_ic` reduces cost. No percentage conversion is silently applied.

Equipment timing is per target: **Immediately** writes `instant = yes`, **New
variants only** writes `instant = no`, and **Native default** omits the field.
The engine documents default/no as applying on new equipment variant creation.
New targets start with Immediately selected. Existing flags/omission load as
authored, and other stat values for that equipment are retained when one changes.

Apply stages the native spirit definition; main Save uses existing backups and
guarded writes. Cancel/Undo/Redo include the bonus changes. No live spirit or
historical setup was populated during this task.

## Exact files changed

| Repository path | Change |
| --- | --- |
| `legacy_of_kattail_painter/country_model.py` | Effective bonus catalogs, existing bonus reader, validation and targeted native writes |
| `legacy_of_kattail_painter/country_ui.py` | Research/equipment tabs, searchable choices, values, instant mode and row editing |
| `legacy_of_kattail_painter/test_spirit_bonuses.py` | Seven model/persistence/mapped Tk regressions |
| `legacy_of_kattail_painter/install.py` | Test distribution manifest |
| `legacy_of_kattail_painter/README.md` | User instructions |
| `legacy_of_kattail_painter/MODLOG.md` | Feature/validation record |
| `modding_documentation/agent_memory/CURRENT_STATUS.md` | Current result and game-check limit |
| `modding_documentation/agent_memory/DECISIONS.md` | Catalog and persistence decisions |
| `modding_documentation/agent_memory/plans/spirit-research-equipment-bonuses.md` | Completed milestones |
| `modding_documentation/agent_memory/spirit_research_equipment_bonuses/README.md` | This report |
| `modding_documentation/agent_memory/spirit_research_equipment_bonuses/verification.json` | Native UI/source-hash evidence |

No game IDs, localization keys, flags, runtime effects or metadata files were
introduced. Native script keys used are `research_bonus`, `equipment_bonus` and
the equipment-level `instant`. Future user edits change the spirit's existing
idea file; new spirits follow the existing `common/ideas/lok_misc_ideas.txt` path.

## Catalogs and preservation

The active installation supplies **139 research categories**, **393 equipment
IDs/type tokens**, and **57 equipment stats**. Categories come from effective
`common/technology_tags` lists. Equipment IDs/types and numeric stats come from
effective `common/units/equipment` definitions, supplemented by module
`add_stats`/`multiply_stats`. Known display/database metadata such as year,
priority and map-icon frame are excluded from stats. Labels use existing native
localization where available, with readable IDs otherwise.

Same-relative-path mod definitions, including empty files, override vanilla.
`replace_path` suppresses inherited folders. No descriptor changes were made.
MIO equipment-group names were not assumed valid in this separate idea field.

Read merges repeated base bonus blocks for the form. Untouched values keep their
original source, including variables. Changed scalar values update all matching
duplicate declarations; removals delete only the selected fields. Other stats,
comments, nested data and unrelated idea effects remain. Empty valid containers
may remain after removing their leaves, preserving attached source text. `None`
for either new optional API argument preserves that entire family, so existing
modifier-only callers retain the previous behavior.

## Native shape

```text
research_bonus = {
	infantry_weapons = 0.15
}
equipment_bonus = {
	infantry_equipment = {
		instant = yes
		soft_attack = 0.2
		build_cost_ic = -0.1
	}
}
```

This illustrates format only; those values were not seeded into the live mod.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_spirit_bonuses.py'`:
  **7 passed**. Covers effective/empty/replaced catalogs, module stats,
  optional-argument preservation, repeated native blocks, comments/variables/
  nested data, exact edited leaves, removal, invalid values/targets/flags with
  atomic failure, new spirits, Undo/Redo/native Save/reload and actual mapped
  bonus tab input/explicit instant modes/Cancel/Apply.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  **204 passed**. Existing country/spirit/trait/portrait workflows retained.
- `python -m py_compile` on `country_model.py`, `country_ui.py`, `install.py` and
  `test_spirit_bonuses.py` under `legacy_of_kattail_painter/`: passed. Cache
  redirected to system Temp using `PYTHONPYCACHEPREFIX`.
- Real native mapped Tk probe loaded `AUR_one_aircraft_rule_all`, including its
  existing two research categories and equipment target. New category search,
  equipment/stat selection, explicit `instant = no`, Add/Apply/Undo and Cancel
  passed while retaining unrelated bonuses. Live Save forbidden; **zero callback
  errors**, **4,324 native source hashes unchanged**. See `verification.json`.
- Installer file existence, task diff review, global and scoped `git diff --check`
  passed. New test/report files checked separately. Unrelated working-tree
  changes were retained.

No bitmap/state/topology edit was made, so map validation was not required.
**HOI4 and CWTools were not run.** The editor/native persistence path is tested;
actual research/equipment effect magnitudes and variant timing need a game check.

## Primary sources and next action

- `common/ideas/lok_attributes_ideas.txt:44`: existing mod research_bonus category
  usage, including nuclear/computing categories.
- `common/ideas/lok_AUR_ideas.txt:41` and nearby AUR entries: working-style native
  equipment_bonus equipment/stat/instant blocks, plus research_bonus blocks.
- Installed game root:
  `C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV`.
  `documentation/effects_documentation.md:1175` documents add_equipment_bonus as
  the same usage as ideas/national spirits; line 1189 defines instant's default
  and new-variant behavior.
- `common/technology_tags/00_technology.txt`: active research category schema.
- `common/units/equipment/infantry.txt` and `ship_hull_heavy.txt`: native equipment
  IDs/types/stat fields; effective module files supply additional stat names.

Restart the painter, author a research/equipment bonus, Apply and Save, then use
a fresh campaign to verify the spirit's research tooltip and equipment/variant
stats. No automatic change to production spirits is pending.

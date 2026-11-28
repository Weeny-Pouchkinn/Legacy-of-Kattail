# Land OOB editor and placeholder retirement - 2026-11-27

## Completed behavior

Land OOB is an independent map view/brush. The left palette has a searchable
country selector, source selector for variants, a template list/counts, Global
view, Place divisions/Edit division names actions, quantity, Copy template and
Division list. New/Edit template uses the existing palette buttons. Province
gradients and number labels show the selected country's selected template, all
its templates, or all nations/templates in Global view. Placement is disabled
in Global view. Viewport rendering, overlays and image export use MapConfig.

Left-click/drag places the entered number once per province; right-click removes
that many matching units. Shift picks an existing template. Amount is 1-1000;
placement requires an assigned land province but does not change ownership or
require it to belong to the country. Palette totals refresh at stroke release.
Edit division names opens all divisions in a clicked province; Division list
opens the full country/global list. Each row can receive a manual name, generated
name, or deletion. Done groups edits; Cancel rolls back the dialog's edits.

Template editor has full/short name and combat/support lists with native subunit
pickers, column/row editing and cell removal. It validates designer dimensions,
slot collisions, section types, support uniqueness and per-column battalion
groups. Dimensions come from the native/game mod defines. Subunits use effective
flat common/units/*.txt definitions and mod overrides; nested name databases
are deliberately not parsed as subunits. Copy template selects a source country,
OOB variant and template, then a destination name/short name. It copies template
fields without copying divisions. Renaming a template updates deployed references
while retaining division names. Unknown fields, unchanged cell attributes and
comments, air/naval blocks and instant effects are preserved.

Each template's shortened name is stored in a native comment:
`# LOK_PAINTER_SHORT_NAME = "Regulars"`. This adds no unsupported engine key.
Existing templates fall back to their full name until edited. New units receive
explicit native names: ordinal + current state localisation + short template
name. Numbering is per country/template, starting beyond current unit count and
existing numeric name prefixes. English suffixes include 11th/12th/13th/21st.
Existing authored and ordered-name blocks are preserved until edited. A manual
override removes division_name before setting name, keeping the two mutually
exclusive naming forms valid. Explicit regeneration is available per unit.

## Source and save safety

Country oob/set_oob/load_oob references are read with conditional/date context.
Default/global views count primary undated land OOBs, not all DLC/future variants
at once. Conditional/date sources can be selected explicitly for editing/copy.
Supplemental runtime/event loads and engine condition execution are not simulated.
References and parsed OOBs are cached by their actual dependencies.

Shared OOBs use copy-on-write: the first edit copies the complete file to
history/units/<TAG>_painter_land.txt (readable _2 suffix if needed) and changes only
that country's selected reference. Countries without an OOB receive a reference
when a template is first created/copied. All reference/file/template/unit edits
are grouped, undoable drafts. The existing tab-aware Save formatter, UTF-8/BOM
handling, source-conflict checks and backups remain authoritative. Native staged
probes never call Save. Save checks edited division/template references and new
land placement validity. No province geometry/IDs were changed.

## Explicitly requested placeholder cleanup

The user ordered removal of the KTZ_1936 placeholder. Removed references to its
land/air family, including obsolete commented air lines, from 19 histories:

AKR - Artilleriekatzenrepublik.txt; BKM - Bondskrijgsmacht.txt;
BLM - Blessed Mountain.txt; FKN - Freie Katzenrepublic Norddroogien.txt;
KKH - Katzenartig Kaiserliche Herrschaft.txt; KOT - Roquijgrad.txt;
KPE - Kapilan.txt; KRO - Kronk.txt; KSL - Kattensteinland.txt;
KTV - Nordkatzenvolk.txt; KTZ - Katzenartig Imperium.txt;
KVK - Katzenartig Vizekonigreich.txt; MAC - Maizeyrian Cornate.txt;
NDB - Nordblasterien.txt; NKR - North Kronk.txt; NRW - Ascarl.txt;
PMB - Pawmalay Bunker.txt; PRO - Propania.txt; YIN - Yinja.txt.

All are under history/countries/. Deleted history/units/KTZ_1936.txt and
history/units/KTZ_1936_air.txt; removed the obsolete generator special case from
generate_oobs.py without running that generator. These countries have no army
from this placeholder; no replacement deployments or lore were invented.

Guarded 22-file cleanup backup and exact before/after hashes:
legacy_of_kattail_painter/backups/remove_legacy_oob_20261127_230536_514574/
manifest.json. It contains original country/OOB/generator bytes. Existing
historical verification snapshots/backups were not rewritten as live content.
All active country-history references to the retired family are gone.
Unrelated user state/Imperium edits continue to be preserved.

## Other changed files and identifiers

- legacy_of_kattail_painter/land_oob_model.py (new)
- legacy_of_kattail_painter/land_oob_ui.py (new)
- legacy_of_kattail_painter/test_land_oob.py (new)
- legacy_of_kattail_painter/test_startup_safety.py (Save-hook fixture)
- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/map_render.py
- legacy_of_kattail_painter/model.py
- legacy_of_kattail_painter/install.py
- legacy_of_kattail_painter/README.md
- modding_documentation/agent_memory/plans/land-oob-editor.md (new)
- modding_documentation/agent_memory/land_oob_editor.md (this report)
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md

Python: LandOobStore, LandTemplate, LandDivision, OobSource, LandOobControls,
TemplateDialog, CopyTemplateDialog, DivisionsDialog, ordinal, grid_text.
MapConfig adds oob_template/oob_global/oob_source. Native division_template,
units/division, name, location and country oob/set_oob remain standard fields.
No new country tags, gameplay flags, localisation keys or script effects.

## Validation actually performed

- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_land_oob.py -v`:
  9 new tests pass: source/template/division discovery, names/ordinals, global
  counts, shared isolation, private-file collisions, template copy/rename links,
  comments/unknown fields, validation rejection without drafts, dated/conditional
  selection, Save/reopen, Undo/Redo, gradient/number rendering and actual Tk
  map clicks, right removal, global protection, template/copy/name dialogs.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py'`:
  all 267 tests pass, including the preceding optimization regressions.
- `python -m py_compile` on generate_oobs.py and the eight changed/new painter
  Python files passes with bytecode redirected to a disposable temp directory.
- `python -B tools/validate_map.py`: passes, 21515 provinces, 20926 assigned,
  413 regions and no X crossings.
- Native inventory after retirement: 144 primary land OOB references, 317
  country templates, 1939 divisions and 139 effective land subunit definitions;
  native designer grid 5x5 combat and 1x5 support.
- Native staged probe copied an AUR template to AKR, placed two named units,
  applied a manual name, formatted and validated drafts, confirmed global count
  +2, then Undid everything. Source OOB and AKR history bytes unchanged. Names
  followed ordinal/state/short format. No Save. Actual native Land OOB/global UI
  opened and rendered without callback errors or residual drafts.
- All 263 remaining oob/set_oob/set_air_oob/set_naval_oob declarations found in
  country histories reference existing files. No retired-family references in
  those histories or generator. Cleanup backup entries verified; all 61 installer
  manifest files present. Scoped complete diff/whitespace review performed.
- Post-feature `benchmark_painter.py` (no profile, no concurrent checks):
  Imperium strokes .038507/.030809/.031327 s; idea search .006229 s; first
  catalog 3.688519 s; picker .092386 s; spirit editor .352942 s. Same 4429 icons,
  zero source writes and external changes. Optimization gains retained. Earlier
  before/after profiles/caveats are in painter_optimization.md.

## Primary local references and limits

modding_documentation/wiki_doc/Division modding - Hearts of Iron 4 Wiki.md:
Land units, Division template and Division placement sections establish the
OOB loading, regiments/support coordinates, column-group rules and exclusive
name/division_name forms. Installed common/defines/00_defines.lua lines 864-868
give native designer dimensions; common/units/engineer.txt demonstrates support
group, infantry/armored_blimp_carrier examples land grouping. Native ACR/AUR/KTN
history/units files provide working patterns, extra effects and quoted names.

No fresh game was launched. Next concrete engine check is saving a chosen real
template/deployment and inspecting that fresh campaign's army/templates/names.
Advanced HQ/regimental-support/unknown fields are preserved but not exposed as
new dedicated form controls; future event/DLC OOB execution is not simulated.
Save ongoing work and restart the painter to load these code changes.

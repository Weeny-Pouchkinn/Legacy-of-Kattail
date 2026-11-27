# Land AI implementation

Date: 2026-11-26. Branch: Painter-Test.

## First live-log repair (2026-11-26)

1. [complete] Inspect the user's current log separately from old diagnostics.
   Nine template groups fail to read roles after empty blocked_for lists;
   1,967 runtime role-none messages follow. Also 12 construction pin_icon errors.
2. [complete] Replace empty AI-template filters with explicit, verified
   exclusions; restore the narrowly missing vanilla construction widget.
3. [static complete; fresh engine log pending] Add engine-hazard regression
   checks, run static/startup checks and inspect a fresh campaign log when
   available. Preserve the requested land balance changes and aircraft deferral.

The pre-fix live log has 2,125 lines: 90 invalid-tag tokens, nine missing template
roles, 1,967 role-none messages, 21 invalid order-assignment commands, 12 missing
construction pin icons, six external Workshop descriptor warnings and 20 dropped
commands. The tag-token sequence starts at each empty blocked_for and consumes
the role/priority tokens. This engine parser behavior was missed by the original
balanced-script validator; the old 2,080 scenario pass did not establish loader
compatibility. Invalid-order/dropped-command causality is not established from
the old log alone and requires comparison with the fresh run.

All nine filters now list PLR/HAR/KAR, verified in country_tags and already
excluded by conventional-country predicates. No role, composition, priority,
successor or readiness predicate changed in this repair. Added the exact
installed vanilla production_building_line_entry.pin_icon using existing
GFX_locked_icon and inherited CONSTRUCTION_MANUALLY_PLACED_TOOLTIP. No new
localization, sprites or country tags were added.

Files changed by the live-log repair:

- `common/ai_templates/generic.txt`
- `interface/countryconstructionsview.gui`
- `tools/validate_land_ai.py`
- `tools/validate_startup.py`
- `modding_documentation/agent_memory/CURRENT_STATUS.md`
- `modding_documentation/agent_memory/DECISIONS.md`
- `modding_documentation/agent_memory/plans/land-ai-implementation.md`

Validation actually performed for the repair:

- `python -B tools/validate_land_ai.py --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV" --baseline legacy_of_kattail_painter/backups/land_ai_20261126`
  passes: all 24 targets / 2,080 scenarios, nine valid nonempty tag filters,
  four unsafe filter fixtures rejected, references/encoding/source boundaries.
  The original failing source was separately supplied to check_country_filters
  and correctly rejected. The original failing engine log was supplied to
  check_engine_log and correctly rejected with counts 9/1,967/12.
- `python -B tools/validate_startup.py --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"`
  passes, now requiring pin_icon in the construction row and verifying its
  inherited sprite. Inherited tooltip verified in installed
  localisation/english/constructions_l_english.yml:106.
- `python -m py_compile tools/validate_land_ai.py tools/validate_startup.py`
  passes with PYTHONPYCACHEPREFIX redirected into the ignored repair backup.
- Reviewed each incremental `git diff --no-index` against pre-fix source copies;
  template structures are identical after removing only country-filter fields.
  The original clean-HEAD GUI bytes match the original land baseline manifest;
  extending that baseline with the same bytes permits a whole-GUI structural
  check proving only pin_icon was added.
- Source/log backup: `legacy_of_kattail_painter/backups/land_ai_error_fix_20261126/`
  (ignored). No diagnostic source or external Workshop descriptor was edited.
- Added optional `--error-log PATH` to the land validator for the observed role
  and pin failures. It requires a fresh caller-verified post-restart log; it is
  not a general claim that all warnings in the game are absent.

Fresh-run engine verification is pending. The user has been asked to restart,
start a fresh campaign, open Construction and advance roughly a week; do not
report the old log as cleared. External ugc descriptor warnings are out of scope.

## Authorized scope

- Change the eight ordinary land terrain widths and extra-direction widths from
  twice vanilla to 1.5 times vanilla. Preserve custom terrain with no vanilla
  counterpart, including choke points and planetary terrain.
- Remove only the anti_tank_equipment requirement of regular mechanized.
- Replace universal motorized infantry targets with affordable foot infantry;
  add explicit mobile, assault and staged armor compositions.
- Make land recruitment/production reflect small, regional and industrial
  economies, with a 2-4 equipped-division objective for armor-oriented regional
  powers. Preserve aircraft/naval scripts and production requests.
- Repair directly coupled land calendar, research and role mismatches; retain
  the existing tank families and do not introduce modern armor.

## Milestones

1. [complete] Inspect native/bundled/installed AI syntax, active IDs, initial
   clean Git baseline and validation tools; record original BOM/CRLF encoding.
2. [complete] Apply terrain/mechanized edits and staged land templates with
   stockpile/technology/manpower guards and reachable replacement chains.
3. [complete] Integrate capacity-based recruitment, armored replacement budgets,
   mobile escorts and land research; prevent old additive land policies from
   defeating the profiles. Preserve air/naval behavior byte-for-byte where edited
   files contain mixed systems.
4. [complete: static checks] Run targeted static/scenario validation, map validation, Python
   compilation and full task diff/encoding review. Document limits and any
   unavailable engine/CWTools checks without claiming gameplay validation.

## Evidence and implementation constraints

Read `.agents/rules/hoi4-modding-guide.md`, copilot instructions, current memory,
the earlier AI proposal, local AI-template documentation and installed 1.20.1
AI templates/strategy/trigger/script-constant documentation. Compare with bundled
vanilla examples rather than importing a full vanilla file. Installed game
version differs from descriptor supported 1.17.* / version 1.15.*; leave these
fields unchanged. Strategy weights are not guaranteed division counts. Native
typed army-size checks account for strength; regional goals are equipped-force
objectives and cannot promise an exact queue cap without engine observation.

Use native strategy enable/abort reevaluation, not new world-scan on-actions.
Keep all readiness/capacity logic in country scope. Avoid changing the current
special-project/species restrictions or generating narrative localization.
Use constants only in fields whose syntax supports them; file-local @ values
are appropriate for undocumented numeric AI fields.

## Implemented behavior

Ordinary widths now equal 1.5 times installed vanilla, including additional
attack directions. Plains/hills/desert are 105/52.5, forest/jungle 90/45,
mountain/marsh 75/37.5 and urban 120/60. No custom terrain, map membership or
binary map asset changed. Regular mechanized needs exactly 40 mechanized and
100 infantry equipment; power_motorized retains its separate AT requirement.

The 24 targets have one owning group per role. Important formations:

| Role/stage | Line battalions | Width |
| --- | --- | --- |
| Small-country line | 6 infantry | 12 |
| Regular line | 9 infantry | 18 |
| Industrial line after 104 | 10 infantry | 20 |
| Mobile | 6, then 10 motorized | 12, then 20 |
| Light armor bridge/starter | 3 light + 3 motorized, then 4 + 6 | 12, then 20 |
| Medium starter | 4 medium + 6 motorized | 20 |
| Main medium after 104 / 50 factories / improved hull | 7 medium + 8 motorized | 30 |
| Mechanized armor with 70 factories and logistics | 7 medium + 8 mechanized | 30 |
| Assault armor after 108 / 100 factories / SPG prerequisites | 7 medium + 9 mechanized + 1 medium SPG | 35 |
| Infantry assault | 9 infantry + 1, then 2 artillery | 21, then 24 |
| Selected power infantry, 70 factories and researched unlocks | 8 infantry + 2 power infantry, then 6 + 4 | 20 |
| Static garrison | 5 infantry; engineers for industrial countries | 10 |
| Occupation | 9 cavalry; researched MP upgrade | Not field-combat tuning |
| Mountaineers | 10 mountaineers, then 11 + 1 artillery | 20, then 25 |
| Marines | 9 marines; existing gated 4-amphibious/6-amphibious-mechanized alternative | 18, then 20 |
| Paratroopers | 9 paratroopers | 18 |

Small economies have fewer than 10 military factories and no positive armor,
mobile or assault recruitment contribution from the new conventional policies.
Regional economies have 10-29. Armor-oriented regional countries have appropriate
tank/motorized research and either mobile-warfare doctrine, inherited armor, or
at least 20 factories plus medium-tank research. Their armor demand turns off at
two equipped divisions for 10-19 factories, or four for 20-29. These are native
strength-aware demand objectives, not a hard ceiling on queued units.

Industrial economies start at 30 factories: armor role weight 12, mobile 8;
70-factory economies add 6 armor weight. Existing land doctrine contributions
that would bypass those goals are neutralized while foot-infantry preferences,
air effects and Force Concentration hooks remain. The year-1940 land template
switch now uses 104. Large industrial countries with armor gain an additional
10-point native Force Concentration contribution. No troop micro script added.

Recruitment weights do not depend on a stockpile being consumed by the queue.
Field-conversion guards require manpower and equipment reserves. Limited
archetype-specific production floors replenish rifles, support, artillery, AA,
tanks and trucks, plus researched mechanized/SPG/exoskeleton reserves where
appropriate. Buffer targets exceed conversion thresholds, avoiding a circular
dependency where an upgrade waits for equipment that no unit yet demands.
Native deficits remain the main production driver; floors are temporary minima.

Land research guidance follows both DLC technology namespaces, including an
armor-research bootstrap for countries that do not yet own tank technology.
Small countries without inherited armor do not spend XP on tank designs.
Existing armor can still be developed. Basic medium designs gain a three-man
turret, radio and medium-gun candidates; guns fit through the turret's category
extension. The two obsolete modern-family prescriptions are explicitly disabled.
No new tank, equipment, module, technology or localization ID was introduced.

Paluush/non-playable countries are excluded from new conventional targets and
policies. Existing special-project restrictions remain. No aircraft/naval
equipment, research, target design or policy effects were changed; land production
priorities can naturally affect the remaining factory budget.

## Exact changed files

- `common/terrain/00_terrain.txt`
- `common/units/infantry.txt`
- `common/ai_templates/generic.txt`
- `common/ai_strategy/default.txt`
- `common/ai_strategy/doctrines.txt`
- `common/ai_strategy/lok_land_ai.txt` (new)
- `common/scripted_triggers/lok_ai_land_triggers.txt` (new)
- `common/ai_equipment/generic_tank.txt`
- `interface/countryconstructionsview.gui` (live-log pin repair)
- `tools/validate_land_ai.py` (new)
- `tools/validate_startup.py` (live-log pin regression check)
- `modding_documentation/agent_memory/plans/land-ai-implementation.md` (new)
- `modding_documentation/agent_memory/plans/ai-competence-proposal.md` (historical-status annotation)
- `modding_documentation/agent_memory/CURRENT_STATUS.md`
- `modding_documentation/agent_memory/DECISIONS.md`

Important identifiers: retained the seven original role groups and their active
target IDs. Added `mobile_generic` for the already-requested `mobile` role and
`infantry_assault_generic` / `infantry_assault`. New target IDs include
`infantry_basic`, `light_armor_expanded`, `medium_armor_mechanized`,
`medium_armor_assault`, `mobile_early`, `mobile_standard`,
`infantry_assault_early`, `infantry_assault_mid`, `infantry_power_early`,
`infantry_power_mid`, `garrison_supported`, `suppression_with_police` and
`mountaineers_assault`. New country predicates and policies use `lok_ai_land_`.
No flags, saved variables, events, namespaces, on-actions or sprites were added.

## Validation record and limits

- `python -B tools/validate_land_ai.py --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV" --baseline legacy_of_kattail_painter/backups/land_ai_20261126`
  passes: 24 targets; 2,080 capacity/date/DLC/stockpile/doctrine/strength scenarios;
  additional missing-tech, single-family, restricted-country and inherited-armor
  checks; unique IDs, acyclic successors, equipment/tech/unit references, correct
  support placement, reserve reachability, module/category tokens and turret
  category compatibility. All six armored targets average at least 30 base
  organization including their specified supports. This is not an engine simulation.
- The same command checks exactly 1.5 times installed terrain widths, untouched
  custom terrain, no unrelated battalion/terrain changes, preserved original
  native CRLF/BOM behavior, and unchanged non-land policy structures. Against
  the initially clean HEAD, seven existing native sources changed (including
  the live-log GUI repair) and two were added; all other 4,354 original native
  sources remain unchanged.
- `python -B tools/validate_map.py` passes: 21,515 provinces, 20,926 assigned to
  states, 413 strategic regions, no X crossings.
- `python -B tools/validate_startup.py --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"`
  passes: 56,544 unique localization keys/layers, GUI/startup/history/equipment
  checks; 159 modern and 53 basic technology contexts. “Modern” in this validator
  labels starting-equipment contexts, not the excluded modern-tank family.
- `python -m py_compile tools/validate_land_ai.py` passes.
- `git -c core.fsmonitor=false diff --check`, `git -c core.fsmonitor=false diff --stat`
  and the complete task diffs, including new files via `git diff --no-index`, are
  reviewed. No unrelated pre-existing edits existed at task start. No new
  localization or graphics were generated.
- CWTools CLI is unavailable (`shutil.which('cwtools')` returned None). No parser
  configuration was changed. No game launch, live observer run or in-game
  template/production/deployment test was performed.

Baseline recovery: the first temporary snapshot was inaccessible from subsequent
sandboxed commands. The retained comparison baseline was recovered from the
verified clean starting Git HEAD with the original native CRLF/no-BOM encoding,
then checked against tracked source paths. It is under ignored painter backups;
no generated diagnostics or bytecode are added to Git.

Remaining engine verification: start fresh campaigns with small, armor-oriented
regional and industrial countries. Use `imgui show ai_templates` and
`imgui show ai_division_production`; observe actual field conversion, research,
production, strength-aware 2/4 demand transitions, training-queue overshoot,
replacement supply and AIFC use through years 104/108. Include supported DLC
routes. Static DLC eligibility does not establish the underlying pre-existing
non-NSB equipment pipeline works in game. Values are initial tuning, not proven
balance. Aircraft remain explicitly deferred.

## Primary syntax counsel

- [Bundled vanilla target-template documentation](../../vanilla_folders/vanilla_common/ai_templates/_documentation.md),
  sections “How do AI templates work?”, “Examples”, `enable`,
  `can_upgrade_in_field`, `replace_with`, `replace_at_match`, `target_min_match`.
- [Bundled generic vanilla templates](../../vanilla_folders/vanilla_common/ai_templates/generic.txt),
  armor/infantry/garrison/suppression/mobile structures; installed
  `common/ai_templates/generic.txt` for current regimental-support differences.
- Installed `common/ai_strategy/_documentation.md`, lines 233-280 (AIFC),
  474-514 (category/archetype-specific production and surplus) and 594-640
  (research/unit/XP guidance), under the game root passed in the commands above.
- Installed `documentation/triggers_documentation.md`, headings
  `has_army_size`, `has_equipment`, `has_manpower`, `num_of_military_factories`.
- Manually inspected the installed CWTools extension's cached HOI4 schemas
  under `C:/Users/elowi/.vscode/extensions/tboby.cwtools-vscode-0.10.31/.cwtools/hoi4/Config/`:
  `triggers.cwt`, `alias[trigger:has_army_size]`, accepts equipment-category types;
  `common/terrain.cwt` declares both width modifiers as floats; `ai_strategy.cwt`
  declares the archetype-specific production-floor rule. This is schema counsel,
  not a CWTools diagnostics run.
- Installed `common/ai_equipment/_documentation.md`, role/priority/enable,
  target variant slot/category matching and allowed-module semantics.
- Current [mod medium turret](../../../common/units/equipment/modules/00_tank_modules.txt),
  `tank_medium_three_man_tank_turret.allowed_module_categories`, and
  [chassis research](../../../common/technologies/LOK_NSB_armor.txt) for actual
  slot extensions and unlocks. No module list was imported from another version.

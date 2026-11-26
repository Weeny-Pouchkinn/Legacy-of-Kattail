# AI competence and force-development proposal

Date: 2026-11-26. Inspected branch: `Painter-Test`.
Status: reconnaissance and proposal complete; implementation not requested or performed.

## Recommendation

Build a small set of coherent military profiles that connect research, equipment
design, factory allocation, division composition, field upgrades and offensive
deployment. Prioritize a supplied army with functioning armor and air support
over maximizing division count. Use existing engine AI systems before adding
scripted machinery. No new global daily/weekly/monthly scans are proposed.

The user excludes modern tanks. This proposal therefore does **not** use the
vanilla `modern_armor` / `modern_tank_chassis` family. There is a terminology
conflict worth preserving explicitly: the mod calls `medium_armor` a Main Battle
Tank and its medium chassis MBT chassis. Here “medium” means that existing family;
it does not mean adding another tank class or changing the setting. Existing
light armor is an IFV and heavy armor a Siegebreaker. [R6, R7]

All compositions, industry thresholds, readiness targets and allocation shares
below are **initial balancing proposals**, not measured optima. Online vanilla
advice supplies candidates; this mod's equipment costs, support system, terrain,
calendar and special units determine whether they work.

## 1. Findings established from current source

| Finding | Evidence | Consequence / recommended response |
| --- | --- | --- |
| Land templates use non-NSB tank technology checks. | `armor_generic` checks `basic_medium_tank` and `improved_medium_tank`. AUR's history grants the corresponding `_chassis` technologies instead when NSB is enabled. [R1, R3, R4] | The intended priority multipliers do not activate from the NSB grants. Support both active research routes in template eligibility; do not infer that armor is completely unavailable. |
| Some early/late strategies still use WWII dates. | The early template strategy runs before 1940; the later one after 1940. The campaign runs from 100 to 120. [R2, R5] | The early strategy stays enabled throughout the normal campaign and the later strategy never activates by date. Audit remaining 1938/1939/1940 checks in the same file. Translate by intended stage, not a blind numerical offset. |
| The generic infantry role is actually motorized. | Early target: nine motorized plus one motorized artillery battalion; later: nine motorized, two motorized artillery and one motorized AT. Both have several support elements. [R1] | Potentially sensible for an industrial power, but a costly universal target for weak countries. Introduce affordable line infantry and a separately budgeted mobile role. |
| Armor targets have a limited progression. | Active targets are 5 light + 5 motorized, 4 medium + 4 motorized, then 6 medium + 6 mechanized. The last also requires `armored_car1` for its priority. [R1] | Test a clearer 20-width starter and 30-width main formation. An optional recon technology should not gate the entire mature armor target. |
| A mobile role is requested without a dedicated target group. | `default_mobile_production` requests `type = role_ratio`, `id = mobile`; the seven active groups target armor, garrison, suppression, infantry, mountaineers, marines and paratroopers. [R1, R2] | Add a deliberate mobile target and verify existing division role assignment in the debugger; a weight alone does not define the intended composition. Doctrine strategies also use motorized/artillery role tokens and need the same audit. |
| Progression thresholds need observation, not blanket replacement. | Several `replace_at_match` values are 1.5; comments explicitly say this leaves transition to priority changes. The light target allows field upgrades when light-chassis stock is below 500. [R1] | 1.5 is not automatically a syntax bug. Verify priorities and field conversion in both DLC routes. The low-stock condition is a suspicious readiness rule, not proof of a runtime failure. |
| Garrison and suppression templates spend poorly. | Garrison: four motorized plus engineers. Suppression: four infantry plus MP. [R1] | Use cheap foot troops for static defense. Benchmark cavalry/MP for occupation; keep occupation and map defense as separate roles. |
| Aircraft and naval design prescriptions are absent. | Both generic plane and naval AI files contain zero non-comment code lines. Their vanilla directory is replaced. [R8, R13] | This does **not** mean the AI cannot produce fixed aircraft. It means there are no active mod-authored fits in these files; modular designs must be restored alongside the designer. |
| Aircraft production instructions overlap. | Always-enabled default production and `bba_air_prod_1` both contribute fighter/CAS/bomber requests. [R2] | Consolidate the intended profile or account explicitly for the combined contributions. Strategy values are weights/modifiers, not a literal factory percentage budget. |
| There is little explicit research-profile coverage. | Only `AUR.txt` exists in `common/ai_strategy_plans`; the descriptor replaces `common/ai_focuses`, for which no mod directory exists. Technologies still have their own AI weights. [R3, R13, R14] | Restore deliberate research guidance. Do not describe this as “AI never researches”: technology-level `ai_will_do` still exists. |
| The obsolete modern family has active AI prescriptions but no active technology equipment unlock was found. | Modern AI groups remain in `generic_tank.txt`; a comment-aware scan of all active technology `enable_equipments` found no modern-tank entry. [R7, R9] | Exclude these targets from the redesigned profiles; preserve unrelated source until its references have been audited. Do not use modern tanks as the late-game upgrade destination. |
| Force Concentration is already partly wired. | Doctrine strategies use `force_concentration_factor`, including the mobile-warfare chain. [R10] | Verify that actual doctrine/track IDs activate the intended strategy, then tune concentration and targets. Do not claim the feature needs to be invented. |

Tank design data is not wholly missing: ordinary light/medium/heavy designs,
tier-four designs and basic walker fits already exist. A comment-aware inventory
of all module containers found **no unknown module/category token** in their
slot prescriptions or allowed-module lists. That does not establish legal slot
fit, researched availability, good performance or correct production. Improve
the existing design groups rather than replacing them on the assumption that
all their IDs are broken. [R9]

## 2. What the online advice contributes

- The author of the [StratemGames tank guide](https://stratemgames.space/en/hearts-of-iron-iv/clusters/everything-about-divisions/complete-division-guide/best-division-templates/best-tank-division-template-2026)
  reports testing 20-width 4-medium/6-motorized and larger 36-width formations.
  See “Tank division, 20 Combat Width”, especially its composition and template
  overview; retrieved lines 115-126. It is a useful affordable starting candidate,
  not proof of performance in this mod.
- The author's [infantry guide](https://stratemgames.space/en/hearts-of-iron-iv/clusters/everything-about-divisions/complete-division-guide/best-division-templates/best-infantry-template-2026),
  “Quick Summary” and “Which template should you choose?”, retrieved lines 23-55,
  distinguishes cheap defensive infantry from expensive offensive formations.
  Adopt the separation of jobs; do not adopt every template or armor-in-infantry
  exploit as a default AI requirement.
- [Recent player discussion of fighter designs](https://www.reddit.com/r/hoi4/comments/1wr73h3/psa_do_not_put_twin_engines_on_your_fighters/),
  opening post and cannon/HMG replies, retrieved lines 17-100, favors affordable
  single-engine fighters with guns, protection and range. Replies disagree about
  the cannon transition. Treat it as candidate selection, not a controlled result
  or justification for copying WWII labels into this setting.
- The [Expert AI author's description](https://steamcommunity.com/sharedfiles/filedetails/?id=741805475),
  “Description”, retrieved lines 202-255, describes coordinated research,
  production and design choices and explicitly rejects compatibility with major
  overhauls. Borrow that architectural idea; do not install or copy the mod as a
  compatible drop-in. Its broad claims about tactical limitations should not
  override newer engine Force Concentration capabilities.
- Paradox's [Developer Diary: Small Features](https://store.steampowered.com/news/posts/?appids=394360&enddate=1731506437&feed=steam_community_announcements),
  dated 21 October 2024, section “AI Force Concentration”, explains concentrated
  armies, targets such as supply hubs, and routes that consider terrain and
  railways. The installed strategy documentation confirms the current script
  controls. [R15]

Live `https://hoi4.paradoxwikis.com/AI_modding` returned HTTP 401 during this
research. Engine syntax claims therefore use installed primary documentation,
not unverified search snippets or third-party summaries.

## 3. Template families to benchmark

The mod's ordinary terrain widths are plains/hills/desert 140, forest/jungle
120, mountain/marsh 100 and urban 160. Custom tunnels/bridges/volcanic terrain
are 40, frozen terrain 70 and salt 180. Meogartha is an exceptional width 2.
No terrain changes are proposed. [R11]

This matters: 30-width divisions fill forest width with four units; four
35-width divisions fill plains. Twenty-width divisions fit both 120 and 140
exactly. Those are arithmetic packing observations, **not** a complete combat
model: reinforcement, extra attack directions, targeting, penalties, doctrines
and supply can change the result. Twenty-five-width specialists fit mountain
width four times, but lose that neat fit on the 40-width custom terrain.

All widths in this table use the mod's current battalion definitions before
doctrine changes. Artillery and SP artillery remain **3 width here**; do not
import a guide's assumed 2-width SPG calculation. [R12]

| Purpose | Candidate line battalions | Width | Support policy and progression |
| --- | --- | --- | --- |
| Emergency/static defense | 5-6 infantry | 10-12 | No truck requirement. Engineers only where affordable; do not use as the industrial major's permanent main army. |
| Regular line infantry | 9 infantry, then 10 infantry | 18, then 20 | Engineers, support artillery when affordable; support AA where air defense is needed. Keep upgrades affordable and preserve line coverage. |
| Fire-support infantry | 9 infantry + 1 artillery; optional 9 + 2 | 21; 24 | Separate offensive profile for countries lacking sustainable armor. Compare IC and supply losses against support-only infantry before adopting it widely. |
| Mobile exploitation | 10 motorized; alternate 9 motorized + 1 motorized artillery | 20; 21 | Engineers and affordable fire support. Logistics when fuel/supply demand justifies it. This fills gaps and follows armor; it is not the primary breakthrough force. |
| Starter armor | 4 existing medium armor + 6 motorized | 20 | Engineers; support artillery if useful; AA if needed. Upgrade vehicles first rather than immediately adding every support company. IFV-focused countries can use the existing light family as their chosen armor profile. |
| Main armor | 7 existing medium armor + 8 motorized; progressively replace motorized with mechanized | 30 | Engineers, logistics and situational AA; maintenance where its equipment savings justify the slot and cost. Keep at least 30 organization after all actual supports/doctrines; seek 35-40 where affordable. |
| Optional major-power assault armor | 7 medium armor + 9 mechanized + 1 medium SP artillery | 35 | Experimental plains-oriented alternative, not an automatic upgrade for every country. Reject if organization, replacement cost or supply performance is poor. |
| Mountain force | 10 mountaineers; optional 11 mountaineers + 1 artillery | 20; 25 | Test artillery's terrain dilution. Keep a smaller option for narrow/custom terrain; obey special-forces limits. |
| Marines | 9-10 marines | 18-20 | Engineers/pioneers only if actually unlocked and supported. Amphibious vehicles are an industrial alternative after the whole equipment chain is available. |
| Occupation suppression | Cavalry, initially 8-10 battalions; MP only when its savings justify the cost | Not a combat-width optimization | Benchmark manpower and IC per suppression, including resistance losses. Do not add engineers or combat artillery to this occupation template. |

These templates retain infantry alongside armor deliberately. Current medium
armor has base organization 10 and strength 2; motorized has 60 and 25,
mechanized 60 and 30. A tank-only formation would sacrifice staying power and
replacement economy. The 7/8 candidate has about 36.7 base organization using
line battalions alone; actual displayed organization must be checked after all
support, doctrine and country effects. [R12]

Do not give every template every support company. In particular, mechanized
already needs **50 AT equipment per battalion** in this mod: eight mechanized
battalions require 400 AT equipment before optional AT support. Additional AT
should follow a demonstrated piercing shortfall. Recon and signals need to earn
their IC/organization/XP cost; they are not mandatory filler. [R12]

## 4. Make infantry improve without bankrupting the army

Use three independent progressions:

1. **Equipment quality:** keep researching the relevant rifle/support weapons,
   artillery, AA/AT and support-company improvements, and put their output into
   deployed formations. New equipment does not require changing every battalion.
2. **Organization of the force:** expand small line divisions to the supported
   18-20-width standard, then add justified support. Preserve cheap secondary
   troops and adequate front coverage rather than enlarging all divisions at once.
3. **Mobility and specialist modernization:** industrial countries build a mobile
   arm and mechanize armor escorts. Selected units can progress to existing power
   infantry; this is not a universal replacement of ordinary infantry.

Use years 100/104/108 as planning stages, but eligibility must also require the
actual technology, equipment, manpower and economic capacity. A country that
conquers industry can change profile; an exhausted major must stop expanding.

For exoskeleton users, the current unlock is `exoskeleton_1` in year 102, with
equipment improvements in 106 and 110. A candidate progression replaces two,
then four motorized battalions with `power_motorized` within selected formations.
Each such battalion additionally requires 100 exoskeletons and 50 AT equipment.
Measure the result against mechanized before choosing the preferred path.
Meowrines require their existing special-project route; ordinary research is
explicitly blocked and has AI weight zero. Do not bypass that gate. [R16]

The upgrade mechanism should use native `enable`, `upgrade_prio`, `replace_with`
and `can_upgrade_in_field`. Include intermediate targets that match starting
OOBs sufficiently well; AUR starts with 9-infantry regulars and a 3-light/
3-mechanized armored template, not the generic target. Set conversion readiness
from the full equipment delta, reserve needs and manpower cost. Avoid converting
an army during a supply or replacement crisis. Engine eligibility alone does not
establish that a proposed bulk conversion is prudent. [R4, R14, R17]

## 5. Produce a sustainable armored arm and use it

Assign a coherent profile from economic capacity, existing forces, available
resources, geography, doctrine and authored country restrictions. Suggested
starting bands for testing:

| Capacity | Desired behavior |
| --- | --- |
| Fewer than about 10 military factories | Maintain the line and replacements; no compulsory tank or aircraft industry. Preserve useful inherited equipment. |
| About 10-30 military factories | Choose a limited armor or air investment once essentials are covered. An armor-oriented regional power aims initially for 2-4 equipped 20-width formations, rather than a quota of empty divisions. |
| About 30-70 military factories | Sustain a distinct armored arm and mobile follow-up force; test armor at roughly 10-15% of deployed divisions where supply and front coverage permit. |
| Above about 70 military factories | Test roughly 15-20% armor, substantial aircraft production and selective mechanization. Higher armor shares require evidence of affordable replacement and useful terrain. |

These are proposed observed army compositions, **not literal `role_ratio`
values or guarantees**. Existing additive strategy and doctrine weights must
be included when translating them to script. Division-count shares also understate
the IC share of large armored formations.

For a land-oriented major, one starting **military production** budget to test
is 35% line equipment/support/AA/AT/artillery, 20% armored vehicles, 15% trucks/
mechanized, 20% fighters and 10% CAS. This excludes dockyards and is a calibration
reference, not a universal hard allocation. Raise replacements and logistics
first when losses or supply demand make that budget unsustainable. Aircraft
capacity, fuel, imported resources and actual equipment costs can change it.

The existing fixed buffer of 500 supply trucks/20 trains is a useful starting
mechanism but should be evaluated against small countries and expanding fronts.
Reserve trucks for logistics before promising them to new motorized units.
Use equipment needs, training queues, projected upgrade deltas and replacement
losses to calibrate factory requests; halt expansion when existing units cannot
be equipped. Use separate enter/exit thresholds to avoid repeated profile and
production switching. [R2, R15]

For deployment, use existing **AI Force Concentration**. Check actual doctrine
IDs and the cumulative concentration factor, then tune `front_armor_score`,
`force_concentration_front_factor` and `force_concentration_target_weight` where
documented and appropriate. Direct attention to useful fronts and verified supply
hubs/ports; reduce the attraction of hostile terrain and unaffordable fronts.
Do not invent state IDs or promise perfect encirclement micro. AIFC operates on
forces available after minimum front needs; producing an army that barely holds
its frontage may leave no useful offensive reserve. [R10, R15]

## 6. Improve armor designs within the existing families

Retain existing group IDs where practical and give each profile a small number
of sensible designs:

- **General combat medium:** current medium chassis, researched gun with adequate
  soft attack and piercing, appropriate turret, radio and engine. Avoid maximum
  armor/engine upgrades without checking the cost, reliability and speed result.
- **IFV/light family:** cheaper mobile force and support where its actual combat
  economics justify it. Do not assume vanilla light-tank advice transfers to the
  mod's IFV role unchanged.
- **Siegebreaker:** selected industrial/doctrine profile, not a second compulsory
  armored production tree for every country.
- **SP artillery / tank destroyer:** optional answers to measured firepower or
  piercing needs. Avoid creating another vehicle line without real demand.

For initial testing, target roughly 8 km/h for a mobile armored division where
the current vehicles can afford it, and roughly 80% reliability as a conservative
baseline. These are targets to compare against cost and attrition, not universal
minimums. The division is limited by its slowest relevant component; measure the
finished formation, not just its tank engine upgrade.

Prefer consistent weapon/engine technology upgrades and long-lived production
lines. Update a design for a useful chassis/weapon improvement, not every tiny
available change. Budget army XP across doctrine, templates and equipment; observe
whether an otherwise legal target is starved of XP. [R9, R15]

Continue medium/light/heavy development along their existing 100/104/108 and
gated 112 chassis tiers where available. Atomic tiers are optional existing
content, never a dependency on the excluded modern family. Walker profiles are
separate optional experiments after ordinary armor works; retain their project
and locomotion gates and validate their roles/production independently. [R6]

## 7. Aircraft: improve today's system, then connect the restored designer

The current air tree unlocks fixed aircraft tiers. Generic modular AI is
commented out, and the previous designer-restoration investigation is still a
plan. Do not claim to fix today's air force by pasting module fits into dormant
airframe research. [R8, R18]

**Immediately useful work:** give each economic profile a fighter/CAS research
and production path using equipment it can actually build. The current fighter
progression is `fighter1`/`fighter2`/`fighter3` in 100/104/108, then gated jet
technologies. Prefer upgrades of useful aircraft tiers, replacement of losses,
adequate airfields, fuel and range. Use existing legacy variant upgrades only
where the effective equipment actually exposes them; confirm inheritance rather
than assuming every tier supports the same upgrade block. [R18]

Limit broad bomber diversification: continental powers emphasize fighters and
CAS; distant theaters may justify tactical bombers; maritime profiles get naval
aircraft; strategic bombers require spare industry and a real mission. Carrier
aircraft demand follows actual carrier capacity. Small countries should not be
forced to sustain five competing aircraft categories.

**After the designer proof succeeds:** restore a few legal AI fits using only
existing modules and the final supported frame IDs:

| Role | Design objective |
| --- | --- |
| Budget fighter | Affordable researched engine, efficient air-to-air armament, useful range, affordable protection; no unnecessary second engine. |
| Main fighter | Improve air combat per IC while maintaining mission coverage and survivability. Test HMG/cannon choices against actual mod stats and available thrust; vanilla HMG dominance is not assumed. |
| CAS | Ground attack per IC with adequate range and legal thrust; no expensive air-superiority payload as a default. |
| Long-range support | Tactical bomber or long-range fighter only where ordinary aircraft have poor coverage and the added cost pays off. |
| Naval/carrier | Correct mission-defining weapon, actual carrier eligibility and available deck capacity. |

Names/reskins must fit the setting. The air designer plan already preserves
special nuclear/hypersonic aircraft and their gates. A jet-like name does not
itself give an old module new statistics. Use the existing plane module IDs;
validate slots, technologies, weapon-driven roles, XP and MIO coverage after
the final designer wiring is chosen. [R18]

A practical initial air-production hypothesis for an air-capable continental
power is about two fighters per CAS by **production IC**, adjusted for losses
and enemy air strength. Test it; the current weight numbers do not directly
express that allocation. A useful plane is one that reaches and flies the intended
missions; numbers in a stockpile alone are insufficient.

## 8. Implementation order and acceptance gates

No implementation milestone below is complete. Research and proposal are complete.

| Milestone | Main files / systems | Acceptance gate |
| --- | --- | --- |
| 1. Repair selection and progression | Existing `common/ai_templates/generic.txt`, `common/ai_strategy/default.txt`, relevant research guidance | Correct calendar and NSB/non-NSB eligibility; every requested role has an intended target; starting OOBs can reach it. |
| 2. Add affordable force profiles | Templates, strategies, research priorities; narrowly scoped triggers/constants if genuinely reused | A small nation equips its line; a regional power can afford its selected specialty; a major deploys and replaces armor. No overlapping profile rules or oscillation. |
| 3. Prove actual field upgrades | Target chains, stockpile/manpower readiness, equipment production and XP | Existing deployed formations demonstrably change template and receive the required equipment; ordinary divisions do not all collapse in strength during conversion. |
| 4. Improve current armor and fixed aircraft | Existing tank design groups, active air research/equipment routes, production and logistics | Valid variants; useful vehicle speed/organization/reliability; researched aircraft tiers actually produced and flown. |
| 5. Tune deployment | Doctrine strategy hooks and native Force Concentration | Observe concentrated offensives on useful fronts, successful supply maintenance and infantry follow-up; record failure cases rather than promising micro. |
| 6. Attach designer AI | Coordinated with `air-navy-designer-restoration.md` | AI designs, produces, upgrades and flies valid modular aircraft after the designer itself is proven. |
| 7. Balance against a frozen baseline | Repeatable observation/combat scenarios | Better outcomes across multiple seeds and country capacities without relying on hidden combat or production bonuses. |

For implementation, first build a read-only reference audit for target chains,
requested roles, active technology/equipment/module IDs, legal slots and unlocks.
Account for repeated containers, duplicate-archetype generation, replace paths
and the active DLC route. A simple first-container parser can falsely report
missing modules. Check obsolete references before removing any content.

Then use clean logs and fresh campaigns. Proposed observation points are years
100, 102, 104, 108 and 112, plus before/after each major conversion. Test a small
country, an armor-capable regional country, AUR, a maritime profile and a restricted
Paluush country. Include NSB on/off and the air-designer DLC routes supported by
the actual implementation. Do not force conventional templates on special species
or authored country restrictions.

Record at each checkpoint:

- Deployed divisions by role, widths, organization, strength, actual equipment and
  which starting formations upgraded; training queues and manpower reserve.
- Production IC by equipment role, persistent deficits, stockpiles, resources,
  fuel, trucks/trains, supply status and replacement losses.
- Aircraft designs/tiers, deployed wings, missions, coverage/mission efficiency,
  airfield capacity and air losses normalized by production cost.
- AIFC army creation, useful armor concentration, objective capture, failed
  assaults, terrain/supply bottlenecks and infantry follow-up.
- Technology and XP spending, illegal fits, repeated redesigns, profile churn,
  runtime cost and new relevant log errors.

Use `imgui show ai_templates` and `imgui show ai_division_production` as documented.
Compare identical initial conditions across several seeds. Suggested readiness
targets are sustained approximately 90% equipment strength and a replacement
reserve before major expansion, with thresholds calibrated to the real wars.
They are proposed benchmarks, not verified script triggers or measured outcomes.
Do not declare success from a clean main menu or a larger division count. [R14]

## 9. Scope, uncertainty and work actually performed

- Inspected the working branch, relevant guidance, current memory, active AI
  files, equipment, units, technologies, terrain, AUR country/OOB setup, descriptor,
  existing designer plan and installed primary AI documentation.
- Performed comment-aware parse/inventory queries using the painter's existing
  parser read-only, including active target groups, chassis-tech variants, modern
  unlocks, equipment costs in `need` blocks and module/category reference coverage.
- Searched repository `common`, `events` and `history` for relevant tech/unlock
  references. Checked installed version in `launcher-settings.json`: 1.20.1.
- The descriptor still declares supported 1.17.* and version 1.15.*. This mismatch
  was not changed. Installed examples establish current available controls, not
  automatic compatibility with every engine covered by the descriptor.
- External guides were read as advice, not adopted as a verified mod meta.
  No gameplay, AI observer run, balance test, game launch or CWTools run occurred.
- No gameplay script, localization, equipment, map, descriptor or OOB was edited.
  This task changes only this proposal and its durable memory entries.
- Relevant next work, only if implementation is requested: milestone 1, followed
  by a small-country/AUR proof before expanding profile coverage. Aircraft module
  design remains coupled to the separate designer-restoration feasibility work.

## Local evidence index

Line numbers refer to files inspected on 2026-11-26; links are relative to this plan.

- **R1:** [Generic AI templates](../../../common/ai_templates/generic.txt), lines 1-49, 126-200, 232-383 and the active role declarations through 559.
- **R2:** [Default AI strategies](../../../common/ai_strategy/default.txt), lines 54-70 (buffers), 86-214 and 360-466 (production), 721-765 (mobile/armor demand), 1108-1212 (calendar/template preference).
- **R3:** [AUR strategy plan](../../../common/ai_strategy_plans/AUR.txt), lines 51-70; directory inventory contains only this plan.
- **R4:** [AUR history](<../../../history/countries/AUR - Imperial Regency.txt>), lines 10-86, especially DLC-specific grants 65-86.
- **R5:** [Calendar and movement defines](../../../common/defines/lok_defines.lua), lines 1-11.
- **R6:** [Active NSB research](../../../common/technologies/LOK_NSB_armor.txt), lines 5-194 and 273-359; [non-NSB medium research](../../../common/technologies/armor.txt), lines 1125-1145 and 1327-1345.
- **R7:** [Tank designer names](../../../localisation/english/replace/LOK_tank_designer_l_english.yml), lines 25-51 and 101-118; [unit names](../../../localisation/english/replace/lok_unit_l_english.yml), lines 76-83 and 142.
- **R8:** [Plane AI](../../../common/ai_equipment/generic_planes.txt) and [naval AI](../../../common/ai_equipment/generic_naval.txt), complete files: no non-comment code.
- **R9:** [Tank design AI](../../../common/ai_equipment/generic_tank.txt), lines 715-962 (medium progression), 2339-2514 (modern groups), 2690-2815 (walker fits); [active tank modules](../../../common/units/equipment/modules/00_tank_modules.txt), complete file including repeated module containers.
- **R10:** [Doctrine strategies](../../../common/ai_strategy/doctrines.txt), lines 19-90 for mobile-warfare ratios and Force Concentration; remaining doctrine families contain additional factors.
- **R11:** [Ordinary terrain](../../../common/terrain/00_terrain.txt), lines 29-209; [custom terrain](../../../common/terrain/LOK_terrain.txt), lines 1-43 and 239-313.
- **R12:** [Medium armor](../../../common/units/medium_armor.txt), lines 26-38; [infantry/motorized/mechanized](../../../common/units/infantry.txt), lines 148-235 and 920-974; [artillery](../../../common/units/artillery_brigade.txt), lines 3-108; [SP artillery](../../../common/units/sp_artillery_brigade.txt), lines 71-103; [cavalry](../../../common/units/cavalry.txt), lines 7-53.
- **R13:** [Descriptor](../../../descriptor.mod), lines 2, 11-16, 42 and 64.
- **R14:** [Bundled template documentation](../../vanilla_folders/vanilla_common/ai_templates/_documentation.md), “How do AI templates work?”, “Tips for debugging”, and parameters `enable`, `can_upgrade_in_field`, `replace_with`. Also read the installed equivalent under `C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV/common/ai_templates/_documentation.md`, lines 11-22 and 35-119.
- **R15:** Installed `C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV/common/ai_strategy/_documentation.md`, line 39 (`front_armor_score`), lines 233-280 (Force Concentration), 474-514 (equipment production), 594-640 (research, unit ratios and XP spending); installed `common/ai_equipment/_documentation.md`, lines 1-132 (variant roles, slot matching, requirements, allowed modules).
- **R16:** [Exoskeleton and special infantry research](../../../common/technologies/infantry.txt), lines 3057-3181; [power units](../../../common/units/infantry.txt), lines 381-548.
- **R17:** [AUR starting templates](../../../history/units/AUR_1936.txt), lines 2-63.
- **R18:** [Air research](../../../common/technologies/air_techs.txt), lines 597-977, particularly jet gates 759-849; [fixed aircraft](../../../common/units/equipment/x_plane_airframes.txt), lines 173-327 and 562-602; [air units](../../../common/units/air.txt), lines 15-47; [existing designer plan](air-navy-designer-restoration.md), milestones 1-3 and 6.

Documentation validation commands actually run (with their outcomes):

- `git -c core.fsmonitor=false diff --check`: fails on 933 pre-existing whitespace
  findings, all in `portraits/LOK_portraits.txt`, outside this task.
- `git -c core.fsmonitor=false diff --stat`: reviewed; includes the unrelated
  working changes present before this task, so it is not a task-only change count.
- `git -c core.fsmonitor=false diff -- modding_documentation/agent_memory/CURRENT_STATUS.md modding_documentation/agent_memory/DECISIONS.md`:
  reviewed the full memory diff, preserving unrelated prior entries.
- `git -c core.fsmonitor=false diff --check -- modding_documentation/agent_memory/CURRENT_STATUS.md modding_documentation/agent_memory/DECISIONS.md`:
  passes.
- `git -c core.fsmonitor=false diff --no-index --check -- NUL modding_documentation/agent_memory/plans/ai-competence-proposal.md`:
  no whitespace findings (exit 1 denotes the new file differs from NUL).
- `git -c core.fsmonitor=false diff --no-index -- NUL modding_documentation/agent_memory/plans/ai-competence-proposal.md`:
  reviewed the complete new proposal.
- Read-only Python Markdown-link check: all 30 local targets resolve.

No new game identifiers are introduced by this proposal.

# Air and naval designer restoration: reconnaissance and plan

Date: 2026-11-26. Inspected working branch: `Painter-Test`.
Status: reconnaissance complete; implementation not started or authorized by this planning request.

## Recommendation and scope

Restore the existing designers by reconnecting the mod's equipment, research,
blueprints and AI. Reuse and reskin the **86 aircraft modules and 95 naval
modules already defined in the mod**. Freeze those two identifier sets before
implementation; do not import the larger installed-game module catalogue.

Prefer retaining current equipment and technology IDs, country-specific names,
starting force composition and special-project gates. Prototype a conventional
fighter and frigate before choosing the final equipment wiring. Do not simply
uncomment every dormant file: some target absent hulls, old calendar dates and
different ship classifications.

Restoring the designers requires structural changes beyond localisation: module
slots, matching GUI bindings, unlocks and usable starting variants. That does not
require inventing components. Keep module statistics and combat rules unchanged
in the initial restoration. Separating an existing complete equipment's statistics
into a hull and its fitted modules is necessary to avoid counting weapons,
engines and costs twice; it needs explicit before/after comparisons.

Nuclear propulsion is the principal limit of a strict reskin. A renamed engine
does not acquire nuclear endurance. Keep existing nuclear equipment usable as
fixed designs initially; extending the designer to it must either retain an
explicitly abstract cosmetic treatment or adjust existing engine statistics.
The latter is a separate balance decision, still requiring no new module IDs.

No gameplay files, localisation, graphics, descriptor settings or compatibility
declarations were changed during this reconnaissance.

## Verified current state

| Finding | Evidence and implication |
| --- | --- |
| Designer research tabs are deliberately hidden. | `bba_air_techs_folder`, `mtgnavalfolder` and `mtgnavalsupportfolder` have `available = { always = no }`. Ordinary air/naval tabs exclude Paluush states. Preserve that restriction. [S1] |
| Air designer research is dormant. | `bba_air_techs.txt` has no nonempty uncommented lines. It contains reusable frame, engine, weapon and survivability technology IDs, but should not replace the authored progression wholesale. [S2] |
| Module definitions survive. | Comment-aware block inspection found 86 aircraft and 95 ship modules, gated respectively by `By Blood Alone` and `Man the Guns`. No purpose-built nuclear ship engine is in the mod's module file. [S3, S4] |
| Module unlock coverage is incomplete. | 83 aircraft modules and 12 naval modules have no reference in an active `enable_equipment_modules` technology block. The naval twelve are AA, radar and fire-control systems. This is a reference inventory, **not proof that those modules are inaccessible**: unbound modules may be available without research. Give every exposed module an intentional unlock policy. [S2-S5] |
| Modular airframes survive alongside fixed aircraft. | `plane_airframes.txt` supplies slots; `x_plane_airframes.txt` supplies role duplicates and the fixed-stat aircraft currently unlocked by the ordinary tree. Nuclear duplicate archetypes explicitly use `module_slots = none`. [S6, S7] |
| Ships need reconstruction of slots. | None of the nine naval archetypes in the five `ship_hull_*.txt` files declares a slot block. Their fixed-stat equipment supplies complete weapons and propulsion. Dormant MTG technologies refer to modular hull IDs such as `ship_hull_light_1`, absent from the active mod equipment definitions. [S8-S10] |
| GUI inheritance is only partly useful. | The mod adds tank designer windows only. Installed naval windows bind to `ship_hull_light`, `ship_hull_cruiser`, `ship_hull_heavy`, `ship_hull_carrier`, `ship_hull_submarine` and `ship_hull_super_heavy_1`. Several mod archetypes have different IDs. Installed generic aircraft windows bind primarily to numbered modular airframe IDs. Equipment names alone do not supply those bindings. [S11] |
| AI templates exist as commented references. | Both `generic_planes.txt` (1,330 lines) and `generic_naval.txt` (1,665 lines) have zero nonempty uncommented lines. The descriptor replaces `common/ai_equipment`; inherited vanilla templates cannot be assumed to supply them. [S12, S13] |
| Artwork needs an effective-pool audit. | The descriptor replaces the designer graphic database. `00_plane_icons.txt` supplies generic icons/models, but the later `01_bba_plane_icons.txt` has an empty small-airframe pool. Its effective result must be checked in game rather than assumed. There is no mod ship entry in that database directory; ships also use their blueprint/sprite paths. [S13, S14] |
| Calendar and version assumptions need care. | The campaign runs from 100 to 120. Dormant naval research still contains `start_year = 1922`. The descriptor declares `supported_version="1.17.*"` and `version="1.15.*"`; the installed game reports `1.20.1.0`. Use installed files as version-labelled references, not a silently substituted compatibility target. [S10, S13, S15] |

The repository memory contains historical branch statements. This assessment
was checked against `Painter-Test`, not assumed to describe
`Legacy-of-Kattail-Main` or any private mod.

## Fit to the existing technology level

The existing localisation already establishes the setting: prekaiser propeller
aircraft, Kaisertech jet aircraft, subsequent improved/advanced jets, then nuclear
ramjets. Naval names establish frigates, destroyers, cruisers, nuclear cruisers,
railgun battleships and nuclear supercarriers. These are the basis for the
proposal, rather than new lore. [S16, S17]

### Aircraft: proposed reuse map

These are working labels for planning, not approved production localisation.
`*` below denotes existing size/count variants, not IDs to generate.

| Existing module IDs/family | Proposed presentation | Mechanical boundary |
| --- | --- | --- |
| `engine_1_*` | Prekaiser piston engines | Preserve cheap, early propulsion and existing engine-count distinctions. |
| `engine_2_*` | Kaisertech turbojets | Existing tier-two engine mechanics; coordinate airframe base speed with the current fighter benchmarks. |
| `engine_3_*` | Improved turbojets | Existing tier-three mechanics. |
| `engine_4_*` | Advanced turbojets | Existing tier-four mechanics. |
| `jet_engine_*` | Advanced high-thrust propulsion initially; candidate nuclear ramjet reskin later | `jet_engine_1x` currently adds fuel use and applies a 40% range penalty. Do not promise nuclear endurance with that unchanged profile. [S3:398] |
| `light_mg_*`, `heavy_mg_*` | Light/heavy aircraft gun packs | Keep gun-based air attack. Avoid relabelling every gun as a guided missile. |
| `aircraft_cannon_1_*`, `aircraft_cannon_2_*` | Aircraft cannon / advanced autocannon packs | Preserve existing damage, weight and agility tradeoffs. |
| `large_aircraft_cannon_*`, `tank_buster_1/2` | Heavy aircraft cannon / anti-armour cannon | Keep their actual mission and combat modifiers. |
| `bomb_locks`, `heavy_bomb_locks`, `armor_piercing_bomb_locks`, `rocket_rails` | External ordnance racks, heavy racks, anti-ship ordnance racks, rocket pods | No new missile targeting or guidance rules. |
| `small_bomb_bay`, `medium_bomb_bay`, `large_bomb_bay` | Internal payload bays | Same sizes and mission availability. |
| `torpedo_mounting`, `_2`, `_3`; `guided_anti_ship_missile` | Torpedo packages and the existing guided anti-ship weapon | Preserve the already distinct missile component; do not duplicate it. |
| `recon_camera`, bomb sights, radio navigation and both radar families | Reconnaissance package, targeting suite, navigation suite, search/interception radar | Do not describe radar as stealth or a new detection mechanic. |
| Armour, fuel tanks, self-sealing tanks, drop tanks and material substitutions | Appropriate modern construction and range packages | Preserve durability/range/resource tradeoffs; no imaginary material bonuses. |
| Defensive turret families | Defensive gun/autocannon turrets | Optional later high-tier laser artwork would remain an abstraction of these stats. |

Keep helicopters, transports, superheavy fighters and nuclear aircraft available
through their existing systems until equivalent modular paths are proven. The
large-frame fighter role, carrier aircraft and nuclear duplicate archetypes need
separate checks; a small-frame demonstration is not proof they work. [S7, S18]

### Navy: proposed reuse map

| Existing module IDs/family | Proposed presentation | Mechanical boundary |
| --- | --- | --- |
| `ship_light_battery_1..4` | Light naval guns progressing to advanced automatic batteries | Keep light attack and penetration. |
| `ship_light_medium_battery_1..4` | Destroyer batteries | Keep light-attack role and screen compatibility. |
| `ship_medium_battery_1..4` | Cruiser main batteries | Resolve the classification conflict below before exposing them to mod cruisers. |
| `ship_heavy_battery_1..4`, `ship_super_heavy_battery_1` | Early heavy guns progressing to railgun batteries; superheavy railgun battery | Keep heavy attack, averaged penetration, costs and conversion rules. |
| Dual-purpose batteries and secondary families | Dual-purpose naval guns and defensive batteries | Preserve the actual AA/surface split. |
| `ship_anti_air_1..4` | AA battery progressing to automated CIWS | Laser CIWS is an optional final-tier visual theme, not a new missile-interception system. |
| `ship_torpedo_1..4`, `ship_torpedo_sub_1..4` | Torpedo launchers and advanced/homing torpedo packages | Keep torpedo combat behavior. Avoid labelling these as strategic missiles or pretending they use gun hit rules. |
| Depth charges, sonar, radar and fire-control families | ASW weapons, sonar suites, search radar and combat direction systems | Keep existing detection and targeting effects. |
| Light/cruiser/heavy/carrier/submarine engine families | Class-appropriate conventional machinery tiers | Nuclear names need a separate policy; ordinary engine modules do not gain reactor behavior by renaming. |
| Armour families | Class-appropriate protective schemes | Do not promise shields or active interception. |
| `ship_airplane_launcher_1/2` | Reconnaissance aircraft facilities | Retain existing spotting; helicopter artwork is possible only as a visual abstraction. |
| `ship_deck_space`, extra fuel tanks, snorkels and mine warfare | Hangar facilities, endurance packages, submarine support and mine warfare | Preserve capacity, range and mission effects. |

Keep the mod's existing class names: vanilla destroyer equipment is a frigate,
light cruiser equipment a destroyer, and heavy cruiser equipment a cruiser.
Do not reintroduce vanilla labels or reclassify fleets as a side effect. [S17]

**Classification conflict:** `ship_hull_heavy_cruiser` declares `screen_ship`,
while its consuming `heavy_cruiser` sub-unit declares `capital_ship`.
`ship_medium_battery_1` explicitly adds `capital_ship`. Static inspection cannot
establish which battlefield behavior the author intended. Observe the current
fresh-campaign behavior and resolve the intended role before fitting these
batteries. Do not silently delete `add_equipment_type` or change the sub-unit.
The separate `battle_cruiser_hull` is already a capital-ship archetype. [S4:423,
S9:53, S19]

## Implementation milestones

### 1. Freeze the baseline and prove the smallest restoration

- Record the exact module ID sets, equipment IDs, types, slots, unlock ownership,
  current default statistics, graphics and starting country technologies.
- Prototype `fighter_equipment_1` and `destroyer_2` as designer-capable existing
  equipment IDs. Reuse current slot categories and add matching blueprint
  bindings for those IDs/archetypes as required. Establish which slot inheritance
  and default-variant behavior the target engine actually accepts.
- Use a sample fit of an existing tier-two engine, weapon and optional support
  modules. Demonstrate open, fit, save, produce and deploy/refit in game.
- Separate complete-equipment stats from module contributions. For reference,
  the current fighter has speed 1,000, range 1,000 and cost 24; the existing modular
  small airframe has different base values. Blindly adding modules to a complete
  aircraft would not preserve its benchmark. Treat engine values in the game's
  native units; inspect rendered metric labels before claiming physical speeds.
  [S6:231, S7:229]

**Exit:** two functional designs, no added module IDs, no doubled stats or costs,
and an explicit choice of equipment wiring.

Preferred wiring is retrofitting existing equipment IDs: less disruption to
country history, OOBs and project unlocks. If the engine makes that route unsafe,
use the already-defined modular aircraft families and explicitly migrate every
affected starting variant/OOB reference. Restoring standard vanilla naval hull
IDs is a larger alternative and requires adapting the mod's custom archetypes
and class semantics; do not present it as a one-line fallback.

### 2. Connect research without duplicating progression

- Retain current authored air/naval progression and IDs where practical. Add
  component unlocks to the relevant existing technologies. Restore selected
  dormant weapon/engine research nodes only where they provide a real design
  choice; do not activate a parallel complete aircraft tree automatically.
- Align conventional tiers to existing years 97, 100, 104 and 108. Use current
  special-project and nuclear gates for later equipment; do not infer that all
  countries start with the same technology.
- Reuse the existing air page initially so helicopters and special branches stay
  reachable. Enable the existing naval support page for module research after
  calendar repair. A separate BBA frame page is optional; do not enable it merely
  because its ID exists.
- Fix only relevant inherited 1922/1936/etc. research dates against authored
  equivalents. Do not equate all equipment `year` fields to research dates: the
  current equipment also uses 80/84/88/89/94.
- Reconnect AA, radar and fire control to the corresponding existing artillery,
  electronics and naval technologies. Audit all 181 modules, including mines and
  reconnaissance, for deliberate starting availability or research unlock.
- Preserve `is_paluush_state = no`, existing DLC gates and DLC-off routes. Avoid
  duplicate tab positions if multiple pages become visible. [S1, S5, S10, S20]

**Exit:** no unintended fully unlocked module families, unreachable required
parts, bypassed special projects, duplicate research burden or hidden branches.

### 3. Restore conventional aircraft families

- Extend the successful prototype across fighters, CAS, naval bombers, tactical
  and strategic bombers, reconnaissance and their existing carrier variants.
- Keep weapon-driven role selection, mission availability, carrier eligibility,
  wing sizes and production filters synchronized with `common/units/air.txt`.
- Supply valid starter fits using technologies the owning country actually has.
  Reuse the starting-tank effect's organization as a local pattern, but do not
  copy its `allow_without_tech = yes` shortcut into normal module availability.
- Keep excluded special aircraft functional and visible; restoring one research
  page must not remove access to their authored branches. [S7, S18, S21]

**Exit:** each supported role can be designed, produced, assigned and flown, and
existing nonmodular exceptions retain their technology paths.

### 4. Restore naval classes and starting fleets

- Extend the frigate proof to the existing destroyer, cruiser, battleship,
  nuclear-cruiser, submarine and carrier archetypes only after resolving their
  slot/type requirements. Bind custom archetypes to narrowly adapted blueprint
  layouts; reuse existing art and slot names rather than replacing broad UI files.
- Keep nuclear cruisers, ballistic submarines, supercarriers and hypercarriers
  fixed initially wherever their existing capabilities cannot be represented by
  unchanged modules. They remain available; do not replace them with weaker
  generic hulls or claim a ballistic launcher exists in the 95-module set.
- Preserve named starting ships, fleet/task-force membership, counts and owning
  countries. Update equipment/variant references only where the chosen wiring
  requires it. Search all history, focus, event and scripted-effect grants.
- Check screening, capital targeting, deck capacity, aircraft assignment and
  refit behavior for each class. Renamed modules must not alter fleet roles
  accidentally. [S8-S11, S17, S19, S22]

**Exit:** existing fleets load intact; supported ships can be fitted, built,
deployed and refitted; exceptional vessels remain usable and gated correctly.

### 5. Apply names and artwork

- Use the family tables above as a reviewable naming sheet. Put final English
  overrides in the established replace layer; preserve UTF-8 BOM, headers,
  authored country names and descriptions. No generated lore is required.
- Replace WWII-era silhouettes and component images selectively with suitable
  existing mod assets. Preserve sprite IDs wherever possible, verify exact
  texture paths/formats, and keep engine-count/weapon-tier distinctions readable.
- Audit the effective aircraft graphic pools, including the later empty pool,
  and verify default art for countries without national skins. Inspect the
  actual ship blueprint/icon paths before deciding a ship database file is needed.
- Use labels such as improved radar/autocannon/CIWS where the effects support
  them; leave unsupported claims about stealth, laser interception, reactor
  endurance or missile launch mechanics out of descriptions. [S14, S16, S17]

**Exit:** every exposed module/hull has a readable name, correct art and truthful
tooltips, with no new component definitions.

### 6. Restore AI design and production

- Adapt selected existing commented `generic_planes.txt`/`generic_naval.txt`
  templates to the final equipment IDs and supported fits. Reuse their design
  IDs where suitable; do not uncomment templates targeting absent equipment.
- Supply affordable fighter, CAS, bomber, escort, ASW, submarine, capital and
  carrier templates with technology-aware selection. Check XP costs and upgrade
  priorities, plus MIO equipment-group and production-filter coverage.
- Observe both a limited-tech country and a major replacing losses and upgrading
  designs in a running campaign. A designer that only the player can use is an
  incomplete restoration. No new global recurring script scans are needed.

**Exit:** AI nations generate valid fits and sustain air/naval production without
unresearched components, invalid variants or repeated redesign loops.

### 7. Decide nuclear treatment, then complete validation

- Strict cosmetic scope: retain fixed nuclear exceptions, document that coverage
  honestly, and use conventional labels for unchanged designer engines.
- Broader existing-component reuse: reskin existing `jet_engine_*` and selected
  existing ship engine tiers, adjusting only those existing definitions and hull
  budgets as necessary. Agree the endurance/fuel/resource expectations first;
  test whether the shared families can serve the required classes without
  erasing conventional choices. No reactor, shield or missile modules are added.
- Test the DLC combinations applicable to the actual target installation. Local
  presence of DLC folders is not proof of entitlement or active-session state.

**Exit:** all claimed designer coverage is demonstrated in game, or remaining
fixed exceptions and the exact reason for each are explicitly reported.

## Validation and implementation file groups

| Area | Files to inspect/change during implementation | Required proof |
| --- | --- | --- |
| Equipment and modules | `common/units/equipment/plane_airframes.txt`, `x_plane_airframes.txt`, the five `ship_hull_*.txt` files; existing `modules/00_plane_modules.txt` and `00_ship_modules.txt` only if necessary | Exact module-ID set equality; balanced blocks; legal slot/category fits; no double-counted stats; no missing parent/archetype. |
| Research | `common/technology_tags/00_technology.txt`, `common/technologies/air_techs.txt`, selected dormant BBA nodes, `naval.txt`, `MTG_naval*.txt`, relevant electronics/artillery nodes | Every exposed part has intended availability; correct scope/DLC/calendar/project gates; all retained paths reachable. |
| UI/art | Targeted files under `interface/equipmentdesigner/planes/` and `/ships/`; `countrytechtreeview.gui` only if layout needs it; exact sprite/texture owners and graphic pools | Every slot is clickable; no missing pictures; names fit; valid textures and generic fallback. |
| Starting setup | Relevant `history/countries/`, `history/units/`, existing focus/effect grants and `common/units/` | Same starting force identities/counts; valid owned technology and fits; correct role/mission/ship class. |
| AI/production | Existing `common/ai_equipment/generic_planes.txt`, `generic_naval.txt`; equipment groups/filters and relevant strategies | AI creates and produces designs with researched parts. |
| Localisation | Established files under `localisation/english/replace/` | BOM/header preservation; no duplicate keys; source descriptions preserved; truthful effects. |

For the later implementation run `git diff --check`, `git diff --stat` and review
the full `git diff`; run available CWTools and targeted identifier/slot/unlock
audits. Run the localisation analyser using its current interface:
`python loc_analyzer.py` from the repository root (it has a fixed-root `main`,
not an argparse CLI). Treat its generated diagnostic outputs as temporary;
inspect its write behavior before running it. Compile any Python tools actually
changed. Map validation is unnecessary unless implementation unexpectedly edits
map data; that would be a separate scope change.

Engine validation must start with separately archived/clean logs and a fresh
campaign. Exercise research, design/save, production, air missions, carrier air
operations, naval deployment/combat/refit and AI production. Include a restricted
Paluush country, a limited-tech ordinary country and a major. Repeat supported
DLC-off paths. A clean main menu or parser check alone is insufficient.

## Reconnaissance validation actually performed

- Inspected the real working branch and initial Git status. One unrelated
  untracked file already existed: `plans/spirit-research-equipment-bonuses.md`.
- Read project guidance, current memory and the coupled equipment, research,
  localisation, sub-unit, AI, GUI and graphics sources cited below.
- Ran read-only Python searches over repository text and a comment-aware
  brace/block inventory of both module files and active technologies; checked
  commented AI files and absent slot declarations in all nine naval archetypes.
- Compared installed equipment/GUI examples and version metadata. No installed
  game files were changed, and no private-mod directory was inspected.
- Attempted live wiki access and search. Both direct wiki pages returned HTTP
  401; engine conclusions therefore use the installed primary examples and
  repository documentation, not unverified snippets from third-party mirrors.
- Reviewed `git -c core.fsmonitor=false diff`, `diff --stat` and `diff --check`;
  the whitespace check passed. Reviewed the new plan with `git diff --no-index`
  against `NUL` and checked its whitespace separately. All 35 local source links
  resolve. Unrelated concurrent working-tree changes were left untouched.
- No gameplay validation, CWTools run or balancing test was performed. This
  deliverable is a plan, not a functioning designer restoration.

## Sources and precise examples

Paths below are relative to the repository root. Links point back to those
files from this plan's location; line numbers refer to the inspected revision.

- **S1:** [Technology folders](../../../common/technology_tags/00_technology.txt), lines 181-199.
- **S2:** [Dormant BBA research](../../../common/technologies/bba_air_techs.txt), lines 1-14, 987-1041 and 1258-1510.
- **S3:** [Aircraft modules](../../../common/units/equipment/modules/00_plane_modules.txt), lines 1-18 and 398-423; complete file for the 86-module inventory.
- **S4:** [Naval modules](../../../common/units/equipment/modules/00_ship_modules.txt), lines 1-4, 423-457 and 1311-1337; complete file for the 95-module inventory.
- **S5:** [Electronics research](../../../common/technologies/electronic_mechanical_engineering.txt), lines 238-309, 755-790 and 1356-1388 (commented module unlocks); [naval support research](../../../common/technologies/MTG_naval_Support.txt), lines 38-44 and 1753-1768 (active unlock examples).
- **S6:** [Modular airframes](../../../common/units/equipment/plane_airframes.txt), lines 60-85, 213-306.
- **S7:** [Aircraft duplicates and fixed equipment](../../../common/units/equipment/x_plane_airframes.txt), lines 140-170, 229-258, 327-368 and 1792-1817.
- **S8:** [Frigate equipment](../../../common/units/equipment/ship_hull_light.txt), lines 3-53 and 55-105; [submarine equipment](../../../common/units/equipment/ship_hull_submarine.txt), lines 3-69; [carrier equipment](../../../common/units/equipment/ship_hull_carrier.txt), lines 3-78.
- **S9:** [Cruiser equipment](../../../common/units/equipment/ship_hull_cruiser.txt), lines 3-12 and 53-62; [heavy ship equipment](../../../common/units/equipment/ship_hull_heavy.txt), lines 3-18, 60-75 and 117-130.
- **S10:** [Dormant naval hull tree](../../../common/technologies/MTG_naval.txt), lines 10-49 and 64-84; [ordinary naval research](../../../common/technologies/naval.txt), lines 3-21, 36-55 and 1472-1495.
- **S11:** Installed `C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV/interface/equipmentdesigner/ships/ship_hull_{carrier,cruiser,heavy,light,submarine,super_heavy}.gui`, line 7 in each; installed `interface/equipmentdesigner/planes/plane_blueprints_generic.gui`, lines 6-54. These are **1.20.1** examples. Also [local equipment schema](../../../common/units/equipment/_documentation.info), lines 41-104, for slots and defaults.
- **S12:** [Commented aircraft AI](../../../common/ai_equipment/generic_planes.txt), complete file, and [commented naval AI](../../../common/ai_equipment/generic_naval.txt), complete file.
- **S13:** [Descriptor](../../../descriptor.mod), entries replacing technologies, AI equipment and the designer graphic database; first version field and final supported-version field.
- **S14:** [Generic plane graphics](../../../gfx/interface/equipmentdesigner/graphic_db/00_plane_icons.txt), lines 1-22; [later BBA pool](../../../gfx/interface/equipmentdesigner/graphic_db/01_bba_plane_icons.txt), lines 1-16; [existing sprite registrations](../../../interface/Technologies.gfx), lines 7161-7183 and 7337-7339.
- **S15:** [Calendar defines](../../../common/defines/lok_defines.lua), lines 2-3. Installed `launcher-settings.json`, `version` and `rawVersion` properties: `Operation Postern v1.20.1.0.0fd1 (724a)` / `1.20.1.0`.
- **S16:** [Authored aircraft localisation](../../../localisation/english/replace/lok_equip_air_l_english.yml), lines 48-50, 68-87, 94-99 and 139-163.
- **S17:** [Authored naval localisation](../../../localisation/english/replace/lok_equip_naval_l_english.yml), lines 10-27, 30-45, 55-83, 87-115 and 119-150.
- **S18:** [Air sub-units](../../../common/units/air.txt), lines 15-80, 107-157, 166-206 and 226-231; [helicopter equipment](../../../common/units/equipment/helicopters.txt).
- **S19:** [Heavy cruiser sub-unit](../../../common/units/heavy_cruiser.txt), lines 2-8; [light cruiser sub-unit](../../../common/units/light_cruiser.txt), lines 2-8; [destroyer sub-unit](../../../common/units/destroyer.txt), lines 2-8.
- **S20:** [Existing project gates](../../../common/special_projects/projects/lok_projects.txt), lines 87-92 and 155-161; [naval reactor research](../../../common/technologies/electronic_mechanical_engineering.txt), lines 2455-2479.
- **S21:** [Starting tank variants](../../../common/scripted_effects/LOK_starting_tank_variants.txt), lines 1-18: nearby structural example, not approval to bypass component research.
- **S22:** [Amphibious starting navy](../../../history/units/ACR_1936_naval.txt), lines 10-28: existing named nuclear cruisers, cruiser and destroyers with fixed equipment references.
- **S23:** [Local technology reference](<../../wiki_doc/Technology modding - Hearts of Iron 4 Wiki.md>), lines 115-117: equipment and module unlocks. Live pages attempted: [Equipment modding](https://hoi4.paradoxwikis.com/Equipment_modding), [Technology modding](https://hoi4.paradoxwikis.com/Technology_modding); both unavailable with HTTP 401 during reconnaissance.

## Next concrete action

When implementation is requested, begin milestone 1 on the intended branch:
prove a designer-capable existing fighter and frigate with unchanged module ID
sets. Resolve the cruiser type conflict and choose nuclear coverage before
claiming a complete restoration. No implementation is pending within the
current reconnaissance-only request.

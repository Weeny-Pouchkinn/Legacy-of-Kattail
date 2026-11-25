# Current error log: analysis and repair plan

Date: 2026-11-25. Scope: Legacy of Kattail DEV only. The original audit is
retained below as baseline evidence. Repair milestones 1-8 are now implemented;
static checks pass and fresh user-run logs have cleared all original mod-owned
errors. Final GUI dependency corrections are applied and monitored in the latest
run. Milestone 9 retains six external Workshop descriptor warnings.

Implementation, exact paths, decisions and frozen validation evidence:
[repair completion record](../error_log_repair_20261125/README.md).

## Baseline and evidence

- Actual checkout: `Painter-Test`, HEAD `a5958d259`. The root instructions name
  `Legacy-of-Kattail-Main`; this report describes the checkout actually inspected.
- Input: `C:/Users/elowi/Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`,
  modified 2026-11-25 22:17:30 UTC, 208,078 bytes. No separate attachment was
  exposed, so the fresh local game log was used. SHA-256:
  `be30592ced719ca562abd9319d6fee7d025ba3cc2d4399bd211056c2f8203f9d`.
- There are **1,526 timestamped records across 1,528 physical lines**, assigned
  exhaustively to 16 families below. Repeated records are not independent bugs.
- Companion `logs/text.log` contains 7,084 reports for **3,542 duplicate keys**:
  943 have equal values, 2,599 have different values. The one collision warning
  in `error.log` substantially understates this work.
- Installed game: **Operation Postern v1.20.0.0.8873 (0c4f)**, from installed
  `launcher-settings.json:4-5`. The mod still declares `supported_version="1.17.*"`
  and `version="1.15.*"` in `descriptor.mod`. Updating the actual interface
  contract is necessary for this installed build; changing metadata alone will
  not repair it. Neither version field should be silently changed.
- The existing `game.log:7-9` records a single-player start at `100.1.1.12`.
  This audit did not launch the game, reproduce a crash, or exercise gameplay.

[Machine-readable inventory](../error_log_audit_20261125/inventory.json) preserves
every error message, repetition count and log-line span, every colliding key and
its source line numbers/values, the 198 implicated flag paths and hashes, and
the independent seam-scan results. Source-log paths, hashes and modification
times are recorded there. Log line numbers below refer to this frozen baseline.

## Complete error inventory

| Family | Records | Baseline evidence | Planned milestone |
| --- | ---: | --- | --- |
| Equipment variants unavailable | 610 | `error.log:630` onward; 378 artillery, 116 motorized, 116 support, across 24 country names | 4 |
| Character names cannot generate | 341 | `error.log:325` onward; 49 distinct origin names | 5 |
| Flag format warnings | 210 | `error.log:38` onward; 198 distinct existing 24-bit TGA files after ideological fallback | 8 |
| Missing GUI child elements | 117 | `error.log:564` onward; 16 distinct missing child/container combinations; `response_icon` alone repeats 101 times | 1 |
| Scientist portraits cannot generate | 116 | `error.log:345` onward; 29 distinct origins, both genders represented | 5 |
| Units deployed in foreign territory | 64 | `error.log:257-320`; includes 23 unnamed entries needing source tracing | 3 |
| State building-slot overflow | 21 | `error.log:543-563`; deficits total 53 shared slots | 6 |
| Music tracks not registered | 15 | `error.log:9-23`; two local Sabaton playlists | 8 |
| Inherited Romanian scripted GUI | 14 | `error.log:24-37`; invalid ROM scope and missing ROM helpers | 1 |
| Other Workshop descriptor warnings | 6 | `error.log:1-6`; six `ugc_*.mod` files outside this repository | 9 |
| Capitals not owned | 4 | `error.log:99-102`; TEM, FOD, KRO, NKR | 3 |
| Province X crossings | 2 | `error.log:7-8`; both at x=4095, the horizontal wrap seam | 2 |
| Nonexistent PGN declares war | 2 | `error.log:103-104`; one error plus its history-source context | 3 |
| GUI window types undefined | 2 | `error.log:255-256`; engine explicitly warns of likely crashes | 1 |
| Localisation key-collision summary | 1 | `error.log:98`; expanded using all 7,084 lines of `text.log` | 7 |
| Air wings assigned to state without air base | 1 | `error.log:321-323`; one three-line record, three state-215 entries in RST air OOB | 3 |
| **Total** | **1,526** | **1,528 physical lines; no unclassified records** | |

## Milestones, in recommended order

### 0. Freeze and verify the baseline — completed

- [x] Verify checkout, clean initial working tree, installed version and fresh log.
- [x] Classify all error records; expand localisation warnings using `text.log`.
- [x] Inspect relevant source, installed vanilla examples and existing tools.
- [x] Run the current map validator and independently inspect wrap-seam quads.
- [x] Produce this plan and the complete inventory without modifying game data.

Before implementing, confirm these input hashes still match. Re-audit any
externally changed files. The checkout contains user-authored Imperium elements
and state assignments now, so earlier memory describing an empty scaffold is a
historical snapshot, not a current assertion that these definitions are empty.

### 1. Repair the installed game's interface contract — first implementation

**Confirmed cause:** the five overridden mod GUI files lack named elements that
exist in the corresponding installed 1.20 files. This is source-backed interface
drift, not a missing localisation key. Two absent windows have explicit crash
warnings; the log does not prove that either caused an actual crash.

Patch these existing overrides against installed vanilla, retaining custom
layout, map modes, species/culture controls and other mod behavior:

| Mod file | Required names from this log |
| --- | --- |
| `interface/countrytradeview.gui` | `auto_import_priority_window`, `factories_consumer`, `factories_trade`, `auto_import_checkbox`, `auto_import_budget_txt`, `auto_import_slider`, `auto_import_priority_open_button` |
| `interface/countryconstructionsview.gui` | `repair_order_window`, `repair_order_open_button` inside `count_container` |
| `interface/countrydiplomacyview.gui` | `response_icon` inside `diplomacy_action_entry`; `edit_auto_response` and `actions_title` inside `diplomatic_actions`; `recall_volunteers` inside `diplomacy_action_info_window` |
| `interface/unitview.gui` | `recall_volunteers_indicator` inside `army_division_view` |
| `interface/topbar.gui` | `national_focus_shortcut`; `technology_button_shortcut`, `technology_button_ctrl_shortcut`, `technology_button_alt_shortcut` inside `after_intel_agency_button` |

Port the required blocks with their supporting sprites, tooltips, types and
parent relationships. Do not create empty controls merely to silence errors or
replace the entire interface with vanilla. Installed anchors include
`countrytradeview.gui:914`, `countryconstructionsview.gui:648`,
`countrydiplomacyview.gui:1011`, `unitview.gui:1595` and `topbar.gui:884`.

The ROM file is **inherited vanilla**, not present in the mod:
`common/scripted_guis/ROM_diplomacy_scripted_gui.txt:35,42,49,59,85,90,93` in the
game installation. Its ROM tag/helpers are absent after the mod replaces other
vanilla databases. Search all GUI references first; then shadow this one unused
file at the same relative filename with a documented empty override if it has
no intended mod use. Do not add a fictional ROM country or change the global
`replace_path` list. Missing helpers are `ROM_is_improving_relations`,
`ROM_diplo_start_improving_tier` and `ROM_diplo_stop_improving_tier`.

Acceptance: both windows instantiate; trade automation, repair priority,
diplomatic responses, volunteer recall and shortcuts work; all 133 records
assigned to this milestone disappear on a fresh run.

### 2. Repair wrap-seam province crossings and close the validator gap

**Confirmed validator defect:** `tools/validate_map.py:104-119` checks interior
2x2 quads only. Its adjacency scan at lines 126-130 includes horizontal wrap,
but its X-crossing scan does not. Therefore its current success message cannot
establish that the complete map has no X crossings.

Independent read-only scan found exactly two seam quads, ordered top-left,
top-right, bottom-left, bottom-right across columns 4095 and 0:

| Image row, top-left origin | Province IDs |
| ---: | --- |
| 295 | 20846, 21480, 11862, 21454 |
| 591 | 11077, 21454, 11894, 21481 |

The engine reports `(4095,297)` and `(4095,593)`. Its reported row values differ
from this image scan; resolve the actual quad before editing rather than
assuming a coordinate convention.

First add wrap coverage and a seam-specific regression test to
`tools/validate_map.py` / `tools/test_validate_map.py`. Then inspect all map/state
couplings required by AGENTS.md, back up `map/provinces.bmp`, and resolve each
junction with the smallest existing-color pixel edit that preserves province
existence, intended boundaries and valid connectivity. Recompute coastal and
adjacency consequences, including any rail or supply effects. No province ID
renumbering or broad bitmap regeneration is needed by the evidence.

Acceptance: enhanced validator finds these two problems before repair, finds
none afterward, all province colors/IDs survive, and a fresh game enters the
map without either X-crossing warning. Inspect the seam in game.

### 3. Reconcile capitals, deployments, air bases and dormant-country history

Keep current borders as the starting point. These errors do not establish that
state ownership is wrong.

| Country | Configured capital | Current owner | Owned states found |
| --- | ---: | --- | ---: |
| TEM | 1312 | ENO | 3 |
| FOD | 1519 | YIN | 11 |
| KRO | 1043 | KKN | 18 |
| NKR | 1044 | KRO | 13 |

Sources: matching `history/countries/TEM - South Enotita.txt`,
`FOD - Foderation.txt`, `KRO - Kronk.txt`, `NKR - North Kronk.txt`, all at line 1,
and state files `1312-North Slithervich.txt`, `1519-STATE_1519.txt`,
`1043-Kronk4.txt`, `1044-Kronk5.txt`. Select capitals from actually owned states
using existing VPs/region intent; flag genuinely ambiguous intended capitals
for a design decision rather than inventing one or moving borders silently.

Audit every land, naval and air deployment behind the 64 warnings, including
the unnamed records. TEM's parsed land OOB contains 20 divisions, 17 in ENO
territory. KRO and NKR both load `KTZ_1936`, so also check inappropriate shared
OOB reuse before relocating units. The existing painter parser rejects
`history/units/KTZ_1936.txt` with `Unexpected closing brace`; separate that
pre-existing parser issue from what the engine explicitly logged, repair its
structure only after inspecting intended blocks, and check other previously
documented EUL/GAL/KKN OOB parse failures before trusting a deployment audit.

`history/units/RST_1936_air.txt:5,11,20` assigns three wings to state 215;
`history/states/215-State_215.txt` has no `air_base`. Prefer relocation to a
suitable existing owned air base with capacity; add an air base only if the
intended setup requires it. Preserve wing identities and aircraft counts.

PGN currently owns no states. Its history declares war on KOA at
`history/countries/PGN - Piertuguese.txt:12`; its nominal capital 1198 is EUL
territory. Gate the declaration on valid existence and intended conditions, or
move it to the existing creation/release chain if the war is meant to start
there. Trace PGN references before choosing; do not resurrect PGN by assigning
it territory merely to suppress this error.

Acceptance: owned capitals, valid deployment ownership/access, legal air-base
capacity, no invalid PGN declaration, and all 71 records disappear. Exercise
the affected countries and any retained PGN creation/war path.

### 4. Align automatic army generation with available equipment

`common/on_actions/LOK_on_actions.txt:2409-2453` creates a `Standard Infantry`
template containing eight motorized battalions plus artillery and engineers,
then spawns fully equipped divisions for eligible countries without armies.
`history/countries/IRT.txt` and `ANS.txt` have empty technology blocks. The
imported `history/countries/LAU - EU4 import.txt:7-13` grants support/truck tech
but no artillery tech. These are concrete mismatches with that generator.

Verified local unlocks:

| Required equipment | Technology | Source |
| --- | --- | --- |
| `artillery_equipment_1` | `gw_artillery` | `common/technologies/artillery.txt:3-13` |
| `support_equipment_1` | `tech_support` | `common/technologies/support.txt:19-23` |
| `motorized_equipment_0` | `tech_trucks` | `common/technologies/infantry.txt:2229-2241` |
| `motorized_equipment_1` | `motorised_infantry` | `common/technologies/infantry.txt:2289-2302` |

Recommended approach: make the existing startup generator choose a template
whose subunits/equipment the country can supply. Preserve the motorized version
for qualified countries; use an infantry version and conditional support for
others. Check infantry-equipment availability too. If uniform modern armies
are the intended design, instead grant the explicitly approved technology
baseline before spawning and update `tools/import_zzz_from_eu4.py` so future
imports retain it. This alternative changes technology balance and should be
an explicit design choice. Do not grant broad advanced tech silently.

Review the 24 affected countries in the inventory, their OOB variants and
equipment owners, not only the three examples. Some variant warnings may have
additional OOB causes; confirm those after correcting this verified mismatch.
Reuse the existing startup path; add no daily/weekly/global polling loop.

Acceptance: all 610 records disappear and generated armies retain intended
counts, legal templates and usable equipment. Verify representative low-tech,
imported and fully equipped countries after a fresh start.

### 5. Complete random-name and scientist-portrait coverage

Audit the 49 name origins against `common/names/katzen_names.txt` and
`common/names/misc_names.txt`, including both genders, surnames and applicable
cosmetic tags. Missing examples include LAU and the new Jublio/Doughland tags.
Reuse already authored, appropriate pools where the species/culture mapping
establishes that reuse. Record missing approved names as a content dependency;
do not invent lore or assign Katzen names to unrelated species.

The 116 portrait failures cover 29 origins: the 11 new Jublio bodies and 18
Doughland origins. `portraits/00_portraits.txt:1-22` has an active operative
fallback but no active scientist fallback; `no_portraits.txt` is commented out.
`LOK_portraits.txt` contains scientist pools for other tags; for example AXO's
scientist pool is around line 10818. The generic scientist-continent file has
active entries for only some continents. Audit tag and continent fallback
coverage instead of merely uncommenting obsolete vanilla art.

Patch `portraits/LOK_portraits.txt` and/or the appropriate existing fallback
file, plus `interface/lok_generic_species_portraits.gfx` only if necessary.
Resolve every selected sprite to a real large/small texture with matching
gender/species. Existing generic/placeholder textures may be reused where
appropriate; any actual temporary-art choice must be explicit in the change.
Keep `legacy_of_kattail_painter/refactor_characters.py` and existing generation
inputs consistent with the chosen mappings if they would overwrite the repair.

Acceptance: all 457 generation failures disappear; both gender paths and new
scientist/commander generation are exercised without changing authored leaders.

### 6. Give overfilled states sufficient local building capacity

The 21 states are:
`1820, 1832, 1837, 1839, 1840, 1843, 1848, 1852, 1857, 1858, 1861, 1863,
1866, 1869, 1871, 1875, 1880, 1888, 1893, 1895, 1901`.

All logged deficits are 1-5 slots, totaling 53. For example, state 1858 has nine
civilian and four military factories while its `large_city` category grants
eight base slots (`common/state_category/large_city.txt:3`). Factory and dockyard
definitions use `level_cap.shares_slots = yes` in
`common/buildings/00_buildings.txt:55-81,222-237`.

Prefer state-local extra shared slots sufficient to preserve authored factories,
after checking effective technology/idea/startup modifiers and dated setup.
The installed effect docs, `documentation/effects_documentation.md:1268-1275`,
declare `add_extra_state_shared_building_slots` as a state effect. Installed
vanilla history examples are `179-Beja.txt:28` and `6-Belgium.txt:39`.
Avoid increasing every `large_city` state's capacity or deleting factories to
silence the warning. Check the existing startup colony additions separately.

Acceptance: no overflow warnings, unchanged intended factory totals, sufficient
effective capacity in each of the 21 states, no cumulative addition on reload.

### 7. Resolve the full localisation collision set

There are 3,536 duplicated VP keys between the four pairs
`localisation/english/localized_state_names/state_names_{ROQ,KUS,BASILISK,KTZ}_l_english.yml`
and `victory_points_{ROQ,KUS,BASILISK,KTZ}_l_english.yml`, plus six state/region
keys colliding with `localisation/english/lok_jublio_system_l_english.yml`.

Those six are `STATE_1565`, `STATE_1566`, `STATE_1567`, `STATE_1568`, `STATE_1569`
and `STRATEGICREGION_392`, also defined in `state_names_l_english.yml` or
`strategic_region_names_l_english.yml`. Current actual files
`history/states/1565-Sur.txt` and `map/strategicregions/392-Sur.txt` show why the
new-body geography must be checked when selecting the canonical text.

Produce a dry-run patch with one retained definition per key and preserve BOM,
`l_english:` headers, tokens, spelling and line endings. Equal-value duplicates
can be consolidated mechanically. The **2,599 different-value conflicts** need
a reviewed retention decision: examples include
`VICTORY_POINTS_1566_ROQ` (Rhivendelle/Rhivendell), and BASILISK numbered
Torment Nexus names versus named locations. Do not automatically select the
last-loaded file or discard human-written variants. The complete values and
source line numbers are in the inventory.

Check `common/scripted_localisation/` consumers; retaining the same key does
not require renaming those references. If distinct meanings genuinely require
new keys, update their consumers in the same patch. Inspect any name generator
that would recreate the duplicate VP definitions.

Acceptance: exactly one loaded English definition per affected key; no new
missing references or loss of authored text; no collisions in fresh `text.log`.
The existing `loc_analyzer.py` has no CLI options and overwrites
`loc_analysis_results.txt` (`main`, lines 329-480). Run its actual interface
with output safely redirected/restored; use a separate duplicate-key check
because its dictionary loader discards earlier duplicate definitions.

### 8. Remove remaining audio and flag warnings without content changes

The 15 missing songs are playlist references in `music/sabatonsoundtrack.txt`
and `music/sabatonsoundtrack_vol2.txt`. The mod's only `.asset` file,
`music/lok_music.asset`, registers `Brad_Cypy-Robotic_God`; it does not register
these songs. First check installed/enabled DLC assets and the active playset.
Remove or correctly isolate only orphaned optional playlist registrations;
preserve available DLC/custom music. A zero chance weight is not proof that a
missing registration will stop logging. Do not substitute unrelated recordings.

Convert only the 198 implicated TGA files under `gfx/flags/`, `medium/`, `small/`
from 24 to 32 bits. Preserve decoded RGB, dimensions, orientation and existing
alpha semantics; new opaque alpha must be 255. The inventory resolves fallback
paths and records original dimensions/hashes, avoiding 210 repeated rewrites.
Keep the painter/importer flag writers consistent if either reintroduces RGB
output. This is a format/performance warning, not evidence that flags are absent.

Acceptance: no missing-song messages under the relevant DLC configurations;
all 198 files are valid 32-bit TGA with identical RGB/dimensions and render at
all three sizes; all 225 baseline audio/flag records disappear.

### 9. Isolate external descriptor warnings and complete game validation

The six descriptor IDs are `2735339350`, `3305141798`, `3368690477`,
`3446246309`, `3679587713`, `3718330259`. These are other `mod/ugc_*.mod` files,
not this mod's `descriptor.mod`. Reproduce with only Legacy of Kattail DEV
enabled; establish whether the launcher scans subscribed descriptors even when
inactive. If warnings remain, report them separately for update/removal in the
launcher or the owning mods. Do not edit external subscriptions as part of a
patch to this repository. Do not inspect the Private variant.

Run each implementation milestone as a reviewable patch, with:

```text
git -c core.fsmonitor=false diff --check
git -c core.fsmonitor=false diff --stat
git -c core.fsmonitor=false diff
python -B tools/validate_map.py
python -m py_compile <each modified Python script>
```

Add focused checks for seam crossings, valid capital/deployment ownership,
equipment/template compatibility, name/portrait coverage, shared slots,
localisation duplicates/encoding and flag pixel preservation. Use existing
test entry points only after reading their interfaces. Use CWTools when an
actual executable/editor diagnostic source is available; do not assume it ran.

Archive the baseline logs, launch with debug logging, enter a fresh `100.1.1`
campaign and exercise every affected GUI/country path. Advance time to exercise
the startup and recurring behavior, then compare **both** `error.log` and
`text.log` against the inventory. Do not suppress errors or stop after reaching
the main menu. Completion means no unresolved mod-owned baseline families and
no newly introduced errors, with any external Workshop warnings clearly separate.

## Validation actually performed during this analysis

- `git -c core.fsmonitor=false status --short`: initially clean. Git fsmonitor's
  IPC endpoint failed with the unqualified command, so subsequent Git commands
  explicitly disable fsmonitor without changing configuration.
- `python -B tools/validate_map.py`: exit 0, reporting 21,515 provinces,
  20,926 state-assigned provinces, 413 strategic regions and no X crossings.
  **Qualified result:** independent seam scan found the two omitted crossings.
- Read-only Python analysis: all 1,526 records assigned, sums reconciled to
  1,528 lines; all 3,542 localisation collisions indexed against current source;
  actual TGA headers verified as 24-bit for all 198 resolved paths; current
  state owners/capital ownership and TEM deployments parsed; local technology
  unlocks and current installed GUI counterparts inspected.
- No implementation tests, CWTools checks or in-game validation were performed.
- Direct current HOI4 Wiki map/portrait pages returned HTTP 401. This plan relies
  on local project documentation, the actual installed game and its generated
  effect documentation; third-party mirrors were not used as engine authority.

## Unresolved decisions and next action

No repair is blocked from starting: milestone 1 is concrete and source-backed.
Later decisions include intended replacement capitals; whether the automatic
army policy should adapt to technology or grant a common baseline; approved
reuse for missing name/portrait pools; and conflicting authored names. Inspect
existing design evidence before requesting those decisions. Do not claim these
content choices or the two seam pixel edits have already been settled.

Next implementation action: port the missing 1.20 GUI windows/children into
the five existing overrides and isolate the inherited ROM GUI, preserving
custom behavior. Update this plan and CURRENT_STATUS after each verified patch.

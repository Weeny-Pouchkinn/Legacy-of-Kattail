# Current status

## Live painter progress recovered and closed (2026-11-27)

Recovered 14 pending file changes via native Save save_20261127_180401_868855;
user then closed painter, independently verified by zero remaining windows.
Resolved stale icon-file snapshots using guarded temporary restoration of the
exact expected sources, without disabling the conflict guard or discarding data.
Archived raw session/baselines and 16 verified final files; reapplied flat paths
for all three saved EaW icons, including newly saved colonial_troops.tga.
All non-path session files and image bytes are unchanged. Scripts/loc validate.
ZIP CRC and every final-file hash pass. No code changes or engine launch.

Recovery: legacy_of_kattail_painter/backups/session_recovery_20261127_180150_909272/
PainterProgressRecovery_20261127.zip. Exact sources, user-assisted Save/close,
backup paths and validation: session_progress_recovery_20261127.md. Current mod
already contains the recovered progress; reopen painter normally to continue.

## Flat EaW icon paths and own-image import (2026-11-27)

User explicitly superseded the earlier hash/source-subfolder runtime layout.
EaW imports now use gfx/interface/ideas/eaw/<filename>. Different art with the
same name gets a readable _2/_3 suffix; identical bytes reuse the existing file.
Catalog IDs still retain source-relative paths. Reopened flat sprites recover
original attribution from the existing per-spirit credit records, with unique
library-name fallback; no extra metadata catalog is required. Original EaW credit
paths, badges/source filters and deduplication remain intact.

Audited/applied two current saved textures: CTL_axes.tga and deserttribes.dds.
Updated interface/lok_ideas.gfx and credit Mod texture lines; deleted superseded
native files and empty hash/country folders. Images match their old SHA-256
exactly; original library and EaW credit source paths are unchanged. Backup:
legacy_of_kattail_painter/backups/eaw_flat_paths_20261127_174759_248434.
Second audit: zero changes. All unrelated user edits were retained.

Both spirit dialog and gallery now have Import icon actions for own PNG/JPEG/
DDS/TGA/BMP/WebP files. Preserve aspect/alpha on a transparent 60x68 DDS canvas
under gfx/interface/ideas/custom/<readable filename>. Custom registry sprites
use GFX_idea_lok_custom_icon_<stem>; normal spirit aliases retain GFX_idea_<ID>.
Own imports use the Mod source, remain selectable and share preview, grouped
Apply/Undo/Redo/Cancel/Save, collision protection and guarded backups. No live
custom spirit/icon was seeded by validation.

Validation: 230 tests pass; six Python files compile. Eight EaW and three own-
import integration tests cover flat paths/provenance/credits, missing library,
collisions/reuse, guarded migration/idempotence, source fitting/alpha and both
actual Tk import/Cancel/Apply/Undo/Save paths. Native existing-spirit/gallery
import/preview/Cancel passes with Save forbidden, zero callbacks and 4,226 source
hashes unchanged. Diff checks pass; no game launch. Exact files/proof/limits:
eaw_flat_paths/README.md. Restart painter before saving more icons, so the running
old process no longer creates the superseded paths.

## Owner-core audit and Cores/Claims painter (2026-11-27)

Applied 167 missing owner cores across 38 countries. All 1,898 non-excluded owned
base-history states now have their owner's core. SIL demilitarized Katown states
34/36/44/45 retain KTW cores and remain byte-identical. Third-party cores, claims,
ownership, dated history, comments and all non-owner-core tokens are preserved.
Guarded backup: legacy_of_kattail_painter/backups/
owner_core_audit_20261127_164250_453011. Second audit proposes zero changes.

Owners has Ownership and Cores/Claims categories. Transfer Cores defaults on:
ownership reassignment adds the new owner's core and removes only the previous
owner's core. Same-owner strokes are no-ops. Off leaves cores/claims unchanged.
Shared by brush, state editor,
inspector owner action and native field/source edits. Independent Cores/Claims
shows selected-country cores green, claims yellow (core takes priority), and
blue ownership stripes, including gray owned non-core/non-claim states. All
registered tags are listed, including landless tags. Left/right add/remove cores;
Shift-left/right add/remove claims; middle-drag pans. State/region brush scopes,
Undo/Redo/Save, overlays and current-view export share the existing paths.

User explicitly supersedes the earlier capital-ownership guard: edited capitals
must reference a defined state but may be outside ownership, even when the
country owns other land. No capital or territory is reassigned automatically.

Validation: 224 tests pass (seven new core integration tests); 10 Python files
compile; map validator passes before/after (21,515 provinces, 20,926 assigned,
413 regions, no X crossings). Native UI/model/Undo probe passes using verified
landless AAA, with Save forbidden, no callbacks and 4,225 unchanged source hashes.
KTW owns land and was not used as the landless fixture. Diff checks pass. No
engine launch. Exact files, paths/hashes/proof and limits: core_audit/README.md.
Next: restart painter to load controls; inspect new state history in a fresh game.

## EaW national-spirit assets and credit records (2026-11-27)

Painter now reads the supplied assets/eaw_ideas tree: 3,398 DDS/TGA images,
all decoded successfully; five PSD working files excluded. Minister filtering
leaves 2,219 selectable EaW images (4,420 combined choices). Gallery has Mod /
Vanilla / EaW source checkboxes, remembered for the session and reflected in
the dropdown. The user's eaw sun.png was copied exactly to assets/eaw_sun.png;
its lower-left UI margin is separate from the source/game icon.

Actual Apply imports exact asset bytes to gfx/interface/ideas/eaw/<hash>/<path>,
registers the existing GFX_idea_<spirit> convention and stages an EaW Credits.txt
entry with original gfx\interface\ideas path and national-spirit ID/name.
Credits and images share atomic Undo/Redo/Cancel/Save; identical uses deduplicate.
Existing human notes/BOM/newlines are retained. Runtime path retains EaW origin
and original source path after reload, without requiring the library then.
Installer copies the library and credits; no live spirits/assets were seeded.

Validation: all 217 tests pass; four Python files compile; native existing spirit
and gallery filter/search/select/preview/Cancel passed with Save forbidden,
zero callbacks and 4,226 native hashes unchanged. Native image import/credit
Save/reload is exercised in disposable fixtures. Global diff --check passes.
No game launch. Exact paths, source evidence and remaining limits:
eaw_spirit_assets/README.md and verification.json. Next: restart painter; Apply
then Save actual choices to record their usage in the credits file.

## National-spirit icon picker excludes minister portraits (2026-11-27)

Both searchable dropdown and gallery use CountryStore.spirit_icon_catalog.
Portrait paths/names and standard small/large portrait dimensions are excluded,
including texture aliases and plain-named vanilla ministers. Header dimensions
are cached per texture and image draft. Full icon registry still loads/previews
and preserves existing assignments. No native assets changed.

Native catalog audit: 3,617 registered, 2,201 selectable, 1,416 excluded; known
mod/vanilla ministers removed and genuine spirit icons retained. All 212 tests
pass, including mapped Tk picker/Apply and image replacement/Undo regressions;
three Python files compile; diff --check passes. No engine launch needed for this
painter-only change; none claimed. Exact files/sources/limits:
spirit_icon_picker.md. Next: restart painter to load the filtered choices.

## Land-AI live-log parser and construction pin repair (2026-11-26)

Source fixes applied on Painter-Test; fresh-campaign engine confirmation pending.
The first actual post-change log exposed nine failed AI-role entries, 90 tag
parser errors and 1,967 role-none messages after the introduced empty blocked_for
lists. Replaced them with nonempty PLR/HAR/KAR exclusions, all valid tags already
excluded by target eligibility. Roles/compositions/priorities/upgrade links and
land balance changes are preserved. The prior static pass missed this loader
hazard; the validator now rejects empty/ambiguous lists and the real failing file.

Restored exact installed-vanilla production_building_line_entry.pin_icon,
addressing 12 GUI errors; existing sprite/tooltip are verified. Startup checks
now require the widget. Land checks pass 24 targets/2,080 scenarios, nine filters
and four negative fixtures; source-boundary checks prove only the pin changed
in the GUI. Both modified Python validators compile. Original log rejection
test reports the known 9 missing-role / 1,967 role-none / 12 pin failures.

Evidence, exact paths and commands: plans/land-ai-implementation.md, first live-log
repair section. Pre-fix sources/log are in ignored backups/land_ai_error_fix_20261126.
Six external Workshop descriptor warnings are untouched; 21 invalid-order and
20 dropped-command warnings need fresh-log assessment before assigning causality.
Next: user restarts, starts fresh, opens Construction and advances roughly a week;
inspect the new log (optional validate_land_ai.py --error-log PATH). No live
clearance is claimed until that log exists.

## Land AI, 1.5x ordinary frontage and mechanized equipment (2026-11-26)

The validation record in this entry predates the first live-log repair above.

Implemented on `Painter-Test`; gameplay balance and engine behavior remain
unverified. Exact files, IDs, native references, commands and limits:
`plans/land-ai-implementation.md`. Supersedes the land-only planning restriction
and pre-change width/mechanized findings in the reconnaissance entry below.

Ordinary terrain is 1.5x installed vanilla (including extra directions); custom
terrain/map assets unchanged. Regular mechanized no longer consumes 50 AT.
Generic infantry is foot infantry with 12/18/20-width stages. Added explicit
mobile/assault roles, 20-width starters, 30-width medium/mechanized armor and
a gated 35-width alternative. Garrison/suppression/specialist templates are
affordable and staged; 24 targets total. New country-scope predicates/policies
exclude Paluush/non-playable countries and add no recurring scripted scans.

Economies below 10 military factories do not request an expensive land arm;
armor-oriented regional economies (10-29) aim for 2 or 4 equipped divisions;
industrial economies sustain armor/mobile forces with guarded mechanization.
Native weights are objectives, not hard training-queue caps. Added replacement/
upgrade-reserve floors, rifle-shortage prioritization and land research bootstrap.
Tank design XP follows force eligibility/inherited armor; basic medium fits
gain radio/three-man turret/medium-gun candidates. Modern-family fits disabled.
Corrected land calendar switch to 104 and neutralized conflicting expensive
doctrine role contributions. Aircraft/naval policy effects and sources preserved.

Validation: land validator passes 24 targets / 2,080 scenarios plus reference,
organization, reserve, module, terrain, encoding and source-boundary checks.
Map validator passes (21,515 provinces / 413 regions); startup validator passes
(56,544 localization keys/layers / 159 modern and 53 basic equipment contexts).
Python compilation and task diff/whitespace checks pass. No CWTools CLI found;
no game/observer campaign run. Baseline was initially clean Git HEAD; six native
files modified, two added, all 4,355 other original native files unchanged.
Next: fresh-campaign checks of field upgrades, 2/4 regional demand transitions,
production/queue behavior and AIFC at 104/108. Aircraft remain deferred.

## AI competence reconnaissance and proposal (2026-11-26)

Historical reconnaissance before the implementation entry above. Proposal:
`plans/ai-competence-proposal.md`. Verified legacy-vs-NSB priority mismatches,
WWII calendar checks, universal motorized infantry targets, a requested mobile
role without a dedicated target group, commented plane/naval design AI and
existing doctrine Force Concentration hooks. Ordinary terrain widths are twice
the vanilla guide values; mechanized consumes 50 AT equipment per battalion.
No modern-tank technology equipment unlock found in active research; proposal
uses existing light/medium/heavy families and excludes `modern_armor`.

Compared online template advice with current units/equipment/tech/OOBs and
installed 1.20.1 primary AI docs. Read-only parser inventory found no unknown
module/category tokens in tank AI prescriptions, including repeated module
containers. All 30 local proposal links resolve; task-scoped whitespace checks
pass. Global diff check reports pre-existing portrait whitespace warnings.
No game, observer campaign, CWTools or balance test performed; numbers are
proposed benchmarks. Descriptor remains supported 1.17.* / version 1.15.*.
Next, if implementation is requested: repair selection/progression and prove
small-country/AUR field upgrades before expanding military profiles. Modular
aircraft AI remains coupled to designer-restoration feasibility.

## Painter script formatting audit and repair (2026-11-26)

Audited 41 painter Python sources plus direct generation gateways. Native Save
now formats only changed Clausewitz containers with actual nesting tabs and
expanded complex definitions. Small inline parameters/lists retain nearby
native style. Shared field insertion uses syntax depth rather than line column.
Formatting runs after span-based edits, before guarded native writes and CLI
output hashes. Earlier claims of exact source-layout preservation are superseded
for edited containers only; tokens, comments, order and unedited scopes remain.

Applied whitespace-only repair to 180 native files using 63 Save manifests as
provenance. Exact token/comment streams and ordered structures match before and
after for every file. Backup: legacy_of_kattail_painter/backups/
painter_script_formatting_20261126_172635_615366. Of 3,307 provenance records,
3,269 resolve; 38 lack sufficient byte witnesses and are not used for ownership.
Second dry run: zero changes. No gameplay values, IDs or localisation changed.

Validation: all 211 tests pass; 11 Python files compile; map validator passes
before and after. Real existing/new spirit dialog Apply/Undo checks passed,
Save forbidden, zero callbacks and 4,325 native source hashes unchanged.
Scoped diff whitespace checks pass. Global diff check retains 933 inherited
portrait carriage-return warnings; untouched portrait areas were not normalized.
No game/CWTools test. Full exact paths, audit, proof and limits:
painter_script_formatting/README.md. Next: restart painter to load formatter.
## National-spirit research and equipment bonuses (2026-11-26)

Spirit dialog now has Modifiers / Research bonuses / Equipment bonuses tabs.
Search/add/update/remove research-category bonuses and equipment stat bonuses,
with explicit immediate/new-variant/native-default instant mode. New equipment
targets default to immediate; existing flags and omitted defaults load unchanged.
Effective catalogs currently provide 139 categories, 393 equipment IDs/type
tokens, and 57 stats from equipment/module definitions, excluding metadata.

Writer edits only changed scalar leaves across repeated native bonus blocks,
preserving comments, unknown/nested fields and untouched variables. Optional
None API inputs preserve their entire family. Apply/Cancel/Undo/Redo/Save remain
atomic. No live game content or localisation changed.

Validation: seven focused tests and full 204-test suite pass; four Python files
compile. Real AUR_one_aircraft_rule_all mapped dialog load/search/Add/Apply/Undo/
Cancel passed with live Save forbidden, no callbacks, 4,324 native hashes
unchanged. Scoped whitespace/diff checks pass. Game and CWTools not run. Exact
files/IDs/native syntax sources/limits: spirit_research_equipment_bonuses/
README.md and verification.json. Next: restart painter and exercise saved bonus
effects in a fresh campaign.

## Air/naval designer reconnaissance and plan (2026-11-26)

Planning only; no game content changed. Inspected branch is `Painter-Test`.
Older branch statements below remain historical. Detailed evidence, proposed
reskins, milestones and validation gates: `plans/air-navy-designer-restoration.md`.

Verified 86 aircraft and 95 naval modules remain. Designer research tabs are
hidden, BBA research and generic plane/naval AI templates are commented out,
and all nine naval archetypes lack slot blocks. Existing aircraft and naval
localisation already establishes jets, nuclear ramjets and railgun warships.

Proposed approach: freeze current module IDs, prove one existing fighter and
frigate, then restore research/default fits/GUI/AI with existing components.
Cruiser equipment says screen while its sub-unit says capital; intended behavior
needs engine verification. Nuclear engine names alone cannot supply endurance;
fixed special equipment remains the initial fallback. No architecture has been
implemented or validated in game. Installed references are 1.20.1, while the
unchanged descriptor declares supported 1.17.* / version 1.15.*.

Validation: read-only source/reference searches and comment-aware module/tech
inventory; Git diff checks and local Markdown-link checks. Live wiki pages
returned 401. No CWTools/game launch, localisation or map edits. Next concrete
action, if implementation is requested: milestone 1 on the intended branch.

## Vanilla modifier catalog and national-spirit picker (2026-11-26)

Fixed the spirit picker/save check treating tooltip categories as scope rules:
army_core_defence_factor and other army/air/production modifiers are available.
Only synthetic military trait stat fields stay excluded from spirit lists.
Shared catalog now expands the engine documentation's actual Modified types,
preserving case, section boundaries, duplicate-template category unions and
custom overrides. Carries precision and Boolean metadata; spirits accept yes/no
for Boolean modifiers. Wonder help correctly labels categories.

Independent audit: 722 fixed + 3,806 parameterized vanilla IDs = 4,528, all present
in catalog and spirit picker. Total catalog 4,581 / spirit choices 4,569 including
custom definitions, excluding 12 military stat fields only from spirit choices.
Validation: 197 tests pass, six Python files compile; real native spirit exact-ID
search/Add/Apply/Undo and trait picker/Cancel passed with Save forbidden, zero
callbacks and 4,324 native hashes unchanged. No live game content edits. Game
effects/CWTools untested; wiki returned 401 and searches had no results, so
installed primary documentation was authoritative. Full paths, primary lines,
coverage and proof: vanilla_modifier_catalog/README.md, coverage.json,
verification.json. Next: restart painter to load the rebuilt shared catalog.

## Flag symbol picker / Small checkerboard (2026-11-26)

Fixed pre-modal validation in FlagLibraryPicker: 1x1 render collapsed eight
checkerboard columns into inverted rectangles, producing the screenshot's x1/x0
error. Uses existing THUMB (144x92) now. No symbol geometry or game data changed.
Mapped two-symbol checkerboard/Small-checkerboard gallery regression passes,
including green 2x-stretched second symbol, background/symbol acceptance and
grab cleanup. All 31 country/flag tests pass; two Python files compile; all 56
backgrounds render at validation size. Exact files/details: painter MODLOG entry
"Symbol picker with small checkerboard background". No engine test needed for
the UI; no engine verification claimed.

## Imperium shared colors (2026-11-26)

Removed Imperium color uniqueness/reserved-gray restrictions from Apply and
Save; the dialog now says Map color. Distinct elements/states may share any
valid RGB while retaining their IDs and tooltips. Earlier uniqueness notes are
superseded. No native data changed. Three Python files compile and all 10 focused
Imperium tests pass, including duplicate/gray Save/reload with distinct pointers.
Details and exact files: katzenartig_imperium/README.md (color policy update).

## Generic Portrait Groups and country/species integration (2026-11-26)

Added Characters > Generic Portrait Groups: 101 reserved species slots and both
special groups. Altarian labels Species_61 dynamically and retains placeholders.
Role/ideology/gender pool editor supports upload/add/replace/remove with 156x210
large and automatically generated 65x67 Ministermaker small TGAs, previews,
atomic drafts/Cancel/Undo/Save. Shared pool changes update group countries while
preserving their unrelated fields. Vacant pool templates persist only when
needed in legacy_of_kattail_painter/generic_portrait_groups.json; native blocks win.

Species creation automatically allocates its matching slot, including placeholder
registrations beyond 100. Fixed native default layout is independent of editable
Species_0. Country Setup selects a group, suggests national species for new tags,
preserves explicit overrides, and moves native tag pools without duplication.

Coupled native repair: corrected 140 Amphibian + 980 Roqualian sprite references
to the existing registered names; all 38 referenced large/small pairs verified.
151 country blocks and original bytes otherwise unchanged. No live species,
country membership, history, localization or image content changed for this task.

Validation: 192 tests pass including 10 new; nine Python files compile. Actual
native mapped UI probe passes, live Save forbidden, no callbacks; 4,328 native
sources unchanged by probe. All 103 groups' large sprite references resolve.
Scoped code/new source whitespace checks pass. Global diff --check flags 416
changed portrait lines with inherited CRCRLF; before/after byte-only prefix
comparison proves no added line-ending damage. No game/CWTools test. Exact files,
sources, audit/recovery: generic_portrait_groups/README.md, native_repair.json,
verification.json. Next: restart painter, choose/upload a pool and country group,
Save and verify generated leaders/scientists/operatives in a fresh campaign.

## Current error-log audit and repair plan (2026-11-25)

Analysis only on actual branch Painter-Test, HEAD a5958d259. Inspected the fresh
local logs/error.log (22:17:30 UTC), installed HOI4 1.20.0.0.8873, companion
text.log and current sources. Classified all 1,526 timestamped records / 1,528
physical lines into 16 families. No game content or descriptor changes.

Major findings: outdated GUI contracts (including two undefined windows),
startup army templates requiring unavailable equipment, missing random name and
scientist portrait pools, ownership/capital/deployment mismatches, 21 overfilled
states, 198 distinct 24-bit flag files and orphaned Sabaton playlists. text.log
expands one collision warning into 3,542 duplicate keys (2,599 differing values).
Six Workshop descriptor warnings belong outside this repository.

Correction to earlier map-validation confidence: the current validator passes,
but its X-crossing scan omits horizontal wrap. Independent current-bitmap scan
finds two seam crossings matching the fresh log's x=4095 region. Earlier
validator pass statements describe the checks actually performed, not proof of
seam correctness. Imperium's earlier empty-scaffold statement is historical:
current user-authored definitions/assignments were observed and preserved.

Validation: read-only classification/count reconciliation, source/reference
checks, flag-header checks, current-state parsing and python -B
tools/validate_map.py (exit 0, qualified by verified seam gap). No game launch,
CWTools or implementation tests. Full ordered plan, exact sources/paths,
acceptance checks and open design decisions: plans/current-error-log-fix-plan.md.
Complete message/key/path inventory and source hashes:
error_log_audit_20261125/inventory.json. All repair milestones remain pending.
Next action: patch the five GUI overrides against installed 1.20, isolate the
inherited ROM scripted GUI, and verify those interfaces in a fresh campaign.

## Katzenartig Imperium elements and mapmode (2026-11-25)

Implemented States > Katzenartig Imperium with reusable, editable objects in the
same definition database as cultures/species. Each has stable ID, unique RGB,
name and fully manual immediate/delayed text. Left-drag assigns whole states;
right-drag/No element erases, Shift picks. Shared edits propagate; native
Undo/Redo/Cancel and guarded Save apply. Real hover previews show delayed text
after 650 ms, substituting [FROM.GetName]. Names, overlay and export supported.

Installed empty native scripted mapmode, two tooltip dispatchers and BOM English
localization. Element color branches are the catalog; base-history variable
lok_katzenartig_imperium_element is the state pointer. No historical elements or
territory were invented; user defines the extent. No runtime world loop.

Validation: 169 tests pass, eight modified/new Python files compile, map validator
passes (21,515 provinces / 413 strategic regions). Real-mod Tk workflow passed
with live Save forbidden and 4,321 native files unchanged; no callback errors.
Task whitespace checks pass; global pre-existing whitespace remains. Game and
CWTools untested. Exact files/IDs and evidence: katzenartig_imperium/README.md,
verification.json and scaffold.json. Next engine check: author an element, paint,
Save, restart game/new campaign and inspect color plus immediate/delayed tooltip.

## Species/culture map colors and optional groups (2026-11-25)

Fixed painter color writes: literal RGB operands only, every matching duplicate
branch, nearest 0.001 native fractions. Culture 103 had three divisors overwritten
by its RGB literals, producing over-range white; restored num_cultures operands.
Culture averaging no longer includes a gray seed; uncultured gray preserved.
Species mapmode now initializes RGBA in both layers, including transparent
no-minority overlay. Altarian 61 remains #9DFFFF (.616/1/1 in both layers).
The user's reported white Altarian appearance has not been engine-retested;
undefined top-layer output is a plausible cause, not a confirmed diagnosis.

No group supports new/existing cultures, correct array/trigger membership
removal/restoration, and preserved authored ungrouped full descriptions. No
native group/history/localization migration was made. Only the two native
mapmode files were repaired with exact guarded backup; user data retained.

Validation: full painter 160 tests; six focused tests after final tooltip change;
four Python files compile. Native-operation interpreter: 62 majority, 62 minority,
102 culture colors all match painter palettes. Real native Altarian/color and
ungrouped culture 8 UI Apply/Undo passed, no callbacks/drafts, live UI Save
forbidden and 4,213 native hashes unchanged. Map validator passes. Scoped task
whitespace checks pass; global retained/user data has pre-existing whitespace.
No game/CWTools check. Details/files/source locations/recovery:
demographic_map_colors/README.md, audit.json, verification.json. Next: restart
painter and HOI4 and inspect Altarian majority/minority rendering and culture 103.

## Map names, geographic seasons, equator and PNG export (2026-11-25)

Display names now remembers state/region/VP families (defaults off/off/on),
independent of numbers and saved-overlay names. Removed both painting/sidebar
and region-form North/South selectors. Hemisphere always follows exact region
area on the bottom-aligned 2:1 main planet (rows 1024..3071, equator y=2048).
Account for latitude starts on and controls only thermal smoothing inside
+/-10 degrees; rainfall remains climate-led. Off-world regions use direct weather
editing, not an invented main-planet hemisphere. Display equator starts off and
is available in every map mode; current-view PNG export includes overlays,
labels/reference line and crops to actual visible map bounds.

Per explicit user request, all 276 recognized main-planet Koppen regions were
evaluated retaining class: 29 weather files updated, including nine hemisphere
corrections. 247 already match at native precision. One recognized off-world EF
region (282) and 136 custom/unrecognized regions unchanged. Only weather blocks
changed; 4,185 protected sources remained byte-identical. Reapplication backup,
region IDs/latitudes and exact hashes are in map_labels_latitude_export/
reapplication.json. Earlier manual-hemisphere instructions are superseded.

Validation: geography 42 tests, full painter 154 tests, modified Python compilation
and map validation pass. Actual native mapped Tk verifies defaults/independent
names/overlay snapshots, no hemisphere controls, latitude form, global equator
and pixel-exact 1055x733 PNG export. Zero callback errors/drafts; live UI Save
forbidden and 4,213 checked native hashes unchanged. Preview inspected; native
readback verifies all reapplied profiles/classes. git diff checks pass. No game
launch/CWTools; current weather remains an editor approximation. Full exact
files/commands, NASA/NOAA rationale and limitations: map_labels_latitude_export/
README.md. Next: restart painter and check changed weather in a fresh game.

## Terrain blend/trees, province categories and popularity repair (2026-11-25)

Applied refinement supersedes the first masked import's four-pixel height blend,
source normals/colors and EU4 gameplay overrides. Matched relief gain 0.622101,
harmonic correction and inward 48-pixel feather blend into native height style;
regenerated normals/native biome colors and added native tree models. Selected
forest tree cells: 460 -> 2,107; jungle: 0 -> 540. All 580 touched land provinces
now match dominant complete graphical terrain; 160 additional CSV corrections.
2,323 protected hashes and exact exterior/alpha/header/palette checks passed.
Province geometry, graphical terrain, rivers and user's railways stayed fixed.

Provinces now contains Victory points, Railways and gameplay Terrain submodes.
VP/railway features retained; terrain paints only native definition.csv fields,
with Shift-pick, native colors, Undo/Redo and guarded Save. Country writer/helpers
use exact 100% totals on the 0.001 grid. Random fills never allocate Gestalt;
manual positive Gestalt remains supported. Repaired MAJ/ANS/KHO plus PAR/SPT/CER
(same live-log failure), changing only popularity numeric values.

Validation: 148 full painter tests, 11 masked-terrain tests and compilation pass.
Native mapped Tk checks passed all three province modes, terrain Undo/Redo and
MAJ/ANS/KHO politics/random/pie readback: zero callbacks/drafts; 4,214 checked
native hashes unchanged; 1,192 hubs retained. Six repaired fixed-point totals
are exactly 100. After the user's subsequent explicit repair request, the two
impossible routes to isolated province 20841 were removed. All other railway
links/levels remain intact; map validation now passes. Recovery/verification:
railway_jump_repair/README.md and audit.json. Earlier validator failures and
protected railways hashes are historical snapshots before this authorized fix.
git diff --check passes. No game launch/CWTools. Full file list, evidence,
commands, audit/recovery and before/after: terrain_refinement/README.md.
Plan: plans/terrain-blend-province-modes.md. Next: restart painter and verify a
fresh campaign's terrain/trees and six countries' popularity pies in game.

## Masked terrain import and state-history supply hubs (2026-11-25)

Completed both current user requests. Supply reader now finds all 1,192 authored
starting hubs across native state history and supply_nodes.txt. The former
map-only overlay missed 1,146 hubs (1,137 on VP provinces). Shared building counts,
state forms and overlay agree. Removing/re-enabling a history or dual-source hub
patches its original source(s), preserves VPs/date blocks/comments and does not
resurrect it on reopen. No native supply/history/VP migration was made.
145 painter tests, 34 geography and 14 railway tests pass; compilation and native
probe passed. All 1,192 icons render and the read-only probe left 4,224 native
source hashes unchanged with no drafts. See painter MODLOG for exact evidence.

Masked EU4 import applied five map files: terrain.bmp, heightmap.bmp, world_normal,
colormap RGB and definition.csv terrain column. 363 existing province terrain
classifications changed. Preserved every province shape/ID/RGB, water/coastal flag,
state membership, city-light alpha and exterior raster pixel; 2,321 protected
hashes verified. Rivers already matched EU4 exactly inside the mask and remain
unchanged. 3,507 EU4 inland-water pixels that are HOI4 land retain existing assets
and land classification to preserve coastlines. Source EU4 files were read-only.
Five importer tests and byte/pixel readback passed; formats/headers/palettes stayed
native. Exact selection, audit and recovery: masked_eu4_terrain_import/README.md,
audit.json and selection.png. Plan: plans/masked-eu4-terrain-import.md.

Map validator before/after still has only two old railway jumps, now at lines
1308–1309 after the user's railway Save (not the previous 893–894). The user's
existing railway edit was preserved. No game/CWTools validation. Next: restart
painter, then inspect terrain/elevation/river appearance and movement in a fresh
campaign. These remain engine checks, not pending file generation.

## Province railways and supply hub display (2026-11-25)

MAP Paint/View Railways has per-province exact level/erase and left-add/right-
subtract gestures with amount, native cap and Do not add new railways protection.
Railway levels are native links: a province click changes touching links and its
display reports the highest level. New routes need neighboring painted points;
no routing through unpainted land, as explicitly clarified by the user. Preview/
Save compact equal-level links into simple native paths without changing the
network. No metadata, new hubs or native live-file changes were made.

Display supply hubs uses the existing native hub sprite in all modes/overlays.
141 full tests and 13 railway tests passed, including actual Tk gestures, source
preservation, guarded fixture Save/reload, topology/rule cache changes and Undo.
Compilation/scoped whitespace passed; global whitespace remains pre-existing.
Native UI: 5,595 links/5,259 railway provinces, all 46 hub icons, 4,224 source hashes
unchanged, no callbacks/remaining changes. Warm redraws about 40–45 ms.

Known blockers in data, preserved: map validator's two old non-neighbor jumps
(20839–20841, 20841–19461), plus two existing links across explicit impassable
borders (12662–12701 and 13081–13092; adjacencies.csv lines 39/32). New bad links
are rejected. No engine/CWTools check. Next: restart painter; verify resulting
supply/railway behavior in game after an intentional Save. See painter MODLOG and
plans/railway-painting.md. Older deferred-route proposal is now partly superseded.

## Koppen preset painting (2026-11-25)

MAP > Strategic regions has Paint Köppen, a searchable colored left preset list,
and Southern hemisphere (off = North). Click/drag writes complete 12-month native
weather profiles per touched region, including sea-only regions. Shift-click picks
the exact preset and hemisphere; custom weather keeps the current brush. Disabling
restores region edit/assignment. Each preset explicitly includes all nine native
weather fields, with climate-appropriate zeros; existing weights were retained.
Weather painting replaces custom weather but preserves all other region fields.
No climate metadata, game IDs or live native source changes in this task.

31 geography tests and 128 full-suite tests passed; Python compilation and scoped
whitespace checks passed. Native mapped Tk probe passed with live Save forbidden:
4,224 source hashes unchanged, no callback errors or unsaved changes. Fixture
Save/reload, source BOM/CRLF, Undo/Redo and all 60 profiles were verified. Global
whitespace check has pre-existing state-history issues; map validator has only
the known railway jumps at lines 893-894. No game launch/CWTools. Next: restart
the painter; in-game weather still needs checking after an intentional Save.
Details and exact paths/commands: legacy_of_kattail_painter/MODLOG.md.

## Arithmetic precision, building arithmetic and native text colors (2026-11-25)

Resources/population and both state/province building heatmaps now share per-mode
arithmetic controls and Precision range (%). Zero is exact; positive ranges draw
uniform nonnegative integer operands inside the inclusive percentage interval,
once per target per stroke. Reverse gestures subtract/divide sampled operands;
zero division is rejected and integer results round half-up. Resource arithmetic
now also returns whole numbers; precise resource entry retains decimal support.
Normal building clicks remain +/-1 when arithmetic is disabled. Native level,
coast/facility/scope checks still apply, with unchanged targets on failure.

All existing Name color selectors (cultures/groups/species) now discover native
and mod global textcolors, respecting file replacement and case-sensitive IDs.
The current effective table contains 37 codes. Searchable colored rows, swatches
and live name previews update with typing/paste and selection. Preview uses global
RGB, excluding font-local overrides. No color metadata or native GFX changes.

Focused geography and selector suites passed (27 and 10 tests). Native alpha-zero
UI checked all four arithmetic modes, all three color forms with 37 choices,
preview changes, group color Apply/Undo and no callback errors/drafts. All 2,097
checked native source hashes stayed unchanged; live Save was forbidden. Final full suite: 124 tests passed; compilation and whitespace checks passed.
Map validator retains only the two known railway errors; see painter MODLOG. Deferred railway editor proposal
is in legacy_of_kattail_painter/PLAN.md; no railway implementation in this task.

## Categories, resources/population, overlays and summaries (2026-11-25)

States now offer native category create/edit/paint with native color swatches,
shared-slot used/total labels, red over-capacity and faint yellow full stripes.
Capacity is explicitly a static category/state-file check before runtime country
modifiers. Resource/population gradients support precise entry and per-state
Add/Multiply gestures (right-click subtract/divide), clamp at zero and reject
zero division. Population rounds half-up to whole people. Resource colors match
the requested palette. Resources can stripe states whose distinct positive type
count is strictly greater than the entered threshold, including in saved overlays.

Save for Overlay stores one immutable session configuration, rendered against
live drafts at the current camera; opacity and Display numbers affect the shared
raster renderer. Number labels reuse bounded text tiles (16 MiB/4096 entries).
COUNTRIES Summary reports current owned-state starting population/factories/
resources without edits. Strategic regions can color exact native weather matches
to the editor's 30x2 Koppen-inspired presets, with N/S markers and custom gray.
Matching does not store metadata. Category writers use existing native files.

120 tests passed, including fixture Save/reload, real form transactions, strict
resource-type thresholds and arithmetic/overlay edge cases. Native alpha-zero
Tk probes passed across 13 categories, 20 state buildings, 10 resources, climate
matching, country Summary, Undo and Cancel. 3,229 native source hashes stayed
unchanged; no drafts remained and Save was disabled. Warm redraws measured
36.8 ms category, 28.9 ms population, 35.9 ms buildings and 18.4 ms resources on
this machine. Map validation still has only the existing railway errors 893-894.
No live Save/game launch. See painter README/MODLOG for scope and checks.

## Country preview/save consistency and building map modes (2026-11-25)

MAP Paint/View now includes States, Provinces and Strategic regions. States and
Provinces have building submodes with scope-filtered localized palettes, count
heatmaps, positive-only numeric labels and left/right add/remove drag strokes.
All 20 native state-scope building types are listed (shared and nonshared), plus
10 province types; railway routes stay separate. Caps/coasts/placement/group rules
use the existing native state writer. Middle-drag pans. State/region forms open
directly from their map modes; region assignment transfers whole states.

Country color reading now includes draft-only native files and tag/path cache
signatures. Existing duplicate color overrides and UI-color fields synchronize
for the edited country. Apply always writes the entered popularities and refreshes
form/preview from the applied native values. Pie legend percentages are exact and
its layout accommodates all entries. Decimal percentages remain supported by the
installed effects documentation; no integer-only conversion was introduced.

113 full tests pass; 28 country tests passed again after adding an owner-map pixel
assertion. Native UI checked country Apply/Cancel/readback, 20/10 building lists,
once-per-stroke increments/decrements, no zero labels, region controls, matching
boundaries and disabled irrelevant paint scope. Final building redraws were about
50–52 ms locally. Native source hashes stayed unchanged and probes left no drafts.
Compilation and whitespace passed. Map validator still reports only the known
railway errors at 893–894. No live Save or game launch; details in painter MODLOG.

## Layered flags and country overwrite confirmation (2026-11-25)

COUNTRIES > Flags now has live color swatches/paste updates and up to eight symbol
tabs, independent colors/outlines/size/position/stretch/tilt, numeric/slider input
and hit-tested preview dragging. There are 56 backgrounds (39 added). Galleries
preview the full stack, outlines are procedural, and caches stay in memory.
Saved native flag images remain flattened; no persistent layer metadata files.
Unused-tag creation with existing definition/history sources now asks Yes/No,
including empty files; approval reuses filenames/preserves unrelated history and
stages guarded Save. Declining changes no drafts and leaves the form open.

107 painter tests passed. Native mapped alpha-zero UI checked eight actual masks,
all 56 patterns, layered galleries, 1000x730 country layout and Cancel. Cached
eight-symbol preview measured about 91 ms locally. Country/tag/flag source hashes
and drafts stayed unchanged. Python compilation and scoped whitespace checks
passed. No live Save or game launch. Details: legacy_of_kattail_painter/MODLOG.md.

## Country popularity helpers (2026-11-25)

COUNTRIES > Parties & popularity now has random allocation to remaining blank/zero
ideologies (preserving positive entries) and proportional Normalize to 100.
All-zero weights normalize to equal shares. Exact apportionment avoids rounding
drift; both actions update fields and pie together and use existing Apply/Save.
Twenty country tests pass, including four new arithmetic/actual-button tests.
No native data or identifiers changed. Details: painter MODLOG.md.

## Native state/region editors and VP layer (2026-11-24)

On Painter-Test: MAP > States / regions / VPs, sidebar/library and map
double-click entry points now edit state names, native attributes/resources,
shared/nonshared/province buildings, ownership and demographics. Regions move
whole states, reject empty regions and split/unassigned states, and edit names,
naval terrain and weather. Vanilla weather import and 30 editable Köppen-inspired
North/South presets are available. VPs have a gradient map layer, zoomed labels,
map placement/edit/remove and alphabetical base-name localization consolidation.
All data uses existing native files; no painter metadata. No reshaping, railway
route generation or map spawn generation. Restart the painter to load the UI.

All 98 painter tests pass. Isolated model/form tests cover Save/reload,
BOM/versions/comments, unknown/dated
history, building constraints, supply nodes, whole-state transfers/Undo, presets,
vanilla import, VP sorting/conflicts/variants and nested Cancel. Native alpha-zero
mapped Tk checked the three forms, map handoff/grab, minimum-size weather controls,
252 viewport VP items, all 1,902 state rows and unchanged state/region/English-loc
source hashes. Native audit: 413 regions, 1,552 VPs and 4,791 valid weather periods.
Map validation still has only the known railway errors at lines 893–894. No live
Save, game launch or CWTools claim. Exact files/commands: painter/MODLOG (full path
`legacy_of_kattail_painter/MODLOG.md`). Next action: user authoring and game checks
after saving desired edits; no implementation blocker remains.

## Visual flag background/emblem pickers (2026-11-24)

COUNTRIES > Flags arrows, entry double-clicks and Browse buttons now open visual
thumbnail galleries with a large full-flag preview. Current colors/tint/size,
name/code/fuzzy search, source filters, keyboard controls and Cancel/accept are
supported. Rendering is lazy and batched; caches are bounded in memory. No new
assets, native game IDs, data/cache files or writer changes. Restart to load it.

83 tests pass, including three new Tk gallery tests over 1,004 choices. Native
mapped Tk verified 346 emblems (35 visible thumbnails, zero failures), all 17
backgrounds, minimum-size preview layout, arrow callbacks, selection/cancel and
parent grab restoration. Country drafts and checked native source hashes stayed
unchanged. Compilation/whitespace passed; no screenshot review or live Save.
Exact files and commands: legacy_of_kattail_painter/MODLOG.md.


## Native country editor (2026-11-24)

On Painter-Test, added COUNTRIES create/edit with seven tabs: setup and capital
map pick; live party-popularity pie; ideological name/DEF bulk copying/article
helpers; native flag import/design with all/undefined copying; linked character
leaders; starting techs; national spirits/modifiers and vanilla/mod icon library.
17 recolorable flag backgrounds, independent emblem tint, existing Stellaris/EU4
emblems and native reusable DDS mask import are available. New countries register
native definitions/history/flags; Owner palette/library entry points and a Paint
on map button work. No country/flag/spirit JSON/data sidecars are created.

Edited country species/attributes live in country history as native ideas.
Game-consumed lok_country_species_defined_in_history and
lok_country_attribute_defined_in_history flags guard original startup defaults.
Selected attributes reuse native scoped research-bonus templates; untouched tags
keep the previous defaults. No new world loops or global history migration.
Existing character roles/recruitments, dated/conditional setup, unknown fields,
localization BOM and tech/equipment ordering are preserved. Forms support grouped
Undo/Redo/Cancel and native guarded Save.

Validation: 80 tests pass; compilation and scoped whitespace checks pass. All 198
native histories load, with 273 registered tags. Native alpha-zero Tk probes
covered all country tabs, flag/name bulk actions, emblem tint, leader/spirit
creation, icon previews, capital pick/Escape, Apply/Cancel/Undo/Redo and new-country
Owner painting; all 14,521 checked native file hashes stayed unchanged. A full
20-native-file Save/reload fixture passed without a character metadata file.
Guard probe left the other 197 country law setups unchanged. Two existing railway
validator issues remain at lines 893-894. No game/CWTools/screenshot validation.

Restart the painter, open COUNTRIES, edit or create, Apply, then Save. Full source
paths, native destinations, references and limits: legacy_of_kattail_painter/MODLOG.md.
Earlier unrelated working-tree changes and the separate culture/species/wonder
catalog-authoring save/reload milestone are preserved; this does not close that
separate follow-up.


## Painting performance (2026-11-24)

Optimized the existing MAP painter using EU4's viewport rendering pattern.
Only visible pixels plus a pan margin are colored; geometry, static palettes,
country colors, validated catalog parses, Tk images and wonder icons are cached.
Brushes edit immediately; redraw/inspection/status share a 25 ms frame queue,
flushed on release. Repeated motion in painted states skips brush work. Native
catalog existence checks are no longer repeated per province. Undo remains as
before, and caches are bounded and memory-only.

Same-run warm redraw at 25% zoom: culture 170.44 -> 17.75 ms, species
281.82 -> 26.27 ms, owners 251.32 -> 25.75 ms, wonder 211.37 -> 15.64 ms.
Methodology/limits and exact changed paths are in the painter MODLOG.md.
67 fixture tests and compilation pass. Native alpha-zero Tk probes verified all
nine views, pixel-exact viewport/zoom/pan/boundary rendering and actual paint,
release flush, Undo/Redo, discard and fit. All 14,521 checked native file hashes
stayed unchanged. Map validation still reports the two existing railway links on
lines 893-894. No engine/CWTools/screenshot review or game identifiers changed.

Restart the painter to use the optimization. The separate culture/species/wonder
catalog-authoring milestone still needs its full save/reload verification; this
performance task verifies rendering and painting, not every authoring workflow.


## Trait database and commander randomizers (2026-11-24)

Added CHARACTERS / Trait database with General, Admiral, Political advisor and
Other unit views. Reads installed vanilla and mod trait folders; shows origins,
active/overridden definitions and name/ID search. Current data: 3,960 definitions,
1,695 active, 775 searchable modifiers. Native modifier docs/custom definitions
and English localization supply labels/categories. Vanilla is inspect/clone;
file constants resolve on cloning. Mod definitions edit in place. New user traits
write alphabetically to the appropriate common/unit_leader/lok_traits.txt or
common/country_leader/lok_traits.txt and BOM English strings to
localisation/english/painter/traits_l_english.yml. No live dummy traits created.

Military role dialogs roll base skills from current level with active skill
bounds/defines (vanilla 4 + 3*(level-1)), keep level, and roll a chosen count of
generic vanilla traits. Add/replace modes preserve custom/status/scripted traits
and avoid incompatible/unavailable/restricted choices. Field marshals can carry
general traits, matching 25 existing mod cases. All rolls stay local until Apply;
Cancel/Undo/Save guards hold across trait and localisation edits. Existing
character/portrait edits from save_20261124_172934_590513 are preserved.

Validation: 61 fixture tests, compilation, native hidden-Tk source/catalog/
randomizer/editor checks and read-only real verification. All 10,864 current
source hashes unchanged during checks; four pre-existing OOB brace errors remain.
Unchanged view refresh 0.1–0.2 ms, warm role 0.110 s, skills 0.024 s, traits
0.0044 s measured. Changed-code whitespace checks pass. Whole diff still flags
existing common/characters/LOK_eu4_import_characters.txt:35 whitespace.

Historical character migration audit is now stale after the existing save:
portrait GFX, character metadata and English character localisation differ.
Do not revert those authored edits or rewrite the old snapshot to claim a pass.
No live game sources/assets written by this task; future trait files are created
on user Save. No in-game/CWTools/screenshot validation. Exact files/commands and
source references: legacy_of_kattail_painter/MODLOG.md and
plans/trait-database-randomizers.md. Next: restart painter; test saved traits and
tooltips in a fresh game. No editor implementation blocker.

## Painter performance and localized selectors (2026-11-24)

Optimized character-localization prefix matching (removed the measured 87.6
million comparisons), targeted cache invalidation, per-file parsing/catalogs,
batched role edits, unchanged identity and bounded decoded/Tk portrait caches.
Profiled identity apply went from 53.463 s to about 0.52 s; save preparation
29.209 s to about 0.20 s (profiling overhead included). Actual Tk military-stat
apply 0.0256 s, refresh 0.0338 s, warm character/role dialogs 0.190/0.131 s.
First role dialog still loads native names once (1.078 s measured).

All dropdowns accept typing. Localized names precede IDs in parentheses;
alphabetic name/ID ordering, both-field matching, accent/case normalization,
fuzzy suggestions and keyboard/mouse selection share ChoiceBox. TraitChoices
supports multiple localized traits. Country/portrait galleries, nation/tag
filters and map/source/emblem lists use names/IDs consistently. Stored values
remain raw native IDs. New portrait tags can still be typed directly.

Validation: 51 tests, native hidden-Tk interactions with zero callback errors,
Python compilation, original character migration audit and real-data map/tool
checks pass; all 10,863 checked source hashes unchanged. Four pre-existing OOB
parse errors remain. No game content or assets modified for this optimization.
Exact files, commands and measurements: legacy_of_kattail_painter/MODLOG.md and
plans/character-performance-selectors.md. Reproducible read-only benchmark:
`python -B legacy_of_kattail_painter/benchmark_characters.py --profile`.
Next: restart the painter. No remaining implementation blocker; no in-game or
screenshot validation claimed. External source edits still require reload.

## Character workspace and Ministermaker (2026-11-24)

Implemented on Painter-Test: MAP retains existing painting/tools; CHARACTERS has
localised-name/nation galleries, 284 characters (12 unrecruited), native repeated
roles/traits/stats/recruitment and description/credits editing. Independent
portrait library contains 2,565 large/small pairs, arbitrary three-character
tags, additional linked variants and per-native-slot assignment; pair creation
also works inside character editing. Drafts, nested Cancel, Undo/Redo and guarded
Save cover new text/JSON/localisation and binary assets with backup/rollback.

Applied alphabetic tag/neutral-name character localisation and portrait GFX
organisation. All 51,295 English values and 284 character identities/recruitments/
roles preserved. Moved 726 large/source + 682 small original assets; every byte
hash matches. Added 42 derived small portraits, reused two authored images.
Generate small portrait exactly matches the supplied Ministermaker main script
(37x51, 5 degrees, centred 65x67, original border at 8,1), including pixel parity.
An initial overwrite of two small originals was caught/restored from backups;
the regression fix reuses existing art and guards destination collisions.

Validation: 42 fixture tests, 12 Python compilations, read-only audit of 2,869
paths/backups, repeated-Save idempotence, hidden Tk sorting/filter/layout/generator
Apply/Save/reload/Cancel checks pass. Real-data read-only checks preserve 10,863
hashes. Localisation analyser has identical pre/post 2,285 missing-key sets.
Exact paths, identifiers, backups and commands: legacy_of_kattail_painter/MODLOG.md
and plans/character-refactor-audit.json / character-workspace-files.txt.

Limits: five pre-existing generic source textures and ten character sprite
references remain unresolved in available indexes; four existing OOB parse errors
remain. No in-game/CWTools or screenshot validation. No state/map topology work
belongs to this change; concurrent duplicate-history cleanup is preserved below.
Next: restart painter; verify portraits and edited roles in a fresh game.

## State-history duplicate cleanup (2026-11-24)

Current branch verified as Painter-Test. Audited all 1,902 state files and repaired
46 duplicate-history files: removed 39 second ZZZ blocks and merged seven
same-owner blocks (151, 284, 556–559, 953), preserving unique VPs/buildings/claims
and later overlapping building values. All states now contain one history.
Existing edits, state demographics and root data are preserved. One trailing
space in state 557's province list was removed to pass diff validation.

Validation: all state files parse; 1,856 untouched hashes match; all seven merged
VP/building maps and 39 primary histories match originals. Four regression tests,
Python compilation and diff checks pass. Map validator now rejects duplicates;
its only remaining errors are the pre-existing railway links at lines 893–894.
Importer state reader now also rejects duplicate/missing histories. No game test.

Correction to the earlier EU4-import validation note below: that verifier selected
only the first history and did not prove uniqueness. Earlier hashes/counts describe
its snapshot; they are not a current validation after user edits and this cleanup.
50 files have other repeated root resources/scalars, intentionally left unchanged.
Full results/exact paths: state_history_audit/README.md, audit.json and files.txt.
Next: in-game ownership/building check; no duplicate-history implementation blocker.

## EU4 nations in ZZZ territory (2026-11-24)

Installed on Legacy-of-Kattail-Main: 39 countries receive 320 former ZZZ states;
84 remain ZZZ. Reused 34 identities (12 dormant), with LRN -> LAK and NOV -> NFS;
new tags ELC/HIV/INT/MAG/WMD. User explicitly retained all states and excluded
Meogartha. Added missing histories/source leaders, native-sized source flags,
source colours and country species laws. Preserved existing country history/text,
state demographics, all map data and unrelated working edits.

Validation: importer verification passes 631 game output files and 12,102 protected
files. 320 states match originals outside owner/core changes; 234 flags pass exact
pixel/dimension checks. 82 new localisation keys are unique and BOM/header pass.
Localisation analyser's pre/post missing-key sets are identical (2,285); Python
compilation and diff checks pass. Map validator still reports only the existing
railway errors at 893-894. No CWTools executable or in-game validation.

Limits: whole-state geographic approximation; WMD uses its only assigned state 331
because its source capital does not overlap eligible land. Missing histories use
an explicit small starting baseline; unrelated/missing OOBs become an empty OOB.
No force/balance or mission conversion. Existing authored country names prevail.

Exact paths, country mapping, source provenance, validation and recovery:
`eu4_zzz_import/README.md`, `files.txt` and `audit.json`. Tool:
`tools/import_zzz_from_eu4.py --verify`. Originals:
`work/zzz-eu4-import/before/`. Next action: fresh campaign/startup-log check.

## Species invariant, boundary toggles and region brushes (2026-11-24)

Completed on `Legacy-of-Kattail-Main`, based on `ee25bc98`:

- Equal majority/minority species now clears the minority to 1000 in shared
  setters, load/normalisation, raw source edits and the pre-save hook. Majority
  1000 is rejected because it denotes None, not a species. Corrected the three
  existing equal pairs: 447 (1), 888 (44), 1040 (0). Only each minority changed;
  originals are in legacy_of_kattail_painter/backups/save_20261124_104605_259819/.
- Independent boundary toggles draw province/state/strategic-region lines at
  1/2/3 screen pixels. They are off by default and cached at the current zoom.
- State/Strategic region scope applies to culture, majority/minority and owner
  brushes. Region membership comes from map/strategicregions, not country tags
  or a hard-coded state list. Each regional action is grouped for undo/redo,
  deduplicated across a drag and rolled back completely if an edit fails.
  Split states block region painting before any changes. The current 413
  regions have no split states or ambiguous province memberships.

Validation: all 24 fixture tests and four Python compile checks pass. Exact
boundary pixels and width after zoom, source/Save invariant, region membership,
owner/demographic brushes, grouped undo, exclusions, split-state rejection and
failure rollback are covered. Real-data Tk checks passed all toggles, all eight
views, normal/minimum layouts, region 1's five-state painting/undo/redo and raw
source auto-repair. `verify_real.py` passed 1,026 mask-size renders and 10,786
unchanged source hashes during UI-only checks. Existing EUL/GAL/KKN/KTZ OOB brace
errors remain. Map validator before/after has the same railway errors at 893-894;
no map files or localisation changed. Full diff and encoding reviewed.

Next action: restart the painter, select Paint scope and boundary checkboxes.
No new implementation blocker; no in-game validation or screenshot review is
claimed. Map memberships are startup snapshots; restart after topology edits.
Exact changed paths and commands are in legacy_of_kattail_painter/MODLOG.md.

## Persistent state painting and demographic migration (2026-11-24)

Completed on `Legacy-of-Kattail-Main`, based on `a8d83c64`. This supersedes the
read-only limitation in the earlier interface-alignment entry below.

- Applied initial demographics to all 1,902 state-history files and removed
  1,655 startup assignment statements from `common/on_actions/LOK_on_actions.txt`.
  All original culture order/values, majority and minority values are unchanged.
  Four three-culture states (894-897) retain all entries. Runtime `state_cultures`,
  `species`, `minority`, global culture-group catalogs, country species ideas and
  subsequent gameplay/derived-modifier effects are preserved.
- Painter now supports Save/Ctrl+S, exact-byte external-edit checks, source
  backups and rollback for write failures. Source-field drafts also save. Flags
  remain session-only. Backups/bytecode are excluded by the painter's .gitignore.
- Left palette lists named cultures/species/countries with defined-colour swatches.
  Culture has Set/Add/Remove; species has independent Majority/Minority brushes
  and No minority (1000). Species rendering overlays minority-coloured stripes.
  Shift-click picks the assignment and suppresses painting for that gesture.
- Actual map-mode definitions supply 101 culture colours and 61 species colours.
  Named culture 102 (Katzenurkisch) has no defined colour; it remains selectable
  with a labelled grey fallback. All currently assigned IDs have defined colours.

Validation: 16 fixture tests pass, covering save/reload, stale-source rejection,
rollback, BOM/newlines, migration application, exact pixels/stripes and existing
functionality. All seven changed/new Python files compile. Full live-state checks
prove one demographic block per state, exact initial-value equality, preserved
BOM/newlines and identical state text outside the inserted blocks. Surviving
startup syntax trees retain all unrelated effects and ordering.

Real-data checks exercised palettes (102 cultures, 61 majority/62 minority
choices), actual province painting, independent species fields, undo/redo,
all eight views and normal/minimum layouts. `verify_real.py` passed 1,026 mask-size
renders and 10,786 unchanged source hashes during UI-only checks. Four existing
EUL/GAL/KKN/KTZ OOB brace errors remain. `git diff --check` passed. Map validation
before and after reports the same two railway errors on lines 893-894; no map,
localisation or binary graphics files changed. No CWTools executable was found.

Original migration backups:
`legacy_of_kattail_painter/backups/migration_20261124_101441_420939/` (all 1,903
original sources). Exact changed paths are in `plans/painter-editing-files.txt`;
commands/results are in the painter MODLOG.md.

Next action: restart the painter and use Paint > select entry > click/drag > Save.
Fresh-campaign engine validation of state-history initialisation remains pending;
no game launch or screenshot inspection is claimed. Migration runs earlier than
the removed startup assignments, so static equality does not prove timing
equivalence with arbitrary earlier startup effects.

## Painter interface alignment (2026-11-24)

Current branch verified as `Legacy-of-Kattail-Main`. The older sections below
describe work on `jublio-system-backport`; their branch/validation statements are
historical, not a verified status of the current branch.

Changed `legacy_of_kattail_painter/painter.py` to follow the EU4 painter's native
ttk light styling, compact toolbar, left sidebar and dark map canvas. State
controls moved into a scrollable sidebar tab; map/source/flag tabs remain.
Flag previews resize without changing native flag dimensions or mask tinting.
No game scripts, map data, export behavior or game identifiers changed.

Validation: Python compilation and all 11 existing fixture tests passed.
`verify_real.py` exercised real-data Tk controls, demographic drafts, undo/redo,
source filtering and flags; 1,023 renders passed and 10,786 source hashes stayed
unchanged. Additional live Tk geometry checks passed at 1500x900 and 1050x680,
including all tabs, all eight views, state scrolling and preview aspect ratio.
Native `vista` theme was retained. Screenshot inspection was unavailable because
the desktop helper required a usable `CODEX_CLI_PATH`; no screenshot review is
claimed. No game launch was performed.

`python -B tools/validate_map.py` reports railway non-neighbor links on lines
893-894 (20839/20841 and 20841/19461), matching the earlier diagnostic notes.
Map files were untouched. The real-data parser still reports excess closing
braces in EUL/GAL/KKN/KTZ OOBs, already documented in the painter README.

The painter folder was already untracked before this task. Next action: restart
the painter to load the new interface and review its appearance on the user's
display. No implementation blocker remains.

## Jublio system backport (2026-11-04)

Branch `jublio-system-backport`, based on `3abc65d2`. Installed in the working tree, not committed.

**Done:** map grown to 4096x3072 with EU4's solar system chart in rows 0..887; 12 new bodies;
18 Doughland nations at their 100 AKA borders; 11 NPC planet tags; 10 terrains; 12 continents.

**First launch (2026-11-04):** reached nation select, showed a map error warning, then crashed at
game start. Six map errors were logged; all are fixed in the current build.

**Validated (static only):** `work/legacy-kattail-hoi4-space/check_stage.py` passes, including
rules taken from that `error.log`. `tools/validate_map.py` reports the same 2 issues as before the
change, both in `railways.txt` lines 893-894.

**Not validated:** the current build has not been launched, so the crash fix is unconfirmed.
Rendering, AI behaviour and balance are unknown.

**Next action:** launch once and read `error.log`.

**Not done:** space programme decisions for the new bodies; superregion map mode entries;
per-culture state names; final flags.

Generator and full notes: `universal-modder/work/legacy-kattail-hoi4-space/` (`MODLOG.md`). It
reads a pristine export of git HEAD, so re-export it if HEAD moves.

## Conquest release fixes (2026-11-04)

Same branch, uncommitted, independent of the Jublio work. Changed `decide_fate_of_nation`,
`return_occupied_cores_to_puppet`, `lok_peace.1` and `lok_create_blank_occupation_puppet`; added
`common/scripted_triggers/lok_peace_triggers.txt`.

**Validated (static only):** braces and line endings checked, diff reviewed. Not launched.

**Next action:** in game, have two nations carve up a third and release, then check each puppet's
cores match its own land. Then puppet a nation, take more of its land, and confirm only "Return
Territories" shows.

**Unverified:** whether `FROM` keeps its value inside `create_dynamic_country`; what the engine does
when the dynamic tag pool runs out (a failure is only written to `game.log`).

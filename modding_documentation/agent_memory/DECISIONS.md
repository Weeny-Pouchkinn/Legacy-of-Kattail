# Decisions

## 2026-11-26: AI proposal scope and evidence boundary

User request is reconnaissance/proposal, including online template research;
no AI implementation is authorized by this task. Exclude the vanilla modern
tank family. Preserve the existing light/medium/heavy families, whose authored
labels include IFV/MBT/Siegebreaker; do not silently rename them to reconcile
the terminology. Proposed profiles connect research, production, equipment,
templates, field upgrades and native Force Concentration. Values are untested
balancing candidates. Fixed-aircraft improvements can precede designer work;
modular AI fits depend on the separate designer feasibility proof. Do not import
Expert AI as an overhaul-compatible dependency or introduce world-scan pulses.
Evidence, proposed milestones and acceptance gates: `plans/ai-competence-proposal.md`.

## 2026-11-26: Air/naval designer planning scope

User constraint: investigate restoration using existing components through
renaming/reskinning; do not implement during reconnaissance. Freeze the mod's
86 aircraft and 95 naval module IDs rather than importing the installed game's
larger catalogue. Keep descriptor and compatibility declarations unchanged.

The plan recommends a fighter/frigate feasibility proof before broader wiring,
with current equipment IDs preferred. This is a proposal, not an implemented
architecture. Preserve existing special vessels/aircraft as fixed exceptions
until equivalent modular behavior is proven. Nuclear endurance and the conflicting
cruiser screen/capital definitions must not be silently invented or normalized.
Evidence and alternatives: `plans/air-navy-designer-restoration.md`.

## 2026-11-25: Discrete arithmetic variation and native text-color discovery
**Decision:** Precision range is a percentage around a nonnegative integer
operand, sampled uniformly from ceil(lower)..floor(upper), clipping lower at zero.
Zero percent consumes no randomness and uses the exact operand. Sample once per
target per stroke across resources, population and state/province buildings;
right-click uses the same distribution for subtraction/division. Round arithmetic
results half-up to integers, including resources, while retaining decimal precise
resource entry. Reject zero division without resampling. Reuse native building
validators instead of bypassing level/placement/coast rules for bulk arithmetic.
**Rationale:** the user requested integer random amounts and multipliers plus the
same arithmetic editor for both building scopes. Existing ordinary +/-1 gestures
remain available when disabled. Precision is session UI state only.

**Decision:** obtain all global text colors from effective native/mod interface
GFX sources, with case-sensitive codes, native file replacement and draft-aware
caching. Use source comments for names, exclude font-local RGB overrides from the
global catalog, and keep custom unknown authored codes visibly unknown. Shared
picker colors rows and previews the actual edited name plus swatch, including on
paste. Persist only the normal localization color code; no new catalog data file.
**Consequence:** new native colors require no hardcoded UI list update; actual
in-game font overrides may differ from the global-table preview.

Railway editing remains deferred. The requested proposal in painter PLAN.md uses
source-preserving native routes, active bitmap adjacency and staged verification;
no automatic editing of existing railway defects was authorized in this task.

## 2026-11-25: Native starting-setup checks and live session overlays
**Decision:** derive category colors/capacity, resource amounts/types, population,
country totals and climate identity from native definitions and current drafts.
Create categories inside an existing category file and reuse native localization
owners, falling back to existing lok_misc_l_english.yml for new category names.
Count only state buildings with shares_slots=yes. Static capacity includes
category/state factors and direct starting extra slots, capped by numeric native
MAX_SHARED_SLOTS; exclude runtime country/research/conditional effects and label
this limitation. Full and over-capacity warnings are view styling, not paint caps.
**Rationale:** the painter edits starting files; it is not a game script runtime.
Native data remains authoritative, with no persistent painter-only metadata.
**Consequences:** scalar edits validate finite nonnegative amounts, clamp
subtraction, reject zero division, round resource arithmetic to six decimals and
population half-up to whole people. Resource-type warning is strict count > X,
counting distinct positive entries. Country reports sum owned starting states.
Koppen identity requires exact canonical weather matches to the editor's profiles;
custom weather stays gray. North/South and class are reconstructed after reload.

**Decision:** freeze one MapConfig for a session overlay and render both layers
through the same current-camera raster pipeline, including borders and labels.
Snapshot settings, not data or camera; keep input on the active map. Global
Display numbers can hide numeric annotations on both layers, retaining VP names
and N/S markers. Reuse bounded in-memory label tiles/icons for fast redraws.
**Consequences:** live edits and Undo are visible in overlays; overlays disappear
on restart. No UI/session configuration sidecar is written. The installer includes
the shared map_render.py module. README/MODLOG contain palette attribution.

## 2026-11-24: Native trait registries and bounded commander rolls
**Decision:** read both native/mod unit and country-leader trait databases,
honor relative-path replacements including empty files, expose overridden
vanilla for inspection and clone only under unique IDs. Resolve file constants
when cloning; existing mod edits stay in their source. New traits sort into
the family's lok_traits.txt; English names/descriptions sort into
localisation/english/painter/traits_l_english.yml with BOM. This distinct path
keeps the requested basename separate from the installed vanilla file.
Character localisation collection excludes that trait-owned file.
**Rationale:** military/country traits use different native structures; mod
overrides and file-local constants must survive tool editing. Shared localized
selectors show names/IDs while retaining exact native identifiers.
**Consequences:** cached modifier catalog derives from official installed docs
and custom modifier definitions, with native/plural/tooltip aliases and fallback
ID-derived labels. Categories are displayed, not treated as a full scope checker.
Roll base stats using active table bounds and literal level-up defines; retain
level and exclude trait bonuses from the base budget. This is editor generation,
not a full HOI4 VM. Roll generic available vanilla traits with exclusions/rank
checks; preserve custom/status/scripted traits. Explicit and zero-weight
has_trait incompatibilities are respected; conditional/parent-dependent traits
are excluded conservatively. Fresh traits default to manual assignment; clones
retain source generation rules. All changes are guarded drafts with nested
Cancel/Undo. Existing portrait/character saves are retained; the original
migration audit is historical and no longer matches three authored data files.

## 2026-11-24: Cache character data by affected files; separate labels from IDs
**Decision:** keep file inventories/parsed files and derived character catalogs
in memory, invalidate by actual draft category and rebuild only changed files.
Track Undo/Redo/Cancel/reset/create/delete, retain bounded image caches keyed by
source bytes/frame/size, batch role fields and skip unchanged identity updates.
Use direct longest-prefix lookup for related localization keys.
**Rationale:** measured whole-database prefix scans and global cache clears
dominated normal character edits; image reloads were unrelated to stat changes.
**Consequence:** no disk caches or source rewrite needed. External edits remain
subject to reload and guarded Save; benchmark_characters.py uses unsaved drafts.
ChoiceBox separates the displayed localized `Name (ID)` from the bound native
code. Alphabetical lists match names and codes, with typo fallback and explicit
selection for ambiguous names. TraitChoices stores a list of native IDs while
displaying localized entries. Native English names supplement mod localisation
only for display; no game identifiers or strings are renamed or generated.
See legacy_of_kattail_painter/MODLOG.md for measurements and validation.

## 2026-11-24: Native characters with an independent portrait registry
**Decision:** keep native character IDs, repeated role blocks and undated
country-history recruitments authoritative. Edit their localisation dynamically
in tag/neutral-name sections, ordered by displayed character name. Multi-country
characters retain all memberships when unchanged and group under the first tag;
dated/conditional effects are preserved rather than simulated. Store unsupported
editor-only credits, arbitrary portrait tags, notes and additional variant links
in versioned characters_painter_data.json. Native civilian/army/navy slots refer
to independent large/small sprite pairs. No public IDs are renamed for tag edits.
**Rationale:** roles/recruitment must work in the game while a character can have
several reusable portrait variants and credit metadata has no native field.
**Consequences:** English BOM/authored values and existing animated sprite fields
are preserved; gallery uses an animation's first frame. Importing static art
explicitly replaces animation. All portrait asset moves are audited by original
hash; missing art is reported without invented replacements. New image imports
fit native 156x210/65x67 canvases. Ministermaker generation uses the supplied main
script's exact 37x51 resize, 5-degree rotation and border at (8,1), with its own
bundled original border, not the mod's different border or Test/ variant.
Save coordinates text/new files/binary assets/deletions, preflights original
bytes, backs up and rolls back; Cancel/Undo restore absence for new files.
See plans/character-workspace.md and legacy_of_kattail_painter/MODLOG.md.

## 2026-11-24: One authoritative history per state
**Decision:** remove redundant second ZZZ histories while keeping each primary
history exactly. Merge same-owner non-ZZZ histories to retain unique VPs, cores,
claims and provincial/state buildings; keep the later value for overlapping
building settings. Do not change unrelated duplicated resources or scalar fields.
**Rationale:** explicit duplicate-history cleanup; ZZZ shadows are obsolete, while
same-owner blocks sometimes contain distinct, necessary province setup.
**Consequence:** all 1,902 states have one history. Map validator and EU4 importer
reject duplicate/missing histories. Historical import hashes are not a current
validation baseline after this cleanup. See state_history_audit/README.md.

## 2026-11-24: Import EU4 nations within existing ZZZ states
**Decision:** transfer whole states by EU4 default-bookmark ownership pixels,
excluding seas/lakes/impassable terrain and retaining uncolonised land as a vote.
Preserve all existing state/province boundaries and exclude Meogartha, as explicitly
confirmed by the user. Reuse LRN -> LAK and NOV -> NFS and existing dormant tags.
**Rationale:** respect HOI4 ownership granularity and established identity without
worldwide border changes. Keeping uncolonised pixels prevents incidental frontier
slivers from claiming whole states.
**Consequences:** 39 countries/320 states; 84 stay ZZZ. WMD's only imported state
331 is its capital because the source capital does not overlap eligible territory.
Existing country history/localisation wins over conflicting EU4 text. Missing
histories use documented starter values; unrelated OOBs are replaced by an empty
OOB rather than inventing armies. Exact provenance is in eu4_zzz_import/audit.json.

## 2026-11-24: Species invariant and geographic brush scopes
**Decision:** when majority equals minority, keep the majority and clear minority
to 1000, including Diverse (0). Enforce through the shared demographic setter,
normalised load, raw-edit handling and World document pre-save hook. Reject
1000 as a majority ID. Repair three existing equal pairs with guarded backups.
**Rationale:** explicitly requested rule, without changing other demographic data
or introducing game-time polling. Existing runtime identifiers remain intact.
**Consequence:** invalid loaded data appears repaired and is staged for Save;
undo cannot reintroduce an equal pair into the active demographic model.

**Decision:** boundaries are independent display overlays at 1/2/3 screen pixels;
State/Strategic region is a separate paint scope. Region painting changes whole
member states as one undo group and refuses split states before editing.
**Rationale:** culture/species/ownership are state-level data; silently painting
outside a selected region would violate its boundary. The current map has no
split states, but future edits must not assume that remains true.
**Consequence:** all four brushes share region membership and rollback logic;
region membership and boundary geometry are snapshots loaded on painter startup.

## 2026-11-24: State histories own initial demographics
**Decision:** initialise `state_cultures`, `species` and `minority` inside each
state's native history effect block and remove the old startup assignment lists.
Retain these runtime names, culture-group catalogs, country species ideas and
later gameplay conversions. Use the delimited demographic block for editor writes.
**Rationale:** the user requested persistent painting and state-local definitions;
existing map modes, tooltips, focus rewards and scripted effects consume these
containers. Removing the runtime containers would break those consumers.
**Consequence:** new source state is independent of initial owner. Existing
initial values are preserved, but their earlier availability requires a fresh
campaign check. The migration is not intended to preserve existing saves.

## 2026-11-24: Palette colours and persistent saves
**Decision:** derive culture/species RGB directly from the mod's map-mode scripts,
blend multiple culture colours arithmetically, and draw minority species in solid
diagonal bands over the majority. Never hash demographic IDs into arbitrary hues.
Undefined culture 102 remains selectable with a labelled neutral fallback.
**Rationale:** the user requested actual defined colours and visible minorities;
the game shader's grey contribution/alpha are not appropriate editor swatches.
**Consequence:** preview colours express definitions, not exact shader output.
Majority/minority brushes change one field at a time. Save preserves source
encoding/newlines, rejects external changes, backs up originals, atomically
replaces each file and rolls back written files on exceptions. This does not
guarantee a multi-file transaction across power loss. Flags remain session-only.

## 2026-11-24: Share the EU4 painter's native desktop styling
**Decision:** use platform-default ttk controls, compact top tools and a left
sidebar instead of the HOI4 prototype's custom dark theme and banner. Keep
source/state sidebar tabs and map/source/flag workspace tabs for HOI4's existing
controls. Match the EU4 map backdrop (`#1e1e1e`).
**Rationale:** the user requested the EU4 painter's UI style; its `_build_ui` uses
native ttk controls, an 8-pixel padded sidebar and Segoe UI section titles.
**Consequence:** appearance follows the platform theme (verified `vista` here).
The application remains memory-only; state forms scroll and flag previews resize
to accommodate the wider sidebar without changing underlying flag sizes.

## 2026-11-04: Jublio system map layout
**Decision:** add 512 rows on top, for 4096x3072. Old rows 376.. keep their content at rows 888..
**Rationale:** the wiki caps map area at about 13,238,272 px, so this is the tallest multiple of
256 at this width. z counts from the south, so existing coordinates stay valid.
**Consequence:** no further height is available at this width. Old saves are incompatible.

## 2026-11-04: Province density in space
**Decision:** about 879 land px per province, from Muno, Xenon and Merries at chart size. Minimum
6 per body; Glaka at half density.
**Rationale:** the user asked for density matching those three bodies.
**Consequence:** body province counts differ from the EU4 mod, so province IDs do not map 1:1.

## 2026-11-04: Planet ownership
**Decision:** each new body has an NPC tag (`J??`) that owns its surface and a rim state as capital.
**Rationale:** follows MUN, XEN and MRI, including MRI's capital on wasteland state 968.
**Consequence:** new tags must be added wherever MRI is listed.

## 2026-11-04: Doughland is not a space state
**Decision:** continent `jublio_doughland` is left out of `is_space_state`.
**Rationale:** it is inhabited by 18 nations, so ordinary state behaviour fits.
**Consequence:** space state views and colonisation logic do not apply there.

## 2026-11-04: Merries continent
**Decision:** Merries' 23 interior provinces moved from continent 1 to continent 16.
**Rationale:** continent 16 was declared for them, and `is_space_state` tests it.
**Consequence:** `is_space_state` is now true on Merries for the first time, which affects every
script using it. Edge provinces on all three moons stay on continent 1.

## 2026-11-04: Releasing puppets from conquered land
**Decision:** `lok_is_releasable_conquest` defines releasable land everywhere. A nation can only be
released once it no longer exists. If the occupier already has a puppet of that nation, land goes
back to it instead; `unique_puppet_country` puppets do not count. Puppets get cores only on land
they receive. Keeping an occupation can be reconsidered after `@LOK_FATE_RECONSIDER_DAYS`.
**Rationale:** several occupiers of one nation must each be able to release a puppet without
duplicating a puppet they already have or gaining cores on each other's land.
**Consequence:** a surviving rump nation can only regain land through peace deals. Puppets of one
nation under different overlords share a name.


## 2026-11-24: Render painter viewports before coloring

Decision: follow the EU4 painter's viewport/lookup-table pattern. Sample immutable
province IDs at display coordinates before applying current per-state colors;
retain a bounded viewport/halo cache, static palettes and source-sensitive native
color/parse caches. Use Pillow 1-D coordinate resizing to preserve nearest-neighbor
tie behavior exactly. Borders retain display-pixel thickness across crop edges.

Apply every brush edit synchronously, and throttle only rendering, inspection and
status feedback to a 25 ms frame queue. Release flushes the frame. Do not debounce
away paint events, postpone source validation or change existing Undo grouping.
All caches are session memory, with no new painter/source files. Native source
validation remains more expensive for wonders because their startup file is large.


## 2026-11-24: Native country authoring and authoritative history species

Use normal tag/country/history/ideological-localization/TGA/idea/GFX/character
files for country edits, with no country/flag/spirit JSON or custom data sidecars.
New Python modules are implementation, not generated mod data. Current country
quick-add does not touch the legacy character metadata file. Flag recipes remain
session controls; baked flags and imported native DDS masks survive restarts.

Country species and national attributes are native ideas in country history.
Game-consumed history flags make the existing startup defaults respect explicit
choices. Guard attribute tech bonuses as well as ideas, then clone the existing
bonus template into a scoped tag block for the chosen attribute. This avoids
retaining nuclear/computing bonuses from the old default. Untouched countries
keep their existing setup; no automatic global history migration or recurring
loops. New country files use TAG.txt; existing filenames are preserved.

Preserve relative technology/equipment-variant order, unrelated history and
conditional/dated branches. Country forms are transactions including nested
leader/spirit/emblem dialogs. Apply groups all actions; Cancel/Undo restore native
indexes too. All selectors use existing localized name/ID search controls.


## 2026-11-24: Visual flag choice windows

Flag background/emblem arrows open modal thumbnail galleries rather than the
text suggestion popup; typing remains supported in entries. Use the current
palette/tint/size to show actual flag previews. Keep picker candidates local until
acceptance, restore the owning modal grab on close, and leave native writers alone.
Use a virtual canvas and small rendering batches, with bounded window-local image
and mask caches. Do not generate thumbnail caches or new painter game-data files.

## 2026-11-24: Native geography authoring

State edits patch native root/history fields and existing localization owners;
IDs/province lists are fixed. State, region and nested VP dialogs share the
existing draft transaction/guarded Save. Supply nodes use map/supply_nodes.txt,
not invented history fields; railways and spawn placement generation are excluded.
Building scopes, caps/coastal requirements and facility restrictions come from
native definitions and existing map positions. Preserve unchanged authored values
and dated/conditional/unknown script scopes.

Move entire states between strategic regions. Removal needs a destination, with
global checks against empty regions and split/unassigned states. Keep independent
sea provinces in place and synchronize map/paint/boundary indices after draft
changes/Undo. Naval terrain is valid for sea provinces inside mixed regions, as
demonstrated by existing mod files; do not require sea-only regions.

Weather import copies vanilla period weather, not geography. Thirty climate
classes with six-month hemisphere variants are Köppen-inspired editor profiles;
their values are approximations, not observations or an implementation of the
published classification algorithm. Permit native phenomenon weights above one.

VPs are direct starting state-history province/value pairs. On VP Apply,
consolidate exact base localization keys into existing victory_points_l_english,
sort by displayed place name with numeric province-ID ties, preserve versions and
inline comments, and reject conflicting base names atomically. Country-suffixed
variants stay in their files. Keep authored names when removing a VP. Cache only
in-memory province representative pixels, and cull zoomed labels to the viewport.
No painter-specific game-data or disk cache files.

## 2026-11-25: Country popularity allocation

Treat blank/zero popularity as remaining ideologies; preserve entered positive
values and randomly divide only the unallocated part of 100. Reject overfull
totals or a positive remainder without eligible entries, with guidance to
normalize/clear a value. Normalize rescales nonnegative weights (including those
above 100) proportionally; all-zero weights become equal shares. Use exact
fractions and largest remainders at six decimal places or existing finer input
precision, so generated percentages total 100 without float drift. Update form
fields in one batch and redraw the pie once. Keep the native Apply/Save flow.

## 2026-11-25: Multi-symbol flags and country-create source reuse

Keep up to eight symbol layers in the country form, with independent live colors,
mask/size/position/stretch/rotation and procedural mask-dilation outlines. Hit-test
the transformed masks from top to bottom when dragging. Native flag images stay
flattened; do not add persistent layer/design data files. Cache bounded decoded
masks and transformed/outline alpha planes in memory. Debounce typing, throttle
drag updates, and disable Use for invalid inputs. Galleries use the complete stack
and change only their background or active symbol candidate.

Country-create source collisions raise a typed preflight exception with native
paths, before mutations. Ask once with No as default; approval explicitly permits
form-owned setup replacement, reusing the existing history filename and preserving
unknown/dated script and definition fields. Declining leaves the form and drafts
intact. Keep ordinary guarded Save/backups; reject ambiguous multiple histories
rather than deleting or silently choosing a source. Registered tags continue to
be edited through the existing country editor.

## 2026-11-25: Building map paint scopes and country preview readback

State building mode includes every native state-scope type, not only shared-slot
types. Province mode includes province buildings and supply nodes, excluding
railway routes. Use the native state writer and supply file, with existing caps,
coast/placement/exclusivity/group validation. Left adds one, right removes one,
one change per entity per stroke; middle pans. Gray represents zero, and numeric
labels exist only for positive counts. Use cached native building indices and
representative actual province pixels for viewport-cropped state/province labels.
State shapes remain immutable; strategic-region painting only moves whole states.

Read country colors from Documents drafts even before files exist on disk; include
tag/path identity in color cache signatures. Patch all existing native overrides
and UI colors for the edited tag to match the form's single color. Apply writes
the form's popularity block explicitly, then reloads applied values for the pie
and color preview. Display exact decimal percentages and fit the chart legend;
the installed effects_documentation.md set_popularities example uses 54.5/45.5,
so do not impose integer-only values to address a preview issue.

## 2026-11-25: Paint complete native climate profiles per region

Decision: Paint Köppen uses the existing strategic-region native weather profiles,
colored preset palette and exact-weather matching. The South checkbox shifts the
seasonal profile six months; unchecked means North. Replace complete weather
when painting (including custom weather fields), retain every other region field,
and support sea-only regions. Shift-pick takes both profile and hemisphere; no
metadata persists. Keep each region as an ordinary reversible native-file edit.

Rationale: the requested climate brush must set all weather values coherently,
recognize its own results after Save/reload and leave geography untouched. Existing
profiles already include all nine weather fields, including explicit zeros, so
retain the established approximations and enforce completeness with regressions.
Consequences: custom weather is replaced only on painted regions; unpainted
regions and preset tuning are unchanged. See painter MODLOG for validation.

## 2026-11-25: Railway province brushes edit a native link graph

Decision: model railway levels as native undirected province links. Clicking a
province sets/increments/decrements all touching links; its displayed level is
the maximum touching level. Deduplicate edges per stroke. Existing-only blocks
new edges as well as new vertices. New routes use adjacent painted anchors and
neighboring existing railways; no paths cross unpainted land, per user clarification.

Save compacts equal-level chains into simple native paths while retaining every
link/level. Collapse overlapping native links to their maximum level, retain
comments/BOM/newlines and preserve known original invalid links separately.
Use actual orthogonal bitmap/wrap adjacency and native impassable border/state
rules; update rules for drafts/Undo while retaining immutable geometry. Level cap
is NSupply.MAX_RAILWAY_LEVEL, not the generic rail_way building cap. No railway
metadata, singleton routes, global pathfinder or implicit hub creation.

Rationale: engine data describes links, so independent province-level numbers
cannot be saved faithfully at mixed-level junctions. Link-based gestures and
explicit maximum labels provide native roundtrips. Deterministic chain compaction
is an exact graph serialization, not a supply-flow optimization claim.
Consequences: neighboring endpoint displays can change; an isolated first click
is a temporary anchor. Existing known bad links remain visible red; new ones
are refused. Supply hub overlay reuses GFX_supply_hub_icon_strip first frame and
native supply_nodes.txt, with no new art or gameplay scripts.

## 2026-11-25: Preserve both authored starting supply-hub sources

Decision: merge positive direct state-history provincial supply_node entries and
native map/supply_nodes.txt entries for painter inspection/counts/overlay. Read all
undated history/buildings blocks; do not infer hubs from VPs or execute dates/
conditions. Deduplicate by province, using positive maximum where both exist.
Current data has no conflicting levels. Keep VP setup independent.

Rationale: 1,146 existing history-only hubs were invisible in the map-only reader.
Consequences: the current authored union is 1,192 hubs. Update existing sources
in place when editing/removing, synchronize dual declarations, preserve zeros/
comments/dated setup and use the map file only for genuinely new declarations.
No migration or wholesale rewrite of state histories; no hub resurrection.

## 2026-11-25: Import terrain inside an exact mask without province reshaping

Status: height/normal/color blending and province classification below are
superseded by the later native-style refinement decision. Exact mask/topology
preservation and the first-import audit remain valid.

Decision: use the supplied exact black mask and identity-aligned EU4 rasters.
Translate graphical indices semantically and gameplay types by native EU4
province terrain overrides. Only majority-covered compatible land provinces can
change gameplay terrain; keep IDs, RGB, coast/type/continent and membership fixed.
Preserve target water plus EU4-inland-water/HOI4-land disagreements, all exterior
pixels and city-light alpha. Source summer RGB and source normals accompany land
height, with a four-pixel inward seam blend and a preserved coastal rim. Keep the
native indexed BMP palettes and single-mip uncompressed DDS header/layout.

Rationale: source/target inland lake geometry differs inside the selection, while
the user explicitly forbids reshaping provinces. Reclassification/flooding those
land pixels would contradict that constraint. The existing rivers already match
source in the selection, so retain them byte-for-byte.
Consequences: 363 province terrain classifications and four raster assets changed;
3,507 incompatible inland-water pixels remain native HOI4 land. A dry run, exact
staged-hash application, original-file backups and 2,321 protected-file hashes
make this reviewable and reversible. Audit and exact selection are durable under
masked_eu4_terrain_import; engine appearance/movement remains untested.

## 2026-11-25: Native-style masked relief, trees and graphical terrain authority

Decision: supersede the earlier four-pixel feather/source-normal/color copying
and EU4 province override classification. Match surrounding native relief scale,
correct low-frequency boundary offsets harmonically, and feather inward 48
pixels. Regenerate native-convention normals and match native biome colormap
colors. Preserve coast/water mismatches, exterior, alpha and all topology.
Audit every mask-touched land province using dominant native graphical terrain
across the complete province, retaining a tied existing type. Generate trees
only on matching woodland graphics with existing native models/densities;
require entire low-resolution tree footprints to fit the compatible selection.
Rationale: the first import visibly differed from native relief and sometimes
assigned mountain gameplay to forest graphics. Consequences: 160 additional
CSV corrections, native-style relief/colors and 2,647 selected woodland cells
with trees; no shape, river or topology changes. See terrain_refinement audit.

## 2026-11-25: Province edit categories and gameplay-only terrain brush

Decision: expose VP/Railways as Provinces subcategories and add gameplay Terrain
beside Inspect/Buildings. Route gestures and render config through the effective
subcategory; retain dialogs, labels, overlays, level protection and supply hubs.
Terrain drafts patch only definition.csv field 6 and synchronize the cached
world/palette after edits/Undo. Native terrain definitions supply types/colors.
Rationale: align entity-level workflows with the existing state category design.
Consequences: no graphical painting in this brush and no new game identifiers.

## 2026-11-25: Popularity uses exact native precision; Gestalt stays manual

Decision: canonicalize country Apply and Normalize/random remainder output using
largest-remainder apportionment on the 0.001% grid, totaling exactly 100. Reject
invalid totals before Apply. Random filling excludes Gestalt; manual positive
Gestalt survives. All-zero normalization distributes among non-Gestalt entries.
Rationale: user's live log rejects six painter-authored six-decimal blocks;
truncation yields sub-100 native totals despite exact Python sums. Installed
set_popularities docs explicitly allow decimals, so whole-percent rounding is
unnecessary. Consequences: legal fractional shares remain; UI reads canonical
saved values; MAJ/ANS/KHO/PAR/SPT/CER repaired by numeric-span edits only. Engine
reload remains untested; see popularity_precision_repair/audit.json.

## 2026-11-25: Resolve two impossible island railway jumps

Decision: after explicit user request, remove only the level-3 19461-20841 and
20839-20841 links. Current bitmap gives 20841 no land neighbor and no continuous
land route exists; preserve geography and every other railway link/level rather
than invent a cross-water railway. Cached province_adjacencies.csv is stale for
these endpoints, so current bitmap/rules are authoritative. Consequences: map
validator now passes. Previous notes preserving these two jumps are superseded.
Recovery/verification: railway_jump_repair/README.md and audit.json.

## 2026-11-25: Names per entity family and camera-faithful export

Decision: independent session name choices for states/regions/VPs, initially
false/false/true, shared across each family's subcategories. Names are immutable
in saved overlay configs and independent of the global number switch. Hide only
VP names when requested, retaining value/dot controls. Draw optional equator
after compositing; export freshly rendered visible bounds without overscan/UI.
Rationale: user wants readable optional localized names and a faithful viewport
PNG. Consequences: no native map or identifier changes for display/export.

## 2026-11-25: Geographic hemisphere replaces manual controls

Decision: remove North/South selectors everywhere in Koppen painting/preset forms.
Always phase from exact area-weighted land centroid (sea area for sea-only) on the
main planet's bottom-aligned 2:1 projection, not the complete solar-system map.
At current 4096x3072, planet top=1024, bottom=3072, equator=2048. Source EU4
JUBLIO_SYSTEM_README.md:3-6 verifies original 4096x2048 extent and top extension.
Reject off-world auto latitude; keep native weather editing there.

Account for latitude starts enabled, and controls only cubic temperature-season
smoothing inside +/-10 degrees. Preserve annually invariant/even-harmonic terms,
Koppen class and chosen wet/dry structure; recalculate phase/freezing weather
weights. The 10-degree width is an editor approximation. NASA energy-budget
seasonality and NOAA ITCZ evidence justify reducing thermal contrast without
flattening rainfall or claiming a local climate simulation. Exact generated
profiles remain detectable after native Save/reload, without metadata.

Consequences: on explicit user request, re-evaluated 276 recognized main-planet
profiles and changed 29 weather blocks, including nine hemisphere corrections;
custom and off-world profiles preserved. Guarded backup/readback complete.
Sources, IDs, audit and limitations: map_labels_latitude_export/README.md.

## 2026-11-25: Literal-only native demographic colors and deterministic outputs

Decision: write only culture add_to_temp_variable RGB literals and species
set_temp_variable RGB literals; preserve arithmetic references and patch every
matching branch. Use nearest 0.001 fractions, which roundtrip all 256 channel
values. Restore culture 103 divisors, remove gray seed from averages, retain
explicit uncultured gray. Initialize species RGB/alpha: transparent unmatched
minority and opaque neutral unmatched majority. Keep selected Altarian hue.
Rationale: broad variable-name edits corrupted divisors and produced over-range
white; duplicate minority branches could override writes. Unset top-layer output
is unsafe but not yet proven to explain Altarian's white rendering. Consequences:
matching palette/math tests, source-backed repair and an explicit pending engine
check. No shader/art, IDs, assignments or colors redesigned.

## 2026-11-25: Culture group is optional

Decision: represent No group as None in the model and empty code in the picker.
No startup membership/trigger is generated for it; removing an existing group
removes those references. Changing group controls the generated full-description
group clause; leave authored full text intact for unchanged ungrouped cultures.
Rationale: valid existing cultures lack groups and the editor wrongly required
an integer group. Consequences: create/edit/reassign/ungroup survives native
Save/reload/Undo without invented group IDs or None references.

## 2026-11-25: Reusable historical Imperium elements, native state assignments

Decision: one optional Katzenartig Imperium element per state, independent of
owner. Stable numeric IDs (zero unassigned) are saved in the base history variable
lok_katzenartig_imperium_element. Native state-color branches are the definition
catalog; English localization owns each name and both manually authored texts.
Two scripted-localization dispatchers select text in the hovered state context,
following the existing [FROM.GetName] convention. Names/colors/text are shared
objects exposed alongside cultures/species; assigned states retain only the ID.

Rationale: historical organization is authored geography, not current politics.
Native files avoid parallel metadata and runtime world scans. Unique byte RGBs
use three-decimal native fractions; unassigned gray is reserved. Source edits
target direct undated history assignments, preserving dates/other fields. The
painter previews immediate and 650 ms delayed tooltips. Arbitrary game dynamic
functions remain literal in its plain-text preview; engine is authoritative.

Consequences: guarded Save writes definitions/localization/state pointers together;
editing a shared object updates all its states. No deletion or ID renumbering is
introduced. Initial elements/territory remain empty; Schutzone Pegasien/MCF was
an example rather than a historical assignment instruction. Game check pending;
tests/native Tk probe passed. See katzenartig_imperium/README.md for paths/audit.

## 2026-11-25: Conservative startup repairs and editor preflight

Decision: retain current borders and accepted neutral/friendly deployments;
relocate only the 64 logged enemy deployments. Choose owned capitals using
existing VP then population. Use basic infantry for the existing startup army
generator when its motorized/support technology requirements are unmet; grant
no new tech and keep division/battalion counts. Give the 21 overfilled states
53 explicit local shared slots rather than deleting factories or changing a
category globally. Reuse authored generic names and existing scientist art as
native default fallbacks instead of inventing national lore.

Canonical VP localisation remains in victory_points files; current Jublio
state/region names remain in the Jublio file. Preserve all shadowed authored
alternatives verbatim as comments and keep intentional replace-layer overrides.
Write 32-bit RGBA flags with unchanged RGB. Detect horizontal-wrap X crossings;
resolve the two observed junctions with two existing-color pixels.

Painter Save now rejects newly foreign capitals for active countries and new
cross-file localisation collisions, while retaining dormant capitals, grouped
edits/Undo, BOM/header safeguards and intentional replace-layer semantics.
Port only missing current-version GUI blocks and their sprite dependencies,
including the core.gfx circle sprite. No descriptor/replace_path changes.

Rationale: errors came from mismatched ownership, equipment availability,
incomplete inherited GUI contracts and missing fallbacks, not a need for new
territory or content. Consequences and evidence: error_log_repair_20261125/
README.md, verification.json and files.txt. The external Workshop warnings are
not mod-owned errors and are not repaired by modifying this repository.

## 2026-11-26: Generic portrait group identity and vacant templates

Decision: use existing LOK_portraits Species_<ID> and special section headers as
group IDs, preserving all reserved 0..100 slots and dynamically labeling numeric
IDs from species localization. Native country blocks are authoritative. A sparse,
draft-managed generic_portrait_groups.json retains pool templates for groups with
no country, avoiding fake tags or unknown native schema. Existing canonical
role/gender defaults are fixed independently of editable Species_0 pools/art.

Species creation allocates the same ID in the same grouped draft transaction.
Missing registrations beyond 100 reference verified existing placeholder files.
Imports create separate TGAs, large 156x210 and small 65x67 using the existing
Ministermaker routine; existing sprites are updated in place, new ones use a
dedicated generic upload GFX file. Never overwrite a shared placeholder texture.

Country Setup stores the selected group by moving that tag's native portrait
block into the chosen section, removing prior definitions across portrait files.
New-country UI suggests its national species until overridden. Existing choices
and external/native pools are preserved unless explicitly changed; None in the
model preserves them, empty string deliberately clears country-specific pools.
Pool membership edits target that role/gender in each country, retaining other
fields/comments. No runtime iteration, game localization or species/tag migration.

Coupled repair: native special groups used inverted sprite prefixes. Change only
the 1,120 bad references to the already registered names, with exact guarded
backup and existing large/small texture verification. Preserve inherited CRCRLF
bytes despite Git whitespace diagnostics. Native UI and tests passed; game
rendering remains untested. See generic_portrait_groups/README.md and audits.

## 2026-11-26: Engine modifier categories are tooltip groups, not scope gates

Decision: build the shared modifier catalog from complete installed engine
documentation, expanding each parameterized heading using its Modified types.
Keep exact case, isolate category metadata per section and union repeated
template entries. Retain vanilla/custom modifier-definition overlays, localized
labels with readable fallback, and display precision/Boolean type metadata.
Do not write redundant game definitions for built-in engine modifiers.

Remove the category=country whitelist from spirit selection and save validation.
The installed modifier-definition documentation explicitly describes category
filtering as tooltip behavior; actual vanilla country ideas use army-tagged
army_core_defence_factor. Exclude only synthetic military trait stat bonuses and
weights from the spirit chooser, maintaining their proper trait context. Allow
documented yes/no values; numeric values remain finite native game units.

Consequences: all 4,528 documented vanilla IDs and custom definitions are visible
to shared editors, including parameterized building/equipment/resource families.
Catalog presence does not prove a particular modifier has an effect in every
script context. Full coverage/native UI audit in vanilla_modifier_catalog/;
no live idea/trait or game definition was changed, and no engine test claimed.

## 2026-11-26: Native spirit bonus families and targeted leaf edits

Decision: expose research_bonus and equipment_bonus separately from ordinary
modifier fields, using actual technology_categories, active equipment IDs/type
tokens and equipment/module stat definitions. Respect same-file overrides, empty
mod files and replace_path when building catalogs. Do not offer MIO-only group
IDs as equipment targets without proof of support in this idea field.

Read all repeated base bonus blocks for the form. On Apply, patch only changed
scalar values across matching duplicates; removals delete only owned leaves.
Retain comments, unrelated/nested content and unchanged variables, leaving valid
empty containers when necessary. API None preserves a bonus family entirely.
Use native fractional game units with finite-number validation, no implicit
percentage conversion or invented research/equipment/stat IDs.

Instant is per equipment target: new targets default yes; existing yes/no/omitted
flags are preserved until edited. Native default/no applies on new equipment
variant creation, while yes applies immediately (installed effect docs).
Consequences: source-preserving national-spirit authoring with existing guarded
Apply/Cancel/Undo/Save semantics; no live data migration. Tests/native mapped UI
passed; in-game effects untested. See spirit_research_equipment_bonuses/README.md.

## 2026-11-26: Painter layout at final write boundaries and proven-output repair

Decision: format changed structured script containers centrally at Documents.save
and direct CLI generation boundaries. Never format between primitive span-based
patches: their parsed offsets still refer to earlier text. Inserting a missing
field uses real syntax depth even when the parent begins halfway along a line.
Complex objects/bodies expand; short native parameter blocks and lists can stay
inline. Unedited containers are excluded. Lexer tokens including comments must
remain byte-identical strings in the same order, with a successful parse.

Exclude line-oriented map records, CSV, JSON, Lua, localisation and binary assets.
Their formats use their own writers. Preserve BOM/encoding and newline family.
Do not globally reformat handwritten sources. Existing-output repair selects
scopes from hash-proven Save before/after records, then checks both exact tokens
and independent ordered structure and uses guarded backups. Missing provenance
is reported, never inferred. Existing malformed carriage returns outside selected
scopes remain. Full evidence: painter_script_formatting/README.md.

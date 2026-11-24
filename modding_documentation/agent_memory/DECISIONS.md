# Decisions

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

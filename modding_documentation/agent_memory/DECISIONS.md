# Decisions

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

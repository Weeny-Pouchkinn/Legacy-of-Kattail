# Decisions

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

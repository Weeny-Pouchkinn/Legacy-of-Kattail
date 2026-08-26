# Interface ownership migration — 2026-08-26

## Summary

The `interface/` tree was reorganized by content ownership while preserving
sprite identifiers, active definition blocks, GUI object names, and the
lexical final-definition winner for every GFX identifier.

The original before inventory contained 37 `.gfx` files and 47 `.gui` files.
The first ownership migration produced 166 `.gfx` files and 46 `.gui` files;
the subsequent portrait consolidation leaves the tree with 78 `.gfx` files;
the final country-GFX merge leaves the current tree with 70 `.gfx` files and
46 `.gui` files. The one-file reduction in GUI files is the removal
of `lok_FRA.gfx` and `lok_FRA.gui`, which contained comments only and no active
definitions.

The migration preserved all 10,943 active named GFX definition blocks, 10,806
unique identifiers, and 137 pre-existing duplicate identifier names (274
duplicate occurrences). Duplicate definitions were not silently deduplicated.

## Ownership layout

- `lok_country_<TAG>.gfx` holds each country's ideas, focus icons, modifiers,
  and estates where applicable, separated by comments. The wrongly placed AUR
  entries from the former KTZ idea file were assigned to AUR by their
  identifiers.
- `lok_shared_*.gfx` holds shared event pictures, focus icons, leader/species
  portraits, technology icons, terrain, unit icons, autonomy icons, ideas,
  and bookmarks.
- `lok_system_*.gfx` / `.gui` holds system UI such as Parliament, alerts,
  ideology, state actions, nuclear tracking, species, strategic resources,
  wonders, private sector, planets, economy, and the intentionally retained
  novelty views.
- `zzz_lok_override_*.gfx` holds explicit late-loading replacements for the
  former `interface/replace/lok_general_stuff.gfx` and the walker role sprite.
- `lok_leader_portraits.gfx` is the single canonical file for all 585 named
  character-portrait definitions. Its 93 country sections are sorted by tag
  and followed by `GENERIC`, `MISCELLANEOUS`, and `SHARED TEMPLATES` sections.
  `lok_shared_species_portraits.gfx` remains separate for reusable species
  placeholders.

Vanilla-style filenames were retained for the modified game GUI files and
other files whose names are part of the base interface structure, including
country views, `frontendmainview.gui`, `topbar.gui`, `unitview.gui`,
`Technologies.gfx`, `subuniticons.gfx`, `core.gfx`, the 1960 technology files,
the equipment designer paths, and the nudge/faction/landmark files.

## Coupled tooling

Repository generators were updated to write into the new locations:

- Parliament generation writes `lok_system_parliament_assets.gfx` and
  `lok_system_parliament.gui`.
- Generic species portraits write `lok_shared_species_portraits.gfx`.
- Character, focus-icon, and national-spirit tools select the relevant
  `lok_country_<TAG>_*` file.
- Wonder documentation points to `lok_system_wonders.gfx`.
- The character creator appends to `lok_leader_portraits.gfx` and recognizes
  the country section comments.
- The remaining country-owned GFX files are now merged into 20 canonical
  `lok_country_<TAG>.gfx` files. Each file separates its ideas, focus icons,
  modifiers, and estates definitions with comments; TAI includes all three
  applicable sections plus estates.

## Validation

- `python tools/interface_reorganization.py --compare-head`: active GFX block
  fingerprint comparison passed.
- `python tools/merge_country_gfx.py`: merged 28 source country GFX files into
  20 country files.
- The same audit's lexical final-definition winner comparison passed for every
  sprite identifier.
- The generated GFX formatter checked all 60 owned registry files and
  normalized structural indentation to tabs in the 54 files that needed it,
  including the consolidated portrait registry.
- Exact-content checks passed for 35 direct GUI/GFX renames.
- Interface brace-balance check passed for every `.gfx` and `.gui` file.
- `git diff --check` passed.
- `py_compile` passed for the updated migration and generator tools except
  `generate_lok_parliament_gui.py`; that script already fails on its original
  f-string syntax at line 1038 in `HEAD`, unrelated to this path-only change.

## Uncertainties

No Hearts of Iron IV session was launched. Runtime loading and the effective
case-sensitive file enumeration order remain untested; the static audit uses
the repository's lexical path order and confirms that its final winners are
unchanged.

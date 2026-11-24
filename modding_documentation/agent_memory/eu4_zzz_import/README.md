# EU4 nations imported into former ZZZ territory

Completed 2026-11-24 on Legacy-of-Kattail-Main. Installation is in the working
copy; no commit or game launch was performed.

## Result

320 states transferred from ZZZ to 39 nations. ZZZ retains 84 of its original
404 states. The initial text count of 444 included 40 commented ownership lines.
The user explicitly required existing states and exclusion of Meogartha (MGA).
No province/state boundaries, map assets, state demographics, manpower, resources,
buildings, existing third-party cores or other countries' territory changed.

Reuse: 34 established HOI4 tags, including 12 reactivated dormant declarations.
Aliases: EU4 LRN -> HOI4 LAK (Laurendaar), EU4 NOV -> HOI4 NFS (Novian Arikhanate).
Five new tags: ELC, HIV, INT, MAG, WMD. Added 17 missing country histories,
14 source-named leaders, and reused URS_Grizz, USS_Panda and VPL_Pompilidae.

All 39 countries receive their EU4 RGB colours and default/current-ideology
flags in three native sizes: 82 by 52, 41 by 26, and 10 by 7 pixels. The 11
single-colour source flags are retained as supplied, not new artwork.
Other ideology artwork is preserved; the default flag covers missing variants.
Existing HOI4 country names and history remain authoritative where present.
82 missing localisation entries were copied from EU4 into a new UTF-8 BOM file;
existing localisation files were not edited.

## Geographic method and limits

Evaluated EU4 province history through 100.1.1.12, matching HOI4's bookmark.
Both rasters are 4096 by 3072, aligned directly with no scaling or cropping.
For each currently ZZZ-owned state, count EU4 ownership pixels after excluding
EU4 seas, lakes and impassable provinces. Uncolonised habitable pixels compete
with countries; retain ZZZ if uncolonised land wins or there are no habitable
pixels. Transfer the entire existing state to its largest ownership category.
State cores/controllers referring to ZZZ become the assigned owner; add an
owner core where missing. No split state or new province was created.

Capitals use the greatest overlap with each EU4 capital province within assigned
territory. WMD's EU4 capital has no eligible overlap; state 331, its sole assigned
state, is its HOI4 capital. This is an explicit conversion choice.

Existing 22 country histories change only capital and OOB references. Missing
histories use a small native HOI4 starting baseline (3 research slots, 50% stability
and war support, five basic technologies, source ideology/leader, 100% ruling-party
popularity). They are not an economic or military balance conversion. Source
ideology consolidation is lossy; reverse mappings follow EU4's migration audits.
New leaders use existing species portrait sprites, including existing placeholders.
The existing startup species-law section adds the 17 missing country assignments;
state demographic definitions and existing assignments remain unchanged.

Invalid/unrelated dormant OOB references, especially KTZ_1936, are replaced by
LOK_eu4_import_empty; missing OOBs also load that explicit empty file. No army,
navy or air force was invented or converted from EU4. Existing country-specific
OOBs are kept only when their deployment locations belong to assigned territory.
The source import does not recreate EU4 missions, events or political mechanics.

## Countries

| EU4 | HOI4 | Source nation | States | Capital state |
|---|---|---|---:|---:|
| ANT | ANT | Kingdom of Antophilia | 6 | 172 |
| AXO | AXO | Maritime Republic of Axolina | 7 | 1084 |
| BAZ | BAZ | Kingdom of Bogdessa | 5 | 1328 |
| COU | COU | Altarian Council | 7 | 148 |
| CRA | CRA | Craeythin Conformity | 2 | 1263 |
| DAW | DAW | Serene Svitanok State | 10 | 134 |
| DRO | DRO | Droogian Councils of Moldoshia | 8 | 503 |
| ELC | ELC | East-Laurandar Company | 3 | 1063 |
| FMT | FMT | Free Macaquian Territories | 3 | 1105 |
| FOF | FOF | Formicidean Federation | 4 | 310 |
| FOR | FOR | Formicidea | 8 | 181 |
| FRO | FRO | Mountain Domains of Frosilvania | 3 | 945 |
| FRU | FRU | Principality of Calderitia | 13 | 1124 |
| HIV | HIV | Hivelands | 9 | 1107 |
| INT | INT | Intaria | 1 | 182 |
| IOS | IOS | Empire of Ilyania | 9 | 1245 |
| ITZ | ITZ | Federation of Itzoltenia | 2 | 944 |
| LAU | LAU | United Laurnaise States | 26 | 467 |
| LRN | LAK | Laurendaar | 5 | 1066 |
| MAG | MAG | Magma Legions | 5 | 419 |
| NDF | NDF | Neuvorian Defense Federation | 3 | 101 |
| NOV | NFS | Novian Arikhanate | 13 | 312 |
| PMA | PMA | Cyberpuff Incorporated | 6 | 1338 |
| PMC | PMC | United Agrarian Republics of Oyskterland | 4 | 1091 |
| PMD | PMD | United Waceg Trading Bureaus | 4 | 1098 |
| PMM | PMM | West-Puffian Reaping Conglomerate | 7 | 1095 |
| PMT | PMT | New Republic of Shurlidy | 3 | 137 |
| PMW | PMW | Puffiland Securities | 5 | 497 |
| PUF | PUF | Puffiland Monarchical Republic | 9 | 1340 |
| SAR | SAR | Grand Duchy of Saru | 8 | 1100 |
| SNO | SNO | Empire of Snowdonia | 9 | 460 |
| TUN | TUN | Imperiet-av-Tundrabor | 2 | 978 |
| URS | URS | Federation of Urscydia | 21 | 190 |
| USS | USS | Urscydian Socialist Republic | 4 | 1264 |
| VAR | VAR | Greater Vardalvian Vampiric Domains | 4 | 263 |
| VIV | VIV | Puffian Councils of Vivhilland | 6 | 1236 |
| VPL | VPL | Vespidian Legionary State | 4 | 1133 |
| WMD | WMD | Watermasters' Domain | 1 | 331 |
| WSF | WSF | West Flusion | 71 | 922 |

## Validation actually performed

- `python -m py_compile tools/import_zzz_from_eu4.py` passed; its generated bytecode
  was removed. No cache or temporary diagnostic was added to the patch.
- `python -B tools/import_zzz_from_eu4.py --eu4 "C:/Users/elowi/Documents/Paradox Interactive/Europa Universalis IV/mod/LegacyOfKattailEU4"`
  completed as a dry run before installation.
- The same command with `--apply` installed the audited plan and verified it.
- `python -B tools/import_zzz_from_eu4.py --verify` passed: 39 countries,
  320 state transfers, 631 game-content output files, 12,102 protected files.
- Changed script blocks parse; static tags and character IDs are unique, capital
  ownership, country definitions, recruited characters, OOBs and portraits resolve.
- Independent original-byte comparisons: all 320 state files are identical outside
  changed ownership/core lines. Existing country histories are identical outside
  capital/OOB lines, and country definitions outside RGB. State BOM/newlines match.
- All 82 added localisation keys are unique across active localisation, BOM/header
  are correct, and no replacement characters were introduced.
- Ran `loc_analyzer.py` through `runpy.run_path(..., run_name="__main__")`, redirecting
  its fixed diagnostic output to ignored scratch instead of editing the tracked
  snapshot. Repeated with pre-import files supplied as a read-only baseline.
  Both runs report the identical set of 2,285 missing keys and 7,894 potentially
  unused keys. No new missing keys were introduced.
- Exact pixel comparisons passed for all 234 converted flags; all are RGB TGA at
  native dimensions. A source/converted contact sheet was visually inspected.
- `python -B tools/validate_map.py` run before and after: identical two existing
  non-neighbour railway errors at line 893 (20839/20841) and line 894 (20841/19461).
  These failures are unrelated: all map files match their pre-import hashes.
- `git -c core.fsmonitor=false diff --check` passed. Ran `git diff --stat` and
  `git diff`, reviewed task-specific changes against pre-import bytes, and checked
  all generated text. Existing painter/user changes are preserved.
- No CWTools executable was found. No in-game test is claimed.

## Files, sources and recovery

[files.txt](files.txt) lists every exact changed/new path for this task, including
its documentation and importer. [audit.json](audit.json) records every country,
state vote, output hash, protected hash and source-file hash. It is the detailed
provenance record, not a game input. [Importer](../../../tools/import_zzz_from_eu4.py)
uses dry-run-by-default and refuses repeated installation.

Source root: the active local LegacyOfKattailEU4 mod, read only. Sources:
`history/provinces`, `history/countries`, `common/country_tags`, `common/countries`,
`common/cultures`, `map/provinces.bmp`, `map/definition.csv`, `map/default.map`,
`map/climate.txt`, English localisation, `gfx/flags`, `ideology-merge-audit.json`
and `ideology-merge-round2-audit.json`. Exact file references are in audit.json.
HOI4 syntax/reference: `.agents/rules/hoi4-modding-guide.md`,
`modding_documentation/copilot_instructions.md`,
`modding_documentation/wiki_doc/Country creation - Hearts of Iron 4 Wiki.md`,
nearby native country/character/OOB files and the current ideology/portrait catalogs.
Tag aliases are corroborated by dormant declarations, NFS state history/species,
NFS_neutrality and LAK_neutrality localisation, and their existing flags.

Original bytes of replaced game files, including pre-existing user edits, are
saved under `work/zzz-eu4-import/before/`. New-file versus replaced-file status
can be established from the exact path list and this backup. Do not restore
against a later edited working tree without comparing it first.

Remaining work: restart HOI4, begin a fresh campaign, select imported countries
and inspect capitals, names, flags, tooltips and startup logs. Engine loading,
AI behaviour, supply across new borders and balance remain untested. Existing
railway errors remain outside this import's scope.

# State-history duplicate audit — 2026-11-24

Branch: `Painter-Test`. Audited all **1,902** `.txt` files under `history/states`.
Found 46 files with two direct `history` blocks; no missing histories or parse
errors. **All 1,902 now have exactly one history block.**

## Changes

Removed 39 redundant second ZZZ histories, preserving each primary history exactly,
including current owners, demographic setup, victory points and provincial buildings.
State 1124 (`1124-Calderi.txt`) now has only its FRU history.

Consolidated seven same-owner cases: 151 (BRA), 284 (FKS), 556–559 (MEW) and 953
(SOF). Preserved all unique VPs, cores, claims, state buildings and provincial
buildings from both blocks. For overlapping building fields, retained the later
source value: state 151 industrial_complex 0; state 284 industrial_complex 1 and
arms_factory 1; state 953 infrastructure 3 and industrial_complex 0. No new values
were invented. See audit.json for complete conflict records.

Added `state_history_count` to `tools/validate_map.py`, with four regression tests,
and made `tools/import_zzz_from_eu4.py` reject states with anything other than one
history. The previous importer read only the first history; its earlier verification
was insufficient to detect later ZZZ blocks. Its old audit is a historical snapshot,
not a current hash baseline after this cleanup and intervening user edits.

Unrelated uncommitted edits were preserved. State IDs, province membership, resources,
manpower and categories are unchanged. No localisation or map assets changed. The
only formatting change outside history nodes removes one trailing space on state
557's province-list line, newly exposed as added whitespace in the consolidation diff.

## Validation

- Parsed all 1,902 state files after repair: exactly one history each, unique IDs,
  balanced complete blocks and no parse errors. Importer's state reader also loads
  all 1,902 successfully.
- Original-byte hashes confirm the other 1,856 state files are unchanged by this
  task. Independent parsed comparisons confirm all root fields and demographics
  were preserved; all 39 retained primary histories are identical to their originals.
- Independent union comparisons confirm all seven consolidated histories retain
  their VP, core, claim and final building values. BOM and newline sequences match
  each original, including pre-existing CR/CR/LF files.
- `python -B tools/test_validate_map.py`: four tests pass (duplicate ZZZ block,
  comments/quoted braces, dated effects, missing history).
- `python -m py_compile tools/validate_map.py tools/test_validate_map.py tools/import_zzz_from_eu4.py work/state-history-audit/cleanup.py`:
  passed, using ignored `work/state-history-audit/pycache` as PYTHONPYCACHEPREFIX.
- `python -B tools/validate_map.py`: original validator before changes reported two
  railway errors; upgraded validator before repair detected all 46 duplicate files
  plus those two errors. After repair, only the identical railway failures remain:
  line 893 (20839/20841) and line 894 (20841/19461). No duplicate-history errors.
- `git -c core.fsmonitor=false diff --check`: passed after the one whitespace fix.
  `git diff --stat` and `git diff` were run and reviewed, separating pre-existing
  working edits. No game launch or in-game test is claimed.

## Exact state changes

| State | Primary owner retained | Extra owner | Action |
|---:|---|---|---|
| 1107 | HIV | ZZZ | Remove ZZZ block |
| 1108 | HIV | ZZZ | Remove ZZZ block |
| 1109 | HIV | ZZZ | Remove ZZZ block |
| 1121 | FRU | ZZZ | Remove ZZZ block |
| 1122 | FRU | ZZZ | Remove ZZZ block |
| 1123 | FRU | ZZZ | Remove ZZZ block |
| 1124 | FRU | ZZZ | Remove ZZZ block |
| 1125 | FRU | ZZZ | Remove ZZZ block |
| 1126 | FRU | ZZZ | Remove ZZZ block |
| 1127 | FRU | ZZZ | Remove ZZZ block |
| 1130 | FRU | ZZZ | Remove ZZZ block |
| 1145 | HIV | ZZZ | Remove ZZZ block |
| 1146 | HIV | ZZZ | Remove ZZZ block |
| 1147 | HIV | ZZZ | Remove ZZZ block |
| 1148 | HIV | ZZZ | Remove ZZZ block |
| 1149 | HIV | ZZZ | Remove ZZZ block |
| 1156 | ZZZ | ZZZ | Remove ZZZ block |
| 1158 | ZZZ | ZZZ | Remove ZZZ block |
| 1258 | URS | ZZZ | Remove ZZZ block |
| 1259 | URS | ZZZ | Remove ZZZ block |
| 1265 | CRA | ZZZ | Remove ZZZ block |
| 1266 | CRA | ZZZ | Remove ZZZ block |
| 1278 | ZZZ | ZZZ | Remove ZZZ block |
| 1306 | MAG | ZZZ | Remove ZZZ block |
| 1309 | MAG | ZZZ | Remove ZZZ block |
| 1310 | MAG | ZZZ | Remove ZZZ block |
| 151 | BRA | BRA | Merge same-owner blocks |
| 167 | FRU | ZZZ | Remove ZZZ block |
| 2 | ZZZ | ZZZ | Remove ZZZ block |
| 224 | ZZZ | ZZZ | Remove ZZZ block |
| 237 | ZZZ | ZZZ | Remove ZZZ block |
| 246 | ITZ | ZZZ | Remove ZZZ block |
| 249 | WSF | ZZZ | Remove ZZZ block |
| 253 | FRU | ZZZ | Remove ZZZ block |
| 284 | FKS | FKS | Merge same-owner blocks |
| 331 | WMD | ZZZ | Remove ZZZ block |
| 362 | HIV | ZZZ | Remove ZZZ block |
| 419 | MAG | ZZZ | Remove ZZZ block |
| 423 | MAG | ZZZ | Remove ZZZ block |
| 465 | SNO | ZZZ | Remove ZZZ block |
| 556 | MEW | MEW | Merge same-owner blocks |
| 557 | MEW | MEW | Merge same-owner blocks |
| 558 | MEW | MEW | Merge same-owner blocks |
| 559 | MEW | MEW | Merge same-owner blocks |
| 943 | ITZ | ZZZ | Remove ZZZ block |
| 953 | SOF | SOF | Merge same-owner blocks |

## Other audit findings

50 files contain other repeated state-level fields, primarily `resources`, plus
some manpower/category/supply settings. These are separate from duplicated history
blocks and were preserved to avoid an unrequested resource or state-stat change.
Exact files/fields are recorded under `other_root_duplicates_unchanged` in audit.json.

## Sources, paths and recovery

[files.txt](files.txt) lists every exact path changed by this task. [audit.json](audit.json)
records the original hashes for all 1,902 files, the 46 changes, final hashes,
conflict choices and validation. Raw pre-edit files are backed up under
`work/state-history-audit/before/`; the dry-run/apply script and detailed validation
are in the same ignored work directory. No commit was made.

Primary sources: each state's existing history blocks; local
`modding_documentation/wiki_doc/State modding - Hearts of Iron 4 Wiki.md`, sections
History and Examples (repeatable VP entries, state/provincial building structure);
`.agents/rules/hoi4-modding-guide.md`; `modding_documentation/copilot_instructions.md`;
existing painter source-span parser; `tools/validate_map.py`. No external information
or new identifiers were needed for the state edits.

Remaining: in-game verification of state ownership/buildings. The existing railway
errors and unrelated repeated root fields remain; no duplicate state history remains.

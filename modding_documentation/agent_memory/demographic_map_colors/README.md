# Species/culture colours and optional culture groups - 2026-11-25

## Findings and changes

The user identifies Altarian (species 61): its saved light cyan appears white in
game. Both original native layers already contained #9DFFFF-equivalent RGB;
the RGB itself was not white. The top layer did not initialize red/green/blue/
alpha when minority=1000 (no minority), or for any unmatched minority. Added
explicit defaults: top alpha=0, bottom alpha=1, neutral RGB fallback. Valid
majority/minority branches keep their existing alpha=1/.75 behavior. Altarian's
six-decimal channels are now native three-decimal (.616,1.000,1.000), preserving
#9DFFFF. This removes undefined outputs and unsafe extra precision. Whether the
uninitialized overlay caused this particular white appearance remains an
unverified engine-rendering hypothesis; no game restart/render test occurred.

Confirmed culture defect: set_map_color walked every matching variable name,
including divide_temp_variable operands. It wrote the RGB value over the intended
num_cultures divisor. Native culture 103 (Novaratite) had all three corrupted
operands. A limited fixed-point interpreter of those native operations produced
RGB (1.247,1.247,1.249), which clamps to white. Restored all three divisors and
preserved its intended #3944CA color using native fractions (.224,.267,.792).
The initial gray/count=1 seed also tinted every culture average toward gray,
unlike the painter. It now starts at zero and uses a gray fallback only when
there are no cultures. Single cultures and mixed averages now match definitions
within the native fixed-point arithmetic precision.

The writer now changes only literal add_to_temp_variable culture color definitions
or set_temp_variable species definitions. Math references/divisors stay intact.
Every matching branch is updated: minority IDs 20-23 have duplicate native
branches, and changing only the first used to be overwritten by the later branch.
Their existing duplicate branches were retained (currently identical); future
edits synchronize their color values without deleting authored logic.

New and edited colors use nearest 0.001 fractions. This grid can reproduce all
256 byte channel values exactly after conversion back to bytes; regression checks
exercise every value, zero and full intensity included. No palette hues were
redesigned and existing species/culture identities remain unchanged.

Culture groups are optional. No group is an explicit editor choice. New ungrouped
cultures have no group-array/trigger membership or fictitious None group reference.
Moving a grouped culture to No group removes those memberships; assigning a real
group restores them. Editing an already ungrouped culture preserves authored
full-description text; new/changed ungrouped descriptions contain name/description
without a group clause. Undo/Redo, native Save/reload and localization BOM work.

## Exact files changed by this task

- common/map_modes/LOK_species_map_mode.txt
- common/map_modes/LOK_culture_map_mode.txt
- legacy_of_kattail_painter/demographics.py
- legacy_of_kattail_painter/painter.py
- legacy_of_kattail_painter/install.py
- legacy_of_kattail_painter/test_demographic_colors.py
- legacy_of_kattail_painter/README.md
- legacy_of_kattail_painter/MODLOG.md
- modding_documentation/agent_memory/CURRENT_STATUS.md
- modding_documentation/agent_memory/DECISIONS.md
- modding_documentation/agent_memory/plans/demographic-map-colors.md
- modding_documentation/agent_memory/demographic_map_colors/README.md
- modding_documentation/agent_memory/demographic_map_colors/audit.json
- modding_documentation/agent_memory/demographic_map_colors/verification.json

No native IDs/localization keys or gameplay flags added/renamed. Existing
LOK_species_map_mode, LOK_culture_map_mode, species/minority 61, culture 103,
num_cultures, red/green/blue/alpha and group-array/trigger conventions retained.
Only the two native mapmode files were written to repair existing game data.
Native group/country/state/localization data was not bulk migrated. User edits
predating this task, including the requested Altarian hue, were preserved.

## Validation actually performed

- python -B -m unittest discover -s legacy_of_kattail_painter -p test_demographic_colors.py:
  six passed, including every 0-255 channel roundtrip, literal-only edits,
  real single/mixed native arithmetic, duplicate execution, new branch creation,
  grouped/ungrouped transitions, save/reopen/Undo and mapped Tk No group Apply.
  Repeated after the final ungrouped tooltip separator change: six pass.
- python -B -m unittest discover -s legacy_of_kattail_painter -p 'test_*.py':
  160 passed in 23.998 seconds; the final tooltip-only formatting tweak was
  followed by the six focused tests above.
- python -m py_compile legacy_of_kattail_painter/demographics.py
  legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/install.py
  legacy_of_kattail_painter/test_demographic_colors.py: passed, PYTHONPYCACHEPREFIX
  directed to Temp.
- Staged exact native before/after diff inspected, then guarded atomic native
  application with original-byte backup. audit.json records exact hashes/path.
- python -B legacy_of_kattail_painter/backups/mapmode-color-fix-stage/verify_native.py:
  passed. Limited native-operation interpreter evaluates all 62 majority, 62
  minority and 102 single-culture color paths; every output matches the painter
  palette. No-minority alpha=0 even with previously white RGBA inputs. Mixed
  cultures/no-culture fallback stay in range. Every culture divisor is intact.
  Real mapped Tk Altarian majority/minority Apply/Undo and ungrouped native
  culture 8 Apply/Undo passed. Live UI Save forbidden, no callbacks or drafts,
  4,213 native source hashes unchanged. verification.json records the results.
- python -B tools/validate_map.py: passed, 21,515 provinces, 20,926 assigned,
  413 strategic regions and no X crossings.
- git diff --check -- legacy_of_kattail_painter/demographics.py
  legacy_of_kattail_painter/painter.py legacy_of_kattail_painter/install.py:
  passes. New test/report whitespace and task-baseline native diffs checked.
  Global git diff --check still reports pre-existing/user whitespace in culture
  103 lines retained verbatim and unrelated startup/trigger/state-history edits.
  These were not reformatted. Complete task diffs and git diff --stat reviewed.

## Sources and limits

Installed common/map_modes/documentation.md (top/bottom rendering order and
color block section) defines player scope/FROM state, and returned RGB/alpha
variables. Installed documentation/modifiers_documentation.md lines 6-7 states
numbers support up to three decimals; repository wiki_doc/Data structures -
Hearts of Iron 4 Wiki.md describes the 1/1000 fixed-point grid. Installed effects
reference entries for set/add/divide/multiply_temp_variable provide the native
arithmetic conventions. The active common/map_modes files and existing nearby
working branches were inspected before edits.

The interpreter is a bounded regression aid, not the HOI4 engine. The user's
latest error.log contains no species/culture mapmode-specific parse error. No
running hoi4 process was available during investigation. No game was launched,
no engine rendering or CWTools validation performed, and logs were not changed.

Next: restart the painter and fully restart HOI4, then inspect Altarian majority
states with no minority and mixed states with Altarian stripes, plus culture 103.
The white rendering report still needs that engine confirmation; the saved RGB,
alpha defaults, culture arithmetic and optional-group flows are verified.

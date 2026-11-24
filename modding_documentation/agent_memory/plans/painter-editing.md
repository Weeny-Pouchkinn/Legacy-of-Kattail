# State demographic painting — 2026-11-24

Scope: save state painting, migrate initial culture/species/minority assignments
from startup into state histories, provide EU4-style layer palettes, majority
and minority species brushes, minority stripes, and map-mode-defined colours.
Retain runtime `state_cultures`, `species`, `minority`, culture-group registries,
country species ideas and later gameplay conversions. No binary topology edits.

- [x] Inspect instructions, existing painter, startup evaluator, runtime readers,
  map palettes and native state-history examples.
- [x] Implement guarded, backed-up saves and reviewed migration application.
- [x] Add defined-colour rendering and layer palettes/brush controls.
- [x] Run fixtures and migration dry run; inspect output and apply to live mod.
- [x] Validate all migrated values, references, encoding and map baseline;
  exercise painting/save/reload in fixtures and actual Tk controls; update memory.

Baseline: clean working tree at `a8d83c64`; 1,902 states and 1,655 initial startup
statements evaluated, no missing state references. Earlier staged migration was
never installed. Map validator's known railway failures must be checked again.
Wiki live access failed; local State modding reference and installed native state
271 show state histories are effect scopes. Game launch remains unverified.

Completed: migration applied with original backups; all initial values match,
all state content outside the delimited blocks is preserved, startup's surviving
AST is unchanged, and no map/localisation/binary assets changed. Sixteen fixtures
and all seven Python compile checks pass. Tk fixtures cover actual painting,
independent fields, minority clearing, Shift picking and Save/reload. Real data
passes palettes, province painting, undo/redo, all views and both window sizes.
`verify_real.py` passes 1,026 mask-size renders and 10,786 unchanged hashes during
UI-only checks. Map validator reports the same two baseline railway errors.

Remaining: restart the painter to use the feature; verify initialisation in a
fresh campaign. No game launch, CWTools diagnostics or screenshot review claimed.
See CURRENT_STATUS.md and the painter MODLOG.md for evidence and limitations;
painter-editing-files.txt lists every exact changed/new repository path.

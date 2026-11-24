# MODLOG — Legacy of Kattail painter

## 2026-11-24 — EU4 interface styling

Replaced the forced dark `clam` theme and banner with native ttk controls,
compact Undo/Redo/Discard, Paint/View and zoom tools. Matched the EU4 painter's
left sidebar, section typography, spacing and `#1e1e1e` map canvas. Sources and
scrollable state setup share sidebar tabs; map, source fields and flags retain
their workspace tabs. Map inspection opens state setup automatically. Flag
previews fit narrow panes while preserving aspect ratio and native image sizes.
The application still keeps all drafts in memory. No game identifiers changed.

Validation commands:

- `python -m py_compile legacy_of_kattail_painter/painter.py` — passed; bytecode
  redirected outside the repository using `PYTHONPYCACHEPREFIX`.
- `python -B -m unittest discover -s legacy_of_kattail_painter -p test_painter.py -v`
  — all 11 tests passed.
- `python -B legacy_of_kattail_painter/verify_real.py --mod . --output "$env:TEMP/lok-painter-ui-verification"`
  — passed real-data UI/drafts/undo/redo/filter/flag checks, all 1,023 mask-size
  renders, and 10,786 unchanged game-source hashes. Four existing OOB brace
  errors remain, as documented below.
- Additional Python/Tk checks exercised all three workspace tabs, state/source
  navigation, all eight map views, state-form scrolling and flag-preview sizing
  at 1500x900 and 1050x680. Native `vista` theme remained selected. Preview sizes
  were 492x312 and 391x248 respectively.
- `python -B tools/validate_map.py` — failed on the two previously documented
  railway non-neighbor links at lines 893-894; map inputs were not changed.
- `git diff --check`, `git diff --stat`, `git diff` and `git diff --no-index
  --check -- /dev/null legacy_of_kattail_painter/painter.py` — reviewed; no
  whitespace errors. The painter directory was already untracked, so ordinary
  Git diff omits its files; the full painter source was separately reviewed.

Desktop screenshot inspection was unavailable (`CODEX_CLI_PATH` helper error).
Tk controls/layout were checked programmatically; no screenshot or in-game
validation is claimed. Restart the painter to load the updated interface.

## 2026-11-24

Requested: first read-only HOI4 painter, fields for mod-specific content, a flag
maker using tintable white Stellaris masks and a single-colour background, all
under `legacy_of_kattail_painter` in the mod root. User additionally authorised
experimental migration of state culture/species into state files and noted Git
version control.

Route: standalone Python/Tk with Pillow/numpy, reading source data. No source
writers in the application. A separate staging generator and hash-checked
installer handle the authorised migration experiment. No game assets bundled.

Observed source: 1,902 states, 181 country histories, 4,154 script files, 341 flat
Stellaris/Gigastructures mask choices. Dimensions from native mod TGA flags:
82×52, 41×26, 10×7. EU4's loader is not imported because it writes lazy caches.

The mod's state demographics were not native database keys: cultures use
`state_cultures`, majority species uses `species`, and minority uses `minority`
with sentinel 1000. Country species ideas are distinct and remain untouched.
Four freeport states (894–897) have cultures [17, 67, 2]; preserve all three.

Migration stage moves 1,655 initial startup statements to 1,902 state files;
1,903 source files affected including the original startup file. Runtime
variables/arrays remain compatible with consumers. No live source files edited.
Original hash checks prevent applying a stale stage. The complete diff and
per-state initial snapshot are included in `migration_patch/`.

Validation: 11 fixture tests pass, covering ordered cultures/conditions/minorities,
read-only isolation, undo/redo, arbitrary fields, repeated edits, path confinement,
unknown-effect rejection, migration preservation and tintable flat masks. Real
data verification is recorded separately in `verification/verification.json`.
Hidden Tk checks passed; all 1,023 mask/size renders succeeded and 10,786 source
file hashes remained identical. Four existing OOB files have excess closing
braces; they stay accessible through raw source. No OOB repair was attempted.
Independent staged-file checks preserve all original state content outside the
new sections and match the original evaluated demographics. Disposable install
checks verified all 1,903 backups and installed bytes, and rejected stale input
before writes. The installer uses Python because local PowerShell execution
policy rejected .ps1 execution; no policy or registry setting was changed.

Limitations: staged values use undated initial ownership/core history and observed
startup expressions, not a full HOI4 VM. Other startup files/scripted effect calls
and changed initialisation timing require engine validation. No modded launch,
game input takeover, commit, PR or publishing performed. The live mod path is
outside writable roots, so direct installation was unavailable in this session.

Next action: install the folder; optionally apply the reviewed migration using
the installer; run the painter. Validate the migration in a fresh offline game
and inspect relevant logs before accepting it.

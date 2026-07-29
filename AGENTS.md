# AGENTS.md — Legacy of Kattail

## Scope

These instructions apply to the entire repository on the `Legacy-of-Kattail-Main` branch.

Treat this repository as a total-conversion-scale Hearts of Iron IV project. Changes can affect many replaced vanilla paths, a custom map, country history, events, focus trees, decisions, interface files, localisation, and supporting Python tools.

A more specific `AGENTS.md` or `AGENTS.override.md` in a subdirectory may add or override instructions for that subtree. Do not weaken repository-wide safety, validation, encoding, or documentation requirements without an explicit user instruction.

## Project identity and compatibility

- Mod name in `descriptor.mod`: `Legacy of Kattail DEV`.
- Treat `supported_version="1.17.*"` as the current declared game compatibility target.
- `descriptor.mod` also contains `version="1.15.*"`. This is an existing inconsistency: report it when relevant, but do not silently normalize either field.
- The mod uses many `replace_path` entries. Do not add, remove, or reorganize them unless the task explicitly requires it and the consequences have been inspected.
- Do not assume vanilla content remains available in a replaced path.
- Preserve compatibility with the branch being edited rather than with remembered conventions from another branch or mod.
- Ignore compatibility with past saves, this is a rapidly changing development environment, not a deployed live branch.

## Instruction and reference order

For every task, use the following order of authority:

1. The user's current request.
2. This root `AGENTS.md`.
3. A nearer `AGENTS.md` or `AGENTS.override.md`, where applicable.
4. `.agents/rules/hoi4-modding-guide.md`.
5. Relevant files under `modding_documentation/`.
6. Existing nearby implementations in this repository.
7. Current official Hearts of Iron IV modding documentation and the HOI4 Modding Wiki.
8. Vanilla examples matching the declared supported game version.

When sources conflict:

- Do not guess silently.
- Prefer current repository behavior for project-specific naming and structure.
- Prefer current HOI4 documentation for engine syntax.
- Explain the conflict and make the smallest reversible choice.
- Never copy a vanilla pattern from a different game version without checking that its scopes, effects, triggers, database types, and file paths still apply.

Before writing HOI4 script, read `.agents/rules/hoi4-modding-guide.md` and the relevant local documentation. `modding_documentation/copilot_instructions.md` requires generated HOI4 code to follow patterns found in `modding_documentation`.

Treat `errors.txt`, `loc_analysis_results.txt`, and `modding_documentation/error.log` as diagnostic snapshots, not automatically current sources of truth.

## Durable project memory

Conversation context is not project memory. Durable facts must live in the repository.

For a non-trivial, multi-step, or multi-session task, use:

- `modding_documentation/agent_memory/CURRENT_STATUS.md`
- `modding_documentation/agent_memory/DECISIONS.md`
- `modding_documentation/agent_memory/plans/<task-name>.md`, when a task needs milestones

Create these files only when they are useful; do not create empty bureaucracy for a one-file fix.

At the start of a substantial task:

1. Read the memory files if they exist.
2. Verify their claims against the current branch.
3. Read the relevant implementation before relying on a status note.
4. Mark stale or contradicted notes instead of propagating them.

At the end of a substantial task:

- Update `CURRENT_STATUS.md` with completed work, current blockers, validation actually performed, and the next concrete action.
- Record durable architectural or design choices in `DECISIONS.md` with date, decision, rationale, and consequences.
- Update the active plan after each completed milestone.
- Store facts and decisions, not chat transcripts.
- Clearly label hypotheses, unresolved questions, and unverified assumptions.
- Never claim a feature is complete merely because files were generated.

## Repository orientation

Inspect the relevant areas before editing:

- `.agents/rules/` — project-specific agent and scripting guidance
- `.config/core/` — local CWTools/core configuration
- `common/` — game databases, scripted effects/triggers, focus trees, decisions, ideas, on-actions, and related systems
- `events/` — event namespaces and event definitions
- `history/` — countries, states, units, and other historical setup
- `interface/` — GUI, sprite, and interface definitions
- `localisation/english/` — English localisation
- `map/` — custom map data and binary map assets
- `modding_documentation/` — local references, wiki-derived notes, vanilla examples, and diagnostics
- `tools/` — repository validators and helper scripts
- root Python scripts — generators, analysers, and migration utilities

The repository contains existing country-tag-based focus, event, and localisation naming patterns. Follow the nearest relevant implementation instead of inventing a parallel convention.

## Required workflow

### Before editing

1. Restate the concrete task internally and identify what is out of scope.
2. Read the relevant project instructions and memory files.
3. Search the entire repository for:
   - identifiers to be added or changed
   - event namespaces
   - country tags
   - state and province IDs
   - focus, decision, idea, character, trait, technology, and sprite IDs
   - localisation keys
   - scripted effect, trigger, variable, flag, and event-target names
4. Inspect at least one nearby working example of the same content type.
5. Identify all directly coupled files.
6. Note assumptions that cannot be verified from the repository.
7. For broad work, write a milestone plan before implementation.

### While editing

- Make the smallest coherent patch that satisfies the request.
- Preserve existing formatting, ordering, encoding, and line endings unless a change is required.
- Do not reformat unrelated blocks.
- Do not rewrite whole files when a targeted edit is sufficient.
- Do not perform speculative cleanup alongside feature work.
- Do not silently rename public identifiers.
- Do not delete apparently unused content without checking references across the repository.
- Do not use subagents unless the user explicitly requests them.
- Stop and report when a required fact cannot be established safely.

### After editing

1. Review the complete diff.
2. Check every new and changed reference.
3. Run the narrowest relevant validators.
4. Update durable project memory for substantial work.
5. Report what changed, what was validated, and what remains uncertain.

## Clausewitz/HOI4 scripting conventions

### Formatting and naming

- Use tabs for indentation in HOI4 script files, following existing project style.
- Use lowercase script keys and `snake_case` custom identifiers unless an established engine or repository convention requires otherwise.
- Keep country tags uppercase.
- Preserve existing namespace and prefix conventions.
- Use descriptive identifiers; avoid generic names such as `event_1`, `temp_effect`, or `new_focus`.
- Keep braces, assignment operators, and block structure consistent with nearby files.
- Do not use unsupported comparison forms such as `<=` or `>=`; express conditions using documented HOI4 syntax.
- Do not use unsupported unary negation of variable references. Use documented variable operations or an explicit intermediate value.
- Do not introduce magic numbers when a script constant, named variable, or documented threshold is more maintainable.

### Identifiers and references

Before creating an identifier, search for exact and prefix matches.

Identifiers that must remain unique in their applicable namespace include, but are not limited to:

- event namespace and numeric ID combinations
- focus IDs
- decision and decision-category IDs
- idea and idea-category IDs
- character IDs
- trait IDs
- dynamic modifier IDs
- scripted effect and trigger names
- technology IDs
- equipment and unit IDs
- sprite names
- localisation keys
- country tags
- state and province IDs

Do not infer that different filenames make duplicate IDs safe.

When changing an identifier, update every reference and matching localisation key, or provide an explicit migration plan. Avoid identifier renames unless they are necessary.

### Scopes, triggers, and effects

- Confirm the expected scope for every trigger and effect.
- Trace `ROOT`, `FROM`, `PREV`, `THIS`, event targets, saved scopes, and iterators explicitly.
- Do not paste an effect into a different scope merely because the syntax parses.
- Prefer an existing scripted trigger or scripted effect when it expresses the intended behavior.
- Move repeated logic into `common/scripted_triggers/` or `common/scripted_effects/` when reuse is real and improves clarity.
- Keep tunable values in existing script-constant systems when appropriate.
- Use flags for durable booleans and variables for quantities; do not interchange them casually.
- Avoid broad `every_country`, `every_state`, or `every_character` loops unless necessary.
- Avoid global daily, weekly, or monthly iteration through all entities unless the user explicitly requires it and the performance cost is justified.
- Prefer event-driven updates, cached flags, scoped on-actions, or bounded lists.

### Events

- Declare and reuse a clear namespace with `add_namespace`.
- Follow existing repository ID patterns such as `namespace.number`.
- Search the repository before assigning an event number.
- Use `is_triggered_only = yes` when an event is only called by script.
- Keep player-visible consequences in option effects and tooltips.
- Place internal bookkeeping, setup, hidden flags, variables, and non-player-facing effects inside `hidden_effect` where appropriate.
- Do not expose implementation details in generated tooltips.
- Ensure every visible title, description, and option has a valid localisation key.
- Verify event pictures and sounds exist before referencing them.
- Do not create polling events when an on-action or direct event chain is sufficient.

### National focuses

- Store focus trees under `common/national_focus/`.
- Follow the repository's country-tag-based file and ID conventions.
- Keep focus trees spatially compact and readable.
- Check `x`, `y`, and `relative_position_id` relationships for overlaps and unintended drift.
- Verify every prerequisite, mutually exclusive link, bypass, availability condition, completion reward, and shared focus reference.
- Duplicate focus IDs are never acceptable, even when they are in different trees.
- Ensure focus icons and localisation keys exist.
- Do not copy an entire vanilla tree to implement a small custom branch.
- Keep branch logic aligned with the intended player path; do not add unrequested alternate-history outcomes.

### Decisions and missions

- Store decision categories under `common/decisions/categories/`.
- Store decisions and missions under `common/decisions/`.
- Verify category membership, visibility, availability, activation, cancel, timeout, and completion scopes.
- Use custom trigger tooltips when raw scripted conditions would be unclear to players.
- Ensure costs, durations, cooldowns, and AI weights are explicit and internally consistent.
- Avoid high-frequency decision checks that scan the entire world.

### On-actions and recurring logic

- Reuse appropriate vanilla or project on-actions before creating a new recurring pulse.
- Keep on-action effects narrowly scoped.
- Document any new persistent flags or variables.
- Ensure repeated actions are idempotent where duplicate execution is possible.
- Do not place expensive world scans on daily, weekly, or monthly pulses without a written justification.

## Localisation

Localisation is encoding-sensitive.

- English localisation belongs under `localisation/english/` unless the existing feature uses a more specific established subfolder.
- Preserve UTF-8 with BOM.
- Preserve the first line exactly as `l_english:` including its encoding marker.
- Do not convert localisation files to plain UTF-8 without BOM, ANSI, UTF-16, or another encoding.
- Follow existing filename and key-prefix conventions.
- Keep the `:0` version marker where the surrounding files use it.
- Preserve `$TOKENS$`, `[Scope.GetFunctions]`, `£icons£`, colour codes, escaped characters, and scripted-localisation calls exactly unless intentionally changing them.
- Do not overwrite human-written localisation without explicit instruction.
- Do not invent production-ready lore, names, political claims, or narrative text when the user has not supplied or requested it.
- When a required description has no approved text, prefer a syntactically valid empty value rather than fabricated prose.
- When the user explicitly requests AI-written placeholder localisation, mark it with the exact comment:
  `#AI-Generated Placeholder, change later!`
- Ensure every new visible game object has the required keys.
- Remove orphaned keys only after proving they are unreferenced.
- Requirements, costs, and effects shown to players must match the actual scripted values.

Before bulk localisation edits, make a targeted backup or use a script that can perform a dry run. Inspect the diff for BOM loss, escaped quote damage, and accidental line-ending conversion.

## Interface and graphics

- Search for an existing sprite definition before adding one.
- Keep sprite names globally unique.
- Follow established `interface/` and `gfx/` paths and naming patterns.
- Verify that every referenced texture exists with the correct case-sensitive path.
- Preserve expected DDS, TGA, PNG, and BMP formats, dimensions, compression, mipmaps, and alpha behavior.
- Do not fabricate binary image contents in text.
- When a temporary image is explicitly needed, copy an appropriate existing placeholder according to the project guide and clearly report it.
- Do not replace broad vanilla interface files for a local visual change unless the repository already does so and the task requires it.
- Check GUI element names, container relationships, scripted GUI references, and localisation together.
- Treat interface edits as potentially global because this mod replaces large portions of vanilla content.

## Map and state-history safety

The repository contains a custom map. Map edits are high risk and often require coordinated changes.

Before changing map data, inspect:

- `map/definition.csv`
- `map/provinces.bmp`
- `map/heightmap.bmp`
- `map/rivers.bmp`
- `map/terrain.bmp`
- `map/adjacencies.csv` or the repository's active adjacency source
- `map/strategicregions/`
- `map/supplyareas/`, where applicable
- `map/railways.txt`
- `map/supply_nodes.txt`
- `history/states/`
- relevant country and building history
- `modding_documentation/province_adjacencies.csv`

Rules:

- Never assign a province or state ID from memory.
- Verify province colours against `definition.csv`.
- Keep province IDs, RGB values, state membership, strategic regions, supply data, buildings, victory points, naval bases, railways, and adjacency links synchronized.
- Do not edit binary map assets unless the task explicitly requires it.
- Preserve the bitmap format expected by the engine.
- Check that province RGB values are unique and defined.
- Check that state and strategic-region province lists contain valid IDs.
- Check owner, controller, core, claim, and country-tag references.
- Check coastal, naval, impassable, and adjacency behavior after topology changes.
- A successful main-menu load is not sufficient validation for map work; some errors appear only after selecting a country or entering the map.

For map-related changes, run:

```bash
python tools/validate_map.py
```

Treat failures as blocking unless the failure is proven to be pre-existing and unrelated. Report pre-existing failures separately.

## History files

- Preserve historical dates and date-block structure.
- Verify country tags before assigning owners, controllers, cores, claims, leaders, or units.
- Keep state history consistent with map province membership.
- Check capital states, victory points, buildings, resources, and supply connections.
- Verify character IDs and recruitment effects.
- Do not invent historical setup to make a parser error disappear.
- When changing a start-state fact, search for events, focuses, decisions, scripted triggers, and localisation that assume the old fact.

## Python tools and generated content

The repository contains validators, analysers, and content-generation scripts.

- Target the repository's supported Python version and existing style.
- Prefer `pathlib` and explicit UTF-8/BOM handling where relevant.
- Do not hardcode a local absolute path.
- Do not make destructive bulk rewrites without a dry-run mode, backup, or reversible patch.
- Validate script inputs before writing files.
- Make generation deterministic where practical.
- Do not overwrite hand-authored content by default.
- Do not commit caches, temporary files, or generated diagnostics unless the repository intentionally tracks them.
- For a modified Python file, run at minimum:

```bash
python -m py_compile path/to/modified_script.py
```

- For a generator, inspect representative generated output and the resulting Git diff.
- Read a script's source or `--help` output before guessing command-line flags.
- Use `loc_analyzer.py` according to its actual current interface rather than assuming invocation syntax.

## Validation matrix

Run checks appropriate to the changed content. Do not claim a check was run when it was not.

### Every patch

```bash
git diff --check
git diff --stat
git diff
```

Also:

- inspect for unrelated edits
- verify balanced braces and complete blocks
- search for duplicate or colliding identifiers
- search for stale references to renamed identifiers
- confirm all new files are in the intended directories
- confirm case-sensitive paths
- check that generated files were not added accidentally

### HOI4 script

- Use repository/editor CWTools diagnostics when available.
- Check `.config/core/` before changing local parser behavior.
- Validate trigger and effect scopes, not just syntax.
- Start from a clean or clearly separated HOI4 `error.log`.
- Launch with debug logging when the environment supports it.
- Exercise the specific event, focus, decision, GUI, or history path changed.

### Localisation

- Verify UTF-8 BOM and the untouched `l_english:` header.
- Check duplicate keys.
- Check missing and orphaned keys relevant to the patch.
- Run the repository localisation analyser using its documented/current interface.
- Inspect rendered tokens, icons, variables, and line breaks in game when possible.

### Map

```bash
python tools/validate_map.py
```

Then, when the game is available:

- clear or archive the previous error log
- load the mod
- select a country
- enter the map
- inspect the changed region
- test supply, movement, adjacency, ownership, and state selection as relevant

### Game validation

A parser-clean file is not proof of correct gameplay.

When possible, verify:

- the mod reaches the main menu
- the intended country can be selected
- the relevant save/start date loads
- the changed content is reachable
- tooltips match actual effects
- AI behavior does not trigger obvious loops
- no new relevant errors or exceptions appear

Never report “tested in game” unless the game was actually launched and the affected path was exercised.

## Forbidden shortcuts

Do not:

- invent identifiers without a repository search
- assume a vanilla identifier exists inside a replaced path
- copy large vanilla files for a small change
- silently modify `descriptor.mod`, `replace_path`, or compatibility versions
- bulk-format unrelated code
- convert localisation encoding
- overwrite human-authored localisation with generated prose
- edit diagnostic output as though it were source code
- hide validation failures
- call a generated file complete without inspecting it
- add expensive global recurring loops as a convenience
- delete content merely because a text search found no obvious reference
- claim uncertainty has been resolved when it has not

## Completion report

Every completed task must end with a concise report containing:

1. **Summary** — what behavior or content changed.
2. **Files changed** — exact paths.
3. **Identifiers** — important IDs, namespaces, keys, flags, variables, or sprites added, changed, or removed.
4. **Validation** — exact commands and manual checks actually performed, with outcomes.
5. **Uncertainties** — assumptions, unavailable tools, or untested game behavior.
6. **Remaining work** — only genuine follow-up work, not speculative scope expansion.

For an incomplete task, clearly distinguish:

- completed work
- partial work
- blockers
- safe next action

Accuracy is more important than presenting the task as finished.

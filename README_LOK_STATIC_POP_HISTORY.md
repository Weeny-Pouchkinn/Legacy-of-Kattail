# Legacy of Kattail - Static Population History Generator

This is the first pass that moves starting population groups into **state history** instead of constructing them at runtime.

## What it generates

For every state whose starting owner is a playable country, the generator inserts a marked block directly inside `history = { ... }` in that state's existing history file.

Each population group is the same index across five parallel arrays:

- `lok_pop_species_array`
- `lok_pop_culture_array`
- `lok_pop_politics_array`
- `lok_pop_amount_array` - thousands of people
- `lok_pop_reserved_array` - always `0` for now

The generated state block contains literal `clear_array` / `add_to_array` effects and comments describing every generated split and every individual group. There is no runtime game-start allocator.

## IMPORTANT: scripted effect inputs

LoK must **not** use pseudo-parameter calls like:

```txt
LOK_add_pop_group = { SPECIES = 1 CULTURE = 5 POLITICS = 1 AMOUNT = 250 }
```

The included toolkit follows the working convention: set temp variables immediately before calling the effect with `= yes`.

Example:

```txt
set_temp_variable = { lok_pop_input_species = 1 }
set_temp_variable = { lok_pop_input_culture = 5 }
set_temp_variable = { lok_pop_input_politics = 1 }
set_temp_variable = { lok_pop_input_amount = 250 }
set_temp_variable = { lok_pop_input_reserved = 0 }
LOK_add_prepared_pop_group = yes
```

Filtered population change likewise uses caller-prepared temps:

```txt
# Remove one million Katzen Socialists of any culture.
set_temp_variable = { lok_pop_change_amount = -1000 }
set_temp_variable = { lok_pop_filter_species = 1 }
set_temp_variable = { lok_pop_filter_culture = -1 }
set_temp_variable = { lok_pop_filter_politics = 1 }
LOK_change_state_population = yes
```

## Run against the current repo checkout

From the LoK mod root:

```bat
python tools\generate_lok_pop_history.py . --in-place
```

Or make a separate patch directory instead of editing the checkout:

```bat
python tools\generate_lok_pop_history.py .
```

The default deterministic seed is `20260826`. Change the fuzz while preserving reproducibility with:

```bat
python tools\generate_lok_pop_history.py . --in-place --seed 12345
```

The generated block is bracketed by:

```txt
# >>> LOK GENERATED POP GROUPS START >>>
...
# <<< LOK GENERATED POP GROUPS END <<<
```

Re-running replaces only the marked block, so regeneration is idempotent. If you manually tune a generated state and want to preserve the tuning, either stop regenerating that state or move/remove the generator markers around your hand-authored data.

## How current demographics are resolved

The generator reads the current checkout rather than hardcoding a stale snapshot. It resolves:

- starting state owner / manpower / state category from `history/states/*.txt`;
- national ideological shares from `history/countries/*.txt` `set_popularities`;
- current LoK `species`, `minority`, and `state_cultures` startup assignments from `common/on_actions/*.txt`;
- LoK's `is_non_playable_country` tags from `common/scripted_triggers/*.txt`.

If a playable-owned state is missing explicit species/culture data, the generator falls back to that owner's population-weighted modal species/culture and places a `GENERATOR WARNING` comment in the state block and in the report. It does not pretend to evaluate arbitrary conditional PDX triggers.

## Fuzz rules

The generator deliberately makes states editable rather than mechanically identical.

- Majority/minority species: majority is randomly 60-80%, minority gets the remainder.
- Two cultures: first culture is randomly 40-60%, second gets the remainder.
- No minority / one culture: that dimension is 100% one value.
- Politics: each state gets 1-3 ideologies, normally 2. Large urban states are more likely to get 3.
- Large urban states are biased toward Social Democrat `[2]`, Social Liberal `[3]`, and Market Liberal `[4]` when those tendencies exist nationally.
- A country-level balancing pass tries to keep the population-weighted sum of its generated states close to the country's existing `set_popularities`.

Species, culture, and politics are crossed to create the concrete population groups. Amounts are rounded to 0.001k (one person), with the rounding remainder corrected so each state's generated groups sum to the vanilla state manpower.

## Runtime initialization is now small

`common/on_actions/LOK_pop_groups_on_actions.txt` does not generate populations. At startup it only calls `LOK_rebuild_pop_caches` on states that already contain static groups.

That rebuild calculates:

- `lok_pop_total_k`
- `lok_pop_group_count`
- `lok_state_species_total_ids_array`
- `lok_state_species_total_amount_array`
- `lok_state_culture_total_ids_array`
- `lok_state_culture_total_amount_array`
- `lok_state_parties_array` - raw population totals for politics indices 0-9

Then it calls `LOK_rebuild_state_political_pie = yes`, so the existing state political pie chart and Dominant Ideologies map mode are projections of the actual pop groups.

The old `LOK_DEBUG_state_political_pie_chart.txt` is included as an empty replacement because its randomizer would otherwise overwrite real pop-derived politics.

## Six-month merge

`LOK_pop_groups.1` runs every 180 days and merges duplicate five-field population groups. This is runtime maintenance only; it does not construct starting demographics.

## Reports

Every generator run writes `_LOK_pop_generation_reports/` containing:

- `country_politics.csv` - target national popularity versus generated population-weighted result;
- `states.csv` - one row per generated state with its resolved demographics, politics, group count, and warnings;
- `warnings.txt` - unsupported/missing source-data warnings.

These are meant to make hand-tuning the first pass easy.

## Windows in-place note

`RUN_GENERATOR_IN_PLACE.bat` runs the generator with `--no-support-files`. The support files are already present because this package is extracted into the mod root, so copying them again is unnecessary. The generator also independently detects source == destination and skips such copies. This avoids Windows `PermissionError: [WinError 32]` / same-file errors.

## Herzlands selector support

The generator resolves simple static scripted country selectors used by startup demographics.
In particular, the current repo assigns Katzen species to the Herzlands warlords through:

```txt
every_country = {
    limit = { is_herzlands_warlord = yes }
    every_owned_state = { set_variable = { species = 1 } }
}
```

`is_herzlands_warlord` itself references `is_releasable_herzlands_warlord`. The generator now
expands static `tag = TAG`, `OR = { ... }`, and positive scripted-trigger references recursively.
The old generator ignored this `every_country` block, which caused Herzlands states to have no
resolved species and therefore no generated pop groups.

## Generator formatting / startup-parser notes

The generator inserts its block at the same indentation level as the other entries inside each state's `history = { ... }` block. It derives that indentation from the file instead of hardcoding it.

The startup-demographic parser also understands the current simple conditional state assignment used by FOD/Loris (`NOT = { check_variable = { species = 1 } }`), so the Katzen-minority setup is carried into generated state history instead of producing an unsupported-condition warning.

Warnings about omitted political tendencies are informational: with a hard cap of 1-3 ideologies per state, a one-state country physically cannot represent more than three nonzero national tendencies. The generator keeps the largest tendencies and now reports the omitted ideology names and their combined national share.

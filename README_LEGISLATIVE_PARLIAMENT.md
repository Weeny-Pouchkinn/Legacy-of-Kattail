# Legislative Body + Parliamentary Actions update

Target: Legacy of Kattail `global-rework-2`.

## Installation

Copy this archive's contents into the mod root, replacing the three existing files when asked:

- `common/scripted_effects/LOK_parliament_effects.txt`
- `common/scripted_guis/LOK_parliament_gui.txt`
- `common/on_actions/LOK_parliament_on_actions.txt`
- `interface/lok_system_parliament.gui`

Everything else is additive.

Then run **once** from the mod root:

```text
python tools/apply_legislative_body_history.py
```

That script is intentionally source-only, not an installer. It edits the current checkout's own `common/idea_tags/00_idea.txt` and `history/countries/*.txt`, so it does not overwrite country-history content with stale copies.

## Legislative Body assignment

The history patch follows the requested rules:

- `ROQ` -> Direct Democracy
- `MCF` -> Parliament, regardless of ideology
- authoritarian_democratic / neutrality / fascism -> Upper Council
- every other starting ruling ideology -> Parliament

The result is written directly into each history file as e.g.:

```txt
# Legislative Body Type
add_ideas = lok_legislative_parliament
```

It also adds `lok_legislative_body` as a fifth slot in the existing `government` idea category beside mobilization/economy/trade/economy.

## Election cadence

- Parliament: 104 weeks
- Upper Council: no scheduled elections
- Direct Democracy: 4 weeks

This uses a four-week gameplay month because the requested GUI timer is explicitly week-based. Scheduled elections reset the timer. Snap elections (Dissolve Assembly and Re-Incorporate Party) deliberately do not.

On election, every legal party receives seats proportional to current party popularity after banned parties are removed and the remainder is renormalized to 100%. All bankrolls are cancelled before the new shares are applied.

## Party management

Click **Manage Party** on a row to switch the top-right panel from global actions to that party. Clicking the same row again returns to global actions.

### Political Concessions
- Base PP cost = seat share in percentage points (10.5% seats -> 10.5 PP)
- multiplied by `1 + modifier@lok_sway_party_cost`
- doubled in Direct Democracy
- +5 percentage points current Opinion
- four-week per-party cooldown

### Bankroll Party
- toggle
- +5 percentage points target Opinion while active
- FC usage = 0.1 per percentage point of seats (100% -> 10 FC)
- Upper Council pays half
- unavailable in Direct Democracy
- all bankrolls cancelled by any election

### Exclude Party
- unavailable in Direct Democracy
- ruling party cannot be excluded
- PP cost = 5 per percentage point of seats (10.5% -> 52.5 PP)
- stability loss = one percentage point per percentage point of seats (10.5% -> -10.5% stability)
- current seats are proportionally redistributed across the remaining legal parties

### Re-Incorporate Party
- restores status 1 (neutral/legal)
- calls a snap election
- unavailable in Direct Democracy
- does not reset scheduled timer

## Global actions

### Dissolve the Assembly
Parliament only. Calls a snap election without resetting the 104-week timer.

### Exercise Emergency Powers
Sets `lok_has_emergency_powers`. All nine parties immediately lose 5 percentage points of current Opinion. No parliamentary-approval bypass is implemented yet, per request.

## Fiscal capacity integration

`lok_parliament_bankroll_dynamic_modifier` feeds `lok_parliament_bankroll_fiscal_usage` into the existing custom modifier `lok_fiscal_capacity_usage`, then invokes the existing `LOK_update_fiscal_capacity` effect.

## Important implementation note

The existing parliament data model is preserved:
- party indices 0..8
- `pol_party_array = 3` means excluded/hostile
- party popularity is mirrored to `lok_parliament_party_share_real_array`
- `lok_parliament_party_share_array` remains the seat distribution
- approval / target / government approval arrays are unchanged

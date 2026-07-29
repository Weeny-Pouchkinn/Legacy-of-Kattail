# Signed-Axis Great Game System

## Public API and ownership

The Great Game is a reusable diplomatic contest over every state owned by a host country. Each country may belong to only one live game. The host owns the live participant/state arrays and round clock; each participant owns its role, alignment, multiplier, action allowance, UI mirror values, country-scope references, and decision target-state array.

Country references are stored as scope-valued variables:

- `lok_gg_host_ref`
- `lok_gg_beneficiary_ref`
- `lok_gg_positive_side_ref`
- `lok_gg_negative_side_ref`

They are entered with `var:lok_gg_host_ref = { ... }` and displayed with forms such as `[?lok_gg_host_ref.GetNameDef]`. The decision category reads only participant-local UI mirrors, avoiding unsupported chained numeric localisation such as `FROM.owner.variable`.

Call `lok_begin_great_game_configuration = yes` in the prospective host scope, configure the host and each foreign country, append every foreign country scope to the host's `lok_gg_setup_participants`, then call `lok_start_great_game = yes` in host scope. Do not add the host to the setup array. Failed validation retains staging and sets `lok_gg_setup_invalid`; no live country or state data is written.

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	set_variable = { lok_gg_setup_round_limit = 20 }
	set_variable = { lok_gg_setup_host_multiplier = 1 }
	set_variable = { lok_gg_setup_host_actions = 1 }
	PRL = {
		set_country_flag = lok_gg_setup_main_claimant
		set_variable = { lok_gg_setup_alignment = 1 }
		set_variable = { lok_gg_setup_multiplier = 1 }
		set_variable = { lok_gg_setup_actions = 1 }
	}
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	lok_start_great_game = yes
}
```

Use `lok_abort_great_game = yes` from the host or any live participant to cancel without settlement.

## Configuration

Host setup:

- `lok_gg_setup_round_limit` (default 20, maximum 200)
- `lok_gg_setup_host_multiplier` (default 1)
- `lok_gg_setup_host_actions` (default 1, maximum 20)
- `lok_gg_setup_doomed` flag
- `lok_gg_setup_participants` array (maximum 50)

Foreign participant setup:

- `lok_gg_setup_alignment`: `1` supports the positive claimant, `-1` supports the negative claimant, `0` supports the host
- `lok_gg_setup_multiplier` (default 1, not negative)
- `lok_gg_setup_actions` (default 1, integer allowance from 0 through 20)
- `lok_gg_setup_main_claimant`: with alignment `1`, the positive principal; with `-1`, the optional negative principal

Exactly one positive principal and at most one negative principal are required. A negative supporter requires a negative principal. Doomed games require both principals. Host/participants must exist, own eligible host states where applicable, be unique, and not already have `lok_gg_in_game`.

## Rounds, decisions, and influence

Rounds last ten days. The host alone receives the scheduled daily event; it decrements the clock and mirrors round data to participants. AI countries spend their local actions at each round opening. At a boundary, spill and isolation resolve and either the next round starts or settlement occurs.

`lok_great_game_influence_state` targets the participant's local `lok_gg_target_states`. A direct action rolls 5, 10, 15, 20, or 25 with equal probability. Principal claimants may gain up to +6 cohesion from adjacent same-side footholds and an external border. The sum is multiplied by the actor multiplier and rounded. Positive actors add, negative actors subtract, and host-aligned actors move influence toward zero without crossing it. Influence clamps to -100 through +100; one-sided games also clamp at zero.

A foothold begins at +30 or -30. Passive spill is snapshotted for every state before any influence changes: adjacent footholds contribute strength 1/2/3 at absolute influence 30–49/50–74/75–100, with bonuses for multiple sources, complete surrounding, and a principal-country border. Each sign is capped at 8 and opposing spill is netted. After spill, unsupported positive or negative influence decays one point toward zero, or two points for a foothold. A same-side direct action during the current round suppresses isolation; host-aligned actions do not.

## Settlement and cleanup

Normal settlement gives a state to the positive principal only above +50 and to the negative principal only below -50. Exact +50, -50, and all intermediate values remain with the host.

Doomed settlement assigns every state by sign. A zero state uses, in order, adjacent foothold count, external principal border, then a 50/50 random choice. All winners and compliance values are snapshotted before transfers. Non-capitals transfer before the former host capital. Compliance is absolute final influence clamped to 0–100, with a minimum of 10 in doomed mode. Cores and resistance are not edited.

If settlement leaves the host landless, the recipient of the former capital annexes it with troop transfer after all state distribution. This is intended to clean up units and country relations without changing the already completed multi-recipient state split; it requires in-game verification against the supported engine build.

Cleanup is idempotent and clears all Great Game flags, variables, arrays, state markers, and staged metadata. Active validation aborts on loss of the positive principal or host eligibility, removes states no longer held by the host, and converts a non-doomed contest to one-sided if its negative principal disappears.

Performance is bounded by the configured participants and the host's starting states. There is one daily event per active host, no daily global country scan, and spill/resolution iterate only host-owned arrays.

## Configuration examples

### 1. One-sided normal game

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	PRL = {
		set_country_flag = lok_gg_setup_main_claimant
		set_variable = { lok_gg_setup_alignment = 1 }
	}
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	lok_start_great_game = yes
}
```

### 2. Two-sided normal game

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	MEW = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = -1 } }
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	add_to_array = { array = lok_gg_setup_participants value = MEW }
	lok_start_great_game = yes
}
```

### 3. PRL with MEO, LIO, and CAT against MEW over WPR

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	MEW = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = -1 } }
	MEO = { clr_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	LIO = { clr_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	CAT = { clr_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	add_to_array = { array = lok_gg_setup_participants value = MEW }
	add_to_array = { array = lok_gg_setup_participants value = MEO }
	add_to_array = { array = lok_gg_setup_participants value = LIO }
	add_to_array = { array = lok_gg_setup_participants value = CAT }
	lok_start_great_game = yes
}
```

### 4. MEW with four actions

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	MEW = {
		set_country_flag = lok_gg_setup_main_claimant
		set_variable = { lok_gg_setup_alignment = -1 }
		set_variable = { lok_gg_setup_actions = 4 }
	}
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	add_to_array = { array = lok_gg_setup_participants value = MEW }
	lok_start_great_game = yes
}
```

### 5. Non-default multipliers

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	set_variable = { lok_gg_setup_host_multiplier = 0.75 }
	PRL = {
		set_country_flag = lok_gg_setup_main_claimant
		set_variable = { lok_gg_setup_alignment = 1 }
		set_variable = { lok_gg_setup_multiplier = 1.25 }
	}
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	lok_start_great_game = yes
}
```

### 6. Host supporter

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	MEO = {
		clr_country_flag = lok_gg_setup_main_claimant
		set_variable = { lok_gg_setup_alignment = 0 }
	}
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	add_to_array = { array = lok_gg_setup_participants value = MEO }
	lok_start_great_game = yes
}
```

### 7. Thirty-round game

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	set_variable = { lok_gg_setup_round_limit = 30 }
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	lok_start_great_game = yes
}
```

### 8. Doomed game

```hoi4
WPR = {
	lok_begin_great_game_configuration = yes
	set_country_flag = lok_gg_setup_doomed
	PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
	MEW = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = -1 } }
	add_to_array = { array = lok_gg_setup_participants value = PRL }
	add_to_array = { array = lok_gg_setup_participants value = MEW }
	lok_start_great_game = yes
}
```

### 9. Starting from an event

```hoi4
immediate = {
	hidden_effect = {
		WPR = {
			lok_begin_great_game_configuration = yes
			PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
			add_to_array = { array = lok_gg_setup_participants value = PRL }
			lok_start_great_game = yes
		}
	}
}
```

### 10. Starting from a focus reward

```hoi4
completion_reward = {
	WPR = {
		lok_begin_great_game_configuration = yes
		PRL = { set_country_flag = lok_gg_setup_main_claimant set_variable = { lok_gg_setup_alignment = 1 } }
		add_to_array = { array = lok_gg_setup_participants value = PRL }
		lok_start_great_game = yes
	}
}
```

The debug console event `event lok_debug.22` starts the two-sided default PRL–MEW contest over WPR through this same public API.

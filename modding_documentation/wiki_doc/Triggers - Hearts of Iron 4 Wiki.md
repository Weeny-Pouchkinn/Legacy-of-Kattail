This is a community maintained wiki. If you spot a mistake, please help with fixing it.

**Conditions** (also known as **Triggers**) are used to check whether certain conditions are fulfilled in the game's current state or not, without being able to change anything in the game's state.<sup id="ref_a"><a href="https://hoi4.paradoxwikis.com/Triggers#cnote_a">[a]</a></sup> These return a [boolean](http://en.wikipedia.org/wiki/Boolean_data_type "wp:Boolean data type") (true or false), which may be interpreted by the block where it's used. Usually blocks that allow using triggers are an [AND](https://hoi4.paradoxwikis.com/Triggers#AND) unless stated otherwise, which would instantly stop execution upon receiving a single false statement and return false. Please note that the `yes` and `no` inputs are case-sensitive and must not contain any uppercase letters.

The list of triggers may be outdated. A complete, but unsorted, list of triggers can be found in /Hearts of Iron IV/documentation/triggers\_documentation.html or /Hearts of Iron IV/documentation/triggers\_documentation.md. As of 1.17.1.1, this file was last updated in the version 1.17.0.

## Operators\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=1 "Edit section: Operators") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=1 "Edit section: Operators")\]

Every trigger uses one of the three operators: The equality sign `=` or the comparison signs `>` and `<`.

The equality sign can either mean strict equality (Unlike previous games in the series where it checked for being equal or greater than) or can serve as a way to introduce a block of additional triggers, as in `has_opinion = { target = GRE value < -10 }`. The comparison signs serves as strict comparison: `has_political_power > 100` will not be true if the country has exactly 100 political power, for instance.

Not all triggers support the equality sign or comparison signs. See the details for each trigger in the notes for it. If not stated otherwise, the trigger only supports the equality sign.

## Context scopes\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=2 "Edit section: Context scopes") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=2 "Edit section: Context scopes")\]

There are three general scopes all triggers operate in:

-   country
-   state
-   character

They give context to a trigger by stating what the trigger is checking against.

Each country acts as a sub-scope of the general country scope, i.e. `GER = { }` will check only against Germany, whereas `any_country` will check against all countries. Likewise for states and characters.

Triggers won't work in scopes they are not assigned to. Country triggers will not work for states or vice-versa.

## Scopes\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=3 "Edit section: Scopes") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=3 "Edit section: Scopes")\]

These don't serve as triggers, but rather as scopes that change for whom the triggers are being checked. Each one also serves as an [AND statement](https://hoi4.paradoxwikis.com/Triggers#AND).

### Trigger scopes\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=4 "Edit section: Trigger scopes") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=4 "Edit section: Trigger scopes")\]

These can only be used as triggers; trying to use them as [effects](https://hoi4.paradoxwikis.com/Effects "Effects") will result in nothing happening.

Trigger scopes:  
Collapse
| Name | Usage | Target type | Example | Description | Version Added |
| --- | --- | --- | --- | --- | --- |
| all\_country | Always usable | Country | `all_country = { … }` | Checks if all countries meet the triggers. | 1.0 |
| any\_country | Always usable | Country | `any_country = { … }` | Checks if any country meets the triggers. | 1.0 |
| all\_other\_country | Within country scope only | Country | `all_other_country = { … }` | Checks if all countries other than the one where this scope is located meet the triggers. | 1.0 |
| any\_other\_country | Within country scope only | Country | `any_other_country = { … }` | Checks if any country other than the one where this scope is located meets the triggers. | 1.0 |
| all\_country\_with\_original\_tag | Always usable | Country | 
```
all_country_with_original_tag = {
    original_tag_to_check = TAG  #required
    …                  #triggers to check
}
```

 | Checks if all countries originating from the specified country, including the dynamic countries created for civil wars and other purposes, meet the triggers. `original_tag_to_check = TAG` is used to specify the original tag. | 1.9 |
| any\_country\_with\_original\_tag | Always usable | Country | 

```
any_country_with_original_tag = {
    original_tag_to_check = TAG  #required
    …                  #triggers to check
}
```

 | Checks if any country originating from the specified country, including the dynamic countries created for civil wars and other purposes, meets the triggers. `original_tag_to_check = TAG` is used to specify the original tag. | 1.9 |
| all\_neighbor\_country | Within country scope only | Country | `all_neighbor_country = { … }` | Checks if all countries that border the one where this scope is located meet the triggers. | 1.0 |
| any\_neighbor\_country | Within country scope only | Country | `any_neighbor_country = { … }` | Checks if any country that borders the one where this scope is located meets the triggers. | 1.0 |
| any\_home\_area\_neighbor\_country | Within country scope only | Country | `any_home_area_neighbor_country = { … }` | Checks if any country that borders the one where this scope is located, as well as being in its home area - meaning a direct land connection between the capitals of countries - meets the triggers. | 1.0 |
| all\_guaranteed\_country | Within country scope only | Country | `all_guaranteed_country = { … }` | Checks if all countries that are guaranteed by the one where this scope is located meet the triggers. | 1.9 |
| any\_guaranteed\_country | Within country scope only | Country | `any_guaranteed_country = { … }` | Checks if any country that is guaranteed by the one where this scope is located meets the triggers. | 1.9 |
| all\_allied\_country | Within country scope only | Country | `all_allied_country = { … }` | Checks if all countries that are allied with the one where this scope is located - meaning that they are either a subject of the country, its overlord, or that they share a faction - meet the triggers. Does not include the country itself. | 1.9 |
| any\_allied\_country | Within country scope only | Country | `any_allied_country = { … }` | Checks if any country that is allied with the one where this scope is located - meaning that they are either a subject of the country, its overlord, or that they share a faction - meets the triggers. Does not include the country itself. | 1.9 |
| all\_occupied\_country | Within country scope only | Country | `all_occupied_country = { … }` | Checks if all countries that are occupied by the one where this scope is located - meaning that the occupied country has core states controlled by the occupier country - meet the triggers. | 1.9 |
| any\_occupied\_country | Within country scope only | Country | `any_occupied_country = { … }` | Checks if any country that is occupied by the one where this scope is located - meaning that the occupied country has core states controlled by the occupier country - meets the triggers. | 1.9 |
| all\_enemy\_country | Within country scope only | Country | `all_enemy_country = { … }` | Checks if all countries that are at war with the one where this scope is located meet the triggers. | 1.9 |
| any\_enemy\_country | Within country scope only | Country | `any_enemy_country = { … }` | Checks if any country that are at war with the one where this scope is located meets the triggers. | 1.9 |
| all\_subject\_countries | Within country scope only | Country | `all_subject_countries = { … }` | Checks if all countries that are a subject of the one where this scope is located meet the triggers. Notice the plural spelling in the scope. | 1.11 |
| any\_subject\_country | Within country scope only | Country | `any_subject_country = { … }` | Checks if any country that is a subject of the one where this scope is located meets the triggers. | 1.11 |
| any\_country\_with\_core | Within state scope only | Country | `any_country_with_core = { … }` | Checks if any country that has the current scope as a core state meets the triggers. **Does not have an equivalent for other effect/trigger scope types.** | 1.12 |
| all\_country\_of | Alway usable | Country | 

```
all_country_of = {
tooltip = my_loc # Optional bindable localization
target = { SWE NOR FIN DEN ICE }
has_defensive_war = yes
}

all_country_of = {
    tooltip = my_loc # Optional bindable localization
target = constant:country_groups:nordics
has_defensive_war = yes
}

```

 | Checks if all of the provided countries fulfill the specified triggers. The \`target\` supports script constants and \`tooltip\` supports bindable localization. | 1.17 |
| any\_country\_of | Alway usable | Country | 

```
any_country_of = {
tooltip = my_loc # Optional bindable localization
target = { SWE NOR FIN DEN ICE }
has_defensive_war = yes
}

any_country_of = {
    tooltip = my_loc # Optional bindable localization
target = constant:country_groups:nordics
has_defensive_war = yes
}

```

 | Checks if any of the provided countries fulfills the specified triggers. The \`target\` supports script constants and \`tooltip\` supports bindable localization. | 1.17 |
| all\_state | Always usable | State | `all_state = { … }` | Check if all states meet the triggers. | 1.0 |
| any\_state | Always usable | State | `any_state = { … }` | Check if any state meets the triggers. | 1.0 |
| any\_state\_in | Always usable | State | 

```
any_state_in = {
  array = array_of_states  #required 
    …                  #triggers to check
}
```

Requires on of the following fields

```
array = <array_of_states>
continent = <continent_name>
ai_area = <ai_area_name>
strategic_region = <strategic_region_number>
```

 | Check if any state in the given category meets the trigger. | 1.15 |
| any\_state\_of | Alway usable | State | 

```
any_state_of = {
tooltip = my_loc # Optional bindable localization
target = { 1 42 1992 }
controller = {
has_defensive_war = yes
}
}

any_state_of = {
    tooltip = my_loc # Optional bindable localization
target = constant:country_groups:nordics
controller = {
has_defensive_war = yes
}
}

```

 | Checks if any of the provided states fulfills the specified triggers. The \`target\` supports script constants and \`tooltip\` supports bindable localization. | 1.17 |
| all\_neighbor\_state | Within state scope only | State | `all_neighbor_state = { … }` | Check if all states that are neighbour to the one where this scope is located meet the triggers. | 1.0 |
| any\_neighbor\_state | Within state scope only | State | `any_neighbor_state = { … }` | Check if any state that is neighbour to the one where this scope is located meets the triggers. | 1.0 |
| all\_owned\_state | Within country scope only | State | `all_owned_state = { … }` | Check if all states that are owned by the country where this scope is located meet the triggers. | 1.0 |
| any\_owned\_state | Within country scope only | State | `any_owned_state = { … }` | Check if any state that is owned by the country where this scope is located meets the triggers. | 1.0 |
| all\_core\_state | Within country scope only | State | `all_core_state = { … }` | Check if any state that is cored by the country where this scope is located meets the triggers. | 1.11 |
| any\_core\_state | Within country scope only | State | `any_core_state = { … }` | Check if all states that are cored by the country where this scope is located meet the triggers. | 1.11 |
| all\_controlled\_state | Within country scope only | State | `all_controlled_state = { … }` | Check if all states that are controlled by the country where this scope is located meet the triggers. | 1.9 |
| any\_controlled\_state | Within country scope only | State | `any_controlled_state = { … }` | Check if any state that is controlled by the country where this scope is located meets the triggers. | 1.9 |
| all\_unit\_leader | Within country scope only | Unit Leader | `all_unit_leader = { … }` | Checks if all unit leaders (corps commanders, field marshals, admirals) that are employed by the country where this scope is located meet the triggers. | 1.5 |
| any\_unit\_leader | Within country scope only | Unit Leader | `any_unit_leader = { … }` | Checks if any unit leader (corps commander, field marshal, admiral) that is employed by the country where this scope is located meets the triggers. | 1.5 |
| all\_army\_leader | Within country scope only | Unit Leader | `all_army_leader = { … }` | Checks if all army leaders that are employed by the country where this scope is located meet the triggers. | 1.5 |
| any\_army\_leader | Within country scope only | Unit Leader | `any_army_leader = { … }` | Checks if any army leader that is employed by the country where this scope is located meets the triggers. | 1.5 |
| all\_navy\_leader | Within country scope only | Unit Leader | `all_navy_leader = { … }` | Checks if all navy leaders that are employed by the country where this scope is located meet the triggers. | 1.5 |
| any\_navy\_leader | Within country scope only | Unit Leader | `any_navy_leader = { … }` | Checks if any navy leader that is employed by the country where this scope is located meets the triggers. | 1.5 |
| all\_operative\_leader | Within country scope or operations only | Operative | `all_operative_leader = { … }` | Checks if all operatives that are employed by the country where this scope is located meet the triggers. | 1.9 |
| any\_operative\_leader | Within country scope or operations only | Operative | `any_operative_leader = { … }` | Checks if any operative that is employed by the country where this scope is located meets the triggers. | 1.9 |
| all\_character | Within country scope only | Character | `all_character = { … }` | Checks if all characters that are recruited by the country where this scope is located meet the triggers. | 1.11 |
| any\_character | Within country scope only | Character | `any_character = { … }` | Checks if any character that is recruited by the country where this scope is located meets the triggers. | 1.11 |
| any\_country\_division | Within country scope only | Division | `any_country_division = { … }` | Checks if any division owned by the current country meets the triggers. | 1.12 |
| any\_state\_division | Within state scope only | Division | `any_state_division = { … }` | Checks if any division within the current state meets the triggers. | 1.12 |
| all\_military\_industrial\_organization | Within country scope only | MIO | `all_military_industrial_organization = { … }` | Checks if all MIOs within the current country meet the conditions. | 1.13 |
| any\_military\_industrial\_organization | Within country scope only | MIO | `any_military_industrial_organization = { … }` | Checks if any MIO within the current country meets the conditions. | 1.13 |
| all\_purchase\_contract | Within country scope only | Purchase contract | `all_purchase_contract = { … }` | Checks if all purchase contracts within the current country meet the conditions. | 1.13 |
| any\_purchase\_contract | Within country scope only | Purchase contract | `any_purchase_contract = { … }` | Checks if any purchase contract within the current country meets the conditions. | 1.13 |
| all\_scientists | Within country scope only | Character | `all_scientistst = { … }` | Checks if all scientists of the Country in scope matches the triggers. | 1.15 |
| any\_scientist | Within country scope only | Character | `any_scientist = { … }` | Checks if at least one active scientist of the Country in scope matches the triggers. | 1.15 |
| all\_active\_scientist | Within country scope only | Character | `all_active_scientist = { … }` | Checks if all active scientists of the Country in scope matches the triggers. | 1.15 |
| any\_active\_scientist | Within country scope only | Character | `any_active_scientist = { … }` | Checks if at least one active scientist of the Country in scope matches the triggers. | 1.15 |

### Dual scopes\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=5 "Edit section: Dual scopes") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=5 "Edit section: Dual scopes")\]

The following scopes can be used either as effect or trigger scopes; some can also be used as the right side of some effects and triggers as a target. If usage as a target is possible, it's marked within the table.

Several dual scopes may have a scope that varies depending on where it's used, such as variables, which can be set to anything.

Dual scopes:  
Collapse
| Name | Usage | Target type | Example | Description | Usable as target | Version Added |
| --- | --- | --- | --- | --- | --- | --- |
| TAG | Always usable | Country scope | `SOV = { country_event = my_event.1 }` | The country defined by the tag or tag alias. Tag aliases are defined in /Hearts of Iron IV/common/country\_tag\_aliases, as a way to refer to a specific country (such as a side in a civil war) in addition to its actual tag. If the country with the exact tag doesn't exist, but a dynamic country originating from the specified tag does, the scope will refer to the dynamic country. | ✓ | 1.0 |
| <state\_id> | Always usable | State scope | `123 = { transfer_state_to = SCO }` | The state defined by this id. | ✓ | 1.0 |
| <character> | not within Character scope | Character scope | `ENG_theodore_makhno = { set_nationality = UKR }` | On game versions prior to 1.12.8, the character must be already recruited by the country this is scoped from. | ✓ | 1.11 |
| mio:<MIO> | Within country scope only | MIO scope | `mio:AST_cockatoo_doe_organization = { … }` | The MIO identified by that ID as defined within the /Hearts of Iron IV/common/military\_industrial\_organization/organizations/\*.txt file. | ✓ | 1.13 |
| sp:<special\_project> | Within country scope only | Special project scope | `sp:sp_land_flamethrower_tank = { … }` | The special project identified by that ID as defined within the /Hearts of Iron IV/common/special\_projects/projects/\*.txt file. | ✓ | 1.15 |
| ROOT | Always usable | Depends on usage | 
```
ENG = {
    FRA = {
        GER = {
            declare_war_on = {
                target = ROOT
                type = annex_everything
            }
        }
    }
} #GER declares war on ENG (if there is no scope before ENG)

```

 | Targets the root node of the block, an inherent property of each block. Most commonly, this is the default scope: for example, ROOT [within a national focus](https://hoi4.paradoxwikis.com/National_focus_modding "National focus modding") will always refer to the country doing the focus and ROOT [within a event](https://hoi4.paradoxwikis.com/Event_modding "Event modding") will always refer to the country getting the event. However, some blocks do distinguish between the default scope and ROOT, such as [certain scripted GUI contexts](https://hoi4.paradoxwikis.com/Scripted_GUI_modding "Scripted GUI modding") or [certain on actions](https://hoi4.paradoxwikis.com/On_actions#La_R.C3.A9sistance "On actions"). If a block doesn't have ROOT defined (such as [on\_startup in on actions](https://hoi4.paradoxwikis.com/On_actions#on_startup "On actions")), then it is impossible to use it. | ✓ | 1.0 |
| THIS | Always usable | Depends on usage | 

```
set_temp_variable = { target_country = THIS }
```

 | Targets the current scope where it's used. For example, when used in [every\_state](https://hoi4.paradoxwikis.com/Triggers#every_state), it will refer to the state that's currently being evaluated. Primarily useful for [variables](https://hoi4.paradoxwikis.com/Variables "Variables") (as in the example, where omitting it wouldn't work) or for [built-in localisation commands](https://hoi4.paradoxwikis.com/Localisation#Namespaces "Localisation"), where some scope must be specified. More rarely, this may help with scope manipulation when using [PREV](https://hoi4.paradoxwikis.com/Triggers#PREV). Since omitting it makes no difference in how the code gets interpreted, there is little to no usage outside of these cases. | ✓ | 1.0 |
| PREV | Always usable | Depends on usage | 

```
FRA = {
    random_country = {
        GER = {
            declare_war_on = {
                target = PREV
                type = annex_everything
            }
        }
    }
} #Germany declares war on random_country

```

 | Targets the scope that the current scope is contained in. Can have additional applications where the assumed default scope differs from the ROOT, such as in state events or some on\_actions. Can be chained indefinitely as PREV.PREV. **Commonly results in broken-looking tooltips**: what's shown to the player doesn't always correlate with reality.

See also: [PREV usage](https://hoi4.paradoxwikis.com/Scopes#PREV_usage "Scopes").

 | ✓ | 1.0 |
| FROM | Always usable | Depends on usage | 

```
declare_war_on = {
    target = FROM
    type = annex_everything
}

FROM = {
    load_oob = defend_ourselves
}

```

 | Can be chained indefinitely as FROM.FROM. Used to target various hardcoded scopes inherent to the block, often a secondary scope in addition to ROOT. For example:

In [events](https://hoi4.paradoxwikis.com/Event_modding "Event modding"), this refers to the country that sent the event (i.e. if the event was fired [using an effect](https://hoi4.paradoxwikis.com/Event_modding#Effect "Event modding"), then it's the ROOT scope where it was fired).  
In [targeted decisions](https://hoi4.paradoxwikis.com/Decision_modding#targeted_decisions "Decision modding") or [diplomacy scripted triggers](https://hoi4.paradoxwikis.com/Conditions#Scripted_triggers "Conditions"), this refers to the scope that is targeted.  


 | ✓ | 1.0 |
| overlord | Within country scope only | Country scope | `overlord = { … }` | The overlord of the country if it is a subject. [Subject to the 'invalid event target' error.](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") | X | 1.3 |
| faction\_leader | Within country scope only | Country scope | `faction_leader = { add_to_faction = FROM }` | Faction leader of the faction the country is a part of. [Subject to the 'invalid event target' error.](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") | X | 1.10.1 |
| owner | Within state, character, or combatant scope only | Country scope | `owner = { add_ideas = owns_this_state }` | In state scope, the country that owns the state. In combatant scope, the country that owns the divisions. In character scope, the country that has recruited the character. [Subject to the 'invalid event target' error](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") when used for a state. | X | 1.0 |
| controller | Within state scope only | Country scope | 

```
controller = { 
    ROOT = {
        create_wargoal = {
            target = PREV
            type = take_state_focus
            generator = { 123 }
        }
    }
}
```

 | The controller of the current state. [Subject to the 'invalid event target' error.](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") | X | 1.0 |
| capital\_scope | Within country scope only | State scope | `capital_scope = { … }` | The state where the capital of the current country is located in. [Subject to the 'invalid event target' error](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") in rare cases. | X | 1.0 |
| event\_target:<event\_target\_key> | Always usable | Depends on usage | `event_target:my_event_target = { … }` | Saved [event target or global event target](https://hoi4.paradoxwikis.com/Data_structures#Event_targets "Data structures"), with no space after the colon. [Subject to the 'invalid event target' error.](https://hoi4.paradoxwikis.com/Scopes#Invalid_event_target "Scopes") | ✓ | 1.0 |
| var:<variable> | Always usable | Depends on usage | `var:my_variable = { … }`  
`add_to_faction = my_variable` or  
`add_to_faction = var:my_variable` | [Variable](https://hoi4.paradoxwikis.com/Variable "Variable") set to a scope.

When used as a target rather than a scope, the `var:` can be omitted in most cases.

 | ✓ | 1.5 |

## Flow control tools\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=6 "Edit section: Flow control tools") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=6 "Edit section: Flow control tools")\]

These are triggers that serve as more of a way to establish a connection in how triggers are evaluated. Each one serves as a trigger scope with additional arguments and can be used regardless of scope.

Flow control tools:  
Collapse
| Name | Additional parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| AND | None | 
```
AND = {
    original_tag = GER
    has_stability > 0.5
}
```

 | Returns false if any sub-trigger returns false, true otherwise. Evaluation stops at the first false sub-trigger. | Only necessary within [OR statements](https://hoi4.paradoxwikis.com/Triggers#OR) and [NOT statements](https://hoi4.paradoxwikis.com/Triggers#NOT), as everything else is implicitly AND. | 1.0 |
| OR | None | 

```
OR = {
    original_tag = ENG
    original_tag = USA
}
```

 | Returns true if any sub-trigger returns true, false otherwise. Evaluation stops at the first true sub-trigger. |  | 1.0 |
| NOT | None | 

```
NOT = {
    has_stability > 0.5
    has_war_support > 0.5
}
```

 | Returns false if any sub-trigger returns true, true otherwise. Evaluation stops at the first true sub-trigger. | Equivalent to a NOR rather than a NAND. | 1.0 |
| count\_triggers | `amount = <int>`  
The amount of triggers that need to be fulfilled. | 

```
count_triggers = {
    amount = 2
    10 = { state_population = 100000 }
    11 = { state_population = 100000 }
    12 = { state_population = 100000 }
}
```

 | Sums the results of all sub-triggers (false=0, true=1) and returns true if the sum is at least `amount`. |  | 1.5 |
| if | `limit = <trigger block>`

`else_if = <if-trigger>`  
Alternative condition. Optional.  
`else = <AND-trigger>`  
Final alternative condition. Optional.

 | 

```
if = {
    limit = {
        has_dlc = "Poland: United and Ready"
    }
    has_political_power > 100
}
else_if = {
    limit = {
        has_dlc = "Waking the Tiger"
    }
    has_war_support > 0.5
}
else = {
    always = no
}

```

 | If `limit` is true, the sub-triggers are evaluated like an AND-trigger. If `limit` is false, `else_if` blocks are tried in sequence and finally `else` (if present). _Otherwise true is returned_. | Both nested (As in inside of `if = { ... }`) and unnested (As in the example) `else` and `else_if` exist. In case of overlap, unnested is preferred.

Can be useful for tooltip management: same as in effects, if the limit is unmet, nothing appears. If it is met, then the limit is hidden while the condition outside of the limit appears in the tooltip.

`if = { limit = { trigger_1 = yes } trigger_2 = yes }` is equivalent to `OR = { NOT = { trigger_1 = yes } trigger_2 = yes }`, but generates a different tooltip.

 | 1.0 |
| hidden\_trigger | None | 

```
hidden_trigger = {
    country_exists = GER
}
```

 | Hides the triggers from the tooltip shown to the player. | Also serves as an [AND statement](https://hoi4.paradoxwikis.com/Triggers#AND). | 1.0 |
| custom\_trigger\_tooltip | `tooltip = <string>`  
The localisation key to use. | 

```
custom_trigger_tooltip = {
    tooltip = sunrise_invasion_tt
    any_state = {
        is_owned_by = JAP
        is_on_continent = europe
        is_coastal = yes
    }
}
```

 | Hides the triggers from the tooltip shown to the player and instead uses the specified localisation key. | Alias for [#custom\_override\_tooltip](https://hoi4.paradoxwikis.com/Triggers#custom_override_tooltip) trigger (see that trigger for more info). Kept for backward compatibility. Prefer [#custom\_override\_tooltip](https://hoi4.paradoxwikis.com/Triggers#custom_override_tooltip) instead.

Also supports [Localisation#Bindable\_localisation](https://hoi4.paradoxwikis.com/Localisation#Bindable_localisation "Localisation").

 | 1.0 |
| custom\_override\_tooltip | `tooltip = <string>`  
The localisation key to use.

`not_tooltip = <string>`  
The localisation key to use for NOT block. Optional.

 | 

```
custom_override_tooltip = {
    tooltip = {
      localization_key = GER_inner_circle_focus_in_progress_tt
  CHARACTER = GER_rudolf_hess
  FLAG_DAYS = [?GER_rally_the_industrialists_in_progress_flag:days]
    }
    not_tooltip = MY_TOOLTIP_NOT
    <triggers>
}
```

 | An [AND](https://hoi4.paradoxwikis.com/Triggers#AND) trigger that has an overriden custom tooltip. | A positive tooltip can be set with `tooltip` and the tooltip to be used inside a [NOT](https://hoi4.paradoxwikis.com/Triggers#NOT) can be set with `not_tooltip`. If no positive tooltip is provided and the root key is a localization key (not a formatter, see formatted localization), then a negative tooltip will be generated by appending `_NOT` to the root localization for the positive tooltip. Both `tooltip` and `not_tooltip` are bindable localizations.

[Can also be used as effect.](https://hoi4.paradoxwikis.com/Effects#custom_override_tooltip "Effects")  
Also supports [Localisation#Bindable\_localisation](https://hoi4.paradoxwikis.com/Localisation#Bindable_localisation "Localisation").

 | 1.15 |

## Any scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=7 "Edit section: Any scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=7 "Edit section: Any scope")\]

These triggers do not require any particular scope.

### General\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=8 "Edit section: General") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=8 "Edit section: General")\]

General any-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| always | `<bool>`  
Boolean. | 
```
always = yes
```

 | Always returns true or false. Useful for debugging. |  | 1.0 |
| has\_global\_flag | `<string>`  
The flag to check. | 

```
has_global_flag = my_flag
```

 | Checks if the specified flag has been set. |  | 1.0 |
| has\_global\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_global_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.0 |
| has\_dlc | `<string>`  
The DLC name to check for. | 

```
has_dlc = "Waking the Tiger"
```

 | Checks if the specified DLC is enabled. |  | 1.0 |
| has\_start\_date | `<date>`  
The date to check for. | 

```
has_start_date > 1950.01.01
```

 | Checks if the specified date was the start date used for the current game. | Year.Month.Day

Must use either > or < operators.

 | 1.0 |
| date | `<date>`  
The date to check for. | 

```
date < 1950.01.01
```

 | Checks if the specified date against the current date. | Year.Month.Day

Must use either > or < operators.

 | 1.0 |
| difficulty | `<int>`  
The difficulty value. | 

```
difficulty > 0
```

 | checks if the specified difficulty against the current difficulty. | Must use either > or < operators. | 1.0 |
| has\_any\_custom\_difficulty\_setting | `<bool>`  
Boolean. | 

```
has_any_custom_difficulty_setting = yes
```

 | Checks if any custom difficulty setting is changed from their default value. | Custom difficulty in this case refers to /Hearts of Iron IV/common/difficulty\_settings/\*.txt, used in base game to strengthen a specific country. | 1.0 |
| has\_custom\_difficulty\_setting | `<string>`  
The setting to check. | 

```
has_custom_difficulty_setting = custom_diff_strong_sov
```

 | Checks if the specified custom difficulty setting is changed from the default value. | Custom difficulty in this case refers to /Hearts of Iron IV/common/difficulty\_settings/\*.txt, used in base game to strengthen a specific country. | 1.0 |
| game\_rules\_allow\_achievements | `<bool>`  
Boolean. | 

```
game_rules_allow_achievements = yes
```

 | Checks if all of the active game rule options allow achievements. |  | 1.9 |
| country\_exists | `<scope> / <variable>`  
The country to check. | 

```
country_exists = GER
```

 | Checks if the specified country currently exists in game. |  | 1.0 |
| is\_ironman | `<bool>`  
Boolean. | 

```
is_ironman = yes
```

 | Checks if the current game is running in Ironman mode. |  | 1.0 |
| is\_historical\_focus\_on | `<bool>`  
Boolean. | 

```
is_historical_focus_on = yes
```

 | Checks if the current game is running with Historical Focuses on. |  | 1.0 |
| is\_tutorial | `<bool>`  
Boolean. | 

```
is_tutorial = yes
```

 | Checks if the current game is running in Tutorial mode. |  | 1.0 |
| is\_debug | `<bool>`  
Boolean. | 

```
is_debug = yes
```

 | Checks if game is in debug mode (launched with -debug argument). |  | 1.9 |
| threat | `<float>`  
The amount to check for. | 

```
threat > 0.5
```

 | Checks if World Tension is above the specified amount. | Must use either > or < operators. | 1.0 |
| has\_game\_rule | `<string>`  
The game rule to check for.

`<string> / <bool>`  
The option to check.  


 | 

```
has_game_rule = { rule = GER_can_remilitarize_rhineland option = yes }
```

 | Checks if a game rule is set to a particular option. |  | 1.5 |
| has\_completed\_custom\_achievement | `mod = <mod ID>`  
The mod where the achievement is from.

`achievement = <achievement ID>`  
The name of the achievement.

 | 

```
has_completed_custom_achievement = {
    mod = my_mod_unique_id
    achievement = my_achievement_token
}
```

 | Checks if the player controlling the current scope has completed the specified custom achievement. | The achievement (including the ID of the mod it's from) is defined within /Hearts of Iron IV/common/achievements/\*.txt files<sup id="cite_ref-1"><a href="https://hoi4.paradoxwikis.com/Triggers#cite_note-1">[1]</a></sup>. The achievement could be completed during a previous session, not necessarily the current one.

If the mod defining the achievement is not loaded, the trigger evaluates as false.

 | 1.12.5 |

### Career profile\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=9 "Edit section: Career profile") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=9 "Edit section: Career profile")\]

Career profile-releated any-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| career\_profile\_check\_medal | `medal = <medal>`  
Medal to check.
`???`  


 | 

```
career_profile_check_medal = {
  medal = raining_debris_medal
  ???
}
```

 | Checks if the required medal is achieved and collected. | Provide no tooltip. | ??? |
| career\_profile\_check\_ribbon | `ribbon = <ribbon>`  
Ribbon to check.

`tooltip = <loc_key>`  
Optional.

 | 

```
career_profile_check_ribbon = {
  ribbon = orchestra_of_boom
  tooltip = my_loc_key
}
```

 | Checks if the required ribbon is achieved and collected. | By default provide no tooltip. | ??? |
| career\_profile\_check\_playthrough\_ratio | `frits = <variable>`  

`second = <variable>`

`ratio = <int>`  
Ratio.  
`compare = <type>`  
The type of comparison.



 | 

```
career_profile_check_playthrough_ratio = {
  first = enemy_casualties
  second = total_own_casualties
  ratio = 4
  compare = greater_than_or_equals
}
```

 | Compares the ratio (first/second) of two playthrough values to a number. | Provide no tooltip.

Possible compare types:

-   less\_than
-   less\_than\_or\_equals
-   greater\_than
-   greater\_than\_or\_equals
-   equals
-   not\_equals

 | ??? |
| career\_profile\_check\_playthrough\_value | `{ ... }`

**OR**  
`var = <variable>`  
Value to compare.  
`value = <int>`  
Value to compare to.  
`compare = <type>`  
The type of comparison. Optional.  
`tooltip = <loc_key>`  
Optional.  
`tooltip_value = <int>`  
Optional.

 | 

```
career_profile_check_playthrough_value = {
  plan_landlocked_battleship > 1
  plan_landlocked_carrier > 0
}
```

```
career_profile_check_playthrough_value = {
  var = deployed_airplanes_with_air_defense_gold
  value = 100
  compare = greater_than_or_equals
  tooltip = CAREER_PROFILE_TRIGGER_DEPLOYED_AIRPLANES_WITH_AIR_DEFENSE
  tooltip_value = 100

```

 | Compares a playthrough value to a number. | By default provide no tooltip.

Possible compare types:

-   less\_than
-   less\_than\_or\_equals
-   greater\_than
-   greater\_than\_or\_equals
-   equals
-   not\_equals

 | ??? |
| career\_profile\_check\_points | `value = <int>`  
Value to compare.

`compare = <type>`  
The type of comparison.  
`tooltip = <loc_key>`  
Optional.  


 | 

```
career_profile_check_points = {
  value = 5000
  compare = greater_than_or_equals
  tooltip = CAREER_PROFILE_TRIGGER_MINED_SEA_REGIONS
}
```

 | Compares a career points value to a number. | By default provide no tooltip.

Possible compare types:

-   less\_than
-   less\_than\_or\_equals
-   greater\_than
-   greater\_than\_or\_equals
-   equals
-   not\_equals

 | ??? |
| career\_profile\_check\_ratio | Possible the same as [#career\_profile\_check\_playthrough\_ratio](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_ratio). | Possible the same as [#career\_profile\_check\_playthrough\_ratio](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_ratio). | Compares the ratio (first/second) of two career profile values to a number. | Possible the same as [#career\_profile\_check\_playthrough\_ratio](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_ratio). | ??? |
| career\_profile\_check\_value | Possible the same as [#career\_profile\_check\_playthrough\_value](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_value). | Possible the same as [#career\_profile\_check\_playthrough\_value](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_value). | Compares a career profile value to a number. | Possible the same as [#career\_profile\_check\_playthrough\_value](https://hoi4.paradoxwikis.com/Triggers#career_profile_check_playthrough_value). | ??? |
| career\_profile\_has\_player\_flag | `<string>`  
The flag to check. | 

```
career_profile_has_player_flag = career_profile_overrun_infantry_flag
```

 | Checks if the flag is set for the local player. |  | ??? |

### Variables\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=10 "Edit section: Variables") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=10 "Edit section: Variables")\]

Variable-related triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_variable | `<variable>`  
The variable to check. | 
```
has_variable = my_var
```

 | Checks if the specified variable exists for the current scope. |  | 1.5 |
| check\_variable | `var = <variable>`  
The variable to check.

`value = <float> / <variable>`  
The value to check for.  
`compare = <type>`  
The type of comparison. Optional, can use < or > instead.

 | 

```
check_variable = {
    var = my_var
    value = 10
    compare = greater_than_or_equals
}

```

```
check_variable = {
    my_var > 10
}

```

 | Check the specified variable for the current scope. | Possible compare types:

-   less\_than
-   less\_than\_or\_equals
-   greater\_than
-   greater\_than\_or\_equals
-   equals
-   not\_equals

 | 1.5 |

Remember that variables need to refer to the scope they were set in. This means you can't check a country variable in a state scope without scoping the variable.

For example, to get the country variable whilst in a state scope, you'd do the following:

```
<country> = {
    <state> = {
        limit = {
            check_variable = { from.my_country_var > 0.0 }
        }
    }
}

```

See [Variables](https://hoi4.paradoxwikis.com/Variables "Variables") for more information.

### Debugging\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=11 "Edit section: Debugging") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=11 "Edit section: Debugging")\]

These are usable as both effects and triggers and are used for debugging, with the player never seeing them.

Debugging-helpful triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| log | `<string>`  
What to log. Supports dynamic localisation.  
 | 
```
log = "Added [?temp_add] to [THIS.GetTag]'s variable [?THIS.varvalue]"
```

 | Appends an entry into the game.log and, if open, the console when evaluating the trigger. | game.log is stored within /Hearts of Iron IV/logs/ in the [user directory](https://hoi4.paradoxwikis.com/Modding "Modding") | 1.5 |
| print\_variables | `print_global = <bool>`  
Print global variables. Defaults to `no`.

`var_list = <list>`  
The variables to print. Defaults to all variables.  
`file = <string>`The file path to log to. Defaults to "variable\_dump". Does not include the `.log` extension.  
`text = <string>`Text to prepend. Defaults to "No Header".  
`append = <bool>`Whether to append to the file instead of overwrite. Defaults to `yes`

 | 

```
print_variables = {
    var_list = { myvar1 myvar2 }
    file = "my_dump_file"
    text = "my header"
}
```

 | Dumps the specified variables from the current scope and optionally the global scope into a log file with the specified name. | The log will be within /Hearts of Iron IV/logs/variable\_dumps/ in the [user directory](https://hoi4.paradoxwikis.com/Modding "Modding"). See also [debugging variables](https://hoi4.paradoxwikis.com/Variables#Debugging "Variables"). | 1.5 |

## Country scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=12 "Edit section: Country scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=12 "Edit section: Country scope")\]

Can be used in **country** scope.

### General\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=13 "Edit section: General") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=13 "Edit section: General")\]

General country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| exists | `<bool>`  
Boolean. | 
```
exists = yes
```

 | Checks if the current scope exists in game. |  | 1.0 |
| tag | `<scope> / <variable>`  
The country to check. | 

```
tag = GER
```

```
tag = var:my_country
```

 | Checks if the current scope is the specified country. | Only checks the actual tag while excluding dynamic countries, see [original\_tag](https://hoi4.paradoxwikis.com/Triggers#original_tag) if they should be included. | 1.0 |
| original\_tag | `<scope> / <variable>`  
The country to check. | 

```
original_tag = GER
```

```
original_tag = var:my_country
```

 | Checks if the current scope originates from the specified country. | This also includes dynamic countries: civil war breakaways and countries created via [create\_dynamic\_country](https://hoi4.paradoxwikis.com/Effect#create_dynamic_country "Effect"). True for the original country. | 1.0 |
| is\_ai | `<bool>`  
Boolean. | 

```
is_ai = yes
```

 | Checks if the current scope is AI. |  | 1.0 |
| has\_collaboration | `target = <country>`  
The country to check.

`value <> <decimal>`  
The value of the collaboration on the 0-1 scale.

 | 

```
has_collaboration = {
    target = GER
    value > 0.5
}
```

 | Checks if the current scope has a collaboration level in the target scope. | The target is occupied by the current scope. Must use < or > in the value argument. | 1.9 |
| has\_country\_flag | `<string>`  
The flag to check. | 

```
has_country_flag = my_flag
```

 | Checks if the current scope has the specified flag. |  | 1.0 |
| has\_country\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_country_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.0 |
| has\_cosmetic\_tag | `<string>`  
The cosmetic tag to check. | 

```
has_cosmetic_tag = SOV_custom
```

 | Checks if the current scope has the specified cosmetic tag active. |  | 1.5 |
| has\_event\_target | `<event target>`  
The event target to check. | 

```
has_event_target = my_var
```

 | Checks if current scope or global scope has the specified event target saved. |  | 1.0 |
| has\_decision | `<string>`  
The decision to check. | 

```
has_decision = my_decision
```

 | Checks if the current scope has the specified decision activated. |  | 1.5 |
| has\_dynamic\_modifier | `modifier = <string>`  
The dynamic\_modifier to check.

`scope = <scope>`  
The country to check. Optional, if the original modifier has been targeted.

 | 

```
has_dynamic_modifier = {
    modifier = my_dynamic_modifier
    scope = GER
}

```

 | Checks if the current scope has the specified dynamic modifier activated. |  | 1.6 |
| has\_active\_mission | `<string>`  
The mission to check. | 

```
has_active_mission = my_mission
```

 | Checks if the current scope has the specified mission active. |  | 1.5 |
| has\_country\_custom\_difficulty\_setting | `<bool>`  
Boolean. | 

```
has_country_custom_difficulty_setting = yes
```

 | Checks if the any custom difficulty setting targeting the current scope is changed from the default value. | Custom difficulty in this case refers to /Hearts of Iron IV/common/difficulty\_settings/\*.txt, used in base game to strengthen a specific country. | 1.0 |
| has\_terrain | `<terrain>`  
Terrain. | 

```
has_terrain = urban
```

 | Checks if the current scope has any provinces of the specified terrain. | Only can be used in country scope. | 1.11 |
| is\_dynamic\_country | `<bool>`  
Boolean. | 

```
is_dynamic_country = yes
```

 | Checks if the current scope is a dynamic country. | Dynamic countries include those generated in civil wars as well as those generated with the create\_dynamic\_country effect, such as collaboration governments. | 1.11 |
| num\_of\_supply\_nodes | `<int>`  
The amount to check for. | 

```
num_of_supply_nodes > 10
```

 | Checks if the current scope has the specified amount of supply nodes under control. | Can only use < or > operators. | 1.11 |
| <resource> (resource\_count\_trigger) | `<int>`  
The amount to check for. | 

```
tungsten > 10

```

 | Checks if the current scope has the specified amount of the specified resource. | Must use either > or < operators for amount.

[Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_resource_count_trigger)

 | ??? |
| has\_resources\_in\_country | `resource = <resource>`  
The resource to check for.

`amount = <int>`  
The amount to check for.  
`extracted = <bool>`  
Limits the checked resources only to those gained from the state's base value and multiplicative modifiers on top of it if true. Optional, defaults to false.  
`buildings = <bool>`  
Limits the checked resources only to those gained from the state's modifiers applied by buildings. Optional, defaults to false.

 | 

```
has_resources_in_country = {
    resource = oil
    amount > 10
    extracted = yes
}

```

 | Checks if the current scope has the specified amount of the specified resource in reserve. | Must use either > or < operators for amount. 'In reserve' means that it's not spent on equipment production or exports. | 1.12 |

### National focuses\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=14 "Edit section: National focuses") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=14 "Edit section: National focuses")\]

National focus-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_focus\_tree | `<string>`  
The focus tree to check. | 
```
has_focus_tree = soviet_tree
```

 | Checks if the current scope has the specified focus tree. |  | 1.3 |
| has\_completed\_focus | `<string>`  
The focus to check. | 

```
has_completed_focus = my_focus
```

 | Checks if the current scope has the specified focus completed. |  | 1.0 |
| focus\_progress | `focus = <string>`  
The focus to check.

`progress = <string>`  
The progress to check for.

 | 

```
focus_progress = {
  focus = my_focus
  progress > 0.5
}

```

 | Checks if the specified focus has been completed the specified percent for the current scope. | Must use either > or < operators for progress. | 1.0 |
| has\_shine\_effect\_on\_focus | `<string>`  
The focus to check. | 

```
has_shine_effect_on_focus = GER_wunderwaffe
```

 | Check if country has shine effect on focus (either manually achieved or by being worked on). | Note that tooltips are only shown in debug mode.

Shine can be added manually by selecting focus, or via [activate\_shine\_on\_focus](https://hoi4.paradoxwikis.com/Effects#activate_shine_on_focus "Effects") effect.

 | 1.15 |

### Politics\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=15 "Edit section: Politics") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=15 "Edit section: Politics")\]

Political country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| <ideology> (ideology\_support\_trigger) | `<ideology> = <float> / <variable>`  
The amount of the ideology to check for. | 
```
fascism > 0.5
```

```
democratic > party_popularity@communism
```

 | Checks if the current scope has popularity of the specified ideology above the specified amount. |  | 1.0 |
| has\_political\_power | `<float> / <variable>`  
The amount to check for. | 

```
has_political_power > 100
```

 | Checks if the current scope has the specified amount of political power. | Must use either > or < operators. | 1.0 |
| political\_power\_daily | `<float> / <variable>`  
The amount to check for. | 

```
political_power_daily > 1
```

 | Checks if the current scope has the specified amount of daily political power gain. | Must use either > or < operators. | 1.5 |
| political\_power\_growth | `<float> / <variable>`  
The amount to check for. | 

```
political_power_growth > 1
```

 | Checks if the current scope has the specified amount of daily political power gain. | Must use either > or < operators. | 1.5 |
| command\_power | `<float> / <variable>`  
The amount to check for. | 

```
command_power > 1
```

 | Checks if the current scope has the specified amount of command power. | Must use either > or < operators. | 1.5 |
| command\_power\_daily | `<float> / <variable>`  
The amount to check for. | 

```
command_power_daily > 1
```

 | Checks if the current scope has the specified amount of daily command power gain. | Must use either > or < operators. | 1.5 |
| has\_war\_support | `<float> / <variable>`  
The amount to check for. | 

```
has_war_support > 0.5
```

 | Checks if the current scope has the specified percentage of War Support. | Must use either > or < operators. | 1.5 |
| has\_stability | `<float> / <variable>`  
The amount to check for. | 

```
has_stability > 0.5
```

 | Checks if the current scope has the specified percentage of Stability. | Must use either > or < operators. | 1.5 |
| has\_government | `<ideology>`  
The ideology group to check for.

**OR**  
`<country>`  
The country to compare with.

 | 

```
has_government = fascism
```

```
has_government = ROOT
```

 | Checks if the ruling party of the current scope meets the requirements of being either the specified ideology group or having the same ideology group as the specified country. |  | 1.0 |
| has\_elections | `<bool>`  
Boolean. | 

```
has_elections = yes
```

 | Checks if the current scope holds elections. |  | 1.0 |
| is\_staging\_coup | `<bool>`  
Boolean. | 

```
is_staging_coup = yes
```

 | Checks if the current scope is staging a coup. |  | 1.3 |
| is\_target\_of\_coup | `<bool>`  
Boolean. | 

```
is_target_of_coup = yes
```

 | Checks if the current scope is the target of a coup. |  | 1.0 |
| has\_civil\_war | `<bool>`  
Boolean. | 

```
has_civil_war = yes
```

 | Checks if the current scope has a civil war active. |  | 1.0 |
| civilwar\_target | `<scope>`  
The target country. | 

```
civilwar_target = GER
```

 | Checks if the specified country is a target of a civil war. |  | 1.0 |
| has\_manpower\_for\_recruit\_change\_to | `value = <float>`  
The amount to check for.

`group = <group>`  
The group to check for.

 | 

```
has_manpower_for_recruit_change_to = {
    value > 0.05
    group = mobilization_laws
}
```

 | Checks if the current scope has the specified amount of manpower for changing the specified idea group. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.0 |
| has\_rule | `<string>`  
The rule to check for. | 

```
has_rule = can_create_factions

```

 | Checks if the current scope has the specified country rule. |  | 1.6 |
| has\_casualties\_war\_support | `<float> / <variable>`  
The amount to check for. | 

```
has_casualties_war_support < 0
```

 | Checks if the current scope has the specified percentage of war support from own combat casualties. | Must use either > or < operators. | 1.12 |
| has\_convoys\_war\_support | `<float> / <variable>`  
The amount to check for. | 

```
has_convoys_war_support < 0
```

 | Checks if the current scope has the specified percentage of war support from own convoys sunk. | Must use either > or < operators. | 1.12 |
| has\_bombing\_war\_support | `<float> / <variable>`  
The amount to check for. | 

```
has_bombing_war_support < 0
```

 | Checks if the current scope has the specified percentage of war support from own states bombed by the enemy. | Must use either > or < operators. | 1.12 |

### Balance of power\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=16 "Edit section: Balance of power") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=16 "Edit section: Balance of power")\]

Balances of power are stored within /Hearts of Iron IV/common/bop/\*.txt files.

Balance of power-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_power\_balance | `id = <bop ID>`  
The balance to check for. | 
```
has_power_balance = {
    id = TAG_my_bop
}
```

 | Checks if the current scope has the specified balance of power active. |  | 1.12 |
| has\_any\_power\_balance | `<bool>`  
Boolean. | 

```
has_any_power_balance = yes
```

 | Checks if the current scope has any balance of power active. |  | 1.12 |
| power\_balance\_value | `id = <bop ID>`  
The balance to check in.

`value = <float>`  
The value to check for.

 | 

```
power_balance_value = {
    id = TAG_my_bop
    value > 0.7
}
```

 | Checks if the current scope has the specified value within the balance of power. | Either =, >, or < operators are allowed. | 1.12 |
| power\_balance\_daily\_change | `id = <bop ID>`  
The balance to check in.

`value = <float>`  
The value to check for.

 | 

```
power_balance_daily_change = {
    id = TAG_my_bop
    value < -0.01
}
```

 | Checks if the current scope's balance of power changes each day by the specified value. | Either =, >, or < operators are allowed. | 1.12 |
| power\_balance\_weekly\_change | `id = <bop ID>`  
The balance to check in.

`value = <float>`  
The value to check for.

 | 

```
power_balance_weekly_change = {
    id = TAG_my_bop
    value < -0.01
}
```

 | Checks if the current scope's balance of power changes each week by the specified value. | Either =, >, or < operators are allowed. | 1.12 |
| is\_power\_balance\_in\_range | `id = <bop ID>`  
The balance to check in.

`range = <range ID>`  
The range to check for.

 | 

```
is_power_balance_in_range = {
    id = TAG_my_bop
    range > TAG_my_bop_right_range
}
```

 | Checks if the current scope's balance of power value lies within the specified range. | Ranges are defined within the balance of power. Can use either =, >, and < operators. In case of > or <, the comparison is 'strict', i.e. excluding the range itself. | 1.12 |
| is\_power\_balance\_side\_active | `id = <bop ID>`  
The balance to check in.

`side = <side ID>`  
The side to check.

 | 

```
is_power_balance_side_active = {
    id = TAG_my_bop
    side = TAG_my_bop_right_range
}
```

 | Checks if the specified balance of power has a side active. | Sides are defined within the balance of power. "Active" means that the side is among those that are currently visible instead of relying on the current value. | 1.12 |
| has\_power\_balance\_modifier | `id = <bop ID>`  
The balance to check in.

`modifier = <modifier ID>`  
The [static modifier](https://hoi4.paradoxwikis.com/Static_modifiers "Static modifiers").

 | 

```
has_power_balance_modifier = {
    id = TAG_my_bop
    modifier = TAG_my_bop_modifier
}
```

 | Checks if the current scope's balance of power value activates a modifier. | BoP modifiers are defined within /Hearts of Iron IV/common/modifiers/\*.txt files, while they're activated in the balance of power definition. | 1.12 |

### Buildings\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=17 "Edit section: Buildings") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=17 "Edit section: Buildings")\]

Building-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| <building> (building\_count\_trigger) | `<int>`  
The amount of the specified building to to check for. | 
```
arms_factory > 10
```

 | Checks if the current scope has the specified amount of the specified building. | Must use either > or < operators. Works in the state scope as well, unlike the other triggers.

[Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_building_count_trigger)

 | 1.0 |
| num\_of\_military\_factories | `<int>`  
The amount to check for. | 

```
num_of_military_factories > 10
```

 | Checks if the current scope has the specified amount of military factories. | Must use either > or < operators. | 1.0 |
| num\_of\_civilian\_factories | `<int>`  
The amount to check for. | 

```
num_of_civilian_factories > 10
```

 | Checks if the current scope has the specified amount of civilian factories. | Must use either > or < operators. | 1.0 |
| num\_of\_naval\_factories | `<int>`  
The amount to check for. | 

```
num_of_naval_factories > 10
```

 | Checks if the current scope has the specified amount of dockyards. | Must use either > or < operators. | 1.0 |
| num\_of\_available\_military\_factories | `<int>`  
The amount to check for. | 

```
num_of_available_military_factories > 10
```

 | Checks if the current scope has the specified amount of available military factories. | Must use either > or < operators. | 1.0 |
| num\_of\_available\_civilian\_factories | `<int>`  
The amount to check for. | 

```
num_of_available_civilian_factories > 10
```

 | Checks if the current scope has the specified amount of available civilian factories. | Must use either > or < operators. | 1.0 |
| num\_of\_available\_naval\_factories | `<int>`  
The amount to check for. | 

```
num_of_available_naval_factories > 10
```

 | Checks if the current scope has the specified amount of available dockyards. | Must use either > or < operators. | 1.0 |
| num\_of\_factories | `<int>`  
The amount to check for. | 

```
num_of_factories > 10
```

 | Checks if the current scope has the specified amount of military, civilian or dockyard factories. | Must use either > or < operators. | 1.0 |
| num\_of\_controlled\_factories | `<int>`  
The amount to check for. | 

```
num_of_controlled_factories > 10
```

 | Checks if the current scope has the specified amount of military, civilian or dockyard factories under control. | Must use either > or < operators. | 1.11 |
| num\_of\_owned\_factories | `<int>`  
The amount to check for. | 

```
num_of_owned_factories > 10
```

 | Checks if the current scope has the specified amount of military, civilian or dockyard factories under owned states. | Must use either > or < operators. | 1.11 |
| num\_of\_civilian\_factories\_available\_for\_projects | `<int>`  
The amount to check for. | 

```
num_of_civilian_factories_available_for_projects > 10
```

 | Checks if the current scope has the specified amount of civilian factories usable for projects. | Must use either > or < operators. | 1.5 |
| ic\_ratio | `tag = <scope>`  
The country to check.

`ratio = <float>`  
The ratio to check for.

 | 

```
ic_ratio = {
    tag = GER
    ratio > 0.5
}

```

 | Checks if the current scope has the specified ratio of factories with the target country. | Must use either > or < operators for ratio. | 1.0 |
| has\_damaged\_buildings | `<bool>`  
Boolean. | 

```
has_damaged_buildings = yes
```

 | Checks if the current scope has any damanged buildings in their states. |  | 1.0 |
| has\_built | `type = <building>`  
The building to check for.

`value = <int>`  
The amount to check for.

 | 

```
has_built = {
    type = arms_factory
    value > 10
}

```

 | Checks if the current scope has built the specified building the specified number of times. | Must use either > or < operators for value. | 1.0 |

### Technology\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=18 "Edit section: Technology") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=18 "Edit section: Technology")\]

Technology-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_tech | `<string>`  
The technology to check for. | 
```
has_tech = my_technology
```

 | Checks if the current scope has the specified technology. |  | 1.0 |
| is\_researching\_technology | `<string>`  
The technology to check for. | 

```
is_researching_technology = my_tech
```

 | Checks if the current scope is currently researching the specified technology. |  | 1.0 |
| can\_research | `<string>`  
The technology to check for. | 

```
can_research = my_tech
```

 | Checks if the current scope can start researching the specified technology. |  | 1.0 |
| original\_research\_slots | `<int>`  
The amount to check for. | 

```
original_research_slots > 3
```

 | Checks if the current scope had the specified amount of slots at game start. | Must use either > or < operators. | 1.0 |
| amount\_research\_slots | `<int>`  
The amount to check for. | 

```
amount_research_slots > 3
```

 | Checks if the current scope has the specified amount of research slots. | Must use either > or < operators. | 1.3 |
| is\_in\_tech\_sharing\_group | `<string>`  
The group to check for. | 

```
is_in_tech_sharing_group = us_research
```

 | Checks if the current scope is in the specified technology sharing group. |  | 1.3 |
| num\_tech\_sharing\_groups | `<int>`  
The amount to check for. | 

```
num_tech_sharing_groups > 3
```

 | Checks if the current scope is in the specified amount of technology sharing groups. | Must use either > or < operators. | 1.3 |
| has\_tech\_bonus | `technology = <string>`  
The technology to check for. Optional.

`category = <string>`  
The category to check for. Optional.  


 | 

```
has_tech_bonus = {
    technology = my_tech
}
```

```
has_tech_bonus = {
    category = my_category
}

```

 | Checks if the current scope has a technology bonus in the specified category, or for the specific technology. |  | 1.3 |
| land\_doctrine\_level | `<int>`  
The amount to check for. | 

```
land_doctrine_level > 2
```

 | Checks if the current scope has the specified amount of land doctrine technologies. | Must use either > or < operators. | 1.0 |
| num\_researched\_technologies | `<int>`  
The amount to check for. | 

```
num_researched_technologies > 10
```

 | Checks how many technologies the target has researched. | Must use either > or < operators. | 1.3 |
| is\_special\_project\_being\_researched | `sp:<string>`  
A special project to check for. | 

```
is_special_project_being_researched = sp:sp_air_radar
```

 | Checks if the country in scope is currently researching the special project in input. |  | 1.15 |
| is\_special\_project\_completed | `sp:<string>`  
A special project to check for. | 

```
is_special_project_completed = sp:sp_land_flamethrower_tank
```

 | Checks if the current scope has the specified special project completed. |  | 1.15 |

### Ideas\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=19 "Edit section: Ideas") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=19 "Edit section: Ideas")\]

Idea-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_idea | `<string>`  
The idea to check for. | 
```
has_idea = my_idea
```

 | Checks if the current scope has the specified idea. |  |
| has\_idea\_with\_trait | `<string>`  
The trait to check for. | 

```
has_idea_with_trait = my_trait
```

 | Checks if the current scope has any ideas with the specified trait. |  | 1.0 |
| has\_allowed\_idea\_with\_traits | `idea = <string>`  
The trait to check for.

`limit = <int>`  
The amount to check for.  
`characters = <bool>`  
If set, will only run this on characters.  
`ignore = { <ideas> }`  
If set, ignores the ideas inside. Optional.  


 | 

```
has_available_idea_with_traits = {
    idea = my_trait
    limit = 1
    ignore = { generic_head_of_intelligence }
}

```

 | Checks if the current scope has the specified amount of ideas with the specified trait. | ignore = idea\_name works for 1 idea. | 1.9.1 |
| has\_available\_idea\_with\_traits | `idea = <string>`  
The trait to check for.

`limit = <int>`  
The amount to check for.  
`characters = <bool>`  
If set, will only run this on characters.  
`ignore = { <ideas> }`  
If set, ignores the ideas inside. Optional.  


 | 

```
has_available_idea_with_traits = {
    idea = my_trait
    limit = 1
    ignore = { generic_head_of_intelligence }
}

```

 | Checks if the current scope has the specified amount of ideas with the specified trait. | ignore = idea\_name works for 1 idea. | 1.0 |
| amount\_taken\_ideas | `amount = <int>`  
The amount to check for.

`slots = { <string> }`  
The slot type.

 | 

```
amount_taken_ideas = {
    amount > 3
    slots = {
        political_advisor
    }
}

```

 | Checks if the current scope has the specified amount of ideas of the specified slot type. Excludes spirits, hidden ideas, and laws. | Slots types are found in /Hearts of Iron IV/common/idea\_tags/\*.txt. | 1.4 |

### Diplomacy\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=20 "Edit section: Diplomacy") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=20 "Edit section: Diplomacy")\]

Diplomatic country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| is\_major | `<bool>`  
Boolean. | 
```
is_major = yes
```

 | Checks if the current scope is considered a Major. |  | 1.0 |
| is\_ally\_with | `<scope> / <variable>`  
The country to check for. | 

```
is_ally_with = GER
```

```
is_ally_with = var:country
```

 | Checks if the current scope is an ally (Faction members or subject-master relation). |  | 1.0 |
| is\_spymaster | `<bool>`  
Boolean. | 

```
is_spymaster = yes
```

 | Checks if the current scope is the spymaster of a faction. |  | 1.9 |
| has\_non\_aggression\_pact\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_non_aggression_pact_with = GER
```

 | Checks if the current scope has a non-aggression pact with the specified country. |  | 1.0 |
| is\_guaranteed\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_guaranteed_by = GER
```

 | Checks if the current scope has been guaranteed by the specified country. |  | 1.0 |
| has\_guaranteed | `<scope> / <variable>`  
The country to check for. | 

```
has_guaranteed = GER
```

 | Checks if the current scope has guaranteed the specified country. |  | 1.0 |
| has\_military\_access\_to | `<scope> / <variable>`  
The country to check for. | 

```
has_military_access_to = GER
```

 | Checks if the current scope has military access to the specified country. |  | 1.0 |
| gives\_military\_access\_to | `<scope> / <variable>`  
The country to check for. | 

```
gives_military_access_to = GER
```

 | Checks if the current scope gives military to the specified country. |  | 1.0 |
| is\_neighbor\_of | `<scope> / <variable>`  
The country to check for. | 

```
is_neighbor_of = GER
```

 | Checks if the current scope is a neighbor of the specified country. |  | 1.0 |
| is\_owner\_neighbor\_of | `<scope> / <variable>`  
The country to check for. | 

```
is_owner_neighbor_of = GER
```

 | Checks if the current scope is a neighbor of the specified country with their core territory only. |  | 1.0 |
| is\_puppet\_of | `<scope> / <variable>`  
The country to check for. | 

```
is_puppet_of = GER
```

 | Checks if the current scope is a puppet of the specified country. | A "puppet" is an autonomous state that has `is_puppet = yes` in its definition within /Hearts of Iron IV/common/autonomous\_states/. For any subject type, see [is\_subject\_of](https://hoi4.paradoxwikis.com/Triggers#is_subject_of). | 1.0 |
| is\_subject\_of | `<scope> / <variable>`  
The country to check for. | 

```
is_subject_of = GER
```

 | Checks if the current scope is a subject of the specified scope. |  | 1.0 |
| is\_puppet | `<bool>`  
Boolean. | 

```
is_puppet = yes
```

 | Returns true if the current country is a puppet. | A "puppet" is an autonomous state that has `is_puppet = yes` in its definition within /Hearts of Iron IV/common/autonomous\_states/. For any subject type, see [is\_subject](https://hoi4.paradoxwikis.com/Triggers#is_subject). | 1.0 |
| is\_subject | `<bool>`  
Boolean. | 

```
is_subject = yes
```

 | Checks if the current scope is a subject. |  | 1.0 |
| has\_subject | `<bool>`  
Boolean. | 

```
has_subject = GRE
```

 | Checks if the country has for subject the given country. |  | 1.0 |
| num\_subjects | `<int>`  
The amount to check for. | 

```
num_subjects > 3
```

 | Checks if the current scope has the specified amount of subjects. | Must use either > or < operators. | 1.3 |
| has\_autonomy\_state | `<string>`  
The autonomy state to check for. | 

```
has_autonomy_state = autonomy_dominion
```

 | Checks if the current scope is in the specified autonomous state. |  | 1.0 |
| compare\_autonomy\_state | `<string>`  
The autonomy state to check for. | 

```
compare_autonomy_state > autonomy_dominion
```

 | Checks if the current scope's autonomy state `min_freedom_level` is less or greater than that of the specified autonomy state. The special value "autonomy\_free" compares as greater than any autonomy state. If the current scope is not a subject, it is treated as greater than any autonomy state (including "autonomy\_free"). With `=`, checks if the current scope is in the specified autonomous state. |  | 1.0 |
| compare\_autonomy\_progress\_ratio | `<float>`  
The amount to check for. | 

```
compare_autonomy_progress_ratio > 0.5
```

 | Checks if the current scope autonomy progress is at the specified ratio. If the current scope is not a subject, the ratio is 1. |  | 1.3 |
| has\_opinion\_modifier | `<string>`  
The opinion modifier to check for. | 

```
has_opinion_modifier = my_modifier
```

 | Checks if the current scope has the specified opinion modifier. |  | 1.0 |
| has\_opinion | `target = <scope>`  
The country to check for.

`value = <float>`  
The amount to check for.

 | 

```
has_opinion = {
    target = GER
    value > 50
}

```

 | Checks if the current scope has the specified opinion of the target country. | Must use either > or < operators. | 1.0 |
| has\_relation\_modifier | `target = <scope>`  
The country to check for.

`modifier = <modifier>`  
The modifier to check for.

 | 

```
has_relation_modifier = {
    target = GER
    modifier = my_modifier
}

```

 | Checks if the current scope has the specified relation modifier with the specified country. |  | 1.0 |
| has\_legitimacy | `<int>`  
Amount to check. | 

```
has_legitimacy > 50
```

 | Checks how much legitimacy the current government in exile has. | Must use either > or < operators. Legitimacy ranges from 0 to 100. | 1.6 |
| is\_exile\_host | `<bool>`  
Boolean. | 

```
is_exile_host = yes
```

 | Checks if the current country is hosting an exile. |  | 1.6 |
| is\_hosting\_exile | `<tag>`  
Country. | 

```
is_hosting_exile = POL
```

 | Checks if the current country is hosting a specific exile. |  | 1.6 |
| is\_government\_in\_exile | `<bool>`  
Boolean. | 

```
is_government_in_exile = yes
```

 | Checks if the current country is exiled in a different country. |  | 1.6 |
| is\_exiled\_in | `<tag>`  
Country to be exiled in. | 

```
is_exiled_in = POL
```

 | Checks if the current country is exiled in a specific country. |  | 1.6 |
| received\_expeditionary\_forces | `sender = <tag>`  
Country which sent forces.

`value <> <int>`  
Amount of forces.

 | 

```
received_expeditionary_forces = {
    sender = POL
    value > 10
}
```

 | Checks if the current country received X units in expeditions from the specified country. |  | 1.6 |
| can\_declare\_war\_on | `<tag>`  
Country to check. | 

```
can_declare_war_on = POL
```

 | Checks if the current scope is able to declare war on the specified country. |  | 1.9 |
| foreign\_manpower | `<int>`  
Amount to check. | 

```
foreign_manpower > 10000
```

 | Checks how much foreign manpower we have received for garrisoning. | Must use either > or < operators. | 1.9 |
| is\_embargoed\_by | `<scope>`  
Amount to check. | 

```
is_embargoed_by = USA
```

 | Checks if the current scope is embargoed by the specified country. |  | 1.12 |
| is\_embargoing | `<scope>`  
Amount to check. | 

```
is_embargoing = CUB
```

 | Checks if the current scope is embargoing the specified country. |  | 1.12 |

### Faction\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=21 "Edit section: Faction") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=21 "Edit section: Faction")\]

Faction-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| is\_in\_faction | `<bool>`  
Boolean. | 
```
is_in_faction = yes
```

 | Checks if the current scope is in a faction. |  | 1.0 |
| is\_in\_faction\_with | `<scope> / <variable>`  
The country to check for. | 

```
is_in_faction_with = GER
```

```
is_in_faction_with = var:country
```

 | Checks if the current scope is in a faction with the specified country. |  | 1.0 |
| is\_faction\_leader | `<bool>`  
Boolean. | 

```
is_faction_leader = yes
```

 | Checks if the current scope is the leader of a faction. |  | 1.0 |
| num\_faction\_members | `<int> / <variable>`  
The amount to check for. | 

```
num_faction_members > 1
```

 | Checks if the faction of the current scope has the specified amount of members. | Must use either > or < operators. | 1.0 |
| has\_manpower\_to\_become\_leader | `<bool>`  
Boolean | 

```
has_manpower_to_become_leader = yes
```

 | Checks if the current country exceeds the current faction leader and its subjects in deployed manpower. |  | 1.17 |
| has\_industry\_to\_become\_leader | `<bool>`  
Boolean | 

```
has_industry_to_become_leader = yes
```

 | Checks if the current country exceeds the faction leader in number of factories. |  | 1.17 |
| has\_enough\_influence\_for\_leadership | `<bool>`  
Boolean | 

```
has_enough_influence_for_leadership = yes
```

 | Checks if the current country has enough political influence to become faction leader. |  | 1.17 |
| has\_faction\_template | `<template_id>`  
Faction template id. | 

```
has_faction_template = faction_template_chinese_united_front
```

 | Checks if the current country is in a faction with a template. |  | 1.17 |
| has\_active\_rule | `<rule_id>`  
Faction rule id. | 

```
has_active_rule = government_in_exile_allowed
```

 | Checks if the country's faction has a specific active rule. |  | 1.17 |
| has\_faction\_goal | `<goal_id>`  
Faction goal id. | 

```
has_faction_goal = faction_goal_resource_control
```

 | Checks if the country's faction has an active or completed goal. |  | 1.17 |
| has\_completed\_faction\_goal | `<goal_id>`  
Faction goal id. | 

```
has_completed_faction_goal = faction_goal_resource_control
```

 | Checks if the country's faction has successfully completed a goal. |  | 1.17 |
| faction\_goal\_fulfillment | `goal = <goal_id>`  
Faction goal id.

`value = <float> / <variable>`  
The amount to check for.

 | 

```
faction_goal_fulfillment = {
    goal = faction_goal_resource_control
    value > 0.85
}
```

```
faction_goal_fulfillment = {
    goal = faction_goal_resource_control
    value > 0.5
    value < 0.85
}
```

 | Checks fulfillment of a faction goal for the current country's faction. | Value supports > and <, can accept variables, can be repeated multiple times. | 1.17 |
| faction\_manifest\_fulfillment | `<float> / <variable>`  
The amount to check for. | 

```
faction_manifest_fulfillment > 0.95
```

 | Checks manifest fulfillment value of current country's faction manifest. |  | 1.17 |
| faction\_upgrade\_level | `<upgrade_token>`  
Faction upgrade token. | 

```
faction_upgrade_level > upgrade_token
```

 | Checks the active faction member upgrade against the specified upgrade. | Works with >, <, = | 1.17 |
| faction\_power\_projection | `<int> / <variable>`  
The amount to check for. | 

```
faction_power_projection > 100
```

 | Checks power value of current country's faction projection. |  | 1.17 |
| faction\_influence\_rank | `<int> / <variable>`  
The amount to check for. | 

```
faction_influence_rank < 5
```

 | Checks influence rank in the faction of the current country. |  | 1.17 |
| faction\_influence\_ratio | `<float> / <variable>`  
The amount to check for. | 

```
faction_influence_ratio > 0.1
```

 | Checks influence ratio of current country in the faction. |  | 1.17 |
| faction\_influence\_score | `<int> / <variable>`  
The amount to check for. | 

```
faction_influence_score > 100
```

 | Checks influence value of current country in the faction. |  | 1.17 |
| can\_assign\_supportive\_scientist\_to\_faction | `<specialization>`  
Specialization. | 

```
can_assign_supportive_scientist_to_faction = specialization_land
```

 | Checks if the faction from the country in scope has a free slot for a supportive scientist for the country with the specialization type. |  | 1.17 |
| has\_faction\_research\_unlocked | `<bool>`  
Boolean. | 

```
has_faction_research_unlocked = yes
```

 | Whether the faction has unlocked the research. |  | 1.17 |
| has\_faction\_military\_unlocked | `<bool>`  
Boolean. | 

```
has_faction_military_unlocked = yes
```

 | Whether the faction has unlocked the military operations. |  | 1.17 |
| compare\_ideology\_with\_faction | `value = <float> / <variable>`  
The amount to check for.

`leader = <tag>`  
Country to check.

 | 

```
compare_ideology_with_faction = {
    value > 0.5
    leader = FROM
}
```

 | Compares the ideology support of the country's ruling party for the ideology of the faction it wants to join. | Tooltip is visible only if 'leader' is in faction. | 1.17 |

### War\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=22 "Edit section: War") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=22 "Edit section: War")\]

War-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_war | `<bool>`  
Boolean. | 
```
has_war = yes
```

 | Checks if the current scope is at war. |  | 1.0 |
| has\_war\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_war_with = GER
```

```
has_war_with = var:country
```

 | Checks if the current scope is at war with the specified country. |  | 1.0 |
| has\_offensive\_war\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_offensive_war_with = GER
```

 | Checks if the current scope is in an offensive war against the specified country. |  | 1.0 |
| has\_offensive\_war\_without\_friend | `<scope> / <variable>`  
The country to check for. | 

```
has_offensive_war_without_friend = GER
```

 | Is country at offensive war without specific ally present. |  | 1.17 |
| has\_defensive\_war\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_defensive_war_with = GER
```

 | Checks if the current scope is in an defensive war against the specified country. |  | 1.0 |
| has\_offensive\_war | `<bool>`  
Boolean. | 

```
has_offensive_war = yes
```

 | Checks if the current scope is in an offensive war. |  | 1.0 |
| has\_defensive\_war | `<bool>`  
Boolean. | 

```
has_defensive_war = yes
```

 | Checks if the current scope is in a defensive war. |  | 1.0 |
| has\_war\_together\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_war_together_with = GER
```

 | Checks if the current scope is in a war alongside the specified country. |  | 1.0 |
| has\_war\_with\_major | `<bool>`  
Boolean. | 

```
has_war_with_major = yes
```

 | Checks if the current scope is at war with any other country that is considered major. |  | 1.12 |
| has\_war\_with\_wargoal\_against | `target = <scope> / <variable>`  
The country to check for.

`type = <wargoal>`  
The wargoal to check for. Optional.

 | 

```
has_war_with_wargoal_against = {
    target = ENG
    type = independence_wargoal
}
```

 | Checks if the current scope is at war with the specified country with the specified wargoal being active. | Wargoals are stored within /Hearts of Iron IV/common/wargoals/\*.txt files. If no wargoal is specified, checks for _any_ wargoal. Joining an ally in their war does not count as a wargoal. | 1.12 |
| surrender\_progress | `<float> / <variable>`  
The amount to check for. | 

```
surrender_progress > 0.1
```

 | Checks if the current scope has the specified amount of surrender progress. | Must use either > or < operators. | 1.0 |
| any\_war\_score | `<float>`  
The amount to check for. | 

```
any_war_score > 10
```

 | Checks if the current scope has the specified amount of **war progress** (not war participation)<sup id="cite_ref-2"><a href="https://hoi4.paradoxwikis.com/Triggers#cite_note-2">[2]</a></sup> in any war. | Must use either > or < operators. | 1.0 |
| has\_capitulated | `<bool>`  
Boolean. | 

```
has_capitulated = yes
```

 | Checks if the current scope has capitulated. |  | 1.0 |
| days\_since\_capitulated | `<int>`  
Amount of days. | 

```
days_since_capitulated > 10
```

 | Checks the amount of days since the target last capitulated. | If the target never capitulated, the amount of days is extremely large. Recommended to combine with has\_capitulated. | 1.9 |
| has\_border\_war\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_border_war_with = GER
```

 | Checks if the current scope has a border war with the specified country. |  | 1.5 |
| has\_border\_war\_between | `attacker = <scope> / <variable>`  
The state to check for.

`defender = <scope> / <variable>`  
The state to check for.

 | 

```
has_border_war_between = {
    attacker = 1
    defender = 2
}

```

 | Checks if there is a border war between the two specified states. |  | 1.5 |
| has\_border\_war | `<bool>`  
Boolean. | 

```
has_border_war = yes
```

 | Checks if the current scope has a border war active. |  | 1.5 |
| has\_added\_tension\_amount | `<float> / <variable>`  
The amount to check for. | 

```
has_added_tension_amount > 10
```

 | Checks if the current scope has caused the specified amount of World Tension. | Must use either > or < operators. | 1.0 |
| has\_wargoal\_against | `<scope> / <variable>`  
The country to check for. | 

```
has_wargoal_against = GER
```

 | Checks if the current scope has any wargoal against the specified country. |  | 1.0 |
| has\_wargoal\_against | `target = <scope> / <variable>`  
The country to check for.

`type = <string>`  
The type of wargoal to check for.

 | 

```
has_wargoal_against = {
    target = FROM
    type = take_state
}

```

 | Checks if the current scope has a specific wargoal type against the specified country. |  | 1.8 |
| is\_justifying\_wargoal\_against | `<scope> / <variable>`  
The country to check for. | 

```
is_justifying_wargoal_against = GER
```

 | Checks if the current scope is justifying a wargoal against the specified country. |  | 1.0 |
| has\_annex\_war\_goal | `<scope> / <variable>`  
The country to check for. | 

```
has_annex_war_goal = GER
```

 | Checks if the current scope has the Annex wargoal against the specified country. |  | 1.0 |
| any\_claim | `<bool>`  
Boolean. | 

```
any_claim = yes
```

 | Checks if the current scope has any claims on another country. |  | 1.0 |
| is\_in\_peace\_conference | `<bool>`  
Boolean. | 

```
is_in_peace_conference = yes
```

 | Checks if the current scope is in a peace conference. | Please test this in-game for 1.12. | 1.0 |
| controls\_province | `<id>`  
The province to check for. | 

```
controls_province = 1239
```

 | Checks if the current scope has control of the specified province. |  | 1.9 |
| longest\_war\_length | `<int>`  
Amount of months. | 

```
longest_war_length > 3
```

 | Checks how long a country has been at war, in months. |  | 1.14 |
| war\_length\_with | `tag = <scope> / <variable>`  
Target country.

`months = <int>`  
Amounth of months.

 | 

```
war_length_with = {
    tag = GER
    months > 3
}
```

 | Checks how long a country has been at war with specific country, in months. |  | 1.14 |
| has\_truce\_with | `<scope> / <variable>`  
The country to check for. | 

```
has_truce_with = GER
```

 | Checks if the country has truce with the specified country. |  | 1.16 |
| has\_naval\_control | `<id> / <variable>`  
The region to check in. | 

```
has_naval_control = 16
```

 | Checks if friendly nations and country scope together has enough naval dominance to assert control in strategic region. |  | 1.17 |
| has\_enemy\_naval\_control | `<id> / <variable>`  
The region to check in. | 

```
has_enemy_naval_control = 16
```

 | Checks if any enemy has enough naval dominance to assert control in certain strategic region. |  | 1.17 |

### State\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=23 "Edit section: State") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=23 "Edit section: State")\]

These are state-related triggers in the country scope, not [state-scoped triggers](https://hoi4.paradoxwikis.com/Triggers#State_scope).

State-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| controls\_state | `<scope> / <variable>`  
The state to check for. | 
```
controls_state = 39
```

```
controls_state = var:state
```

 | Checks if the current scope has control of the specified state. |  | 1.0 |
| owns\_state | `<scope> / <variable>`  
The state to check for. | 

```
owns_state = 39
```

 | Checks if the current scope owns the specified state. |  | 1.0 |
| num\_of\_controlled\_states | `<int>`  
The amount to check for. | 

```
num_of_controlled_states > 5
```

 | Checks if the current scope has the specified amount of controlled states. | Must use either > or < operators. | 1.0 |
| num\_occupied\_states | `<int>`  
The amount to check for. | 

```
num_occupied_states > 5
```

 | Checks if the current scope has the specified amount of occupied states. | Must use either > or < operators. | 1.0 |
| has\_full\_control\_of\_state | `<scope> / <variable>`  
The state to check for. | 

```
has_full_control_of_state = 39
```

 | Checks if the current scope has total control (100% occupation) of the specified state. |  | 1.3 |
| has\_resources\_rights | `state = <scope> / <variable>`  
The state to check in. Mandatory if used in country scope.

`resources = { <resource> <...> <resource> }`  
Resources to check for. Optional, defaults to any if unset.

 | 

```
has_resources_rights = {
  state = 123
  resources = { oil steel }
}
```

 | Checks if there are any resource rights with the specified parameters. | Can be used in either state or country scope. Always returns false if the state has no resources.

[Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_has_resources_rights)

 | 1.12 |
| core\_compliance | `occupied_country_tag = <TAG>`  
The country for which to check compliance.

`value = <int>`  
The value to check for.  


 | 

```
core_compliance = {
    occupied_country_tag = ITA
    value > 10
}

```

 | Compares the average compliance of core states of the specified country within controlled states of the current scope. | Must use either > or < operators for value. | 1.9 |
| core\_resistance | `occupied_country_tag = <TAG>`  
The country for which to check resistance.

`value = <int>`  
The value to check for.  


 | 

```
core_resistance = {
    occupied_country_tag = ITA
    value > 10
}

```

 | Compares the average resistance of core states of the specified country within controlled states of the current scope. | Must use either > or < operators for value. | 1.9 |
| garrison\_manpower\_need | `<int>`  
Amount to check. | 

```
garrison_manpower_need > 10000
```

 | Checks how much garrison manpower we need for resistance in controlled states. | Must use either > or < operators. | 1.9 |
| has\_core\_occupation\_modifier | `occupied_country_tag = <scope> / <variable>`  
The country to check.

`modifier = <token>`The modifier to check.

 | 

```
has_core_occupation_modifier = {
  occupied_country_tag = ITA
  modifier = token
}
```

 | Checks if the current scope has an occupation modifier for resistance/compliance that applies to our occupied states of a specified country. |  | 1.9 |
| occupation\_law | `<law ID>`  
The law to check. | 

```
POL = {
  POL = {
    occupation_law = foreign_civilian_oversight
  }
}
```

\# Checks POL's default occupation law

```
HOL = {
  BEL = {
    occupation_law = foreign_civilian_oversight
  }
}
```

\# Checks HOL's occupation law over BEL | Checks the occupation law that's either the default or applied over a specific country. | Checks [PREV's](https://hoi4.paradoxwikis.com/Scopes#PREV_usage "Scopes") occupation law over the current country. If they're the same scope, checks the default occupation law.

[Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_occupation_law)

 | 1.12 |
| has\_contested\_owner | `<state> / <variable>`  
State to check. | 

```
has_contested_owner = 42
```

 | Checks if a state has the specified country as a contested owner. The trigger can be used either from a country or a state scope and accepts the other as parameter. | [Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_has_contested_owner) | 1.15 |
| owns\_any\_state\_of | `<states>`  
States to check. | 

```
owns_any_state_of = {
  123
  246
}
```

 | Check if the country owns any of the states in the list. | The same as:

```
OR = {
  owns_state = 123
  owns_state = 246
}
```

 | 1.16 |
| is\_on\_same\_continent\_as | `<scope> / <variable>`  
The state to check for. | 

```
is_on_same_continent_as = 111
```

 | Checks if the scope country is on the same continent as the given state. The capital state is used for given country tag. | [Can also be used in state scope.](https://hoi4.paradoxwikis.com/Triggers#s_is_on_same_continent_as) | 1.17 |

### Military\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=24 "Edit section: Military") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=24 "Edit section: Military")\]

Military-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_army\_experience | `<float> / <variable>`  
The amount to check for. | 
```
has_army_experience > 10
```

```
has_army_experience > var:number
```

 | Checks if the current scope has the specified amount of Army experience. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.3 |
| has\_air\_experience | `<float> / <variable>`  
The amount to check for. | 

```
has_air_experience > 10
```

 | Checks if the current scope has the specified amount of Air experience. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.3 |
| has\_navy\_experience | `<float> / <variable>`  
The amount to check for. | 

```
has_navy_experience < 10
```

 | Checks if the current scope has the specified amount of Navy experience. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.3 |
| has\_manpower | `<float> / <variable>`  
The amount to check for. | 

```
has_manpower > 1000
```

 | Checks if the current scope has the specified amount of manpower. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.0 |
| has\_army\_manpower | `size = <int>`  
The amount to check for. | 

```
has_army_manpower = {
    size > 1000
}

```

 | Checks if the current scope has an army using the specified amount of manpower. | Must use either > or < operators. | 1.0 |
| manpower\_per\_military\_factory | `<float>`  
The amount to check for. | 

```
manpower_per_military_factory > 1000
```

 | Checks if the current scope has the specified manpower times their number of military factories. | Must use either > or < operators. | 1.0 |
| conscription\_ratio | `<float> / <variable>`  
The ratio to compare with. | 

```
conscription_ratio < 0.2
```

 | Checks if the current scope has the specified conscription ratio currently, not to be mixed up with the target conscription ratio. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.9 |
| current\_conscription\_amount | `<float> / <variable>`  
The amount to compare with. | 

```
current_conscription_amount > 2000
```

 | Checks if the current scope has already conscripted that much manpower. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.9 |
| target\_conscription\_amount | `<float> / <variable>`  
The amount to compare with. | 

```
target_conscription_amount > 2000
```

 | Checks if the current scope is targeting to conscript that much manpower. | **Must** use either > or < operators as = operator checks for the **exact** value | 1.9 |
| num\_divisions | `<int>`  
The amount to check for. | 

```
num_divisions > 5
```

 | Checks if the current scope has the specified amount of divisions. | Must use either > or < operators. | 1.3 |
| num\_of\_nukes | `<int>`  
The amount to check for. | 

```
num_of_nukes > 5
```

 | Checks if the current scope has the specified amount of nukes. | Must use either > or < operators. | 1.0 |
| casualties | `<int>`  
The amount to check for. | 

```
casualties > 10000
```

 | Checks if the current scope has suffered the specified amount of casualties. | Must use either > or < operators. | 1.0 |
| casualties\_k | `<int>`  
The amount to check for. | 

```
casualties_k > 10
```

 | Checks if the current scope has suffered the specified amount of casualties in thousands. | Must use either > or < operators. | 1.0 |
| casualties\_inflicted\_by | `opponent = <tag>`  
The tag that inflicted the casualties.

`thousands <> <int>`  
The amount of casualties in thousands.

 | 

```
casualties_inflicted_by = {
    opponent = POL
    thousands > 10
}
```

 | Checks if the current scope has suffered the specified amount of casualties in thousands from a specific country. | Must use either > or < operators for thousands. | 1.6 |
| amount\_manpower\_in\_deployment\_queue | `<float>`  
The amount to check for. | 

```
amount_manpower_in_deployment_queue > 1000
```

 | Checks if the current scope has the specified amount of manpower in their deployment queue. | Must use either > or < operators. | 1.5 |
| has\_attache\_from | `<scope> / <variable>`  
The country to check for. | 

```
has_attache_from = GER
```

 | Checks if the current scope has an attache from the specified scope. |  | 1.5 |
| has\_attache | `<bool>`  
Boolean. | 

```
has_attache = yes
```

 | Checks if the current scope has an attache. |  | 1.5 |
| is\_lend\_leasing | `<scope> / <variable>`  
The country to check for. | 

```
is_lend_leasing = GER
```

 | Checks if the current scope is lend leasing to the specified scope. |  | 1.0 |
| has\_template | `<string>`  
The name of the template. | 

```
has_template = "Infantry Division"
```

 | Checks if the current scope has a division template of the specified name. |  | 1.0 |
| has\_template\_majority\_unit | `<string>`  
The unit to check for. | 

```
has_template_majority_unit = infantry
```

 | Checks if the current scope has a division template composed mostly of the specified unit. |  | 1.0 |
| has\_template\_containing\_unit | `<string>`  
The name of the unit. | 

```
has_template_containing_unit = light_armor
```

 | Checks if the current scope has a division template contained any of the specified unit. |  | 1.0 |
| strength\_ratio | `tag = <scope>`  
The country to check for.

`ratio <> <float>`  
The ratio to check for.

 | 

```
strength_ratio = {
    tag = GER
    ratio > 1
}

```

 | Checks if the current scope has the specified strength ratio against the specified country. The ratio is the number of fielded divisions of the current scope divided by those of `tag` (or 1 if `tag` has no divisions). The ratio gets increased by 10% if the current scope has a stronger air forces.<sup id="cite_ref-3"><a href="https://hoi4.paradoxwikis.com/Triggers#cite_note-3">[3]</a></sup> | Must use > or < in the ratio. | 1.0 |
| fighting\_army\_strength\_ratio | `tag = <scope>`  
The country to check for.

`ratio <>= <float> / <variable>`  
The ratio to check for.

 | 

```
fighting_army_strength_ratio = {
    tag = GER
    ratio > 0.7
}

```

 | Compares the total army fighting strength between the scope country and the one set with 'tag'. | Ratio can be '<','>' or '='. | 1.15 |
| naval\_strength\_ratio | `tag = <scope>`  
The country to check for.

`ratio <> <float>`  
The ratio to check for.

 | 

```
naval_strength_ratio = {
    tag = GER
    ratio <> 1
}

```

 | Checks if the current scope has the specified naval strength ratio against the specified country. | Must use > or < in the ratio. | 1.0 |
| naval\_strength\_comparison | `other = <scope>`  
The country to check for.

`tooltip = <string>`  
The ratio to check for. Optional.  
`ratio <> <float>`  
The ratio to check for.  
`sub_unit_def_weights = { ... }` The weight to assign to each unit. Optional.

 | 

```
naval_strength_comparison = {
    other = POL
    tooltip = my_loc_key_tt
    ratio > 1
    sub_unit_def_weights = {
        carrier = 1
        submarine = 2
    }
}

```

 | Checks if the current scope has the specified naval strength ratio against the specified country. | Must use > or < in the ratio. If sub\_unit\_def\_weights is unset, each unit is assumed to have 1 weight. If sub\_unit\_def\_weights is set, only specified units will be counted towards strength. Units are defined in /Hearts of Iron IV/common/units/\*.txt. | 1.6 |
| alliance\_strength\_ratio | `<float> / <variable>`  
The ratio to check for. | 

```
alliance_strength_ratio > 0.5
```

 | Checks if the current scope and allies has an army strength higher than the specified ratio against estimated enemy strength. | Must use either > or < operators. | 1.0 |
| alliance\_naval\_strength\_ratio | `<float> / <variable>`  
The ratio to check for. | 

```
alliance_naval_strength_ratio > 0.5
```

 | Checks if the current scope and allies has an naval strength ratio higher than the specified ratio against estimated enemy strength. | Must use either > or < operators. | 1.0 |
| enemies\_strength\_ratio | `<float> / <variable>`  
The ratio to check for. | 

```
enemies_strength_ratio > 0.5
```

 | Checks if the estimated enemy army strength ratio is higher than the specified ratio. | Must use either > or < operators. | 1.0 |
| enemies\_naval\_strength\_ratio | `<float> / <variable>`  
The ratio to check for. | 

```
enemies_naval_strength_ratio > 0.5
```

 | Checks if the estimated enemy naval strength ratio is higher than the specified ratio. | Must use either > or < operators. | 1.0 |
| has\_army\_size | `size = <float>`  
The amount to check for.

`type = <string>`  
The battalion type to check for. Divisions that are majority made up of battalions in that type count. Optional, counts all divisions by default.  


 | 

```
has_army_size = {
    size > 10
    type = armor
}

```

 | Checks if the current scope has the specified number of divisions, or of a specified type of division. | Battalion types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.0 |
| has\_navy\_size | `size = <float> / <variable>`  
The amount to check for.

`type = <string>`  
The type to check for. Optional.  
`archetype = <string>`  
The ship archetype to check for. Optional.  


 | 

```
has_navy_size = {
    size > 10
    type = capital_ship
    archetype = ship_hull_heavy
}

```

 | Checks if the current scope has the specified number of ships, or of a specified type of ship. | Ship types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. Ship archetypes are found in /Hearts of Iron IV/common/units/equipment/\*.txt files. | 1.0 |
| has\_deployed\_air\_force\_size | `size = <float>`  
The amount to check for.

`type = <string>`  
The type to check for. Optional.  


 | 

```
has_deployed_air_force_size = {
    size > 10
    type = cas
}

```

 | Checks if the current scope has the specified number of aircraft, or of a specified type of aircraft. | Airwing types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.0 |
| divisions\_in\_state | `size = <float>`  
The amount to check for.

`type = <string>`  
The battalion type to check for. Divisions that are majority made up of battalions in that type count. Optional, counts all divisions by default.  
`unit = <string>`  
The exact battalion to check for. Divisions that are majority made up of that battalions count. Optional, counts all divisions by default.  
`state = <scope> / <variable>`  
The state to check in.

 | 

```
divisions_in_state = {
    type = armor
    size > 10
    state = 49
}

```

 | Checks if the specified state contains the specified amount of divisions. | Battalions and their types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.0 |
| army\_manpower\_in\_state | `amount <> <float>`  
The amount to check for.

`type = <string>`  
The type to check for. Optional.  
`state = <scope> / <variable>`  
The state to check in.

 | 

```
army_manpower_in_state = {
    type = support
    amount > 10000
    state = 49
}

```

 | Checks if the specified state contains the specified amount of army manpower within the state. | Battalion types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.6 |
| divisions\_in\_border\_state | `size = <float>`  
The amount to check for.

`type = <string>`  
The battalion type to check for. Divisions that are majority made up of battalions in that type count. Optional, counts all divisions by default.  
`state = <scope> / <variable>`  
The state to check in.  
`border_state = <scope> / <variable>`  
The border state to check in.

 | 

```
divisions_in_border_state = {
    type = infantry
    size > 10
    state = 49
    border_state = var:state
}

```

 | Checks if the border provinces between the specified state and border state contain the specified amount of divisions. | Battalion types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.5 |
| num\_divisions\_in\_states | `count = <int>`  
The amount to check for.

`states = { <int> <...> <int> }`  
The states to check in.  
`types = { <string> <...> <string> }`  
The battalion types to check for. Divisions that are majority made up of battalions in that type count. Optional, counts all divisions by default.  
`exclude = { <string> <...> <string> }`  
The sub-units to exclude from the search. Divisions that are majority made up of specified battalions are excluded. Optional, excludes no divisions by default.

 | 

```
num_divisions_in_states = {
    count > 24
    states = { 550 559 271 }
    exclude = { irregular_infantry }
}

```

 | Checks if the specified states contain enough divisions of the specified types. | Divisions and their types are defined within /Hearts of Iron IV/common/units/\*.txt files. Can use either =, >, or < operators for count. The tooltip does not specify the states the check runs for nor the filtered types. | 1.12 |
| num\_battalions\_in\_states | `count = <int>`  
The amount to check for.

`states = { <int> <...> <int> }`  
The states to check in.  
`types = { <string> <...> <string> }`  
The battalion types to check for.  
`exclude = { <string> <...> <string> }`  
The sub-units to exclude from the search.

 | 

```
num_battalions_in_states = {
    count > 24
    states = { 550 559 271 }
    exclude = { irregular_infantry }
}

```

 | Checks if the specified states contain enough battalions (or sub-units) of the specified types. | Battalions and their types are defined within /Hearts of Iron IV/common/units/\*.txt files. Can use either =, >, or < operators for count. The tooltip does not specify the states the check runs for nor the filtered types. | 1.12 |
| ships\_in\_state\_ports | `size = <float>`  
The amount to check for.

`type = <string>`  
The type to check for. Optional.  
`state = <scope> / <variable>`  
The state to check in.  


 | 

```
ships_in_state_ports = {
    type = capital_ship
    size > 10
    state = 49
}

```

 | Checks if the specified state contains the specified amount of ships, or of ships of the specified type. | Ship types are defined within /Hearts of Iron IV/common/units/\*.txt files. Must use either > or < operators for size. | 1.0 |
| num\_planes\_stationed\_in\_regions | `value = <float>`  
The amount to check for.

`regions = { <id> <...> <id> }`  
The regions to check in.  


 | 

```
num_planes_stationed_in_regions = {
    value > 10
    regions = { 123 321 }
}

```

 | Checks if the current scope has the specified number of aircraft stationed within strategic regions. | Must use either =, >, or < operators for value. | 1.12 |
| has\_volunteers\_amount\_from | `tag = <scope>`  
The country to check for.

`count = <int>`  
The amount to check for.

 | 

```
has_volunteers_amount_from = {
    tag = GER
    count > 10
}

```

 | Checks if the current scope has recieved volunteers from the specified country of the specified amounts. | Must use either > or < operators for count. | 1.0 |
| convoy\_threat | `<float>`  
The threat to compate with. | 

```
convoy_threat > 0.5

```

 | Checks how much the convoys are threatened. | Must use either > or < operators for count. Threat is always between 0 and 1. | 1.6 |
| has\_mined | `target = <tag>`  
The country the coast of which is mined.

`value <> <int>`  
The amount of mines to compare with.

 | 

```
has_mined = {
    target = POL
    value > 1000
}
```

 | Checks if the current scope has X mines on the coast of the specified country. | Must use either > or < operators for value. | 1.6 |
| has\_mines | `region = <ID>`  
The strategic region that contains the mines.

`amount = <int>`  
The amount of mines to compare with.

 | 

```
has_mined = {
    target = POL
    amount = 1000
}
```

 | Checks if the current scope has at least X mines within the specified strategic region. |  | 1.6 |
| mine\_threat | `<float>`  
The threat to compate with. | 

```
mine_threat < 0.6
```

 | Checks how dangerous enemy mines are. | Must use either > or < operators for count. Threat is always between 0 and 1. | 1.6 |
| has\_military\_industrial\_organization | `<token>`  
The id to check for. | 

```
has_military_industrial_organization = infantry_mio_token
```

 | Checks if the current scope has a MIO with the specified name. | Accepts variables. | 1.13 |
| has\_tactic | `<tactic>`  
The tactic to check for. | 

```
has_tactic = tactic_masterful_blitz
```

 | Check if the given tactic is unlocked (or active by default) for the country. |  | 1.17 |

### Doctrine\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=25 "Edit section: Doctrine") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=25 "Edit section: Doctrine")\]

Doctrine-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_any\_grand\_doctrine | `<string>`  
Doctrine folder. | 
```
has_any_grand_doctrine = land
```

 | Checks if any grand doctrine in folder is currently active for the country. | Folders are land, naval and air. | 1.17.2 |
| has\_doctrine | `<grand doctrine> / <subdoctrine>`  
The doctrine to check for. | 

```
has_doctrine = mobile_warfare # Grand doctrine
```

```
has_doctrine = mobile_infantry # Subdoctrine
```

 | Checks if the given grand doctrine or subdoctrine is currently active for the country. |  | 1.17 |
| has\_subdoctrine\_in\_track | `<track>`  
The track to check for. | 

```
has_subdoctrine_in_track = infantry
```

 | Checks if any subdoctrine is currently assigned to (any instance of) the given track. |  | 1.17 |
| has\_completed\_subdoctrine | `<subdoctrine>`  
The subdoctrine to check for. | 

```
has_completed_subdoctrine = mobile_infantry
```

 | Checks if the current country has ever completed the specified subdoctrine (even if it was later switched out). |  | 1.17 |
| has\_completed\_track | `<track>`  
The track to check for. | 

```
has_completed_track = infantry
```

 | Checks if the given subdoctrine track has been completed |  | 1.17 |
| has\_mastery | `amount = <int>`  
The amout to check for.

`track = <track>`  
The track to check for.

 | 

```
has_mastery = {
    amount = 200
    track = infantry
}
```

 | Checks if any track of the given type has at least X mastery. |  | 1.17 |
| has\_mastery\_level | `amount = <int>`  
The amount to check for.

`subdoctrine = <subdoctrine>`  
The subdoctrine to check for.

 | 

```
has_mastery_level = {
    amount = 2
    subdoctrine = mobile_infantry
}
```

 | Checks if the country has reached the specified number of mastery levels (rewards) for the given subdoctrine. |  | 1.17 |

### Equipment\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=26 "Edit section: Equipment") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=26 "Edit section: Equipment")\]

Equipment-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| stockpile\_ratio | `archetype = <string>`  
The equipment archetype to check for.
`ratio = <float>`  
The ratio of equipment to check for.

 | 

```
stockpile_ratio = {
    archetype = infantry_equipment
    ratio > 0.5
}
```

 | Checks if the current scope has stockpiled the specified equipment to the specified ratio against fielded equipment of the same type. | Must use either > or < operators for ratio.  
For the convoy equipment which is not fielded as other equipments, ratio shall be not a percentage but a direct amount (for instance 256 convoys) | 1.5 |
| has\_equipment | `<equipment> = <int> / <variable>`  
The equipment to check for, and the amount to check for. | 

```
has_equipment = {
    infantry_equipment_1 > 10
}
```

 | Checks if the current scope has the specified equipment to the specified amount. | Must use either > or < operators. | 1.0 |
| has\_any\_license | `<bool>`  
Boolean. | 

```
has_any_license = yes
```

 | Checks if the current scope has any licenses from other countries. |  | 1.0 |
| is\_licensing\_any\_to | `<scope> / <variable>`  
The country to check for. | 

```
is_licensing_any_to = GER
```

 | Checks if the current scope is licensing to the specified scope. |  | 1.0 |
| is\_licensing\_to | `target = <scope>`  
The country to check for.

`archetype = <string>`  
The equipment archetype to check for. Optional.  
**Equipment scope**  
`type = <string>`  
The equipment to check for. Optional.  
`version = <int>`  
The variant id of the equipment. Optional.

 | 

```
is_licensing_to = {
    target = GER
    archetype = infantry_equipment
}
```

```
is_licensing_to = {
    target = GER
    equipment = {
        type = light_tank_equipment
        version = 1
    }
}
```

 | Checks if the current scope is licensing the specified equipment to the specified country. |  | 1.0 |
| has\_license | `from = <scope>`  
The country to check for.

`archetype = <string>`  
The equipment archetype to check for. Optional.  
**Equipment scope**  
`type = <string>`  
The equipment to check for. Optional.  
`version = <int>`  
The variant id of the equipment. Optional.

 | 

```
has_license = {
    from = GER
    archetype = infantry_equipment
}
```

```
has_license = {
    from = GER
    equipment = {
        type = light_tank_equipment
        version = 1
    }
}
```

 | Checks if the current scope has a license for the specified equipment from the specified country. |  | 1.0 |
| fuel\_ratio | `<float> / <variable>`  
The ratio to check with. | 

```
fuel_ratio > 0.4
```

 | Checks the fuel ratio of the country. | Must use either < or > operators. | 1.6 |
| has\_fuel | `<int> / <variable>`  
The amount to compare with. | 

```
has_fuel > 400
```

 | Checks the fuel amount of the country. | Must use either < or > operators. | 1.6 |
| has\_design\_based\_on | `<archetype>`  
The equipment archetype. | 

```
has_design_based_on = light_tank_chassis
```

 | Checks if the country has a builtable non-obsolete design based on the specified equipment archetype. | Equipment archetypes can be seen in /Hearts of Iron IV/common/units/equipment/\*. | 1.11 |

### Intelligence\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=27 "Edit section: Intelligence") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=27 "Edit section: Intelligence")\]

Intelligence-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| estimated\_intel\_max\_piercing | `tag = <scope>`  
The country to check for.
`value = <int>`  
The amount to check for.

 | 

```
estimated_intel_max_piercing = {
    tag = GER
    value > 2
}
```

 | Checks if the specified scope has the specified amount of piercing based on the current scope's intel. | Must use either > or < operators for value. | 1.0 |
| estimated\_intel\_max\_armor | `tag = <scope>`  
The country to check for.

`value = <int>`  
The amount to check for.

 | 

```
estimated_intel_max_armor = {
    tag = GER
    value > 2
}
```

 | Checks if the specified scope has the specified amount of armor based on the current scope's intel. | Must use either > or < operators for value. | 1.0 |
| compare\_intel\_with | `target = <tag> / <variable>`  
The target to compare with.

`civilian_intel <>= <float> / <variable>`  
Comparison of civilian intel.  
`army_intel <>= <float> / <variable>`  
Comparison of army intel.  
`navy_intel <>= <float> / <variable>`  
Comparison of navy intel.  
`airforce_intel <>= <float> / <variable>`  
Comparison of airforce intel.  


 | 

```
compare_intel_with = { 
    target = POL 
    civilian_intel > 0.5
    army_intel = 0
    navy_intel < 0
}
```

 | Compares intel between 2 countries. | Can use < (in which case the current country has x less intel), >, and = (in which case it must be equal). | 1.9 |
| intel\_level\_over | `target = <tag> / <variable>`  
The target to compare with.

`civilian_intel <>= <float> / <variable>`  
Comparison of civilian intel.  
`army_intel <>= <float> / <variable>`  
Comparison of army intel.  
`navy_intel <>= <float> / <variable>`  
Comparison of navy intel.  
`airforce_intel <>= <float> / <variable>`  
Comparison of airforce intel.  


 | 

```
intel_level_over = { 
    target = POL 
    civilian_intel > 0.5
    army_intel = 0
    navy_intel < 0
}
```

 | Checks the intel level from the current country over a specified country. | Can use < (in which case the current country has x less intel), >, and = (in which case it must be equal). | 1.9 |
| has\_intelligence\_agency | `<boolean>`  
The intelligence agency to check.  
 | 

```
has_intelligence_agency = yes
```

 | Checks if the current scope has an intelligence agency. |  | 1.9 |
| network\_national\_coverage | `target = <tag> / <variable>`  
The country which is checked.

`value <> <float> / <variable>`  
The value of network.

 | 

```
network_national_coverage = {
    target = POL
    value < 70
}
```

 | Checks network national coverage over a specific country. | Must use < or > for value. |
| network\_strength | `target = <tag>`  
The country which is checked.

`state = <id> / <variable>`  
The state which is checked.  
`value <> <float> / <variable>`  
The strength of network.

 | 

```
network_strength = {
    target = POL
    value < 70
}
```

 | Checks network national coverage over a specific country. | Must use < or > for value. Can use either or both of target and state. | 1.9 |
| has\_done\_agency\_upgrade | `<string>`  
The agency upgrade to check. | 

```
has_done_agency_upgrade = upgrade_army_department
```

 | Checks if the current scope has the specified agency upgrade (to its highest level). |  | 1.9 |
| agency\_upgrade\_number | `<int> / <variable>`  
The amount of agency upgrades to check for. | 

```
agency_upgrade_number > 4
```

 | Checks the number of upgrades done in the current scope's intelligence agency. | Must use either > or < operators. | 1.9 |
| decryption\_progress | `target = <tag>`  
The country to compare with.

`value <> <float>`  
The value to compare.

 | 

```
decryption_progress = {
    target = POL
    value < 0.5
}
```

 | Checks the decryption progress towards a country. | Must use either > or < operators for value. | 1.9 |
| has\_captured\_operative | `<tag>/<bool>`  
Country whose operative was captured/Whether an operative was captured. | 

```
has_captured_operative = POL
```

```
has_captured_operative = yes
```

 | Checks if the current scope has captured an operative. |  | 1.9 |
| has\_finished\_collecting\_for\_operation | `target = <tag>`  
Country towards whom the operation is targeted.

`operation = <token>`  
The operation which current scope is planning against the target.

 | 

```
has_finished_collecting_for_operation = {
    target = POL
    operation = operation_infiltrate_armed_forces_navy
}
```

 | Checks if the current scope has finished collecting resources for an operation. |  | 1.9 |
| is\_preparing\_operation | `target = <tag>`  
Country towards whom the operation is targeted.

`operation = <token>`  
The operation which current scope is planning against the target. Optional.

 | 

```
is_preparing_operation = {
    target = POL
    operation = operation_infiltrate_armed_forces_navy
}
```

 | Checks if the current scope is preparing an operation against the specified country. |  | 1.9 |
| is\_running\_operation | `target = <tag>`  
Country towards whom the operation is targeted.

`operation = <token>`  
The operation which current scope is planning against the target. Optional.

 | 

```
is_running_operation = {
    target = POL
    operation = operation_infiltrate_armed_forces_navy
}
```

 | Checks if the current scope is running an operation against the specified country. |  | 1.9 |
| num\_finished\_operations | `target = <tag>`  
Country towards whom the operation is targeted.

`operation = <token>`  
The operation which current scope is planning against the target. Optional.

 | 

```
num_finished_operations = {
    target = POL
    operation = operation_infiltrate_armed_forces_navy
}
```

 | Checks how many finished operations the current scope had against the specified country. |  | 1.9 |
| has\_operation\_token | `tag = <tag>`  
Country towards whom the operation is targeted.

`token = <token>`  
The operation token.

 | 

```
has_operation_token = {
    tag = POL
    token = token_name
}
```

 | Checks if the current scope has an operation token against an another country. |  | 1.9 |
| is\_active\_decryption\_bonuses\_enabled | `<tag>`  
The country towards which the bonus is enabled. | 

```
is_active_decryption_bonuses_enabled = POL
```

 | Checks if the current scope has any decryption bonuses towards the specified country. |  | 1.9 |
| is\_cryptology\_department\_active | `<bool>`  
Boolean. | 

```
is_cryptology_department_active = yes
```

 | Checks if the current scope has a cryptology department active. |  | 1.9 |
| is\_decrypting | `<tag>`  
The country which is decrypted. | 

```
is_decrypting = POL
```

 | Checks if the current scope is decrypting a certain country. |  | 1.9 |
| is\_fully\_decrypted | `<tag>`  
The country which is decrypted. | 

```
is_fully_decrypted = POL
```

 | Checks if the current scope has fully decrypted a certain country. |  | 1.9 |
| num\_fake\_intel\_divisions | `<int>`  
Amount of divisions. | 

```
num_fake_intel_divisions > 10
```

 | Checks the amount of fake intel divisions. | Must use either < or >. | 1.9 |
| num\_free\_operative\_slots | `<int>`  
Amount of slots. | 

```
num_free_operative_slots > 2
```

 | Checks the amount of free operative slots. | Must use either < or >. | 1.9 |
| num\_operative\_slots | `<int>`  
Amount of slots. | 

```
num_operative_slots > 2
```

 | Checks the amount of operative slots. | Must use either < or >. | 1.9 |
| num\_of\_operatives | `<int>`  
Amount of operatives. | 

```
num_of_operatives > 2
```

 | Checks the amount of operatives. | Must use either < or >. | 1.9 |

### AI\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=28 "Edit section: AI") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=28 "Edit section: AI")\]

AI-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| ai\_irrationality | `<int>`  
The amount to check for. | 
```
ai_irrationality > 10
```

 | Checks if the current scope AI has the specified irrationality. | Must use either > or < operators. | 1.0 |
| ai\_liberate\_desire | `target = <scope>`  
The country to check for.

`count = <float>`  
The amount to check for.

 | 

```
ai_liberate_desire = {
    target = GER
    count > 1
}

```

 | Checks if the current scope AI has the specified liberation desire towards the specified country. | Must use either > or < operators for count. | 1.0 |
| ai\_has\_role\_division | `<string>`  
The role to check for. | 

```
ai_has_role_division = infantry
```

 | Checks if the current scope AI has a division with the specified role. | Roles are defined in /Hearts of Iron IV/common/ai\_templates/\*.txt | 1.0 |
| ai\_has\_role\_template | `<string>`  
The role to check for. | 

```
ai_has_role_template = armor
```

 | Checks if the current scope AI has a division template with the specified role. | Roles are defined in /Hearts of Iron IV/common/ai\_templates/\*.txt | 1.0 |
| ai\_wants\_divisions | `<int>`  
The amount to check for. | 

```
ai_wants_divisions > 10
```

 | Checks if the current scope AI desires the specified amount of divisions. | Must use either > or < operators. | 1.0 |
| has\_template\_ai\_majority\_unit | `<string>`  
The unit to check for. | 

```
has_template_ai_majority_unit = infantry
```

 | Checks if the current scope AI has a division template mostly made up of the specified unit. |  | 1.0 |

### Characters\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=29 "Edit section: Characters") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=29 "Edit section: Characters")\]

These are character-related triggers in the country scope, not [character-scoped triggers](https://hoi4.paradoxwikis.com/Triggers#Character_scope).

Character-related country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| can\_be\_country\_leader | `<character>`  
The character to check. | 
```
can_be_country_leader = POL_character_test
```

 | Checks if the specified character has a country leader role, active or not, and can utilise it in this country. |  | 1.11 |
| has\_character | `<string>`  
The character to check. | 

```
has_character = my_character
```

 | Checks if the current scope has the specified character recruited. The character does NOT need to be in power. |  | 1.11 |
| has\_country\_leader | `ruling_only = <bool>`(default = yes) Limit check to ruling only.

`character = <character_token>` (recommended criteria) The character to check for. Optional.  
`name = <string>`  
The name to check for. Optional.  
`id = <int>`  
The id to check for. Optional.  


 | 

```
has_country_leader = {
    id = 10
}

```

```
has_country_leader = {
character = SPR_niceto_alcala_zamora
ruling_only = yes
}


```

```
has_country_leader = {
    name = "John Smith"
    ruling_only = yes
}

```

 | Checks if the current scope has the specified country leader. |  | 1.3 |
| has\_country\_leader\_ideology | <ideology>

Checks the ideology of the active country leader

 | 

```
has_country_leader_ideology = nazism
```

 | Checks if the current scope's active country leader has the specified ideology. |  | 1.11 |
| has\_country\_leader\_with\_trait | `<string>`  
The trait to check. | 

```
has_country_leader_with_trait = champion_of_peace_1
```

 | Checks if the leader of the country has a specific trait. |  | 1.6 |
| is\_female | `<bool>`  
Boolean. | 

```
is_female = yes
```

 | Checks if the current country leader is female. |  | 1.9 |
| has\_unit\_leader | `<int>`  
The id to check for. | 

```
has_unit_leader = 1
```

 | Checks if the current scope has a unit leader with the specified id. | Only the legacy ID can be used, the character ID doesn't work. | 1.0 |
| has\_scientist\_specialization | `specialization = <specialization_token>`  
Specialization. | 

```
has_scientist_specialization = specialization_nuclear
```

 | Checks if the country in scope has a scientist with a skill level of at least 1 in specialization. |  | 1.15 |

### Peace conferences\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=30 "Edit section: Peace conferences") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=30 "Edit section: Peace conferences")\]

These are not exactly peace conference-related triggers, but **those that can only be used within peace conferences**.

Peace conference-only country-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| pc\_is\_winner | `<bool>`  
Boolean. | 
```
pc_is_winner = yes
```

 | Checks if the current scope is a winner within the peace conference. |  | 1.12 |
| pc\_is\_on\_winning\_side | `<bool>`  
Boolean. | 

```
pc_is_on_winning_side = yes
```

 | Checks if the current scope is on the winning side within the peace conference. |  | 1.12 |
| pc\_is\_loser | `<bool>`  
Boolean. | 

```
pc_is_loser = yes
```

 | Checks if the current scope is a loser within the peace conference. |  | 1.12 |
| pc\_is\_untouched\_loser | `<bool>`  
Boolean. | 

```
pc_is_untouched_loser = yes
```

 | Checks if the current scope is an untouched loser within the peace conference. |  | 1.12 |
| pc\_is\_on\_same\_side\_as | `<scope>`  
Country to check for. | 

```
pc_is_on_same_side_as = BHR
```

 | Checks if the current scope is on the same side of the peace conference as the specified country. |  | 1.12 |
| pc\_is\_liberated | `<bool>`  
Boolean. | 

```
pc_is_liberated = yes
```

 | Checks if the current scope has been liberated within the peace conference. |  | 1.12 |
| pc\_is\_liberated\_by | `<scope>`  
Country to check for. | 

```
pc_is_liberated_by = BHR
```

 | Checks if the current scope has been liberated within the peace conference by the specified country. |  | 1.12 |
| pc\_is\_puppeted | `<bool>`  
Boolean. | 

```
pc_is_puppeted = yes
```

 | Checks if the current scope has been puppeted within the peace conference. |  | 1.12 |
| pc\_is\_puppeted\_by | `<scope>`  
Country to check for. | 

```
pc_is_puppeted_by = BHR
```

 | Checks if the current scope has been puppeted within the peace conference by the specified country. |  | 1.12 |
| pc\_is\_forced\_government | `<bool>`  
Boolean. | 

```
pc_is_forced_government = yes
```

 | Checks if the current scope has had an enforced government change within the peace conference. |  | 1.12 |
| pc\_is\_forced\_government\_by | `<scope>`  
Country to check for. | 

```
pc_is_forced_government_by = BHR
```

 | Checks if the current scope has had an enforced government change within the peace conference demanded by the specified country. |  | 1.12 |
| pc\_is\_forced\_government\_to | `<ideology group>`  
Ideology group to check for. | 

```
pc_is_forced_government_to = democratic
```

 | Checks if the current scope has had an enforced government change to the specified ideology group. |  | 1.12 |
| pc\_total\_score | `<decimal>`  
Scope to check for. | 

```
pc_total_score > 2400
```

 | Checks if the current scope has the specified amount in total score within the peace conference. | Can only be used for the winning countries. | 1.12 |
| pc\_current\_score | `<decimal>`  
Scope to check for. | 

```
pc_current_score > 100
```

 | Checks if the current scope has the specified amount in current score within the peace conference. | Can only be used for the winning countries. | 1.12 |

## Faction scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=31 "Edit section: Faction scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=31 "Edit section: Faction scope")\]

Can be used in **faction** scope.

There are currently no faction-specific triggers.

## State scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=32 "Edit section: State scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=32 "Edit section: State scope")\]

Can be used in **state** scope.

### General\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=33 "Edit section: General") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=33 "Edit section: General")\]

General state-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| state | `<scope> / <variable>`  
The state to check for. | 
```
state = 10
```

```
state = var:state
```

 | Checks if the current scope is the specified state. |  | 1.0 |
| region | `<int>`  
The strategic region id to check for. | 

```
region = 10
```

 | Checks if the current scope is a state in the specified strategic region. |  | 1.0 |
| <building> (building\_count\_trigger) | `<int>`  
The amount of the specified building to check for. | 

```
arms_factory > 10
```

 | Checks if the current scope has the specified amount of the specified building. | Must use either > or < operators.

[Can also be used in building scope.](https://hoi4.paradoxwikis.com/Triggers#building_count_trigger)

 | 1.0 |
| free\_building\_slots | `building = <string>`  
The building to check for.

`size = <int>`  
The amount to check for.  
`include_locked = <bool>`  
Whether to include locked slots.

 | 

```
free_building_slots = {
    building = arms_factory
    size > 10
    include_locked = yes
}

```

 | Checks if the current scope has available slots for the specified amount of buildings. | Must use either > or < operators for size. | 1.0 |
| non\_damaged\_building\_level | `building = <string>`  
The building to check for.

`level = <int>`  
The amount to check for.  


 | 

```
non_damaged_building_level = {
    building = arms_factory
    level > 4
}

```

 | Checks if the current scope has the specified amount of the specified buildings that are undamaged. | Must use either > or < operators for level. | 1.9 |
| any\_province\_building\_level | `building = <string>`  
The building to check for.

`limit = <int>`  
The amount to check for.  
**Province scope**  
`id = <int>`  
The province to check for.  
`limit_to_border = <bool>`  
Whether to limit check to border provinces.

 | 

```
any_province_building_level = {
    province = {
        id = 445
        id = 494
        limit_to_border = yes
    }
    building = bunker
    level < 5
}

```

 | Checks if the current scope has the specified provincal building at the specified amount in the specified provinces. | Must use either > or < operators for level. | 1.0 |
| has\_state\_flag | `<string>`  
The flag to check for. | 

```
has_state_flag = my_flag
```

 | Checks if the current scope has the specified flag. |  | 1.0 |
| has\_state\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_state_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.0 |
| state\_population | `<float>`  
The amount to check for. | 

```
state_population > 10000
```

 | Checks if the current scope has the specified state population. | Must use either > or < operators. | 1.0 |
| state\_population\_k | `<float>`  
The amount to check for. | 

```
state_population_k > 10
```

 | Checks if the current scope has the specified state population in thousands. | Must use either > or < operators. | 1.0 |
| is\_capital | `<bool>`  
Boolean. | 

```
is_capital = yes
```

 | Checks if the current scope is a capital. |  | 1.5 |
| is\_controlled\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_controlled_by = GER
```

 | Checks if the current scope is controlled by the specified country. |  | 1.0 |
| is\_fully\_controlled\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_fully_controlled_by = GER
```

 | Checks if the current scope is fully controlled by the specified country. |  | 1.5 |
| is\_owned\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_owned_by = GER
```

 | Checks if the current scope is owned by the specified country. |  | 1.0 |
| is\_claimed\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_claimed_by = GER
```

 | Checks if the current scope is claimed by the specified country. |  | 1.0 |
| is\_core\_of | `<scope> / <variable>`  
The country to check for. | 

```
is_core_of = GER
```

 | Checks if the current scope is a core of the specified country. |  | 1.0 |
| is\_owned\_and\_controlled\_by | `<scope> / <variable>`  
The country to check for. | 

```
is_owned_and_controlled_by = GER
```

 | Checks if the current scope is owned and controlled by the specified country. |  | 1.0 |
| is\_demilitarized\_zone | `<bool>`  
Boolean. | 

```
is_demilitarized_zone = yes
```

 | Checks if the current scope is a demilitarized zone. |  | 1.0 |
| is\_border\_conflict | `<bool>`  
Boolean. | 

```
is_border_conflict = yes
```

 | Checks if the current scope is part of a border war. |  | 1.0 |
| is\_in\_home\_area | `<bool>`  
Boolean. | 

```
is_in_home_area = yes
```

 | Checks if the current scope is connected to the capital state over land. The scope needs to be owned as well for the statement for it to be true. |  | 1.0 |
| is\_coastal | `<bool>`  
Boolean. | 

```
is_coastal = yes
```

 | Checks if the current scope is a coastal state. |  | 1.0 |
| is\_one\_state\_island | `<bool>`  
Boolean. | 

```
is_one_state_island = yes
```

 | Checks if the current scope is a coastal state with no adjacent land states. | An adjacent land state may be connected via a naval crossing. | 1.13 |
| is\_island\_state | `<bool>`  
Boolean. | 

```
is_island_state = yes
```

 | Checks if the current scope is a state where every province has no land neighbour. | An adjacent land division may be connected via a naval crossing. | 1.0 |
| is\_on\_continent | `<string>`  
The continent to check for. | 

```
is_on_continent = europe
```

 | Checks if the current scope is on the specified continent. | Continents are found in /Hearts of Iron IV/map/continent.txt. | 1.0 |
| is\_on\_same\_continent\_as | `<scope> / <variable>`  
The country to check for. | 

```
is_on_same_continent_as = FRA
```

 | Checks if the scope state is on the same continent as the given state. The capital state is used for given country tag. | [Can also be used in country scope.](https://hoi4.paradoxwikis.com/Triggers#is_on_same_continent_as) | 1.17 |
| impassable | `<bool>`  
Boolean. | 

```
impassable = yes
```

 | Checks if the current scope is impassable. |  | 1.9.1 |
| has\_state\_category | `<string>`  
The category to check for. | 

```
has_state_category = rural
```

 | Checks if the current scope has the specified category. | State categories are found in /Hearts of Iron IV/common/state\_category/\*.txt. | 1.0 |
| state\_strategic\_value | `<int>`  
The amount to check for. | 

```
state_strategic_value > 10
```

 | Checks if the current scope has the specified strategic value. | Must use either > or < operators. | 1.5 |
| state\_and\_terrain\_strategic\_value | `<int>`  
The amount to check for. | 

```
state_and_terrain_strategic_value > 10
```

 | Checks if the current scope has the specified state and terrain strategic value. | Must use either > or < operators. | 1.5 |
| num\_owned\_neighbour\_states | `owner = <scope>`  
The country to check for.

`count = <int>`  
The amount to check for.

 | 

```
num_owned_neighbour_states = {
    owner = GER
    count > 2
}

```

 | Checks if the current scope has the specified amount of neighbor states belonging to the specified country. | Must use either > or < operators for count. | 1.0 |
| distance\_to | `value = <float>`  
The distance to check for.

`target = <scope>`  
The state to compare against.

 | 

```
distance_to = {
    value > 1000
    target = 49
}

```

 | Checks if the current scope is at the specified distance from the specified state. | Must use either > or < operators for distance. | 1.0 |
| ships\_in\_area | `area = <int>`  
The strategic region to check for.

`size = <int>`  
The amount to check for.

 | 

```
ships_in_area = { area = 104 size > 14 } 
```

 | Checks if the current scope has the specified amount of ships in the specified strategic region. | Must use either > or < operators for count. | 1.0 |
| <resource> (resource\_count\_trigger) | `<int>`  
The amount to check for. | 

```
tungsten > 10

```

 | Checks if the current scope has the specified amount of the specified resource. | Must use either > or < operators for amount.

[Can also be used in country scope.](https://hoi4.paradoxwikis.com/Triggers#resource_count_trigger)

 | ??? |
| has\_resources\_amount | `resource = <string>`  
The resource to check for.

`amount = <int>`  
The amount to check for.  
`delivered = <bool>`  
If specified, checks the amount after the modifiers are applied rather than the base resource value.

 | 

```
has_resources_amount = {
    resource = oil
    amount > 10
    delivered = yes
}

```

 | Checks if the current scope has the specified amount of the specified resource. | Must use either > or < operators for amount. | 1.3 |
| has\_resources\_rights | `receiver = <scope>`  
The receiver of the resource rights. Mandatory if used in state scope.

`resources = { <resource> <...> <resource> }`  
Resources to check for. Optional, defaults to any if unset.

 | 

```
has_resources_rights = {
  receiver = POL
  resources = { oil steel }
}
```

 | Checks if there are any resource rights with the specified parameters. | Can be used in either state or country scope. Always returns false if the state has no resources.

[Can also be used in country scope.](https://hoi4.paradoxwikis.com/Triggers#has_resources_rights)

 | 1.12 |
| days\_since\_last\_strategic\_bombing | `<int>`  
The amount to compare with. | 

```
days_since_last_strategic_bombing < 10 
```

 | Checks how many days have passed since the last strategic bombing of the state. | Must use either > or < operators. | 1.6 |
| has\_railway\_connection | `<scope> / <variable>`  
The states to check.

`<id>`

The provinces to check. Optional.

 | 

```
has_railway_connection = {
start_state = 10
target_state = 90
}

```

```
has_railway_connection = {
start_province = 402
target_province = 9400
}


```

 | Returns true if the states are connected by a railway. Can also check provinces. |  | 1.11 |
| can\_build\_railway | `<scope> / <variable>`  
The states to check.

`<id>`

The provinces to check. Optional.

 | 

```
can_build_railway = {
start_state = 10
target_state = 90
}

```

```
can_build_railway = {
start_province = 402
target_province = 9400
}


```

 | Returns true if a railway can be built between states. Can also check for provinces. |  | 1.11 |
| has\_railway\_level | `<scope> / <variable>`  
The states to check.

`<int>`

Railway level.

 | 

```
has_railway_level = {
    state = 114
    level = 5
}

```

 | Checks if a state contains a railway at or above the specified level. | Works with level 1, 2, 3, 4 or 5. Level 0 does not work. | 1.11 |
| pc\_does\_state\_stack\_demilitarized | `<bool>`  
Boolean. | 

```
pc_does_state_stack_demilitarized = yes
```

 | Checks if the current scope was demilitarised during a current or previously-ended peace conference. |  | 1.12 |
| pc\_does\_state\_stack\_dismantled | `<bool>`  
Boolean. | 

```
pc_does_state_stack_dismantled = yes
```

 | Checks if the current scope was dismantled during a current or previously-ended peace conference. |  | 1.12 |
| pc\_is\_state\_claimed | `<scope>`  
Country to check for. | 

```
pc_is_state_claimed = yes
```

 | Checks if the current scope was claimed by any country during the peace conference. | **Can only be used within peace conferences.** | 1.12.8 |
| pc\_is\_state\_claimed\_by | `<scope>`  
Country to check for. | 

```
pc_is_state_claimed_by = BHR
```

 | Checks if the current scope was claimed by the specified country during the peace conference. Note, that "claim" in this context, while includes, is NOT limited to outright taking: forcing government, puppeting and liberating will render that trigger true as well. If one looks specifically for states taken by victors for themselves, [pc\_is\_state\_claimed\_and\_taken\_by](https://hoi4.paradoxwikis.com/Triggers#pc_is_state_claimed_and_taken_by) should be used. | **Can only be used within peace conferences.** | 1.12 |
| pc\_is\_state\_claimed\_and\_taken\_by | `<scope>`  
Country to check for. | 

```
pc_is_state_claimed_and_taken_by = SOV
```

 | Checks if the current scope was claimed with "Take State" action (i.e. annexed) by the specified country during the peace conference. | **Can only be used within peace conferences.** |  |
| pc\_is\_state\_outside\_influence\_for\_winner | `<scope>`  
Country to check for. | 

```
pc_is_state_outside_influence_for_winner = ROOT
```

 | Checks if the current state is outside of the influence of the specified winner country. | **Can only be used within peace conferences.** Was called pc\_is\_state\_outside\_influence\_for prior to 1.12.8. | 1.12.8 |
| pc\_turn | `<int>`  
The amount of turns to check for. | 

```
pc_turn > 20
```

 | Compares the amount of turns that have passed during the peace conference with a number. | **Can only be used within peace conferences.** | 1.12.8 |
| can\_construct\_building | `<build type>`The type of building. | `can_construct_building = bunker` | Checks if the country (as ROOT) and state in scope can build a building in the state. |  | 1.15 |
| has\_contested\_owner | `<country> / <variable>`  
Country to check. | 

```
has_contested_owner = GER
```

 | Checks if a state has the specified country as a contested owner. The trigger can be used either from a country or a state scope and accepts the other as parameter. | [Can also be used in country scope.](https://hoi4.paradoxwikis.com/Triggers#has_contested_owner) | 1.15 |

### Resistance and Compliance\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=34 "Edit section: Resistance and Compliance") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=34 "Edit section: Resistance and Compliance")\]

Resistance-related state-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| compliance | `<int>`  
The amount to compare with. | 
```
compliance > 50
```

 | Compares the compliance value of the current scope with the given value. | Must use either > or < operators. | 1.9 |
| compliance\_speed | `<int>`  
The amount to compare with. | 

```
compliance_speed > 50
```

 | Compares the compliance speed of the current scope with the given value. | Must use either > or < operators. | 1.9 |
| has\_active\_resistance | `<bool>`  
Boolean. | 

```
has_active_resistance = yes
```

 | Checks if the current scope has non-zero resistance. |  | 1.9 |
| has\_resistance | `<bool>`  
Boolean. | 

```
has_resistance = yes
```

 | Checks if the current scope has resistance. |  | 1.9 |
| resistance | `<int>`  
The amount to compare with. | 

```
resistance > 50
```

 | Compares the resistance value of the current scope with the given value. | Must use either > or < operators. | 1.9 |
| resistance\_speed | `<int>`  
The amount to compare with. | 

```
resistance_speed > 50
```

 | Compares the resistance speed of the current scope with the given value. | Must use either > or < operators. | 1.9 |
| resistance\_target | `<int>`  
The amount to compare with. | 

```
resistance_target > 50
```

 | Compares the target resistance value of the current scope with the given value. | Must use either > or < operators. | 1.9 |
| has\_occupation\_modifier | `<token>`  
The occupation modifier to check. | 

```
has_occupation_modifier = modifier_name
```

 | Checks if the current scope has an occupation modifier, changing resistance/compliance. |  | 1.9 |
| occupation\_law | `<token>`  
The occupation law to check. | 

```
occupation_law = law_name
```

 | Checks if the current scope has an occupation law. | [Can also be used in country scope.](https://hoi4.paradoxwikis.com/Triggers#occupation_law) | 1.9 |
| occupied\_country\_tag | `<tag>`  
The occupation tag to check. | 

```
occupied_country_tag = POL
```

 | Checks which country creates resistance. |  | 1.9 |

## Character scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=35 "Edit section: Character scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=35 "Edit section: Character scope")\]

Can be used in **Character** scope.

### General\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=36 "Edit section: General") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=36 "Edit section: General")\]

General character-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| is\_character | `<scope>`  
Character ID. | 
```
is_character = POL_test_character
```

 | Checks if the current character's token matches up with the specified one. |  | 1.11 |
| can\_be\_country\_leader | `<bool>`  
Boolean. | 

```
can_be_country_leader = yes
```

 | Checks if the character in the current scope has a country leader role, active or non-active. |  | 1.11 |
| is\_country\_leader | `<bool>`  
Boolean. | 

```
is_country_leader = yes
```

 | Checks if the character in the current scope is the active country leader. |  | 1.11 |
| is\_unit\_leader | `<bool>`  
Boolean. | 

```
is_unit_leader = yes
```

 | Checks if the character in the current scope has an active unit leader (Army/Navy leader) role. |  | 1.11 |
| is\_advisor | `<bool>`  
Boolean. | 

```
is_advisor = yes
```

 | Checks if the character in the current scope has an advisor role (includes advisors/theorists/high command). |  | 1.11 |
| is\_air\_chief | `<bool>`  
Boolean. | 

```
is_air_chief = yes
```

 | Checks if the character in the current scope is selected as an air chief. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_army\_chief | `<bool>`  
Boolean. | 

```
is_army_chief = yes
```

 | Checks if the character in the current scope is selected as an army chief. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_army\_leader | `<bool>`  
Boolean. | 

```
is_army_leader = yes
```

 | Checks if the character in the current scope has an army leader (General/Field Marshal) role. |  | 1.11 |
| is\_navy\_chief | `<bool>`  
Boolean. | 

```
is_navy_chief = yes
```

 | Checks if the character in the current scope is selected as a navy chief. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_navy\_leader | `<bool>`  
Boolean. | 

```
is_navy_leader = yes
```

 | Checks if the character in the current scope has an navy leader (Admiral) role. |  | 1.11 |
| is\_high\_command | `<bool>`  
Boolean. | 

```
is_high_command = yes
```

 | Checks if the character in the current scope is selected as high command. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_corps\_commander | `<bool>`  
Boolean. | 

```
is_corps_commander = yes
```

 | Checks if the character in the current scope is a corps commander. |  | 1.11 |
| is\_operative | `<bool>`  
Boolean. | 

```
is_operative = yes
```

 | Checks if the character in the current scope is an operative. |  | 1.11 |
| is\_political\_advisor | `<bool>`  
Boolean. | 

```
is_political_advisor = yes
```

 | Checks if the character in the current scope is selected as a political advisor. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_theorist | `<bool>`  
Boolean. | 

```
is_theorist = yes
```

 | Checks if the character in the current scope is selected as a theorist. | Prior to 1.12, checked if the character had a role within the slot, regardless of being selected. | 1.11 |
| is\_character\_slot | `<string>`  
The advisor slot to check. | 

```
is_character_slot = political_advisor
```

 | Checks if the character in the current scope has a role within the specified character slot | Character slots are defined within /Hearts of Iron IV/common/idea\_tags/\*.txt. | 1.11 |
| has\_air\_ledger | `<bool>`  
Boolean. | 

```
has_air_ledger = yes
```

 | Checks if the character in the current scope has an air ledger. |  | 1.11 |
| has\_army\_ledger | `<bool>`  
Boolean. | 

```
has_army_ledger = yes
```

 | Checks if the character in the current scope has an army ledger. |  | 1.11 |
| has\_navy\_ledger | `<bool>`  
Boolean. | 

```
has_navy_ledger = yes
```

 | Checks if the character in the current scope has an navy ledger. |  | 1.11 |
| has\_character\_flag | `<string>`  
The flag to check for. | 

```
has_character_flag = my_flag
```

 | Checks if the current scope has the specified flag. |  | 1.11 |
| has\_character\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_character_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.11 |
| has\_trait | `<trait>`  
The trait to check for. | 

```
has_trait = really_good_boss
```

 | Checks if the current scope has the specified trait. |  | 1.5 |
| has\_id | `<int>`  
The id to check for. | 

```
has_id = 1
```

 | Checks if the current character has the specificed ID. |  | 1.5 |

### Advisors\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=37 "Edit section: Advisors") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=37 "Edit section: Advisors")\]

These triggers are to be used specifically for advisors.

Advisor-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| is\_hired\_as\_advisor | `<bool>`  
Boolean.  
 | 
```
is_hired_as_advisor = yes
```

 | Checks if the current character is activated as an advisor in any slot. |  | 1.12.10 |
| not\_already\_hired\_except\_as | `<slot>`  
The slot to check in. | 

```
not_already_hired_except_as = political_advisor
```

 | Checks if the current character is not hired, with the exception of the specified slot. |  | 1.11 |
| advisor\_can\_be\_fired | `<bool>`  
Boolean.

**OR**  
`slot = <slot>`  
The slot to check in.

 | 

```
advisor_can_be_fired = no
```

```
advisor_can_be_fired = {
    slot = political_advisor
}
```

 | Checks if the current character's `can_be_fired` attribute is set or not within a certain slot. | If an advisor is available in multiple slots, the long version is mandatory to use. | 1.12.8 |
| has\_advisor\_role | `<slot>`  
The slot to check in. | 

```
has_advisor_role = political_advisor
```

 | Checks if the character in scope has an advisor role for the given slot. | Possible [advisor](https://hoi4.paradoxwikis.com/Character_modding#Advisors "Character modding") role slots. | ??? |

### Country leaders\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=38 "Edit section: Country leaders") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=38 "Edit section: Country leaders")\]

These triggers are to be used specifically for country leaders.

Country leader-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_ideology | `<ideology>`  
The sub-ideology to check for. | 
```
has_ideology = liberalism
```

 | Checks if the current character has the specificed sub-ideology assigned. |  | 1.11 |
| has\_ideology\_group | `<ideology>`  
The ideology to check for. | 

```
has_ideology_group = democratic
```

 | Checks if the current character has the specificed ideology assigned. |  | 1.11 |

### Unit leaders\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=39 "Edit section: Unit leaders") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=39 "Edit section: Unit leaders")\]

These triggers are to be used specifically for unit leaders, i.e. generals and admirals.

Unit leader-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_unit\_leader\_flag | `<string>`  
The flag to check for. | 
```
has_unit_leader_flag = my_flag
```

 | Checks if the current scope has the specified flag. | Deprecated. Use has\_character\_flag instead. | 1.5 |
| has\_unit\_leader\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_unit_leader_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | Deprecated. Use has\_character\_flag instead. If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.5 |
| is\_leading\_army | `<bool>`  
Boolean. | 

```
is_leading_army = yes
```

 | Checks if the current scope is leading a single army. |  | 1.5 |
| is\_leading\_army\_group | `<bool>`  
Boolean. | 

```
is_leading_army_group = yes
```

 | Checks if the current scope is leading an army group. |  | 1.5 |
| is\_leading\_volunteer\_group | `<tag>`  
Country tag. | 

```
is_leading_volunteer_group = POL
```

 | Checks if the current scope is leading a volunteer army within the specified country. | If the target country is in a civil war, this will only be valid for one side. | 1.11 |
| is\_leading\_volunteer\_group\_with\_original\_country | `<tag>`  
Country tag. | 

```
is_leading_volunteer_group_with_original_country = POL
```

 | Checks if the current scope is leading a volunteer army within a country of the specified original tag. | If the target country is in a civil war, this will only be valid for each side. | 1.11 |
| is\_field\_marshal | `<bool>`  
Boolean. | 

```
is_field_marshal = yes
```

 | Checks if the current scope is a Field Marshal. |  | 1.5 |
| is\_assigned | `<bool>`  
Boolean. | 

```
is_assigned = yes
```

 | Checks if the current scope is an assigned unit leader. |  | 1.5 |
| can\_select\_trait | `<string>`  
The trait to check for. | 

```
can_select_trait = offensive_doctrine
```

 | Checks if the current scope can select the specified trait. |  | 1.5 |
| has\_ability | `<string>`  
The ability to check for. | 

```
has_ability = glider_planes
```

 | Checks if the current scope has the specified unit leader ability. |  | 1.5 |
| skill | `<int>`  
The amount to check for. | 

```
skill > 1
```

 | Checks if the current scope has a Skill above the specified amount. | Must use either > or < operators. | 1.5 |
| skill\_advantage | `<int>`  
The amount to check for. | 

```
skill_advantage > 1
```

 | Checks if the current scope has a Skill advantage above the specified amount in against an enemy unit leader whilst in combat. | Must use either > or < operators. | 1.5 |
| planning\_skill\_level | `<int>`  
The amount to check for. | 

```
planning_skill_level > 1
```

 | Checks if the current scope has a Planning skill above the specified amount. | Must use either > or < operators. | 1.5 |
| logistics\_skill\_level | `<int>`  
The amount to check for. | 

```
logistics_skill_level > 1
```

 | Checks if the current scope has a Logistics skill above the specified amount. | Must use either > or < operators. | 1.5 |
| defense\_skill\_level | `<int>`  
The amount to check for. | 

```
defense_skill_level > 1
```

 | Checks if the current scope has a Defense skill above the specified amount. | Must use either > or < operators. | 1.5 |
| attack\_skill\_level | `<int>`  
The amount to check for. | 

```
attack_skill_level > 1
```

 | Checks if the current scope has a Attack skill above the specified amount. | Must use either > or < operators. | 1.5 |
| average\_stats | `<int>`  
The amount to check for. | 

```
average_stats > 5
```

 | Checks if the current scope has an average skill above the specified amount. | Must use either > or < operators. | 1.5 |
| is\_border\_war | `<bool>`  
Boolean. | 

```
is_border_war = yes
```

 | Checks if the current socpe is in a border war. |  | 1.5 |
| num\_units | `<int>`  
The amount to check for. | 

```
num_units > 5
```

 | Checks if the current scope is commanding the specified amount of divisions. | Must use either > or < operators. | 1.5 |
| is\_exiled\_leader | `<bool>`  
Boolean. | 

```
is_exiled_leader = yes
```

 | Checks if the current scope is a general from an exiled country. |  | 1.6 |
| is\_exiled\_leader\_from | `<tag>`  
Country. | 

```
is_exiled_leader_from = POL
```

 | Checks if the current scope is a general from the specified exiled country. |  | 1.6 |
| is\_female | `<bool>`  
Boolean. | 

```
is_female = yes
```

 | Checks if the current scope is female. | Works for aces. | 1.9 |
| is\_leading\_army\_in\_province | `<province id>` | 

```
is_leading_army_in_province = 1234
```

 | Checks if the current unit leader is leading an army that has any division in a specific province |  | 1.17 |

### Operatives\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=40 "Edit section: Operatives") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=40 "Edit section: Operatives")\]

These triggers only work for operatives.

Operative-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_nationality | `<tag>`  
The nationality to check. | 
```
has_nationality = POL
```

 | Checks if the current operative has the nationality. |  | 1.9 |
| is\_operative\_captured | `<bool>`  
Boolean. | 

```
is_operative_captured = yes
```

 | Checks if the current scope is captured. |  | 1.9 |
| operative\_leader\_mission | `<token>`  
Mission. | 

```
operative_leader_mission = mission_name
```

 | Checks if the current scope is on the given mission. |  | 1.9 |
| operative\_leader\_operation | `<token>`  
Operation. | 

```
operative_leader_operation = operation_name
```

 | Checks if the current scope is on the given operation. |  | 1.9 |

### Scientists\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=41 "Edit section: Scientists") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=41 "Edit section: Scientists")\]

These triggers only work for scientists.

Scientist-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_scientist\_level | `level = <int>`  
Level to check.
`specialization = <specialization_token>`  
Specialization.

 | 

```
has_scientist_level = {
  level > 2
  specialization = specialization_nuclear
}
```

 | Checks if the scientist of the character in scope matches the skill level condition for a specialization. Supports < > = operators. |  | 1.15 |
| is\_active\_scientist | `<bool>`  
 | 

```
is_scientist_active = yes
```

 | Checks if the scientist of the character in scope is assigned to a project. |  | 1.15 |
| is\_scientist\_injured | `<bool>`  
 | 

```
is_scientist_injured = yes
```

 | Checks if the scientist of the character in scope is injured. |  | 1.15 |

## Combat\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=42 "Edit section: Combat") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=42 "Edit section: Combat")\]

These triggers are used within the combatant scope. Some trigger blocks in [abilities](https://hoi4.paradoxwikis.com/Command_power#Abilities_for_field_marshals_and_generals "Command power"), [combat tactics](https://hoi4.paradoxwikis.com/Combat_tactics "Combat tactics"), and [unit leader traits](https://hoi4.paradoxwikis.com/Trait_modding#Unit_leader_traits "Trait modding") check this, and it's impossible to access elsewhere.

Combatant-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| hardness | `<float>`  
The amount to check for. | 
```
hardness > 0.5
```

 | Checks if the current scope has the specified amount of hardness. | Must use either > or < operators. | 1.0 |
| armor | `<float>`  
The amount to check for. | 

```
armor > 0.5
```

 | Checks if the current scope has the specified amount of armor units. | Must use either > or < operators. | 1.0 |
| dig\_in | `<float>`  
The amount to check for. | 

```
dig_in > 0.5
```

 | Checks if the current scope has the specified amount of Dig In bonus. | Must use either > or < operators. | 1.0 |
| min\_planning | `<float>`  
The amount to check for. | 

```
min_planning > 0.5
```

 | Checks if the current scope has the specified amount of planning. | Must use either > or < operators. | 1.0 |
| fastest\_unit | `<float>`  
The speed in km/h to check for. | 

```
fastest_unit > 12
```

 | Checks if the current scope has a unit with the specified speed. | Must use either > or < operators. | 1.0 |
| temperature | `<float>`  
The temperature in celsius to check for. | 

```
temperature > 20
```

 | Checks if the current scope is in a province with a temperature above the specified amount. | Must use either > or < operators. | 1.0 |
| reserves | `<float>`  
The amount to check for. | 

```
reserves > 10
```

 | Checks if the current scope has the specified amount of reserves waiting. | Must use either > or < operators. | 1.0 |
| has\_combat\_modifier | `<string>`  
The modifier to check for. | 

```
has_combat_modifier = river_crossing
```

 | Checks if the current scope has the specified combat modifier. |  | 1.0 |
| is\_fighting\_in\_terrain | `<string>`  
The terrain to check for. | 

```
is_fighting_in_terrain = desert
```

 | Checks if the current scope is fighting in the specified terrain. |  | 1.0 |
| is\_fighting\_in\_weather | `<string>`  
The weather to check for.

**OR**  
`{ <string> <...> <string> }`  
The weather to check for in an OR statement.

 | 

```
is_fighting_in_weather = sandstorm
```

```
is_fighting_in_weather = { rain_light rain_heavy }
```

 | Checks if the current scope is fighting in the specified weather. |  | 1.0 |
| phase | `<bool>`  
Boolean. | 

```
phase = yes
```

 | Checks if the current scope is in phase. |  | 1.0 |
| recon\_advantage | `<bool>`  
Boolean. | 

```
recon_advantage > 0
```

 | Checks if the current scope has x recon advantage. |  | 1.0 |
| night | `<bool>`  
Boolean. | 

```
night = yes
```

 | Checks if the current scope is fighting at night. |  | 1.0 |
| frontage\_full | `<bool>`  
Boolean. | 

```
frontage_full = yes
```

 | Checks if the current scope has a full combat width. |  | 1.0 |
| has\_flanked\_opponent | `<bool>`  
Boolean. | 

```
has_flanked_opponent = yes
```

 | Checks if the current scope has flanked their opponent. |  | 1.0 |
| has\_max\_planning | `<bool>`  
Boolean. | 

```
has_max_planning = yes
```

 | Checks if the current scope has the maximum planning bonus. |  | 1.0 |
| has\_reserves | `<bool>`  
Boolean. | 

```
has_reserves = yes
```

 | Checks if the current scope has any reserves waiting. |  | 1.0 |
| is\_amphibious\_invasion | `<bool>`  
Boolean. | 

```
is_amphibious_invasion = yes
```

 | Checks if the current scope is performing an amphibious invasion. |  | 1.0 |
| is\_attacker | `<bool>`  
Boolean. | 

```
is_attacker = yes
```

 | Checks if the current scope is attacking. |  | 1.0 |
| is\_defender | `<bool>`  
Boolean. | 

```
is_defender = yes
```

 | Checks if the current scope is defending. |  | 1.0 |
| is\_winning | `<bool>`  
Boolean. | 

```
is_winning = yes
```

 | Checks if the current scope is winning their battle. |  | 1.0 |
| is\_fighting\_air\_units | `<bool>`  
Boolean. | 

```
is_fighting_air_units = yes
```

 | Checks if the current scope is fighting air units. |  | 1.0 |
| less\_combat\_width\_than\_opponent | `<bool>`  
Boolean. | 

```
less_combat_width_than_opponent = yes
```

 | Checks if the current scope is fighting with less combat width than their opponent. |  | 1.0 |
| has\_carrier\_airwings\_on\_mission | `<bool>`  
Boolean. | 

```
has_carrier_airwings_on_mission = yes
```

 | Checks if the current scope has carrier airwings on a mission. |  | 1.0 |
| has\_carrier\_airwings\_in\_own\_combat | `<bool>`  
Boolean. | 

```
has_carrier_airwings_in_own_combat = yes
```

 | Checks if the current scope has carrier airwings in their own combat. |  | 1.0 |
| has\_artillery\_ratio | `<float>`  
 | 

```
has_artillery_ratio > 0.1
```

 | Check that ratio of atrillery battalions in the composition of a side of combating troops are over a certain level. |  | ??? |
| has\_unit\_type | `<unit_type>`  
 | 

```
has_unit_type = amphibious_mechanized
```

 | Check if the combatant has at least one of the provided unit types. |  | ??? |

## Division scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=43 "Edit section: Division scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=43 "Edit section: Division scope")\]

Can be used in **Division** scope.

Division-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| division\_has\_majority\_template | `<battalion>`  
Battalion to check for. | 
```
division_has_majority_template = light_armor
```

 | Checks if the current scope is majority made up of the specified battalion. | Battalions are defined within /Hearts of Iron IV/common/units/\*.txt files. | 1.12 |
| division\_has\_battalion\_in\_template | `<battalion>`  
Battalion to check for. | 

```
division_has_battalion_in_template = light_armor
```

 | Checks if the current scope has any battalions of the type in the template. | Battalions are defined within /Hearts of Iron IV/common/units/\*.txt files. | 1.12 |
| unit\_strength | `<float>`  
The amount to check for. | 

```
unit_strength < 0.3
```

 | Checks the current strength of the unit on the scale from 0 to 1. | Must use either the < or > operator. | 1.12 |
| unit\_organization | `<float>`  
The amount to check for. | 

```
unit_organization < 0.3
```

 | Checks the current organisation of the unit on the scale from 0 to 1. | Must use either the < or > operator. | 1.12 |
| is\_unit\_template\_reserves | `<bool>`  
Boolean. | 

```
is_unit_template_reserves = yes
```

 | Checks if the current division has the supply priority set to 'Reserves', i.e. the lowest priority. | Must use either the < or > operator. | 1.12 |
| has\_officer\_name | `<string>`  
The localization key to check. | 

```
has_officer_name = FIN_nikke_parmi
```

 | Checks if the current division has an officer with the provided name key. |  |  |

## MIO scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=44 "Edit section: MIO scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=44 "Edit section: MIO scope")\]

Can be used in **Military-industrial organisation** scope.

MIO-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| is\_military\_industrial\_organization | `<token>`  
MIO to check. | 
```
is_military_industrial_organization = my_mio_token
```

 | Checks if the currently-scoped MIO matches the input token. |  | 1.13 |
| is\_mio\_visible | `<bool>`  
Boolean. | 

```
is_mio_visible = yes
```

 | Checks if the currently-scoped MIO is visible. |  | 1.13 |
| is\_mio\_available | `<bool>`  
Boolean. | 

```
is_mio_available = yes
```

 | Checks if the currently-scoped MIO is visible. |  | 1.13 |
| is\_mio\_assigned\_to\_task | `<bool>`  
Boolean. | 

```
is_mio_assigned_to_task = yes
```

 | Checks if the currently-scoped MIO is assigned to a task. |  | 1.13 |
| has\_mio\_size | `<int>`  
Integer. | 

```
has_mio_size > 3
```

 | Checks the size of the MIO. | Accepts [variables](https://hoi4.paradoxwikis.com/Variables "Variables"). May use < or >. | 1.13 |
| has\_mio\_trait | `<token>`  
Trait to check.

**OR**  
`trait = <token>`  
Trait to check.

 | 

```
has_mio_trait = my_trait_token
```

```
has_mio_trait = {
    token = my_trait_token
}
```

 | Checks whether the MIO has the target trait in its list. |  | 1.13 |
| is\_mio\_trait\_available | `<token>`  
Trait to check.

**OR**  
`trait = <token>`  
Trait to check.  
`check_mio_parent_completed = <bool>`  
Whether to check if the parent traits are complete. True by default. `check_mio_mutually_exclusive = <bool>`  
Whether to check if any mutually exclusive traits are complete. True by default.

 | 

```
is_mio_trait_available = my_trait_token
```

```
is_mio_trait_available = {
    token = my_trait_token
    check_mio_parent_completed = no
}
```

 | Checks whether the MIO has the target trait in its list and whether it's available. |  | 1.13 |
| is\_mio\_trait\_completed | `<token>`  
Trait to check.

**OR**  
`trait = <token>`  
Trait to check.

 | 

```
is_mio_trait_completed = my_trait_token
```

```
is_mio_trait_completed = {
    token = my_trait_token
}
```

 | Checks whether the MIO has the target trait in its list and whether it's completed. |  | 1.13 |
| has\_mio\_number\_of\_completed\_traits | `<int>`  
Integer. | 

```
has_mio_number_of_completed_traits < 2
```

 | Checks the amount of unlocked MIO traits. | Accepts [variables](https://hoi4.paradoxwikis.com/Variables "Variables"). May use < or >. | 1.13 |
| has\_mio\_flag | `<string>`  
The flag to check. | 

```
has_mio_flag = my_flag
```

 | Checks if the current scope has the specified flag. |  | 1.13 |
| has\_mio\_flag | `flag = <string>`  
The flag to check.

`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_mio_flag = {
    flag = my_flag
    days > 30
    date > 1936.6.1
    value > 0
}

```

 | Compares the specified flag's last set date, days since last set, and/or value. | If not set, the value comparison is `>0`. `value` is limited between -32768 and 32767. | 1.13 |
| has\_mio\_policy | `<token>`  
Policy to check. | 

```
has_mio_policy = my_policy_token
```

 | Checks if the currently-scoped MIO has the target policy allowed. |  | 1.13 |
| has\_mio\_policy\_active | `<token>`  
Policy to check. | 

```
has_mio_policy_active = my_policy_token
```

 | Checks if the currently-scoped MIO has the target policy active. |  | 1.13 |
| has\_mio\_research\_category | `<token>`  
Category to check. | 

```
has_mio_research_category = my_research_category_token
```

 | Checks if the currently-scoped MIO has the target research category. |  | 1.13 |
| has\_mio\_equipment\_type | `<token>`  
Type to check. | 

```
has_mio_equipment_type = my_equipment_type_token
```

 | Checks if the currently-scoped MIO has the target equipment types. | The possible equipment types are defined in `script_enum_equipment_bonus_type` (in /Hearts of Iron IV/common/script\_enums.txt) and in /Hearts of Iron IV/common/equipment\_groups.txt files. | 1.13 |

## Contract scope\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=45 "Edit section: Contract scope") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=45 "Edit section: Contract scope")\]

Can be used in **purchase contract** scope.

Contract-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| contract\_contains\_equipment | `<token>`  
Type to check. | 
```
contract_contains_equipment = infantry_equipment
```

 | Checks if the currently-scoped purchase contract contains an equipment type. | May use equipment types, equipment archetypes, or types of equipment archetypes. | 1.13 |
| deal\_completion | `<decimal>`  
Progress to compare with. | 

```
deal_completition > 0.6
```

 | Checks the deal completion with the target value. | May use < or >. On the scale from 0 to 1. | 1.13 |
| seller | `<country>`  
Country to check. | 

```
seller = BHR
```

 | Checks the seller in the current purchase contract. |  | 1.13 |
| buyer | `<country>`  
Country to check. | 

```
buyer = OMA
```

 | Checks the buyer in the current purchase contract. |  | 1.13 |

## Special projects\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=46 "Edit section: Special projects") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=46 "Edit section: Special projects")\]

Special project-scoped triggers:  
Collapse
| Name | Parameters | Examples | Description | Notes | Version Added |
| --- | --- | --- | --- | --- | --- |
| has\_project\_flag | `<string>`  
The flag to check for.
**OR**  
`flag = <string>`  
The flag to check.  
`value = <int>`  
The flag value to check for. Optional.  
`date = <date>`  
The flag creation date to check for. Optional.  
`days = <int>`  
The duration the flag existed for. Optional.

 | 

```
has_project_flag = my_flag
```

```
has_project_flag = {
  flag = my_flag
  value < 12
  date > 1936.3.25
  days > 365
}
```

 | Check if flag has been set within the special project in scope. May checks on the value or date/days since last modified date. | If not set, the value comparison is >0. value is limited between -32768 and 32767. | 1.15 |

## Meta triggers\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=47 "Edit section: Meta triggers") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=47 "Edit section: Meta triggers")\]

Meta triggers are a system added with 1.6 with [![Man the Guns](https://hoi4.paradoxwikis.com/images/thumb/8/86/DLC_Man_the_Guns.png/22px-DLC_Man_the_Guns.png)](https://hoi4.paradoxwikis.com/Man_the_Guns "Man the Guns")[Man the Guns](https://hoi4.paradoxwikis.com/Man_the_Guns "Man the Guns")<sup id="cite_ref-4"><a href="https://hoi4.paradoxwikis.com/Triggers#cite_note-4">[4]</a></sup> used in the exact same manner as [meta effects](https://hoi4.paradoxwikis.com/Effect#Meta_effects "Effect"): in order to tie a trigger block to a dynamic localisation entry. This is usually used in conjunction with [scripted localisation](https://hoi4.paradoxwikis.com/Localisation#Scripted_localisation "Localisation") for non-numerical checks. This also can serve in order to place a variable check where one is not possible.  
Meta triggers work in any scope that supports triggers, including combat scope.

The following arguments go inside of a scripted trigger:

-   `text = { ... }` is a trigger block used by the meta trigger. In here, any string that must be made dynamic is marked with the square brackets on each side as `[EXAMPLE]`.
-   `EXAMPLE = "..."` is a string that will serve as the dynamic replacement for `[EXAMPLE]` within `text = { ... }`. This accepts [dynamic localisation](https://hoi4.paradoxwikis.com/Localisation#Namespaces "Localisation") to a limited degree, such as getting a variable's value with `[?var_name]` or some namespaces like `[ROOT.GetTag]`.
-   `debug = yes`, if added, will add the final output in the [user directory](https://hoi4.paradoxwikis.com/Modding "Modding")'s /Hearts of Iron IV/logs/game.log file for debugging purposes.

For example, the following can be used with [has\_equipment](https://hoi4.paradoxwikis.com/Triggers#has_equipment) to make it depend on a variable's value:

```
meta_trigger = {
    text = {
        has_equipment = { [EQUIPMENT_ARCHETYPE] > 100 }
    }
    EQUIPMENT_ARCHETYPE = "[GetEquipmentArchetype]"
}

```

In this case, `GetEquipmentArchetype` is [scripted localisation](https://hoi4.paradoxwikis.com/Localisation#Scripted_localisation "Localisation"). An example definition of scripted localisation in this case is as such:

```
defined_text = {
    name = GetEquipmentArchetype
    text = {
        trigger = {
            check_variable = { v = 0 }
        }
        localization_key = artillery_equipment
    }
    text = {
        localization_key = infantry_equipment
    }
}
```

## Scripted triggers\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=48 "Edit section: Scripted triggers") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=48 "Edit section: Scripted triggers")\]

Scripted triggers serve a similar purpose to [functions](https://en.wikipedia.org/wiki/Subroutine) in that they can be defined in /Hearts of Iron IV/common/scripted\_triggers/\*.txt and then used elsewhere as a shortened version. Alongside that, the game has certain base game scripted triggers that are checked directly in the game's code determining triggers for functions that cannot be changed.

A scripted trigger is defined simply as

```
scripted_trigger_name = {
<triggers>
}
```

This example can be used as a trigger in regular code as `scripted_trigger_name = yes` or `scripted_trigger_name = no`.

For example, this would be the definition in any scripted trigger file:

```
state_is_in_area = {
    OR = {
        state = 120
        state = 121
        state = 123
        state = 124
        state = 125
    }
}
```

This can then be used in any other trigger block, such as a national focus' available section:

```
focus = {
    id = TAG_focus_id   # Optional attributes, other than available, have been omitted
    available = {
        capital_scope = {
            state_is_in_area = yes
        }
    }
}
```

If there are several definitions of scripted triggers with the exact same name, the game will make the scripted trigger be the one that was [evaluated later, as decided by file names and order in files](https://hoi4.paradoxwikis.com/Modding#Loading_files "Modding").

### Diplomacy scripted triggers\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=49 "Edit section: Diplomacy scripted triggers") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=49 "Edit section: Diplomacy scripted triggers")\]

Diplomacy scripted triggers fall into two mutually exclusive groups: deciding availability and deciding visibility. By default, these are defined in /Hearts of Iron IV/common/scripted\_triggers/diplomacy\_scripted\_triggers.txt and /Hearts of Iron IV/common/scripted\_triggers/00\_diplo\_action\_valid\_triggers.txt respectively. While it is possible to also use them as regular scripted triggers, they will also modify the prerequisites of being able to do a diplomatic action between 2 countries.

A diplomacy scripted trigger is identified by the naming pattern of `DIPLOMACY_<action>_ENABLE_TRIGGER` for availability, such as `DIPLOMACY_GUARANTEE_ENABLE_TRIGGER`, and `is_diplomatic_action_valid_<action>` for visibility, such as `is_diplomatic_action_valid_stage_coup`. In the base game, diplomacy scripted triggers are used to implement the game rules and add some country-specific exceptions, such as the [![Flag of United Kingdom](https://hoi4.paradoxwikis.com/images/thumb/2/29/United_Kingdom.png/24px-United_Kingdom.png)](https://hoi4.paradoxwikis.com/United_Kingdom "United Kingdom") [United Kingdom](https://hoi4.paradoxwikis.com/United_Kingdom "United Kingdom") being unable to release its colonies with the [![Man the Guns](https://hoi4.paradoxwikis.com/images/thumb/8/86/DLC_Man_the_Guns.png/22px-DLC_Man_the_Guns.png)](https://hoi4.paradoxwikis.com/Man_the_Guns "Man the Guns")[Man the Guns](https://hoi4.paradoxwikis.com/Man_the_Guns "Man the Guns") DLC. Checking the base game's contents beforehand or copying it to the mod would ensure that the mod won't accidentally break any existing game rules.

Generally, the pattern in localisation keys used for the button usually matches up with the internal ID of a diplomatic action. If the diplomatic action doesn't already have a scripted trigger in the base game, [entirety of localisation can be searched](https://hoi4.paradoxwikis.com/Modding#Searching_multiple_files "Modding") for the name of the button to find the name of the action. For example, a the English localisation entry of `DIPLOMACY_CALL_ALLY_TITLE:0 "Call to arms"` would suggest that the diplomatic action of calling ally to war is `CALL_ALLY`.

List of known triggers:

```
DIPLOMACY_JOIN_ALLY_ENABLE_TRIGGER
DIPLOMACY_CALL_ALLY_ENABLE_TRIGGER
DIPLOMACY_WAR_ENABLE_TRIGGER
DIPLOMACY_JOIN_FACTION_ENABLE_TRIGGER
DIPLOMACY_CREATE_FACTION_ENABLE_TRIGGER
DIPLOMACY_PEACE_PROPOSAL_ENABLE_TRIGGER
DIPLOMACY_IMPROVERELATION_ENABLE_TRIGGER
DIPLOMACY_NONAGGRESSIONPACT_ENABLE_TRIGGER
DIPLOMACY_REVOKE_NONAGGRESSIONPACT_ENABLE_TRIGGER
DIPLOMACY_OFFER_JOIN_FACTION_ENABLE_TRIGGER
DIPLOMACY_REQUEST_FOREIGN_MANPOWER_ENABLE_TRIGGER
DIPLOMACY_CANCEL_FOREIGN_MANPOWER_ENABLE_TRIGGER
DIPLOMACY_CANCEL_LICENSED_PRODUCTION_ENABLE_TRIGGER
DIPLOMACY_REQUEST_ACCESS_TO_LICENCE_PRODUCTION_ENABLE_TRIGGER
DIPLOMACY_SEND_ATTACHE_ENABLE_TRIGGER
DIPLOMACY_EMBARGO_ENABLE_TRIGGER
DIPLOMACY_SEND_EXP_FORCE_ENABLE_TRIGGER
DIPLOMACY_REQUEST_EXP_FORCE_ENABLE_TRIGGER
DIPLOMACY_RETURN_EXP_FORCE_ENABLE_TRIGGER
DIPLOMACY_ASKSTATECONTROL_ENABLE_TRIGGER
DIPLOMACY_GIVESTATECONTROL_ENABLE_TRIGGER
DIPLOMACY_GUARANTEE_ENABLE_TRIGGER
DIPLOMACY_REVOKE_GUARANTEE_ENABLE_TRIGGER
DIPLOMACY_RELEASE_NATION_ENABLE_TRIGGER
DIPLOMACY_MILACC_ENABLE_TRIGGER
DIPLOMACY_OFFER_MILACC_ENABLE_TRIGGER
DIPLOMACY_REVOKE_OFFER_MILACC_ENABLE_TRIGGER
DIPLOMACY_DOCKING_RIGHTS_ENABLE_TRIGGER
DIPLOMACY_OFFER_DOCKING_RIGHTS_ENABLE_TRIGGER
DIPLOMACY_AIR_BASE_ACCESS_ENABLE_TRIGGER
DIPLOMACY_OFFER_AIR_BASE_ACCESS_ENABLE_TRIGGER
DIPLOMACY_REVOKE_OFFER_DOCKING_RIGHTS_ENABLE_TRIGGER
DIPLOMACY_REVOKE_OFFER_AIR_BASE_ACCESS_ENABLE_TRIGGER
DIPLOMACY_LEND_LEASE_ENABLE_TRIGGER
DIPLOMACY_INCOMING_LEND_LEASE_ENABLE_TRIGGER
DIPLOMACY_REQUEST_LICENSED_PRODUCTION_ENABLE_TRIGGER
DIPLOMACY_GENERATE_WARGOAL_ENABLE_TRIGGER
DIPLOMACY_BOOST_PARTY_POPULARITY_ENABLE_TRIGGER
DIPLOMACY_STAGE_COUP_ENABLE_TRIGGER
DIPLOMACY_LEAVE_FACTION_ENABLE_TRIGGER
DIPLOMACY_ASSUME_FACTION_LEADERSHIP_ENABLE_TRIGGER
DIPLOMACY_KICK_FROM_FACTION_ENABLE_TRIGGER
DIPLOMACY_SEND_VOLUNTEERS_ENABLE_TRIGGER
```

Know tokens for `is_diplomatic_action_valid_<action>` are:

-   **declare\_war**, for the Declare War button
-   **generate\_wargoal**, only affects the war goal menu by greying out the send button
-   **guarantee**, for the Guarantee Independence button
-   **docking\_rights**, for the request docking rights button
-   **offer\_docking\_right**, for the offer docking rights button
-   **create\_faction**, for the create faction button
-   **assume\_faction\_leadership**, for the assume leadership of faction button
-   **kick\_from\_faction**, for the kick from faction button
-   **join\_faction**, for the ask to join faction button
-   **request\_access\_to\_licence\_production**, for the negotiate license button
-   **embargo**, for the embargo button
-   **send\_volunteers**, only affects the sent volunteers menu by greying out the send button
-   **stage\_coup**, for the stage coup button
-   **boost\_party\_popularity**, for the boost party popularity button

Within a diplomacy scripted trigger, the default scope is the country that does the trigger, while [FROM](https://hoi4.paradoxwikis.com/Scopes#FROM "Scopes") is the target of the action. For availability, the trigger's tooltip is shown to the player when hovering over the diplomatic action; in case of country-specific restrictions, using [conditional statements](https://hoi4.paradoxwikis.com/Triggers#if) can ensure that the tooltip would only be generated when needed rather than between any pair of nations.

For example, this trigger will prevent BHR from revoking a guarantee on QAT, while still ensuring the game rule works otherwise:

```
DIPLOMACY_REVOKE_GUARANTEE_ENABLE_TRIGGER = {
    if = {
        limit = {
            has_game_rule = {
                rule = allow_revoke_guarantees
                option = BLOCKED
            }
        }
        custom_trigger_tooltip = {
            tooltip = RULE_ALLOW_REVOKE_GUARANTEES_BLOCKED_TOOLTIP
            always = no
        }
    }
    if = {
        limit = {
            tag = BHR
            FROM = { tag = QAT }
        }
        custom_trigger_tooltip = {
            tooltip = NO_REVOKING_ON_QAT_TT
            always = no
        }
    }
}
```

### Resistance initiation triggers\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=50 "Edit section: Resistance initiation triggers") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=50 "Edit section: Resistance initiation triggers")\]

The behaviour of resistance being automatically initiated is decided by the `should_initiate_resistance` scripted trigger, by default defined in /Hearts of Iron IV/common/scripted\_triggers/00\_resistance\_initiate\_triggers.txt. If it is unfulfilled, the resistance will never initiate unless forced via the [the force\_enable\_resistance effect](https://hoi4.paradoxwikis.com/Effect#force_enable_resistance "Effect"). Likewise, the resistance will always occur if it's true unless forcefully disabled.

The scripted trigger's behaviour can be overwritten with state-specific scripted triggers, which should be named `should_initiate_resistance` with the list of state IDs suffixed at the end, separated by underscores. For example, this ensures that when a state 321 or 123 is controlled by the [![Flag of United Kingdom](https://hoi4.paradoxwikis.com/images/thumb/2/29/United_Kingdom.png/24px-United_Kingdom.png)](https://hoi4.paradoxwikis.com/United_Kingdom "United Kingdom") [United Kingdom](https://hoi4.paradoxwikis.com/United_Kingdom "United Kingdom"), resistance would get initiated if and only if they're national territory of [![Flag of France](https://hoi4.paradoxwikis.com/images/thumb/d/de/France.png/24px-France.png)](https://hoi4.paradoxwikis.com/France "France") [France](https://hoi4.paradoxwikis.com/France "France"); otherwise, the normal behaviour is used:

```
should_initiate_resistance_123_321 = {
if = {
limit = {
tag = ENG
}
is_core_of = FRA
}
else = {
should_initiate_resistance = yes # If this is not done, resistance would always activate due to overwriting that scripted trigger.
}
}
```

### Useful scripted triggers\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=51 "Edit section: Useful scripted triggers") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=51 "Edit section: Useful scripted triggers")\]

These scripted triggers are defined in base game and might be useful to keep in the mod to cut down on the amount of code. As scripted triggers, all of these use a boolean value as argument.

Scripted triggers:  
Collapse
| Name | Scope | Example | Description | Notes |
| --- | --- | --- | --- | --- |
| can\_ROOT\_get\_wargoal\_on\_THIS | Country | 
```
can_ROOT_get_wargoal_on_THIS = yes
```

 | Checks if ROOT can obtain a wargoal on the current scope. | To evaluate as true, the current scope must exist, not share a faction with ROOT, and not be a subject of ROOT. |
| is\_free\_or\_subject\_of\_root | Country | 

```
is_free_or_subject_of_root = yes
```

 | Checks if the current scope is either independent or a subject of ROOT. |  |
| has\_same\_ideology | Country | 

```
has_same_ideology = yes
```

 | Checks if the current scope has the same ideology as ROOT. | Needs modifying if there are custom ideologies. Equivalent to `has_government = ROOT` for base game ideologies. |
| is\_enemy\_ideology | Country | 

```
is_enemy_ideology = yes
```

 | Checks if the current scope has an ideology that is considered enemy to ROOT's. | [![{{{1}}}](https://hoi4.paradoxwikis.com/images/thumb/e/e9/Communism.png/22px-Communism.png)](https://hoi4.paradoxwikis.com/Ideology#Communism "{{{1}}}")[Communism](https://hoi4.paradoxwikis.com/Ideology#Communism "Ideology"), [![{{{1}}}](https://hoi4.paradoxwikis.com/images/thumb/e/e9/Democracy.png/22px-Democracy.png)](https://hoi4.paradoxwikis.com/Ideology#Democracy "{{{1}}}")[Democracy](https://hoi4.paradoxwikis.com/Ideology#Democracy "Ideology"), and [![{{{1}}}](https://hoi4.paradoxwikis.com/images/thumb/1/1f/Fascism.png/22px-Fascism.png)](https://hoi4.paradoxwikis.com/Ideology#Fascism "{{{1}}}")[Fascism](https://hoi4.paradoxwikis.com/Ideology#Fascism "Ideology") are considered enemy to each other. |
| has\_ROOT\_at\_least\_1\_div\_in\_current\_state\_scope | State | 

```
has_ROOT_at_least_1_div_in_current_state_scope = yes
```

 | Checks if ROOT has at least one division in the current scope. |  |
| controls\_or\_subject\_of | State | 

```
controls_or_subject_of = yes
```

 | Checks if the current state is controlled by ROOT or a subject of ROOT. |  |
| is\_controlled\_by\_ROOT\_or\_ally | State | 

```
is_controlled_by_ROOT_or_ally = yes
```

 | Checks if the current state is controlled by ROOT, a subject of ROOT, or a country in the same faction as ROOT. |  |
| owns\_or\_subject\_of | State | 

```
owns_or_subject_of = yes
```

 | Checks if the current scope is owned by ROOT or a subject of ROOT. |  |

## References and notes\[[edit](https://hoi4.paradoxwikis.com/index.php?title=Triggers&veaction=edit&section=52 "Edit section: References and notes") | [edit source](https://hoi4.paradoxwikis.com/index.php?title=Triggers&action=edit&section=52 "Edit section: References and notes")\]

**[^](https://hoi4.paradoxwikis.com/Triggers#ref_a)** **a:** Triggers are able to set and modify [temporary variables](https://hoi4.paradoxwikis.com/Variables "Variables"). This temporary variable itself may be then used separately to change the game's state, such as in a [MTTH block](https://hoi4.paradoxwikis.com/MTTH "MTTH") or if the trigger block is used in some [effect](https://hoi4.paradoxwikis.com/Effect "Effect")'s `limit = { ... }` (most commonly [if statements](https://hoi4.paradoxwikis.com/Effect#if "Effect") or [effect scope limits](https://hoi4.paradoxwikis.com/Scopes#Scope_limits "Scopes")), though the usage of the variable to change the game's state is not a trigger by itself.  

1.  [↑](https://hoi4.paradoxwikis.com/Triggers#cite_ref-1 "Jump up") [\[Modding\] Achievement for mods](https://forum.paradoxplaza.com/forum/index.php?threads/1544899 "forum:1544899")  
    [Tutorial to write achievements files in your mod](https://forum.paradoxplaza.com/forum/index.php?threads/1544901 "forum:1544901")
2.  [↑](https://hoi4.paradoxwikis.com/Triggers#cite_ref-2 "Jump up") [How does any\_war\_score work?](https://forum.paradoxplaza.com/forum/index.php?threads/1124460 "forum:1124460")
3.  [↑](https://hoi4.paradoxwikis.com/Triggers#cite_ref-3 "Jump up") [forum:1356228/#post-26361808](https://forum.paradoxplaza.com/forum/index.php?threads/1356228/#post-26361808 "forum:1356228/")
4.  [↑](https://hoi4.paradoxwikis.com/Triggers#cite_ref-4 "Jump up") [HOI4 Dev Diary - Modding and Traits](https://forum.paradoxplaza.com/forum/index.php?threads/1117516 "forum:1117516")
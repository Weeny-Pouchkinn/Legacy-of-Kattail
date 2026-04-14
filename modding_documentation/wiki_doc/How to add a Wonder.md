## Description

[](https://github.com/Weeny-Pouchkinn/Legacy-of-Kattail/wiki/Wonders#description)

Wonders are state-bound "features" that provide a buff to the nation controlling them, alongside a little bit of lore. Their effects are doubled if the state is the owner's capital, and halved if it is not a core.

![](https://camo.githubusercontent.com/de6ca8f1be1e408350269cb373451599d73518f7298fe0f87074f87cc03e4ed2/68747470733a2f2f676967617374727563747572616c2d656e67696e656572696e672d6c6f72652e776466696c65732e636f6d2f6c6f63616c2d2d66696c65732f73746172742f707972616d69642e706e67)

## Adding your own Wonder

[](https://github.com/Weeny-Pouchkinn/Legacy-of-Kattail/wiki/Wonders#adding-your-own-wonder)

They're a _tad_ tricky as they're coded to be dynamic. The way it works is that the actual _values_ of the wonder's modifiers are stored in the state itself! This means they can be easily altered by script. What wonder a state has is simply determined by the "wonder" variable, with 0 having no Wonder and each wonder having an unique ID. For example, the Katown Pyramid has the ID of 1.

1/ **Define your wonder's modifiers** Head to `dynamic_modifiers/LOK_dynamic_modifiers` and find the `lok_wonder_modifier` entry. Add a block for the name of your wonder modifiers, formatted like so:

```
[modifier 1] = wonder_[WONDER ID]_modifier_0
[modifier 2] = wonder_[WONDER ID]_modifier_1
etc...
```

For the \[WONDER ID\], just see what the ID of the latest block is and add 1.

Example: the Katown Pyramid as shown above:

```
max_planning = wonder_1_modifier_0
army_org_regain = wonder_1_modifier_1
army_org_factor = wonder_1_modifier_2
compliance_growth = wonder_1_modifier_3
```

2/ **Define your wonder's values** Head to `on_actions/LOK_on_actions` and find Line 87. This is where we define the actual _values_ of those modifiers. Add a block of modifiers formatted like so:

```
[THE STATE ID OF THE WONDER] = {
      set_variable = { wonder = [WONDER ID] }
      add_to_array = { array = wonder_modifiers_values value = [VALUE OF MODIFIER 1] }
      add_to_array = { array = wonder_modifiers_values value = [VALUE OF MODIFIER 2] }
      etc...
}
```

So you have _as many add\_to\_arrays_ as there are modifiers for your wonder

Example: the Katown Pyramid, which is in state 509:

```
509 = {
set_variable = { wonder = 1 }

#We store the modifier values in an array
add_to_array = { array = wonder_modifiers_values value = 0.15 }
add_to_array = { array = wonder_modifiers_values value = 0.10 }
add_to_array = { array = wonder_modifiers_values value = 0.10 }
add_to_array = { array = wonder_modifiers_values value = 0.10 }
}
```

3/ **Define loc and GFX** Then its just a matter of defining the picture. Go to `interface/wonder_icon.gfx` and add the proper entry with the icon for your wonder. For the loc, go to `localisation/english/wonders_l_english.yml` and add a line for `var_wonder.[WONDER ID]` and a line for `var_wonder_desc.[WONDER ID]` You need to manually specify the various variables you've used as modifiers, as shown in the example below:

```
var_wonder.1: "Grand Katown Pyramid"
var_wonder_desc.1:0 "Max Planning: [?THIS.wonder_1_modifier_0|%+1=]\nDivision Recovery Rate: [?THIS.wonder_1_modifier_1|%+1=]\nDivision Organization: [?THIS.wonder_1_modifier_2|%+1=]\nCompliance Growth: [?THIS.wonder_1_modifier_3|%+1=]\n§LThe heart of the former Katzenartig Imperium, the Katown Pyramid is a gargantuan mile-tall fortified complex housing countless administrative and military command centers, intended to centralize the governance of the Katzen state.§!"
```

And there you go! The modifiers will automatically be doubled or halved based on if the state is a capital or non-core.

You can then check for the wonder variable in other scopes if you want the presence of a wonder to affect things. For example, the Katown Pyramid (ID = 1) makes its state immune to nukes, so the script that processes nuke devastation will do nothing if the affected state has the "wonder" variable set to 1.
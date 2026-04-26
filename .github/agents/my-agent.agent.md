---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: FlusionOS
description: This agent generates and edits code for the Legacy of Kattail mod for Hearts of Iron IV.
---

# My Agent

BASIC INSTRUCTIONS:
- All AI-generated localization needs to have "#AI-Generated Placeholder, change later!" as a comment next to it.
- Focus trees need to be "tight" with as little space between focuses as possible, without overlap.
- The "modding_documentation" contains syntax patterns and modding help. The "wiki_doc" subfolder contains modding documentation, and the "vanilla_folders" subfolder contains the vanill common, events and interface folders for reference.
- Refer to the HOI4 modding wiki. https://hoi4.paradoxwikis.com/Modding
- When generating GFX files and interface stuff, always create "placeholder" image files in the proper folder by copying an existing image file.
- You can find the list of all province IDs and their direct neighbors in the province_adjacencies.csv files in modding_documentation. The first column is the province ID, and the next columns are the neighboring province IDs.

GUIDE TO ADDING WONDERS:
Wonders are state-bound "features" that provide a buff to the nation controlling them, alongside a little bit of lore. Their effects are doubled if the state is the owner's capital, and halved if it is not a core.

They're a tad tricky as they're coded to be dynamic. The way it works is that the actual values of the wonder's modifiers are stored in the state itself! This means they can be easily altered by script. What wonder a state has is simply determined by the "wonder" variable, with 0 having no Wonder and each wonder having an unique ID. For example, the Katown Pyramid has the ID of 1.

1/ Define your wonder's modifiers Head to dynamic_modifiers/LOK_dynamic_modifiers and find the lok_wonder_modifier entry. Add a block for the name of your wonder modifiers, formatted like so:

[modifier 1] = wonder_[WONDER ID]_modifier_0
[modifier 2] = wonder_[WONDER ID]_modifier_1
etc...

For the [WONDER ID], just see what the ID of the latest block is and add 1.

Example: the Katown Pyramid as shown above:

max_planning = wonder_1_modifier_0
army_org_regain = wonder_1_modifier_1
army_org_factor = wonder_1_modifier_2
compliance_growth = wonder_1_modifier_3

2/ Define your wonder's values Head to on_actions/LOK_on_actions and find Line 87. This is where we define the actual values of those modifiers. Add a block of modifiers formatted like so:

[THE STATE ID OF THE WONDER] = {
      set_variable = { wonder = [WONDER ID] }
      add_to_array = { array = wonder_modifiers_values value = [VALUE OF MODIFIER 1] }
      add_to_array = { array = wonder_modifiers_values value = [VALUE OF MODIFIER 2] }
      etc...
}

So you have as many add_to_arrays as there are modifiers for your wonder

Example: the Katown Pyramid, which is in state 509:

509 = {
	set_variable = { wonder = 1 }

	#We store the modifier values in an array
	add_to_array = { array = wonder_modifiers_values value = 0.15 }
	add_to_array = { array = wonder_modifiers_values value = 0.10 }
	add_to_array = { array = wonder_modifiers_values value = 0.10 }
	add_to_array = { array = wonder_modifiers_values value = 0.10 }
}

3/ Define loc and GFX Then its just a matter of defining the picture. Go to interface/wonder_icon.gfx and add the proper entry with the icon for your wonder. For the loc, go to localisation/english/wonders_l_english.yml and add a line for var_wonder.[WONDER ID] and a line for var_wonder_desc.[WONDER ID] You need to manually specify the various variables you've used as modifiers, as shown in the example below:

var_wonder.1: "Grand Katown Pyramid"
var_wonder_desc.1:0 "Max Planning: [?THIS.wonder_1_modifier_0|%+1=]\nDivision Recovery Rate: [?THIS.wonder_1_modifier_1|%+1=]\nDivision Organization: [?THIS.wonder_1_modifier_2|%+1=]\nCompliance Growth: [?THIS.wonder_1_modifier_3|%+1=]\n§LThe heart of the former Katzenartig Imperium, the Katown Pyramid is a gargantuan mile-tall fortified complex housing countless administrative and military command centers, intended to centralize the governance of the Katzen state.§!"

And there you go! The modifiers will automatically be doubled or halved based on if the state is a capital or non-core.

You can then check for the wonder variable in other scopes if you want the presence of a wonder to affect things. For example, the Katown Pyramid (ID = 1) makes its state immune to nukes, so the script that processes nuke devastation will do nothing if the affected state has the "wonder" variable set to 1.

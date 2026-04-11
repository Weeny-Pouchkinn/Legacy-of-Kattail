To create a modifier that changes with a focus:
- create a dynamic modifier in common/dynamic_modifiers/LOK_dynamic_modifiers.txt
- assign every modifier to a variable. the list of modifiers can be found in modifiers_list.txt
- then in the focus tree, add to that variable.

exemple:
MEW_birth_of_communism = {
	enable = { always = yes }
	icon = GFX_idea_MEW_birth_of_communism

	mass_assault_mastery_gain_factor = 0.25
	industrial_capacity_factory = -0.10
	communism_drift = 0.05
	communism_acceptance = 10
	drift_defence_factor = 0.50
	army_attack_factor = MEW_birth_of_communism_army_attack_factor
	army_defence_factor = MEW_birth_of_communism_army_defence_factor
	war_support_factor = MEW_birth_of_communism_war_support_factor
	stability_factor = MEW_birth_of_communism_stability_factor
}

if i want to make MEW get +10% army attack from focus, i do this in the tree
add_to_variable = { MEW_birth_of_communism_army_attack_factor = 0.10 }

then add this loc as a tooltip for the focus
 MEW_birth_of_communism_army_attack_factor_tt:0 "Modify §Y$MEW_birth_of_communism$§! by: \nArmy Attack Factor: §G+10%§!"

you make the modifier green if its good and red if its bad

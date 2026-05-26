import os
import re
import codecs

workspace = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"

def get_state_file(state_id):
    states_dir = os.path.join(workspace, "history", "states")
    prefix = f"{state_id}-"
    for filename in os.listdir(states_dir):
        if filename.startswith(prefix):
            return os.path.join(states_dir, filename)
    raise Exception(f"State file not found for ID: {state_id}")

def edit_file_content(path, edit_fn):
    # Detect encoding
    with open(path, 'rb') as f:
        raw = f.read(3)
    encoding = 'utf-8-sig' if raw == codecs.BOM_UTF8 else 'utf-8'

    with codecs.open(path, 'r', encoding=encoding) as f:
        content = f.read()
    
    # Store original first line/header exactly to ensure it's not modified
    lines = content.splitlines(keepends=True)
    header = lines[0] if lines else ""
    
    # Normalize newline styles for editing
    has_rn = '\r\n' in content
    content_norm = content.replace('\r\n', '\n')
    
    # Run the editor function
    new_content_norm = edit_fn(content_norm)
    
    # Ensure new content starts with exactly the same unmodified first line
    new_lines = new_content_norm.splitlines(keepends=True)
    if new_lines and lines:
        # Check if first line changed and restore it if necessary
        orig_first_line = lines[0].replace('\r\n', '\n').replace('\r', '\n')
        new_first_line = new_lines[0].replace('\r\n', '\n').replace('\r', '\n')
        if orig_first_line != new_first_line:
            new_lines[0] = lines[0].replace('\r\n', '\n')
            new_content_norm = "".join(new_lines)
            
    # Restore original newline style
    if has_rn:
        new_content = new_content_norm.replace('\n', '\r\n')
    else:
        new_content = new_content_norm
        
    with codecs.open(path, 'w', encoding=encoding) as f:
        f.write(new_content)
    print(f"Successfully edited {os.path.basename(path)}")

# 1. Edit lok_culture_l_english.yml
def edit_lok_culture(content):
    # Fix the duplicate line 1022 or other formatting errors if present
    content = content.replace('culture_95_name:0 "§3Katurneri§!"', 'culture_95_name:0 "§3Far Katzen§!"')
    
    if 'culture_96_name' in content:
        print("Culture 96 already in lok_culture_l_english.yml")
        return content

    target = '  remove_culture_group_1_tt:0'
    insertion = (
        '  #AI-Generated Placeholder, change later!\n'
        '  culture_95_name:0 "§3Far Katzen§!" #AI-Generated Placeholder, change later!\n'
        '  culture_95_desc:0 "" #AI-Generated Placeholder, change later!\n'
        '  culture_95_full:0 "$culture_95_name$ is not part of any $culture_group$.$culture_95_desc$" #AI-Generated Placeholder, change later!\n\n'
        '  #AI-Generated Placeholder, change later!\n'
        '  culture_group_15_name:0 "§YGalletian Group§!" #AI-Generated Placeholder, change later!\n'
        '  culture_group_15_desc:0 "\\n§LCultures of Galletian descent or influence.§!" #AI-Generated Placeholder, change later!\n'
        '  remove_culture_group_15_tt:0 "All cultures of the §YGalletian Group§! culture group are §Oremoved§! from the state\'s cultural makeup." #AI-Generated Placeholder, change later!\n\n'
        '  #AI-Generated Placeholder, change later!\n'
        '  culture_96_name:0 "§OBarzintonite§!" #AI-Generated Placeholder, change later!\n'
        '  culture_96_desc:0 "" #AI-Generated Placeholder, change later!\n'
        '  culture_96_full:0 "$culture_96_name$ is part of the $culture_group_15_name$ $culture_group$.$culture_96_desc$" #AI-Generated Placeholder, change later!\n\n'
        '  #AI-Generated Placeholder, change later!\n'
        '  culture_97_name:0 "§YExtremadoughrian§!" #AI-Generated Placeholder, change later!\n'
        '  culture_97_desc:0 "" #AI-Generated Placeholder, change later!\n'
        '  culture_97_full:0 "$culture_97_name$ is part of the $culture_group_15_name$ $culture_group$.$culture_97_desc$" #AI-Generated Placeholder, change later!\n\n'
    )
    return content.replace(target, insertion + target)

edit_file_content(
    f"{workspace}\\localisation\\english\\lok_culture_l_english.yml",
    edit_lok_culture
)

# 2. Edit LOK_culture_scripted_loc.txt
def edit_scripted_loc(content):
    if 'state_cultures^0 = 96' in content:
        print("Culture 96 already in scripted loc")
        return content

    def insert_after(content_str, match_str, insert_str):
        idx = content_str.find(match_str)
        if idx == -1:
            raise Exception(f"Could not find: {repr(match_str)}")
        end_idx = idx + len(match_str)
        return content_str[:end_idx] + insert_str + content_str[end_idx:]

    # GetCulture1
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^0 = 95 } }\n        localization_key = culture_95_name\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^0 = 96 } }\n        localization_key = culture_96_name\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^0 = 97 } }\n        localization_key = culture_97_name\n    }'
    )
    # GetCulture2
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^1 = 95 } }\n        localization_key = culture_95_name\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^1 = 96 } }\n        localization_key = culture_96_name\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^1 = 97 } }\n        localization_key = culture_97_name\n    }'
    )
    # GetCulture3
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^2 = 95 } }\n        localization_key = culture_95_name\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^2 = 96 } }\n        localization_key = culture_96_name\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^2 = 97 } }\n        localization_key = culture_97_name\n    }'
    )
    # GetCulture1Desc
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^0 = 95 } }\n        localization_key = culture_95_full\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^0 = 96 } }\n        localization_key = culture_96_full\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^0 = 97 } }\n        localization_key = culture_97_full\n    }'
    )
    # GetCulture2Desc
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^1 = 95 } }\n        localization_key = culture_95_full\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^1 = 96 } }\n        localization_key = culture_96_full\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^1 = 97 } }\n        localization_key = culture_97_full\n    }'
    )
    # GetCulture3Desc
    content = insert_after(
        content,
        '        trigger = { check_variable = { state_cultures^2 = 95 } }\n        localization_key = culture_95_full\n    }',
        '\n    text = {\n        trigger = { check_variable = { state_cultures^2 = 96 } }\n        localization_key = culture_96_full\n    }'
        '\n    text = {\n        trigger = { check_variable = { state_cultures^2 = 97 } }\n        localization_key = culture_97_full\n    }'
    )
    # GetCultureTemp
    content = insert_after(
        content,
        '        trigger = { check_variable = { culture_temp = 95 } }\n        localization_key = culture_95_name\n    }',
        '\n    text = {\n        trigger = { check_variable = { culture_temp = 96 } }\n        localization_key = culture_96_name\n    }'
        '\n    text = {\n        trigger = { check_variable = { culture_temp = 97 } }\n        localization_key = culture_97_name\n    }'
    )
    return content

edit_file_content(
    f"{workspace}\\common\\scripted_localisation\\LOK_culture_scripted_loc.txt",
    edit_scripted_loc
)

# 3. Edit LOK_culture_map_mode.txt
def edit_map_mode(content):
    if 'Culture 96' in content:
        print("Cultures 96 & 97 already in map mode")
        return content

    target = """\t\t\t\tif = { #Culture 95
					limit = {
						any_of = {
							array = FROM.state_cultures
							value = v
							check_variable = { v = 95 } 
						}
					}
					add_to_temp_variable = { num_cultures = 1 }

					# Define the culture's colors
					add_to_temp_variable = { culture_95_red = 0.0 }
					add_to_temp_variable = { culture_95_green = 0.55 }
					add_to_temp_variable = { culture_95_blue = 0.55 }

					# Divide by the current amount of cultures
					divide_temp_variable = { culture_95_red = num_cultures }
					divide_temp_variable = { culture_95_green = num_cultures }
					divide_temp_variable = { culture_95_blue = num_cultures}

					if = {
						limit = { check_variable = { num_cultures > 1 } }
						set_temp_variable = { culture_color_factor = num_cultures }
						subtract_from_temp_variable = { culture_color_factor = 1 }
						divide_temp_variable = { culture_color_factor = num_cultures }

						# Divide existing colors by this
						multiply_temp_variable = { red = culture_color_factor }
						multiply_temp_variable = { green = culture_color_factor }
						multiply_temp_variable = { blue = culture_color_factor }
					}

					# Add to the existing color
					add_to_temp_variable = { red = culture_95_red }
					add_to_temp_variable = { green = culture_95_green }
					add_to_temp_variable = { blue = culture_95_blue }
				}"""

    insertion = """

\t\t\t\tif = { #Culture 96
\t\t\t\t\tlimit = {
\t\t\t\t\t\tany_of = {
\t\t\t\t\t\t\tarray = FROM.state_cultures
\t\t\t\t\t\t\tvalue = v
\t\t\t\t\t\t\tcheck_variable = { v = 96 } 
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tadd_to_temp_variable = { num_cultures = 1 }

\t\t\t\t\t# Define the culture's colors
\t\t\t\t\tadd_to_temp_variable = { culture_96_red = 0.757 }
\t\t\t\t\tadd_to_temp_variable = { culture_96_green = 0.506 }
\t\t\t\t\tadd_to_temp_variable = { culture_96_blue = 0.196 }

\t\t\t\t\t# Divide by the current amount of cultures
\t\t\t\t\tdivide_temp_variable = { culture_96_red = num_cultures }
\t\t\t\t\tdivide_temp_variable = { culture_96_green = num_cultures }
\t\t\t\t\tdivide_temp_variable = { culture_96_blue = num_cultures}

\t\t\t\t\tif = {
\t\t\t\t\t\tlimit = { check_variable = { num_cultures > 1 } }
\t\t\t\t\t\tset_temp_variable = { culture_color_factor = num_cultures }
\t\t\t\t\t\tsubtract_from_temp_variable = { culture_color_factor = 1 }
\t\t\t\t\t\tdivide_temp_variable = { culture_color_factor = num_cultures }

\t\t\t\t\t\t# Divide existing colors by this
\t\t\t\t\t\tmultiply_temp_variable = { red = culture_color_factor }
\t\t\t\t\t\tmultiply_temp_variable = { green = culture_color_factor }
\t\t\t\t\t\tmultiply_temp_variable = { blue = culture_color_factor }
\t\t\t\t\t}

\t\t\t\t\t# Add to the existing color
\t\t\t\t\tadd_to_temp_variable = { red = culture_96_red }
\t\t\t\t\tadd_to_temp_variable = { green = culture_96_green }
\t\t\t\t\tadd_to_temp_variable = { blue = culture_96_blue }
\t\t\t\t}

\t\t\t\tif = { #Culture 97
\t\t\t\t\tlimit = {
\t\t\t\t\t\tany_of = {
\t\t\t\t\t\t\tarray = FROM.state_cultures
\t\t\t\t\t\t\tvalue = v
\t\t\t\t\t\t\tcheck_variable = { v = 97 } 
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tadd_to_temp_variable = { num_cultures = 1 }

\t\t\t\t\t# Define the culture's colors
\t\t\t\t\tadd_to_temp_variable = { culture_97_red = 0.850 }
\t\t\t\t\tadd_to_temp_variable = { culture_97_green = 0.750 }
\t\t\t\t\tadd_to_temp_variable = { culture_97_blue = 0.150 }

\t\t\t\t\t# Divide by the current amount of cultures
\t\t\t\t\tdivide_temp_variable = { culture_97_red = num_cultures }
\t\t\t\t\tdivide_temp_variable = { culture_97_green = num_cultures }
\t\t\t\t\tdivide_temp_variable = { culture_97_blue = num_cultures}

\t\t\t\t\tif = {
\t\t\t\t\t\tlimit = { check_variable = { num_cultures > 1 } }
\t\t\t\t\t\tset_temp_variable = { culture_color_factor = num_cultures }
\t\t\t\t\t\tsubtract_from_temp_variable = { culture_color_factor = 1 }
\t\t\t\t\t\tdivide_temp_variable = { culture_color_factor = num_cultures }

\t\t\t\t\t\t# Divide existing colors by this
\t\t\t\t\t\tmultiply_temp_variable = { red = culture_color_factor }
\t\t\t\t\t\tmultiply_temp_variable = { green = culture_color_factor }
\t\t\t\t\t\tmultiply_temp_variable = { blue = culture_color_factor }
\t\t\t\t\t}

\t\t\t\t\t# Add to the existing color
\t\t\t\t\tadd_to_temp_variable = { red = culture_97_red }
\t\t\t\t\tadd_to_temp_variable = { green = culture_97_green }
\t\t\t\t\tadd_to_temp_variable = { blue = culture_97_blue }
\t\t\t\t}"""

    idx = content.find(target)
    if idx == -1:
        raise Exception("Could not find culture 95 block in LOK_culture_map_mode.txt")
    end_idx = idx + len(target)
    return content[:end_idx] + insertion + content[end_idx:]

edit_file_content(
    f"{workspace}\\common\\map_modes\\LOK_culture_map_mode.txt",
    edit_map_mode
)

# 4. Edit LOK_culture_effects.txt
def edit_culture_effects(content):
    if 'remove_culture_group_15' in content:
        print("Group 15 already in LOK_culture_effects.txt")
        return content

    insertion = """
remove_culture_group_15 = {
	custom_effect_tooltip = remove_culture_group_15_tt
	hidden_effect = {
		for_each_loop = {
			array = global.culture_group_15_array
			value = v
			set_temp_variable = { culture_temp = v }
			remove_state_culture = yes
		}
	}
}
"""
    return content.strip() + "\n" + insertion

edit_file_content(
    f"{workspace}\\common\\scripted_effects\\LOK_culture_effects.txt",
    edit_culture_effects
)

# 5. Edit LOK_on_actions.txt
def edit_on_actions(content):
    # 5a. Set Group 15 arrays
    if 'global.culture_group_15_array' not in content:
        target_group = "\t\t\t# Group 14 (Arivoejan)"
        idx = content.find(target_group)
        if idx == -1:
            raise Exception("Could not find Group 14 in on_actions")
        
        # Find the end of Group 14 block (which is double newline or STATE CULTURES)
        target_state_cultures = "\t\t\t# STATE CULTURES"
        idx_sc = content.find(target_state_cultures)
        if idx_sc == -1:
            raise Exception("Could not find STATE CULTURES in on_actions")
        
        group_15_code = (
            "\t\t\t# Group 15 (Galletian)\n"
            "\t\t\tadd_to_array = { array = global.culture_group_15_array value = 71 }\n"
            "\t\t\tadd_to_array = { array = global.culture_group_15_array value = 96 } # Barzintonite\n"
            "\t\t\tadd_to_array = { array = global.culture_group_15_array value = 97 } # Extremadoughrian\n\n"
        )
        content = content[:idx_sc] + group_15_code + content[idx_sc:]

    # 5b. Completely rewrite the STATE CULTURES section
    # Let's locate the entire # STATE CULTURES section and rewrite from # Culture 7 up to # Culture 72
    sc_start = content.find("# STATE CULTURES")
    if sc_start == -1:
        raise Exception("Could not find # STATE CULTURES")
    
    # We will find the start of "# Culture 72" to see where the old block ends
    sc_end = content.find("# Culture 72", sc_start)
    if sc_end == -1:
        raise Exception("Could not find # Culture 72 after STATE CULTURES")
    
    # Let's construct the perfect new blocks for Culture 7, 71, 95, 96, 97
    # First, let's keep Culture 7 exactly as it was. Let's extract it.
    idx_71 = content.find("# Culture 71", sc_start)
    if idx_71 == -1 or idx_71 > sc_end:
        raise Exception("Could not find # Culture 71 block")
        
    culture_7_block = content[sc_start:idx_71]
    
    # Now generate the replacement block for Culture 71, 95, 96, 97
    replacement_cultures = """# Culture 71 - Galletian
\t\t\t212 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t252 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t284 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t291 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t300 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t501 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t701 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t890 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t891 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t892 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t893 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1056 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1057 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1058 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1186 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1187 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1188 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1189 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1210 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1211 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1212 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1213 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1359 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1360 = { add_to_array = { array = state_cultures value = 71 } }
\t\t\t1374 = { add_to_array = { array = state_cultures value = 71 } }

\t\t\t# Culture 95 - Far Katzen (SMI & FKS)
\t\t\t247 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t284 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t300 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t1186 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t1187 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t1192 = { add_to_array = { array = state_cultures value = 95 } }
\t\t\t1193 = { add_to_array = { array = state_cultures value = 95 } }

\t\t\t# Culture 96 - Barzintonite (BAZ cores)
\t\t\t1183 = { add_to_array = { array = state_cultures value = 96 } }
\t\t\t1184 = { add_to_array = { array = state_cultures value = 96 } }
\t\t\t1185 = { add_to_array = { array = state_cultures value = 96 } }
\t\t\t1203 = { add_to_array = { array = state_cultures value = 96 } }

\t\t\t# Culture 97 - Extremadoughrian (PGN & KOA cores, plus 290)
\t\t\t234 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t288 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t290 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1173 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1174 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1175 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1178 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1179 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1180 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1191 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1198 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1199 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1200 = { add_to_array = { array = state_cultures value = 97 } }
\t\t\t1202 = { add_to_array = { array = state_cultures value = 97 } }

\t\t\t"""
    content = content[:sc_start] + culture_7_block + replacement_cultures + content[sc_end:]

    # 5c. Superregion assignment change for BAZ
    content = content.replace(
        "BAZ = { every_owned_state = { add_to_array = { array = global.amphibia_superregion_states } } }",
        "BAZ = { every_owned_state = { add_to_array = { array = global.flusionean_desert_superregion_states } } }"
    )

    # 5d. Remove claim on BAZ by FOD
    content = content.replace(
        "\t\t\tBAZ = { every_owned_state = { add_claim_by = FOD } }\n",
        ""
    )

    # 5e. Remove BAZ from ACR Sphere of Influence
    content = content.replace(
        "\t\t\t\t\t\ttag = BAZ\n",
        ""
    )

    # 5f. Remove BAZ from Amphibian defeat white peace
    content = content.replace(
        "\t\t\t\tFOD = { annex_country = { target = BAZ } }\n",
        ""
    )

    # 5g. BAZ country species setup to Roqualian (ID 3)
    # Check if BAZ species array setup is in the file
    content = content.replace(
        "BAZ = { remove_ideas = var_species_0 add_ideas = var_species_24 }",
        "BAZ = { remove_ideas = var_species_0 add_ideas = var_species_3 }"
    )
    content = content.replace(
        "BAZ = { every_owned_state = { set_variable = { species = 24 } } }",
        "BAZ = { every_owned_state = { set_variable = { species = 3 } } }"
    )

    # 5h. State minorities & demilitarized state 290
    if 'Zuspri minorities' not in content:
        target_state_species = "every_state = { set_variable = { minority = 1000 } }"
        idx = content.find(target_state_species)
        if idx == -1:
            raise Exception("Could not find state minority startup section")
        nl_idx = content.find('\n', idx)
        end_line_idx = nl_idx + 1
        
        minorities_code = (
            "\n\t\t\t# Zuspri minorities\n"
            "\t\t\t1191 = { set_variable = { minority = 4 } }\n"
            "\t\t\t1202 = { set_variable = { minority = 4 } }\n"
            "\t\t\t1180 = { set_variable = { minority = 4 } }\n"
            "\t\t\t1179 = { set_variable = { minority = 4 } }\n"
            "\t\t\t1178 = { set_variable = { minority = 4 } }\n"
            "\n\t\t\t# State 290 Galletian species setup\n"
            "\t\t\t290 = { set_variable = { species = 25 } set_variable = { minority = 1000 } }\n"
        )
        content = content[:end_line_idx] + minorities_code + content[end_line_idx:]

    return content

edit_file_content(
    f"{workspace}\\common\\on_actions\\LOK_on_actions.txt",
    edit_on_actions
)

# 6. Edit state files for KOA, PGN, BAZ, GAL and 290
# 6a. KOA owned & cored states: 1191, 1202, 1180, 1178, 1179, 1174, 1175
koa_states = [1191, 1202, 1180, 1178, 1179, 1174, 1175]
def edit_koa_state(content):
    # Set owner to KOA
    content = re.sub(r'owner\s*=\s*\w+', 'owner = KOA', content)
    # Remove existing cores and add only KOA core
    content = re.sub(r'add_core_of\s*=\s*\w+', '', content)
    content = content.replace("history={", "history={\n\t\tadd_core_of = KOA")
    # Clean up empty lines and retain GAL claim if exists or keep standard format
    if "add_claim_by = GAL" not in content:
        content = content.replace("add_core_of = KOA", "add_core_of = KOA\n\t\tadd_claim_by = GAL")
    # Remove duplicates
    content = re.sub(r'\n\s*\n', '\n', content)
    return content

for s in koa_states:
    path = get_state_file(s)
    edit_file_content(path, edit_koa_state)

# 6b. PGN owned & cored states: 288, 1173, 1198, 1199, 234, 1200
pgn_states = [288, 1173, 1198, 1199, 234, 1200]
def edit_pgn_state(content):
    content = re.sub(r'owner\s*=\s*\w+', 'owner = PGN', content)
    content = re.sub(r'add_core_of\s*=\s*\w+', '', content)
    content = content.replace("history={", "history={\n\t\tadd_core_of = PGN")
    if "add_claim_by = GAL" not in content:
        content = content.replace("add_core_of = PGN", "add_core_of = PGN\n\t\tadd_claim_by = GAL")
    content = re.sub(r'\n\s*\n', '\n', content)
    return content

for s in pgn_states:
    path = get_state_file(s)
    edit_file_content(path, edit_pgn_state)

# 6c. BAZ core states: 1183, 1203, 1184, 1185 (owned and cored by GAL)
baz_cores = [1183, 1203, 1184, 1185]
def edit_baz_core(content):
    # GAL remains owner and core
    content = re.sub(r'owner\s*=\s*\w+', 'owner = GAL', content)
    # Ensure add_core_of = GAL and add_core_of = BAZ are present
    if "add_core_of = BAZ" not in content:
        content = content.replace("history={", "history={\n\t\tadd_core_of = BAZ")
    if "add_core_of = GAL" not in content:
        content = content.replace("add_core_of = BAZ", "add_core_of = BAZ\n\t\tadd_core_of = GAL")
    content = re.sub(r'\n\s*\n', '\n', content)
    return content

for s in baz_cores:
    path = get_state_file(s)
    edit_file_content(path, edit_baz_core)

# 6d. State 290 demilitarized zone
def edit_state_290(content):
    if "set_demilitarized_zone = yes" not in content:
        content = content.replace("history={", "history={\n\t\tset_demilitarized_zone = yes")
    content = re.sub(r'\n\s*\n', '\n', content)
    return content

edit_file_content(get_state_file(290), edit_state_290)

# 7. ACR Faction reference clean up
edit_file_content(
    f"{workspace}\\history\\countries\\ACR - Amphibious Confederal Republic.txt",
    lambda content: content.replace("add_to_faction = BAZ\n", "")
)

# 8. Scripted effects BAZ release cleanup
edit_file_content(
    f"{workspace}\\common\\scripted_effects\\LOK_scripted_effects.txt",
    lambda content: content.replace("\trelease_on_controlled = BAZ\n", "")
)

# 9. BAZ country history redefinition
def edit_baz_history(content):
    content = content.replace("ruling_party = communism", "ruling_party = social_conservative")
    # Redefine popularities
    content = re.sub(
        r'set_popularities\s*=\s*\{.*?\}',
        'set_popularities = {\n\tsocial_conservative = 60\n\tneutrality = 10\n\tsocialism = 10\n\tcommunism = 10\n\tfascism = 10\n}',
        content,
        flags=re.DOTALL
    )
    if "BAZ_Albert_Gouraud" not in content:
        content += "\nrecruit_character = BAZ_Albert_Gouraud\n"
    return content

edit_file_content(
    f"{workspace}\\history\\countries\\BAZ - Bogdessa.txt",
    edit_baz_history
)

# 10. BAZ leader character definition
baz_char_path = f"{workspace}\\common\\characters\\BAZ - characters.txt"
baz_char_content = """characters = {
	BAZ_Albert_Gouraud = {
		name = BAZ_Albert_Gouraud
		portraits = {
			civilian = {
				large = "GFX_portrait_roqualian_generic_civilian_1_male"
			}
		}
		country_leader = {
			expire = "1965.1.1"
			ideology = conservatism
		}
	}
}
"""
with codecs.open(baz_char_path, 'w', encoding='utf-8-sig') as f:
    f.write(baz_char_content)
print(f"Created characters file for BAZ: {baz_char_path}")

# 11. Characters localization
def edit_characters_loc(content):
    if 'BAZ_Albert_Gouraud' in content:
        return content
    
    insertion = (
        "\n  #BAZ\n"
        '  BAZ_Albert_Gouraud_Desc:0 "" #AI-Generated Placeholder, change later!\n'
        '  BAZ_Albert_Gouraud:0 "Albert Gouraud" #AI-Generated Placeholder, change later!\n'
    )
    return content.strip() + insertion

edit_file_content(
    f"{workspace}\\localisation\\english\\characters_l_english.yml",
    edit_characters_loc
)

# 12. BAZ country localization rename to Barzintonian Republic
def edit_countries_loc(content):
    # We will replace Slavic name references for BAZ
    content = content.replace(' BAZ:0 "Bodgessa"', ' BAZ:0 "Barzintonian Republic" #AI-Generated Placeholder, change later!')
    content = content.replace(' BAZ_democratic:0 "Bogdessan Republic"', ' BAZ_democratic:0 "Barzintonian Republic" #AI-Generated Placeholder, change later!')
    content = content.replace(' BAZ_social_conservative:0 "Bogdessan Republic"', ' BAZ_social_conservative:0 "Barzintonian Republic" #AI-Generated Placeholder, change later!')
    content = content.replace(' BAZ_democratic_DEF:0 "the Bogdessan Republic"', ' BAZ_democratic_DEF:0 "the Barzintonian Republic" #AI-Generated Placeholder, change later!')
    content = content.replace(' BAZ_social_conservative_DEF:0 "the Bogdessan Republic"', ' BAZ_social_conservative_DEF:0 "the Barzintonian Republic" #AI-Generated Placeholder, change later!')
    content = content.replace(' BAZ_ADJ:0 "Bodgessan"', ' BAZ_ADJ:0 "Barzintonian" #AI-Generated Placeholder, change later!')
    return content

edit_file_content(
    f"{workspace}\\localisation\\english\\countries_l_english.yml",
    edit_countries_loc
)

# 13. Replace BAZ names with Roqualian French names in misc_names.txt
def edit_names(content):
    # The BAZ block is defined twice on lines 985 and 1111 (or similar)
    # Let's locate the ROQ names block and copy its interior
    roq_start = content.find("ROQ = {")
    if roq_start == -1:
        raise Exception("Could not find ROQ names block")
    roq_end = content.find("}", roq_start)
    roq_block_content = content[roq_start:roq_end + 1]
    
    # Generate BAZ replacement block using ROQ structure
    baz_block_replacement = roq_block_content.replace("ROQ", "BAZ")
    
    # Now find all BAZ blocks and replace them
    # Since they are defined as BAZ = { ... }, we'll use a regex replacement
    pattern = r'BAZ = \{.*?\n\}'
    content = re.sub(pattern, baz_block_replacement, content, flags=re.DOTALL)
    return content

edit_file_content(
    f"{workspace}\\common\\names\\misc_names.txt",
    edit_names
)

# 14. Replace BAZ portraits with ROQ portraits in misc_portraits.txt
def edit_portraits(content):
    roq_start = content.find("ROQ = {")
    if roq_start == -1:
        raise Exception("Could not find ROQ portraits block")
    # Locate matching closing bracket of ROQ block
    # Since the ROQ block has nested brackets, let's parse brackets to find the end index
    brackets = 0
    roq_end = -1
    for idx in range(roq_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                roq_end = idx
                break
    if roq_end == -1:
        raise Exception("Could not find ROQ closing bracket")
        
    roq_block_content = content[roq_start:roq_end + 1]
    baz_block_replacement = roq_block_content.replace("ROQ", "BAZ")
    
    # Find and replace the BAZ block in the file
    baz_start = content.find("BAZ = {")
    if baz_start == -1:
        raise Exception("Could not find BAZ portraits block")
    brackets = 0
    baz_end = -1
    for idx in range(baz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                baz_end = idx
                break
    if baz_end == -1:
        raise Exception("Could not find BAZ closing bracket")
        
    return content[:baz_start] + baz_block_replacement + content[baz_end + 1:]

edit_file_content(
    f"{workspace}\\portraits\\misc_portraits.txt",
    edit_portraits
)

# 15. BAZ generic advisors update
def edit_generic_advisors(content):
    # Find ROQ block
    roq_start = content.find("ROQ = {")
    if roq_start == -1:
        raise Exception("Could not find ROQ advisors block")
    brackets = 0
    roq_end = -1
    for idx in range(roq_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                roq_end = idx
                break
    if roq_end == -1:
        raise Exception("Could not find ROQ closing bracket")
        
    roq_block_content = content[roq_start:roq_end + 1]
    
    # Replace prefixes in ROQ to get the perfect BAZ advisors block
    baz_block_replacement = roq_block_content.replace("ROQ = {", "BAZ = {")
    baz_block_replacement = baz_block_replacement.replace("ROQ_gen_", "BAZ_gen_")
    
    # Locate BAZ block to replace
    baz_start = content.find("BAZ = {")
    if baz_start == -1:
        raise Exception("Could not find BAZ advisors block")
    brackets = 0
    baz_end = -1
    for idx in range(baz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                baz_end = idx
                break
    if baz_end == -1:
        raise Exception("Could not find BAZ advisors closing bracket")
        
    return content[:baz_start] + baz_block_replacement + content[baz_end + 1:]

edit_file_content(
    f"{workspace}\\history\\general\\generic_advisors.txt",
    edit_generic_advisors
)

# 16. GAL OOB Division Relocations
def edit_gal_oob(content):
    # Replace division starting locations from SMI/FKS/lost states to owned provinces
    content = content.replace("location = 1987", "location = 814")
    content = content.replace("location = 6779", "location = 814")
    content = content.replace("location = 17094", "location = 814")
    content = content.replace("location = 2265", "location = 814")
    content = content.replace("location = 310", "location = 814")
    content = content.replace("location = 567", "location = 814")
    content = content.replace("location = 9081", "location = 17881")
    content = content.replace("location = 2526", "location = 17881")
    content = content.replace("location = 17533", "location = 17881")
    return content

edit_file_content(
    f"{workspace}\\history\\units\\GAL_1936.txt",
    edit_gal_oob
)

# 17. SMI Ground OOB (SMI_1936.txt)
smi_oob_path = f"{workspace}\\history\\units\\SMI_1936.txt"
smi_oob_content = """##### Division Templates #####
division_template = {
	name = "Smileycatia Regulars"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
		infantry = { x = 2 y = 0 }
		infantry = { x = 2 y = 1 }
		infantry = { x = 2 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
	}
}

division_template = {
	name = "Smileycatia Garrison"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
	}
}

division_template = {
	name = "Smileycatia Mobile Troops"
	regiments = {
		motorized = { x = 0 y = 0 }
		motorized = { x = 0 y = 1 }
		motorized = { x = 0 y = 2 }
		motorized = { x = 1 y = 0 }
		motorized = { x = 1 y = 1 }
		motorized = { x = 1 y = 2 }
		mot_artillery_brigade = { x = 2 y = 0 }
	}
	support = {
		artillery = { x = 0 y = 0 }
		mot_recon = { x = 0 y = 1 }
	}
}

division_template = {
	name = "Smileycatia Armored Force"
	regiments = {
		mechanized = { x = 0 y = 0 }
		mechanized = { x = 0 y = 1 }
		mechanized = { x = 0 y = 2 }
		light_armor = { x = 1 y = 0 }
		light_armor = { x = 1 y = 1 }
		light_armor = { x = 1 y = 2 }
	}
	support = {
		light_tank_recon = { x = 0 y = 0 }
		engineer = { x = 0 y = 1 }
		artillery = { x = 0 y = 2 }
	}
}

units = {
	division = { name = "1st Cookartagena Regulars" location = 1987 division_template = "Smileycatia Regulars" start_experience_factor = 0.3 }
	division = { name = "1st Granajón Regulars" location = 9081 division_template = "Smileycatia Regulars" start_experience_factor = 0.3 }
	division = { name = "1st San-Sebakestian Garrison" location = 2526 division_template = "Smileycatia Garrison" start_experience_factor = 0.3 }
	division = { name = "1st Granajón Mobile" location = 9081 division_template = "Smileycatia Mobile Troops" start_experience_factor = 0.3 }
	division = { name = "1st Granajón Armored" location = 9081 division_template = "Smileycatia Armored Force" start_experience_factor = 0.4 }
}

instant_effect = {
	add_equipment_production = {
		equipment = {
			type = infantry_equipment_1
			creator = "SMI"
		}
		requested_factories = 5
		progress = 0.4
		efficiency = 50
	}
	add_equipment_production = {
		equipment = {
			type = support_equipment_1
			creator = "SMI"
		}
		requested_factories = 1
		progress = 0.4
		efficiency = 50
	}
}
"""
with codecs.open(smi_oob_path, 'w', encoding='utf-8-sig') as f:
    f.write(smi_oob_content)
print(f"Created SMI ground OOB: {smi_oob_path}")

# 18. FKS Ground OOB (FKS_1936.txt)
fks_oob_path = f"{workspace}\\history\\units\\FKS_1936.txt"
fks_oob_content = """##### Division Templates #####
division_template = {
	name = "Katurneri Regulars"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
		infantry = { x = 2 y = 0 }
		infantry = { x = 2 y = 1 }
		infantry = { x = 2 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
	}
}

division_template = {
	name = "Katurneri Garrison"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
	}
}

division_template = {
	name = "Katurneri Mobile Troops"
	regiments = {
		motorized = { x = 0 y = 0 }
		motorized = { x = 0 y = 1 }
		motorized = { x = 0 y = 2 }
		motorized = { x = 1 y = 0 }
		motorized = { x = 1 y = 1 }
		motorized = { x = 1 y = 2 }
		mot_artillery_brigade = { x = 2 y = 0 }
	}
	support = {
		artillery = { x = 0 y = 0 }
		mot_recon = { x = 0 y = 1 }
	}
}

division_template = {
	name = "Katurneri Armored Force"
	regiments = {
		mechanized = { x = 0 y = 0 }
		mechanized = { x = 0 y = 1 }
		mechanized = { x = 0 y = 2 }
		light_armor = { x = 1 y = 0 }
		light_armor = { x = 1 y = 1 }
		light_armor = { x = 1 y = 2 }
	}
	support = {
		light_tank_recon = { x = 0 y = 0 }
		engineer = { x = 0 y = 1 }
		artillery = { x = 0 y = 2 }
	}
}

units = {
	division = { name = "1st Valledupùr Regulars" location = 2265 division_template = "Katurneri Regulars" start_experience_factor = 0.3 }
	division = { name = "1st Crumbrid Regulars" location = 17533 division_template = "Katurneri Regulars" start_experience_factor = 0.3 }
	division = { name = "1st Solemom Regulars" location = 6779 division_template = "Katurneri Regulars" start_experience_factor = 0.3 }
	division = { name = "1st Valledupùr Garrison" location = 2265 division_template = "Katurneri Garrison" start_experience_factor = 0.3 }
	division = { name = "1st Crumbrid Mobile" location = 17533 division_template = "Katurneri Mobile Troops" start_experience_factor = 0.3 }
	division = { name = "1st Solemom Armored" location = 6779 division_template = "Katurneri Armored Force" start_experience_factor = 0.4 }
}

instant_effect = {
	add_equipment_production = {
		equipment = {
			type = infantry_equipment_1
			creator = "FKS"
		}
		requested_factories = 6
		progress = 0.4
		efficiency = 50
	}
	add_equipment_production = {
		equipment = {
			type = support_equipment_1
			creator = "FKS"
		}
		requested_factories = 1
		progress = 0.4
		efficiency = 50
	}
}
"""
with codecs.open(fks_oob_path, 'w', encoding='utf-8-sig') as f:
    f.write(fks_oob_content)
print(f"Created FKS ground OOB: {fks_oob_path}")

# 19. SMI and FKS history files OOB assignment
def edit_smi_oob_assignment(content):
    if "set_oob" not in content:
        content = content.replace("capital = 1186", "capital = 1186\nset_oob = \"SMI_1936\"")
    return content

edit_file_content(
    f"{workspace}\\history\\countries\\SMI - Smileycatia.txt",
    edit_smi_oob_assignment
)

def edit_fks_oob_assignment(content):
    if "set_oob" not in content:
        content = content.replace("capital = 300", "capital = 300\nset_oob = \"FKS_1936\"")
    return content

edit_file_content(
    f"{workspace}\\history\\countries\\FKS - Far Katzen State.txt",
    edit_fks_oob_assignment
)

print("ALL EDITS COMPLETED SUCCESSFULLY!")

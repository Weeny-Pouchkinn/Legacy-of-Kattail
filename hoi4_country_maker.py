
import os
import re
import glob  # Importing the glob module

def main():
    # User inputs
    tag = input("Country Tag (e.g., SAR): ").strip().upper()
    if len(tag) != 3:
        print("Error: The country tag must be exactly 3 letters.")
        return

    color = input("Country Color (e.g., 24 214 42): ").strip()
    ideology = input("Ideology of the country (e.g., democratic): ").strip()
    name_ideology = input("Name under that ideology: ").strip()
    name_generic = input("Generic name of the country: ").strip()
    adjective = input("Country Adjective: ").strip()
    states = input("States (e.g., 1 43 351 35): ").strip().split()

    # File paths relative to the mod's root folder
    country_tags_file = "common/country_tags/00_countries.txt"
    if tag_exists_in_file(country_tags_file, tag):
        print(f"Error: The tag {tag} already exists in {country_tags_file}.")
        return

    colors_file = "common/countries/colors.txt"
    country_file = f"common/countries/{tag}.txt"
    history_country_file = f"history/countries/{tag} - {name_ideology}.txt"
    localisation_file = "localisation/english/countries_l_english.yml"
    template_history_file = "history/countries/TEMPLATE.txt"

    # Update and create files
    append_to_file(country_tags_file, f'{tag} = "countries/{tag}.txt" #{name_ideology}\n')
    append_to_file(colors_file, f"\n{tag} = {{ color = rgb {{ {color} }} color_ui = rgb {{ {color} }} }}\n")
    write_country_file(country_file, color)
    copy_and_modify_template(template_history_file, history_country_file, tag, ideology)
    append_to_localisation(localisation_file, tag, name_ideology, name_generic, adjective, ideology)
    modify_state_files(states, tag)

def tag_exists_in_file(filename, tag):
    with open(filename, 'r') as file:
        if tag in file.read():
            return True
    return False

def append_to_file(filename, content):
    with open(filename, 'a') as file:
        file.write(content)

def write_country_file(filename, color):
    with open(filename, 'w') as file:
        file.write("graphical_culture = western_european_gfx\n")
        file.write("graphical_culture_2d = western_european_2d\n")
        file.write(f"color = rgb {{ {color} }}\n")

def copy_and_modify_template(src, dest, tag, ideology):
    with open(src, 'r') as source_file:
        content = source_file.read()
    modified_content = content.replace('ruling_party = neutrality', f'ruling_party = {ideology}')
    with open(dest, 'w') as dest_file:
        dest_file.write(modified_content)

def append_to_localisation(filename, tag, name_ideology, name_generic, adjective, ideology):
    with open(filename, 'a') as file:
        file.write("\n\n")
        file.write(f" #{name_ideology}\n")
        file.write(f" {tag}_{ideology.lower()}:0 \"{name_ideology}\"\n")
        file.write(f" {tag}_{ideology.lower()}_DEF:0 \"the {name_ideology}\"\n")
        file.write(f" {tag}_ADJ:0 \"{adjective}\"\n")
        file.write(f" {tag}:0 \"{name_generic}\"\n")

def modify_state_files(states, tag):
    for state in states:
        state_file_pattern = f"history/states/*_{state}.txt"
        for filepath in glob.glob(state_file_pattern):
            modify_state_file(filepath, tag)

def modify_state_file(filepath, tag):
    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    index = next((i for i, line in enumerate(lines) if 'manpower' in line), None)
    if index is not None:
        # Adjusted tabulation
        new_content = '\thistory={\n\t\towner = ' + tag + '\n\t\tadd_core_of = ' + tag + '\n\t}\n'
        lines.insert(index, new_content)

    with open(filepath, 'w') as file:
        file.writelines(lines)

if __name__ == "__main__":
    main()

"""Import EU4 bookmark countries into existing ZZZ states; dry run by default.

Uses the painter's source-span parser and preserves source bytes outside edits.
No province/state geometry, existing localisation or established owners change.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "legacy_of_kattail_painter"))
from model import child, parse, scalar, value, walk  # noqa: E402
from source_io import encode_source  # noqa: E402

DATE = (100, 1, 1, 12)
ALIASES = {"LRN": "LAK", "NOV": "NFS"}
EXCLUDED_TAGS = {"MGA"}  # User explicitly excluded Meogartha.
REPORT = ROOT / "modding_documentation/agent_memory/eu4_zzz_import"
BACKUP = ROOT / "work/zzz-eu4-import/before"
EMPTY_OOB = "LOK_eu4_import_empty"
DATE_KEY = re.compile(r"\d+\.\d+\.\d+(?:\.\d+)?")
TAG_KEY = re.compile(r"[A-Z][A-Z0-9]{2}")
INPUTS: dict[Path, bytes] = {}


def read(path):
    path = Path(path)
    blob = INPUTS.setdefault(path, path.read_bytes())
    try:
        return blob.decode("utf-8-sig")
    except UnicodeDecodeError:
        return blob.decode("cp1252")


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def dated(nodes):
    result = [n for n in nodes if not DATE_KEY.fullmatch(n.key)]
    dates = sorted((n for n in nodes if DATE_KEY.fullmatch(n.key)),
                   key=lambda n: tuple(map(int, n.key.split("."))))
    for node in dates:
        stamp = tuple(map(int, node.key.split(".")))
        if stamp + (0,) * (4 - len(stamp)) <= DATE:
            result.extend(dated(node.children))
    return result


def registry(root):
    result = {}
    for path in sorted((root / "common/country_tags").glob("*.txt")):
        text = read(path)
        dynamic = False
        for node in parse(text):
            if node.key == "dynamic_tags":
                dynamic = scalar(text, [node], node.key) == "yes"
            if TAG_KEY.fullmatch(node.key) and not dynamic:
                if node.key in result:
                    raise ValueError(f"Duplicate static country tag: {node.key}")
                result[node.key] = scalar(text, [node], node.key)
    return result


def localisation(root):
    result = {}
    for path in sorted((root / "localisation").rglob("*l_english.yml")):
        for line in read(path).splitlines():
            match = re.match(r'\s*([^\s:#]+):\d*\s*"((?:\\.|[^"\\])*)"', line)
            if match:
                result[match[1]] = match[2]
    return result


def resolve(text, loc):
    for _ in range(12):
        new = re.sub(r"\$([^$]+)\$", lambda m: loc.get(m[1], m[0]), text)
        if new == text:
            break
        text = new
    return text


def raster(root):
    lookup = np.zeros(1 << 24, dtype=np.uint16)
    definitions = {}
    for line in read(root / "map/definition.csv").splitlines():
        fields = line.split(";")
        if len(fields) > 3 and fields[0].isdigit():
            pid, red, green, blue = map(int, fields[:4])
            definitions[pid] = fields
            lookup[(red << 16) | (green << 8) | blue] = pid
    path = root / "map/provinces.bmp"
    INPUTS[path] = path.read_bytes()
    rgb = np.array(Image.open(io.BytesIO(INPUTS[path])).convert("RGB"), dtype=np.uint32)
    return lookup[(rgb[:, :, 0] << 16) | (rgb[:, :, 1] << 8) | rgb[:, :, 2]], definitions


def states():
    result = {}
    for path in sorted((ROOT / "history/states").glob("*.txt")):
        text = read(path)
        nodes = child(parse(text), "state").children
        histories = [node for node in nodes if node.key == "history"]
        if len(histories) != 1:
            raise ValueError(f"{path.relative_to(ROOT)} has {len(histories)} history blocks; expected exactly one")
        history = histories[0].children
        sid = int(scalar(text, nodes, "id"))
        result[sid] = dict(path=path.relative_to(ROOT).as_posix(),
                           owner=scalar(text, history, "owner"),
                           provinces=[int(n.key) for n in child(nodes, "provinces").children])
    return result


def geography(eu4, source_tags, current):
    hr, _ = raster(ROOT)
    er, _ = raster(eu4)
    if hr.shape != er.shape:
        raise ValueError("Maps must have matching dimensions; no inferred scaling/cropping")
    excluded = {0}
    for filename, keys in [("default.map", ["sea_starts", "lakes"]),
                           ("climate.txt", ["impassable"])]:
        nodes = parse(read(eu4 / "map" / filename))
        for key in keys:
            node = child(nodes, key)
            if node:
                excluded.update(int(n.key) for n in node.children)
    provinces = {}
    for path in sorted((eu4 / "history/provinces").glob("*.txt")):
        match = re.match(r"(\d+)", path.name)
        if match:
            text = read(path)
            nodes = dated(parse(text))
            owner = scalar(text, nodes, "owner")
            provinces[int(match[1])] = dict(owner=owner if owner in source_tags else "",
                                           path=path.relative_to(eu4).as_posix())
    tags = [""] + sorted(source_tags)
    tag_index = {tag: i for i, tag in enumerate(tags)}
    owner_lookup = np.zeros(int(er.max()) + 1, dtype=np.uint16)
    for pid, province in provinces.items():
        owner_lookup[pid] = tag_index[province["owner"]]
    state_lookup = np.zeros(int(hr.max()) + 1, dtype=np.uint16)
    for sid, state in current.items():
        state_lookup[state["provinces"]] = sid
    sr = state_lookup[hr]
    valid = (sr > 0) & ~np.isin(er, list(excluded))
    stride = len(tags)
    votes = np.bincount(sr[valid].astype(np.int64) * stride + owner_lookup[er[valid]],
                        minlength=(max(current) + 1) * stride).reshape(-1, stride)
    records = []
    for sid, state in sorted(current.items()):
        if state["owner"] != "ZZZ":
            continue
        row = votes[sid]
        ranking = sorted(((tags[i], int(n)) for i, n in enumerate(row) if n),
                         key=lambda item: (-item[1], item[0]))
        winner = ranking[0][0] if ranking else ""
        if len(ranking) > 1 and ranking[0][1] == ranking[1][1]:
            raise ValueError(f"State {sid} has a tied source ownership vote")
        target = ALIASES.get(winner, winner) if winner not in EXCLUDED_TAGS else ""
        records.append(dict(id=sid, path=state["path"], source=winner,
                            target=target or "ZZZ", habitable_pixels=int(row.sum()),
                            votes=ranking))
    active = sorted({x["source"] for x in records if x["target"] != "ZZZ"})
    # Existing major countries must match at the same map coordinates.
    agreement = sum(int(votes[sid, tag_index[state["owner"]]])
                    for sid, state in current.items() if state["owner"] in tag_index
                    and state["owner"] not in {"ZZZ", "WWW"})
    if agreement < 100000:
        raise ValueError("Insufficient geographic agreement with established HOI4 owners")
    return records, active, er, hr, sr, provinces, agreement


def edits(text, replacements):
    for start, end, new in sorted(replacements, reverse=True):
        text = text[:start] + new + text[end:]
    return text


def set_scalar(text, key, new):
    matches = [n for n in parse(text) if n.key == key and n.children is None]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous repeated root key {key}")
    if matches:
        node = matches[0]
        return edits(text, [(node.value_start, node.end, new)])
    newline = "\r\n" if "\r\n" in text else "\n"
    return text + newline + f"{key} = {new}" + newline


def plan(eu4):
    existing_tags = registry(ROOT)
    source_tags = registry(eu4)
    current = states()
    records, active, er, hr, sr, provinces, agreement = geography(eu4, source_tags, current)
    target_tags = {ALIASES.get(tag, tag) for tag in active}
    if len(target_tags) != len(active):
        raise ValueError("Source tag aliases collide")
    if target_tags & {s["owner"] for s in current.values() if s["owner"] != "ZZZ"}:
        raise ValueError("An imported tag already owns states; manual review required")
    loc = localisation(ROOT)
    source_loc = localisation(eu4)
    meta_path = eu4 / "tools/culture_painter/country_painter_data.json"
    meta = json.loads(read(meta_path))["countries"]
    ideology_text = read(ROOT / "common/ideologies/00_ideologies.txt")
    ideologies = child(parse(ideology_text), "ideologies").children
    parents = {n.key: group.key for group in ideologies
               for n in child(group.children, "types").children}
    source_ideologies = json.loads(read(eu4 / "ideology-merge-audit.json"))["survivors"]
    renamed = json.loads(read(eu4 / "ideology-merge-round2-audit.json"))["renamed"]
    reverse_aliases = {entry["id"]: old for old, entry in renamed.items()}
    characters = {}
    for path in sorted((ROOT / "common/characters").glob("*.txt")):
        text = read(path)
        for block in parse(text):
            if block.key.lower() == "characters":
                for node in block.children:
                    characters[node.key] = (text, node.children)
    outputs = {}
    newloc = {}
    countries = []
    new_characters = []

    def stage(relative, text):
        path = ROOT / relative
        original = INPUTS.setdefault(path, path.read_bytes()) if path.exists() else None
        blob = encode_source(text, original) if original is not None else text.encode("utf-8")
        if blob != original:
            outputs[relative] = blob

    for record in records:
        if record["target"] == "ZZZ":
            continue
        path = ROOT / record["path"]
        text = read(path)
        nodes = child(parse(text), "state").children
        hist = child(nodes, "history").children
        replacements = []
        for node in hist:
            if node.key in {"owner", "controller", "add_core_of"} and scalar(text, [node], node.key) == "ZZZ":
                replacements.append((node.value_start, node.end, record["target"]))
        if not any(n.key == "add_core_of" and scalar(text, [n], n.key) in {"ZZZ", record["target"]} for n in hist):
            owner = next(n for n in hist if n.key == "owner")
            newline = "\r\n" if "\r\n" in text else "\n"
            replacements.append((owner.end, owner.end, newline + "\t\tadd_core_of = " + record["target"]))
        stage(record["path"], edits(text, replacements))

    tagfile = ROOT / "common/country_tags/00_countries.txt"
    tagtext = read(tagfile)
    extra_tags = []
    colors_path = ROOT / "common/countries/colors.txt"
    colors_text = read(colors_path)
    colors_nodes = parse(colors_text)
    color_edits = []
    species_blocks = []
    for source in active:
        tag = ALIASES.get(source, source)
        history_paths = sorted((eu4 / "history/countries").glob(source + "*.txt"))
        if len(history_paths) != 1:
            raise ValueError(f"Expected one EU4 country history for {source}")
        source_text = read(history_paths[0])
        source_nodes = dated(parse(source_text))
        source_capital = int(scalar(source_text, source_nodes, "capital"))
        owned = [x["id"] for x in records if x["target"] == tag]
        counts = np.bincount(sr[er == source_capital], minlength=max(current) + 1)
        capital = max(owned, key=lambda sid: (int(counts[sid]), -sid))
        capital_method = "largest overlap with EU4 capital province"
        if not counts[capital]:
            old_paths = sorted((ROOT / "history/countries").glob(tag + "*.txt"))
            old_capital = int(scalar(read(old_paths[0]), parse(read(old_paths[0])), "capital", "0")) if old_paths else 0
            capital = old_capital if old_capital in owned else max(owned, key=lambda sid: (len(current[sid]["provinces"]), -sid))
            capital_method = "existing owned capital" if old_capital == capital else "largest owned state (capital outside imported land)"
        source_def = read(eu4 / "common" / source_tags[source])
        color_node = child(parse(source_def), "color")
        color = [int(n.key) for n in color_node.children]
        if len(color) != 3 or any(n < 0 or n > 255 for n in color):
            raise ValueError(f"Invalid source RGB for {source}")
        color_value = "rgb { " + " ".join(map(str, color)) + " }"
        relative_def = "common/" + existing_tags.get(tag, f"countries/{tag}.txt")
        def_path = ROOT / relative_def
        if def_path.exists():
            text = read(def_path)
            node = child(parse(text), "color")
            stage(relative_def, edits(text, [(node.value_start, node.end, color_value)]))
        else:
            stage(relative_def, "graphical_culture = western_european_gfx\n"
                  "graphical_culture_2d = western_european_2d\n" + f"color = {color_value}\n")
        for node in colors_nodes:
            if node.key == tag and node.children is not None:
                for field in node.children:
                    if field.key in {"color", "color_ui"}:
                        color_edits.append((field.value_start, field.end, color_value))
        if tag not in existing_tags:
            pattern = rf'(?m)^#(?={re.escape(tag)}\s*=\s*"countries/)'
            tagtext, matches = re.subn(pattern, "", tagtext)
            if matches > 1:
                raise ValueError(f"Multiple dormant tag declarations for {tag}")
            if not matches:
                extra_tags.append(f'{tag} = "countries/{tag}.txt"')
        history_paths_hoi = sorted((ROOT / "history/countries").glob(tag + "*.txt"))
        if len(history_paths_hoi) > 1:
            raise ValueError(f"Multiple HOI4 histories for {tag}")
        source_ideology = scalar(source_text, source_nodes, "religion")
        upstream = source_ideologies.get(source_ideology, {}).get("from", reverse_aliases.get(source_ideology, source_ideology))
        subtype = upstream.removeprefix("lok_ideology_")
        if subtype not in parents:
            raise ValueError(f"No documented reverse ideology mapping for {source_ideology}")
        party = parents[subtype]
        history_new = not history_paths_hoi
        leader = None
        primary = scalar(source_text, source_nodes, "primary_culture")
        match = re.fullmatch(r"lok_species_(\d+)", primary)
        species = int(match[1]) if match else None
        if species is None:
            for path in sorted((eu4 / "common/cultures").glob("*.txt")):
                text = read(path)
                for _, node in walk(parse(text)):
                    if node.key == primary and node.children is not None:
                        gfx = scalar(text, node.children, "graphical_culture")
                        match = re.fullmatch(r"lok_species_(\d+)gfx", gfx)
                        if match:
                            species = int(match[1])
        if species is None:
            raise ValueError(f"No verified species mapping for {source}: {primary}")
        if history_new:
            # Preserve named HOI4 characters where their identity and party agree.
            monarchs = [n for n in source_nodes if n.key == "monarch" and n.children is not None]
            monarch = monarchs[-1].children if monarchs else None
            if monarch:
                name = " ".join(filter(None, [scalar(source_text, monarch, "name"), scalar(source_text, monarch, "dynasty")]))
                for charid, (chartext, charnodes) in characters.items():
                    if not charid.startswith(tag + "_"):
                        continue
                    name_key = scalar(chartext, charnodes, "name")
                    charname = resolve(loc.get(name_key, name_key), loc)
                    roles = [n for n in charnodes if n.key == "country_leader"]
                    if charname == name and any(parents.get(scalar(chartext, n.children, "ideology")) == party for n in roles):
                        leader = charid
                        subtype = next(scalar(chartext, n.children, "ideology") for n in roles if parents.get(scalar(chartext, n.children, "ideology")) == party)
                        break
                if leader is None:
                    leader = tag + "_eu4_import_leader"
                    if leader in characters or leader in loc:
                        raise ValueError(f"Leader ID collision: {leader}")
                    newloc[leader] = name
                    portrait = f"GFX_portrait_species_{species}_civilian_1"
                    # All species use the project's existing portrait catalog.
                    new_characters.append(f'\t{leader} = {{\n\t\tname = {leader}\n'
                        + ('\t\tgender = female\n' if scalar(source_text, monarch, "female") == "yes" else '')
                        + f'\t\tportraits = {{ civilian = {{ large = {portrait} small = {portrait} }} }}\n'
                        + f'\t\tcountry_leader = {{ ideology = {subtype} expire = "1965.1.1" }}\n\t}}\n')
            relative_history = f"history/countries/{tag} - EU4 import.txt"
            text = f"# Starting setup imported from EU4 {source}, 100.1.1.\ncapital = {capital}\n"
            text += f'oob = "{EMPTY_OOB}"\nset_research_slots = 3\nset_stability = 0.5\nset_war_support = 0.5\n'
            text += "set_technology = {\n\tinfantry_weapons = 1\n\ttech_support = 1\n\ttech_engineers = 1\n\tbasic_train = 1\n\ttech_trucks = 1\n}\n"
            if leader:
                text += f"recruit_character = {leader}\n"
            text += f"set_politics = {{ ruling_party = {party} elections_allowed = no }}\nset_popularities = {{ {party} = 100 }}\n"
            stage(relative_history, text)
        else:
            relative_history = history_paths_hoi[0].relative_to(ROOT).as_posix()
            text = set_scalar(read(history_paths_hoi[0]), "capital", str(capital))
            party = scalar(text, child(parse(text), "set_politics").children, "ruling_party")
            # These dormant histories often point at the unrelated KTZ army.
            # Keep a valid country-specific OOB; otherwise load an explicit empty one.
            oob = scalar(text, parse(text), "oob")
            valid_oob = False
            if oob.startswith(tag + "_") and (ROOT / "history/units" / (oob + ".txt")).is_file():
                oob_text = read(ROOT / "history/units" / (oob + ".txt"))
                parse(oob_text)
                locations = [int(scalar(oob_text, [n], n.key)) for _, n in walk(parse(oob_text))
                             if n.key in {"location", "base"} and n.children is None]
                own_provinces = {pid for sid in owned for pid in current[sid]["provinces"]}
                valid_oob = all(pid in own_provinces for pid in locations)
            if not valid_oob:
                text = set_scalar(text, "oob", f'"{EMPTY_OOB}"')
            stage(relative_history, text)
        name = resolve(source_loc[source], source_loc)
        adjective = resolve(source_loc.get(source + "_ADJ", name), source_loc)
        # Fill gaps only: never overwrite authored HOI4 country names.
        for key, text in {tag: name, tag + "_DEF": name, tag + "_ADJ": adjective,
                          tag + "_" + party: name, tag + "_" + party + "_DEF": name,
                          tag + "_" + party + "_ADJ": adjective}.items():
            if key not in loc:
                newloc[key] = text
        flag_path = eu4 / "gfx/flags" / (source + ".tga")
        INPUTS[flag_path] = flag_path.read_bytes()
        flag = Image.open(io.BytesIO(INPUTS[flag_path])).convert("RGB")
        for folder, size in [("", (82, 52)), ("medium/", (41, 26)), ("small/", (10, 7))]:
            for suffix in ["", "_" + party]:
                relative = f"gfx/flags/{folder}{tag}{suffix}.tga"
                path = ROOT / relative
                if path.exists():
                    INPUTS[path] = path.read_bytes()
                out = io.BytesIO()
                flag.resize(size, Image.Resampling.LANCZOS).save(out, format="TGA")
                if INPUTS.get(path) != out.getvalue():
                    outputs[relative] = out.getvalue()
        if history_new:
            species_blocks.append(f"\t\t\t{tag} = {{ remove_ideas = var_species_0 add_ideas = var_species_{species} }}\n")
        countries.append(dict(source=source, tag=tag, name=name, states=owned,
            capital=capital, capital_method=capital_method, eu4_capital=source_capital,
            definition=relative_def, history=relative_history, history_created=history_new,
            tag_previously_active=tag in existing_tags, ruling_party=party,
            source_ideology=source_ideology, species=species, leader=leader,
            source_history=history_paths[0].relative_to(eu4).as_posix(),
            display_name=resolve(loc.get(tag + "_" + party, name), loc),
            flag_source=flag_path.relative_to(eu4).as_posix(),
            flat_source_flag=len(flag.getcolors(flag.width * flag.height)) == 1))
    stage("common/country_tags/00_countries.txt", tagtext)
    if extra_tags:
        stage("common/country_tags/01_eu4_zzz_countries.txt", "# EU4 nations in former ZZZ states.\n" + "\n".join(extra_tags) + "\n")
    stage("common/countries/colors.txt", edits(colors_text, color_edits))
    stage(f"history/units/{EMPTY_OOB}.txt", "# No HOI4 military deployment was specified by the EU4 country import.\nunits = {\n}\n")
    if new_characters:
        stage("common/characters/LOK_eu4_import_characters.txt", "characters = {\n" + "".join(new_characters) + "}\n")
    if newloc:
        # Existing files are untouched; text is copied from the source mod.
        lines = [f' {key}:0 "{text}"' for key, text in sorted(newloc.items())]
        outputs["localisation/english/LOK_eu4_import_l_english.yml"] = ("l_english:\n" + "\n".join(lines) + "\n").encode("utf-8-sig")
    if species_blocks:
        relative = "common/on_actions/LOK_on_actions.txt"
        text = read(ROOT / relative)
        marker = "\t\t\t#Katzens"
        if text.count(marker) != 1:
            raise ValueError("Country-species insertion point is ambiguous")
        newline = "\r\n" if "\r\n" in text else "\n"
        block = "\t\t\t# Countries restored from the EU4 bookmark.\n" + "".join(species_blocks) + "\n"
        stage(relative, text.replace(marker, block.replace("\n", newline) + marker, 1))
    for relative, blob in outputs.items():
        if relative.endswith(".txt"):
            parse(blob.decode("utf-8-sig"))
    # Snapshot all coupled trees, including existing user edits, before applying.
    protected = {}
    for folder in ["history", "common", "map", "interface", "gfx/flags", "localisation", "legacy_of_kattail_painter"]:
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and not any(x in {"backups", "__pycache__"} for x in path.parts):
                relative = path.relative_to(ROOT).as_posix()
                if relative not in outputs:
                    protected[relative] = sha(path.read_bytes())
    result = dict(date="100.1.1.12", source_root=str(eu4), aliases=ALIASES,
                  excluded_tags=sorted(EXCLUDED_TAGS), countries=countries, states=records,
                  existing_map_agreement_pixels=agreement,
                  files={p: sha(b) for p, b in outputs.items()}, protected=protected,
                  inputs={str(p): sha(b) for p, b in INPUTS.items()},
                  localisation_keys=sorted(newloc), backup=BACKUP.relative_to(ROOT).as_posix())
    return result, outputs


def verify(report):
    for relative, expected in report["files"].items():
        if sha((ROOT / relative).read_bytes()) != expected:
            raise ValueError(f"Imported file changed: {relative}")
    for relative, expected in report["protected"].items():
        if sha((ROOT / relative).read_bytes()) != expected:
            raise ValueError(f"Protected file changed: {relative}")
    tags = registry(ROOT)
    current = states()
    imported = [s for s in report["states"] if s["target"] != "ZZZ"]
    for record in imported:
        text = read(ROOT / record["path"])
        history = child(child(parse(text), "state").children, "history").children
        cores = [scalar(text, [n], n.key) for n in history if n.key == "add_core_of"]
        if current[record["id"]]["owner"] != record["target"] or record["target"] not in cores or "ZZZ" in cores:
            raise ValueError(f"Incorrect owner/core in state {record['id']}")
    all_characters = set()
    all_sprites = set()
    for path in (ROOT / "common/characters").glob("*.txt"):
        for node in parse(read(path)):
            if node.key.lower() == "characters":
                for character in node.children:
                    if character.key in all_characters:
                        raise ValueError(f"Duplicate character: {character.key}")
                    all_characters.add(character.key)
    for path in (ROOT / "interface").rglob("*.gfx"):
        text = read(path)
        all_sprites.update(re.findall(r'\bname\s*=\s*"?(GFX_[\w-]+)', text))
    loc = localisation(ROOT)
    for country in report["countries"]:
        tag = country["tag"]
        if tag not in tags or not (ROOT / "common" / tags[tag]).exists():
            raise ValueError(f"Missing country registration/definition: {tag}")
        if current[country["capital"]]["owner"] != tag:
            raise ValueError(f"Unowned capital: {tag}")
        text = read(ROOT / country["history"])
        nodes = parse(text)
        if int(scalar(text, nodes, "capital")) != country["capital"]:
            raise ValueError(f"Incorrect country capital: {tag}")
        oob = scalar(text, nodes, "oob")
        if not (ROOT / "history/units" / (oob + ".txt")).is_file():
            raise ValueError(f"Missing OOB: {tag}")
        for node in nodes:
            if node.key == "recruit_character" and scalar(text, [node], node.key) not in all_characters:
                raise ValueError(f"Missing recruited character: {tag}")
        if country["history_created"]:
            portrait = f"GFX_portrait_species_{country['species']}_civilian_1"
            if country["leader"] and country["leader"].endswith("_eu4_import_leader") and portrait not in all_sprites:
                raise ValueError(f"Missing species portrait: {portrait}")
        if tag not in loc or tag + "_ADJ" not in loc:
            raise ValueError(f"Missing country localisation: {tag}")
    path = ROOT / "localisation/english/LOK_eu4_import_l_english.yml"
    blob = path.read_bytes()
    if not blob.startswith(b"\xef\xbb\xbfl_english:\n"):
        raise ValueError("Localisation BOM/header changed")
    keys = re.findall(r"(?m)^\s+([^\s:]+):", blob.decode("utf-8-sig"))
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate imported localisation keys")
    print(f"Verified {len(report['countries'])} countries, {len(imported)} transferred states, "
          f"{len(report['files'])} output files and {len(report['protected'])} protected files.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eu4", type=Path, help="Active EU4 mod root (read only)")
    parser.add_argument("--apply", action="store_true", help="Apply after constructing and validating the entire plan")
    parser.add_argument("--verify", action="store_true", help="Verify installed report against current sources")
    args = parser.parse_args()
    installed = REPORT / "audit.json"
    if args.verify:
        verify(json.loads(installed.read_text(encoding="utf-8")))
        return
    if not args.eu4:
        parser.error("--eu4 is required for a dry run or import")
    if installed.exists():
        parser.error("Import is already installed; use --verify")
    result, outputs = plan(args.eu4.resolve())
    scratch = ROOT / "work/zzz-eu4-import"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / ".gitignore").write_text("*\n", encoding="utf-8")
    (scratch / "proposal.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Countries:", len(result["countries"]), "Transferred states:", sum(s["target"] != "ZZZ" for s in result["states"]), "Files:", len(outputs))
    for country in result["countries"]:
        print(country["source"], "->", country["tag"], len(country["states"]), "states; capital", country["capital"], country["capital_method"])
    if not args.apply:
        print("Dry run only; game content is unchanged.")
        return
    for path, before in INPUTS.items():
        if path.read_bytes() != before:
            raise ValueError(f"Source changed while planning: {path}")
    originals = {}
    for relative in outputs:
        path = ROOT / relative
        originals[relative] = path.read_bytes() if path.exists() else None
        if originals[relative] is not None:
            destination = BACKUP / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if destination.read_bytes() != originals[relative]:
                    raise ValueError(f"Backup differs from current source: {relative}")
            else:
                destination.write_bytes(originals[relative])
    written = []
    try:
        for relative, blob in outputs.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            written.append(relative)
        INPUTS.clear()  # Verification must read installed bytes, not planning snapshots.
        verify(result)
    except Exception:
        for relative in reversed(written):
            path = ROOT / relative
            if originals[relative] is None:
                path.unlink()
            else:
                path.write_bytes(originals[relative])
        raise
    REPORT.mkdir(parents=True, exist_ok=True)
    installed.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORT / "files.txt").write_text("\n".join(sorted(outputs)) + "\n", encoding="utf-8")
    print("Installed; exact original bytes are in", BACKUP.relative_to(ROOT))


if __name__ == "__main__":
    main()

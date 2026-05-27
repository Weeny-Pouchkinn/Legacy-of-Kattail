---
trigger: always_on
---

BASIC INSTRUCTIONS:
- All AI-generated localization needs to have "#AI-Generated Placeholder, change later!" as a comment next to it.
- Focus trees need to be "tight" with as little space between focuses as possible, without overlap.
- The "modding_documentation" contains syntax patterns and modding help. The "wiki_doc" subfolder contains modding documentation, and the "vanilla_folders" subfolder contains the vanill common, events and interface folders for reference.
- Refer to the HOI4 modding wiki. https://hoi4.paradoxwikis.com/Modding
- When generating GFX files and interface stuff, always create "placeholder" image files in the proper folder by copying an existing image file.
- You can find the list of all province IDs and their direct neighbors in the province_adjacencies.csv files in modding_documentation. The first column is the province ID, and the next columns are the neighboring province IDs.
- You ARE THE CUSTOM AGENT FOR THE MOD, DO NOT CALL IN A SUB-AGENT TO DO THE WORK!!
- BE VERY CAREFUL WITH ENCODING, DO NOT CHANGE THE FILES' ENCODING OR IT WON'T WORK
- DO NOT CHANGE THE FIRST LINE (with l_english) OF LOCALIZATION FILES

CODING STYLE
Clausewitz script is picky. Follow these rules strictly.

    Indent script blocks with tabs. Use lowercase keys and snake_case for variables and script names.
    Never use <= or >=. They are not supported and will break the game.
        Use check_variable with compare = greater_than_or_equals or compare = less_than_or_equals instead. But this doesn't mean that you should always use the long variant. Use the long variant only when necessary, default to shortened versions for readability, meaning that you are allowed to use < and >.
    Remove magic numbers. The system must rely on variables so that tuning happens in one place. Everything must be dynamic, never hardcode anything.
    Temporary variables don't have a scope, so ROOT.my_temp_var or PREV.my_temp_var will do nothing. Only normal variables have a scope.
    Try to use loops when they improve clarity and avoid repetition.
    Use flags for true or false state, not numeric variables that only ever take 0 or 1.
    Move repeated logic into scripted_effects or scripted_triggers.
    on_weekly, on_daily, on_monthly and similar on actions iterate over all countries by default unless a narrower scope is explicitly required. But these on actions can slow down the game.
        Only use these types of on actions (which iterate through every country by default) when I explicitly ask for it.
        If you believe a whole world iteration is required, stop and ask for permission. Do not implement it until permission is granted.
    Constants @MY_CONSTANT cannot cross file boundaries. They are file scoped.
        Prefer HOI4 script_constants for shared tuning values. They are global (available across script files), improve readability, and have no runtime cost (they are injected on load).
        Script constants are the preferred tuning source, but not every effect field parses constant: tokens. For duration fields that reject constants, such as days = inside timed flags, assign the constant to a normal or temporary variable first and pass that variable to days =.
        Required vanilla docs:
            ~/projects/Hearts of Iron IV/documentation/script_concept_documentation.md (Script Constants section)
            ~/projects/Hearts of Iron IV/common/script_constants/documentation.md (schema + examples)
        Where to put them:
            common/script_constants/ only.
            Create multiple files by subsystem (chemical warfare, events, settings, etc).
        When to use them:
            Use for groups of related constants (tiers, thresholds, AI tuning “tables”, ratio ladders, etc), even if currently only used in one file, if it makes the system clearer and easier to tune.
            Use for values referenced across multiple files (effects/decisions/events/localisation/etc), where @ would force duplication or “keep in sync” comments.
        Important limitation: script_constants cannot be used everywhere. Unsupported fields will throw errors. In that case, use @ constants.
        Prefer the explicit fixed-point access: constant:category.key (e.g. value = constant:chem_cylinder_ratio.low).
    Use event targets (event_target:) to persist a scope pointer across blocks/events when variables/scopes alone are insufficient.
        Required references:
        paradox_wiki/Data structures - Hearts of Iron 4 Wiki.md (Event targets section)
        ~/projects/Hearts of Iron IV/documentation/effects_documentation.md (save_event_target_as, save_global_event_target_as, clear_global_event_target, clear_global_event_targets)
        ~/projects/Hearts of Iron IV/documentation/triggers_documentation.md (has_event_target)
        Prefer regular event targets (save_event_target_as) for short-lived chains; they automatically clear when the originating effect chain ends (but do carry into events fired from that chain).
        Use global event targets (save_global_event_target_as) only when you need persistence beyond a single chain/system; they do not auto-clear and must be cleaned up (e.g. clear_global_event_target = my_target).
        Use them as scopes/targets with event_target:my_target.
        Localisation: when using an event target as a localization scope namespace, the event_target: prefix is not used (e.g. [my_target.GetName]).
    Do not use unary - on variable tokens (e.g. value = -my_var); negate via multiply_*_variable first.
    If an effect or trigger does not accept dynamic values, use meta_effect or meta_trigger with text = { ... } to inject computed variables/localisation into otherwise static fields.
        meta effects can be used in all sorts of creative ways, for example: my_scripted_effect_[ID] = yes, so you can even choose a scripted effect dynamically. Meta effects are very powerful and useful.
    Prefer reusable dynamic scripted effects/triggers for complex/dynamic logic.
        First check existing dynamic effects (in common/scripted_effects/chaosx_dynamic_effects.txt) and use them instead of duplicating logic.
        If no existing effect fits, create a new dynamic effect and document it in the markdown file of the same name (common/scripted_effects/chaosx_dynamic_effects.md) in the same change.
        Keep effect docs explicit: purpose, scope, inputs/outputs, defaults, side effects, and a usage example.
    If MTTH (mean time to happen) variables are required to reduce AI/script clutter (especially in ai_will_do blocks) by centralizing weighted logic, use the hoi4-mtth skill and follow its MTTH guidance before implementing.


LOCALISATION INSTRUCTIONS:
    Localisation files must be encoded as UTF-8 with BOM unless this project explicitly uses another verified encoding.
    When adding or renaming anything visible on screen, update localisation in the same change.
    In scripted localisation, follow the project's established handling of formatting symbols and icons.
    Player-facing text must describe the current world state and player choices, not implementation history or tuning mechanics.
    Do not say a value was capped, hardcoded, newly added, reworked, or changed because of an update request in player-facing text.
    Localisation keys should be consistent and readable.
    Define icons and UI assets in the correct .gfx file and keep naming stable.
    Register new UI assets before requesting art so filenames do not need to change later.
    If using placeholder sprites so the game can load, document that they are placeholders and where final sprites must go.

Trigger, prerequisite, and tooltip clarity
Long trigger blocks should not be exposed raw to the player. Hide them or use scripted localisation, custom trigger tooltips, or named scripted triggers.
When a decision, mission, focus, event option, or GUI button requires control of states, divisions in states, protected borders, held capitals, rail hubs, depots, ports, or named regions, the player-facing text must name the exact states or a clear named region.
Avoid vague requirement text such as:
    required states
    border states
    nearby states
    key states
    sufficient divisions
    enough equipment

Use clear text instead, for example:
    Place 8 supplied divisions in [STATE_A], [STATE_B], and [STATE_C].
    Hold the [NAMED_REGION] for 120 days.
    Keep [CAPITAL_A] and [CAPITAL_B] connected to supply.

Cost localisation should be short, readable, and icon-first.

Good examples:
    2,000 <infantry_equipment_texticon>
    20 <army_xp_texticon> 20 <command_power_texticon>
    200 <support_equipment_texticon>
    Depot control
    
Do not add filler words between costs. For example, use:

20 <army_xp_texticon> 20 <command_power_texticon>

not:

20 <army_xp_texticon> and 20 <command_power_texticon>
# Wonders
> ##### *Documentation Written and Maintained by DecentNameHere*

## Table of Contents
* [Adding New Wonders](#guide-to-adding-new-wonders-)
  * [Step 1 - Defining Wonders Modifiers](#step-1---defining-the-wonders-modifiersbackend)
  * [Step 2 - Adding Localization](#step-2---adding-localization)
  * [Step 3 - Adding Graphics](#step-3---adding-graphics)
    * [Part 1 - Making the Icon](#part-1---making-the-icon)
    * [Part 2 - Implementing The Icon](#part-2---implementing-the-icon)
* [List of Modifers](#list-of-modifiers)
  * [Adding New Modifiers](#adding-new-modifiers)
    * [Step 1 - Updating the Array Backend Code](#step-1-updating-the-array-backend-code)
    * [Step 2 - Updating the Dynamic Modifier Itself](#step-2---updating-the-dynamic-modifier-itself)
    * [Step 3 - Updating the State Tooltip Localization](#step-3---updating-the-state-tooltip-scripted-localisation-)
      * [Part 1 - Creating the New Scripted Loc Code](#part-1---creating-the-new-scripted-loc-code)
      * [Part 2 - Defining the Loc for the Modifier](#part-2---defining-the-loc-for-the-modifier)
      * [Part 3 - Adding them to the Modifier Block Loc-Key](#part-3---adding-them-to-the-modifier-block-loc-key)
* [Current Wonders](#current-wonders)
* [The Wonder Output Modifier, Adding New Modifiers Midgame and Adding Wonders Midgame](#the-wonder-output-modifier-adding-newupdating-modifiers-midgame-and-adding-new-wonders-midgame)
  * [The Wonder Output Modifier](#the-wonder-output-modifier)
  * [Adding New Modifiers Midgame](#adding-newupdating-modifiers-midgame)
  * [Adding New Wonders Midgame](#adding-new-wonders-midgame)
* [Removing Wonders and Modifiers](#removing-wonders-and-modifiers)
  * [Removing Wonders](#removing-wonders)
  * [Removing Modifiers](#removing-modifiers)
* [Documentation Notes](#documentation-notes)

## Guide to Adding New Wonders 
Wonder implementation is done in three steps 
1. Defining the Wonders Modifiers 
2. Adding Localization
3. Adding Graphics

This is provided there are no new modifiers to be added, at which there is a few more steps that will be covered in [The Modifiers Section](#adding-new-modifiers)

### Step 1 - Defining The Wonders Modifiers/Backend
For Wonders present at game start, they need to be defined in [LOK_on_actions.txt](../on_actions/LOK_on_actions.txt), however wonders added midgame use the same script.

````paradox_script
<STATE_ID> = {
    set_variable = { wonder = <WONDER_ID> }
    setup_wonder_array = yes
    #We Set variable wonder_modifiers_values^x relating to the wonder_modifier_x found in LOK_wonder_modifier
    set_variable = { wonder_modifiers_values^<MODIFIER_1_ID> = <MODIFIER_1_VALUE> }
    set_variable = { wonder_modifiers_values^<MODIFIER_2_ID> = <MODIFIER_2_VALUE> }
    set_variable = { wonder_modifiers_values^<MODIFIER_3_ID> = <MODIFIER_3_VALUE> }
    set_variable = { wonder_modifiers_values^<MODIFIER_4_ID> = <MODIFIER_4_VALUE> }   
    \\.....
}
````
These \<VARIABLES> should be relatively simple to understand, \<STATE_ID> is the state you wish to host the wonder in, \<WONDER_ID> is the ID of the wonder you're adding (or editing!), refer to the [List of Current Wonders](#current-wonders) to make sure you dont conflict with anything!
> <b>Any new wonders should be added to this list or passed onto DecentNameHere so i may update the documentation!</b>

\<MODIFIER_X_ID> is the index that your desired modifier is assigned to as found in [List of Modifiers](#list-of-modifiers) and \<MODIFIER_X_VALUE> is the value you want to give your modifier (please reference the [List of Modifiers](#list-of-modifiers) for accepted precision of Modifiers)

An Example of the Katown Pyramid Wonder as defined in [LOK_on_actions.txt](../on_actions/LOK_on_actions.txt)
````paradox_script
    #Katown Pyramid
    509 = {
        set_variable = { wonder = 1 }
        setup_wonder_array = yes
        #We Set variable wonder_modifiers_values^x relating to the wonder_modifier_x found in LOK_wonder_modifier
        set_variable = { wonder_modifiers_values^1 = 0.15 }
        set_variable = { wonder_modifiers_values^2 = 0.10 }
        set_variable = { wonder_modifiers_values^3 = 0.10 }
        set_variable = { wonder_modifiers_values^4 = 0.10 }
    }
````
Now, Provided you dont need to add any new modifiers for your Wonder, you are safe to move onto Step 2!

However, should you need to add new modifiers that arent in our existing list (And please check with other devs to make sure you both arent adding modifiers at the same time!), please refer to [Adding New Modifiers](#adding-new-modifiers)

### Step 2 - Adding Localization
Localization is fairly simple to add due to the large scripted Loc bloc i made. You simply head to [wonders_l_english.yml](../../localisation/english/wonders_l_english.yml) and use the following base localisation strings
```paradox_localisation
  var_wonder.<WONDER_ID>:0 "<WONDER_NAME>"
  var_wonder_desc.<WONDER_ID>:0 "$wonder_effects_tooltips$\n§L<WONDER_DESC>§!"
```
and turn it into this! (Example using the Katown Pyramid)
```paradox_localisation
  var_wonder.1: "Grand Katown Pyramid"
  var_wonder_desc.1:0 "$wonder_effects_tooltips$\n§LThe heart of the Herzlands, the Katown Pyramid is a gargantuan mile-tall fortified complex housing countless administrative and military command centers, intended to centralize the governance of the Katzen state.§!"
```
just replace \<WONDER_ID> with your Wonder ID (Duh!), \<WONDER_NAME> with the name of your Wonder and \<WONDER_DESC> with its description 

And thats it, all other localisation is handled by the scripted localisation modifer bloc and (\$wonder_effects_tooltips$) and doesnt need extra help
> If you are following this and adding new modifiers, dont worry, new modifier related loc will be covered in the [Adding New Modifiers](#adding-new-modifiers) Section

### Step 3 - Adding Graphics
There are two main parts to this step, making the icon, and implementing it.
#### Part 1 - Making the Icon
We'll start with making the icon! Wonder Icons are defined in <i><b>"gfx/interface/wonders/"</b></i> where they are defined as generally <i><b>"wonder_<WONDER_NAME>.dds"</b></i>. In this scenario <WONDER_NAME> could be anything you want (in standard characters and no spaces) as its not tied to any internal code but for the sake of consistency please keep it lower caps and follow what we named the other wonders.

A wonder icon is a 100x61 pixel icon where the icon typically is situated in a 60x61 "square" in the horizontal center of the image (the main point is to keep it centered! if its wide enough to use the whole canvas then feel free just make sure its centered). Typically you should aim to give around 3-4 pixels of empty space inbetween the icon and the border of the canvas in addition to adding a shadow to the icon. 

Shadows can be done relatiely simply in paint.net (which is what i personally recommend for icons). Simply do the following once you have the main icon finished
1. Duplicate the layer using Ctrl+Shift+D
2. Select the bottom layer
3. Press Ctrl+Shift+U (or go to Adjustments>Hue/Saturation) and slide both Saturation and Lightness to 0 and -100 respectively (Completely to the left of the sliders!)
4. Go to Effects>Blurs>Gaussian Blurs and adjust the radius slider until you get a reasonable shadow for the icon
5. Press Ctrl+Shift+F to flatten the image into a single layer
6. Ready to Export!

Thats everything you need for the Icon itself. Save it in the .dds format with your wonder name of choice and move on to part 2
#### Part 2 - Implementing The Icon
Icons are actually "Declared" in [wonder_icon.gfx](../../interface/wonder_icon.gfx). The Way you implement them is fairly simple
```paradox_script
#<WONDER_NAME>
spriteType = { name = "GFX_wonder_<WONDER_ID>" texturefile = "gfx/interface/wonders/<WONDER_ICON_FILENAME>.dds" }
```
Simply past this code beneath the bottommost spriteType in the file (but before the closing bracket!) and substitute \<WONDER_ID> for your ID once again, Substitute \<WONDER_NAME> for your Wonders name (Just for identifying when looking in the file) and paste in your filename from the previous part where it says \<WONDER_ICON_FILENAME>

Once you've done this, you're sorted! your Wonder should be ready to go!.
## List of Modifiers
| ID | Modifier Name                      | Modifier String                           | Decimals Accepted | Higher = Positive/Negative |
|----|------------------------------------|-------------------------------------------|:-----------------:|:--------------------------:|
| 0  | Required Garrisons                 | required_garrison_factor                  |         0         |          Negative          |
| 1  | Max planning                       | max_planning                              |         1         |          Positive          |
| 2  | Army Organization Regain           | army_org_regain                           |         2         |          Positive          |
| 3  | Division Organization              | army_org_factor                           |         1         |          Positive          |
| 4  | Compliance Growth Speed            | compliance_growth                         |         0         |          Positive          |
| 5  | Production Efficiency growth       | production_factory_efficiency_gain_factor |         2         |          Positive          |
| 6  | Heavy Tank Unit Design Cost        | unit_heavy_armor_design_cost_factor       |         2         |          Negative          |
| 7  | Ship Refitting Speed               | refit_speed                               |         0         |          Positive          |
| 8  | Air Mission Efficiency             | air_mission_efficiency                    |         1         |          Positive          |
| 9  | Air Range                          | air_range_factor                          |         2         |          Positive          |
| 10 | Trade deal opinion factor          | trade_opinion_factor                      |         2         |          Positive          |
| 11 | Consumer Goods Factories factor    | consumer_goods_factor                     |         2         |          Negative          |
| 12 | Research Speed                     | research_speed_factor                     |         2         |          Positive          |
| 13 | Leader Skill Bonuses               | skill_bonus_factor                        |         1         |          Positive          |
| 14 | Stability                          | stability_factor                          |         2         |          Positive          |
| 15 | Encryption                         | encryption_factor                         |         2         |          Positive          |
| 16 | Decryption                         | decryption_factor                         |         2         |          Positive          |
| 17 | Mineral Resources Production       | lok_mineral_resources_factor              |         2         |          Positive          |
| 18 | Weekly Manpower                    | weekly_manpower                           |         0         |          Positive          |
| 19 | Railway construction speed         | production_speed_rail_way_factor          |         2         |          Positive          |
| 20 | Infrastructure construction speed  | production_speed_infrastructure_factor    |         2         |          Positive          |
| 21 | Supply Range                       | supply_node_range                         |         0         |          Positive          |
| 22 | Food                               | country_resource_food                     |         0         |          Positive          |
| 23 | Daily Political Power Gain         | political_power_gain                      |         2         |          Positive          |
| 24 | Political Power Gain               | political_power_factor                    |         2         |          Positive          |
| 25 | Industrial Factory Donations       | industrial_factory_donations              |         0         |          Positive          |
| 26 | Planning Speed                     | planning_speed                            |         1         |          Positive          |
| 27 | Monthly Population                 | monthly_population                        |         1         |          Positive          |
| 28 | Recruitable Population             | recruitable_population_factor             |         2         |          Positive          |
| 29 | Daily Support for Unaligned        | neutrality_drift                          |         2         |          Positive          |
| 30 | Daily Fascism Support              | fascism_drift                             |         2         |          Positive          |
| 31 | Resistance Activity Chance         | resistance_activity                       |         1         |          Negative          |
| 32 | Military Factory Donations         | military_factory_donations                |         1         |          Positive          |
| 33 | Coordination                       | coordination_bonus                        |         2         |          Positive          |
| 34 | Air Agility                        | air_agility_factor                        |         2         |          Positive          |
| 35 | Air Attack                         | air_attack_factor                         |         2         |          Positive          |
| 36 | Air Defence                        | air_defence_factor                        |         2         |          Positive          |
| 37 | Airbase Construction Speed         | production_speed_air_base_factor          |         2         |          Positive          |
| 38 | Energy                             | country_resource_energy                   |         0         |          Positive          |
| 39 | Factory Output                     | industrial_capacity_factory               |         2         |          Positive          |
| 40 | Production Efficiency Retention    | line_change_production_efficiency_factor   |         2         |          Positive          |
| 41 | Supertensiles                      | country_resource_supertensiles            |         0         |          Positive          |
| 42 | Food Production                    | lok_food_resources_factor                 |         2         |          Positive          |
| 43 | Strategic Bomber Bombing           | air_strategic_bomber_bombing_factor       |         2         |          Positive          |

### Adding New Modifiers
Adding new modifiers is a somewhat more complicated process but very modular. It is broken down into 3 steps.
1. Updating Array Backend Code
2. Updating the Dynamic Modifier Itself
3. Updating Scripted Localisation

#### Step 1 - Updating the Array Backend Code
So, thanks to Scripted Effects you only need to update 1 scripted Variable, thats it!.

Head to [LOK_scripted_effects.txt](../scripted_effects/LOK_scripted_effects.txt) and search for the Variable <b><i>@wonder_modifier_count</i></b>. Once you've found this variable, update it to the <b>new</b> amount of Modifiers, this will be whatever the latest id is + 1 (due to modifier 0). Once this is done, all the other scripts will reference it for how large to set their modifier arrays to.

#### Step 2 - Updating the Dynamic Modifier Itself.
For your new modifier to even have any effect, it must be added to the actual national spirit modifier <B><I>"lok_wonder_modifier"</I></B> found in [LOK_dynamic_modifiers.txt](./LOK_dynamic_modifiers.txt).

simply add your desired modifier string and then set it to equal <B>"wonder_modifier_values^\<MODIFIER_ID>"</B> where \<MODIFIER_ID> is the Array index assigned to your new modifier(s) when you expanded the arrays in Step 1.

#### Step 3 - Updating the State Tooltip Scripted Localisation 
Now there are three parts to this step.
1. Creating the New Scripted Loc code
2. Defining the Loc for the Modifier
2. Adding them to the Modifier Block Loc-Key

##### Part 1 - Creating the New Scripted Loc Code
For this step you need to head to [LOK_wonder_scripted_loc.txt](../scripted_localisation/LOK_wonder_scripted_loc.txt). Once here, head to the bottom of the file and add the following code
```paradox_script
defined_text = {
    name = wonder_modifier_<MODIFIER_ID>_scripted
    text = {
        trigger = {
            check_variable = {
                var = THIS.wonder_modifiers_values^<MODIFIER_ID>
                value = 0
                compare = not_equals
            }
        }
        localization_key = wonder_modifiers_<MODIFIER_ID>
    }
    text = { localization_key = wonder_effects_NA }
}
```
Like before, \<MODIFIER_ID> is the index assigned to your new modifier. All three of the replace keys in this block need to be swapped out for the id. The purpose of this block is to check if the Modifier actually has a value differnt to 0 (and therefore is being used) and if so, show a the modifier loc key and not an empty string ("wonder_effects_NA")

##### Part 2 - Defining the Loc for the Modifier
Both parts 2 and 3 are located in [wonder_l_english.yml](../../localisation/english/wonders_l_english.yml)

There is a large block of loc keys starting with <b>"wonder_modifiers_x"</b>, you will want to paste the following string
```paradox_localisation
  wonder_modifiers_<MODIFIER_ID>:0 "$<MODIFIER_REAL_LOC_KEY>$: [?THIS.wonder_modifiers_values_real^<MODIFIER_ID>|<FORMATTING_CHARACTERS>]\n"
```
Now, there are a few parts in this section that need to be replaced.
- \<MODIFIER_ID>: Like before, the index assigned to your new modifier


- \<MODIFIER_REAL_LOC_KEY>, this one is more tricky to find. You will want to open the vanilla hoi4 localisation folder and search with the <B>Modifier String</b> (What you added to the Dynamic Modifier in Step 2!) and you will likely find a full caps loc key that reads "MODIFIER_<YOUR_MODIFIER_STRING_HERE>". If it looks like the correct localization for the modifier then you are good to go past this string between the dollar signs.

> <I>If you're adding a Custom modifier added by LOK then simply look for the loc key in our own Loc files</I>

- \<FORMATTING_CHARACTERS>, this one is even more tricky! For this one im just going to copy the table directly from the hoi4 modding wiki

| Code | Effects                                                                                                                                                                                                            |
|------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *    | Converts the variable to SI units—appends "K" or "M" and divides the variable appropriately, such as 65,536 becoming 65.53K and 1,500,000 becoming 1.50M. Displays 2 decimals after the dot by default.            |
| ^    | Same as *.                                                                                                                                                                                                         |
| =    | Prefixes the variable with + if the value is positive or - if it is negative.                                                                                                                                      |
| 0..9 | Controls the number of decimals to display. Due to the nature of the game's variables, there are no more than 3 decimals that can be shown. Using any digit greater than 3 will instead have the same result as 3. |
| %    | Converts the variable to percentage, multiplying by 100 and appending a %. By default, will show 2 digits after the decimal point, though the second digit will always be 0.                                       |
| %%   | Appends a percentage to the end of the variable without multiplying by 100.                                                                                                                                        |
| +    | Colours the variable green if positive, yellow if zero, red if negative.                                                                                                                                           |
| -    | Colours the variable red if positive, yellow if zero, green if negative.                                                                                                                                           |
> <I><B>Source:</B> [Hoi4 Official Wiki, Localisation Modding](https://hoi4.paradoxwikis.com/Localisation#Formatting_variables)</I>

This Tables contains a list of variables you will need to combine together and replace \<FORMATTING_CHARACTERS> with. To find what you actually is the tricky part.
- <B>"Asterisk Symbol or ^":</B> In most cases we dont need this for modifiers. If your modifier is in the realm of thousands or millions consider it but otherwise its unneeded.
- <B>"=":</B> This is needed for all modifiers, place this at the end of your variable string
- <B>"0..9":</B> As the table says this has no use after 3, but to find how precise (AKA how many decimals the variable has) i recommend looking at <B>"script_documentation.json"</B> (Found in Vanilla Installation in "Hearts of Iron IV\documentation\script_documentation.json")
  - > <I>For Custom Modifiers added by LOK, the Precision value will be found in <B>"common/modifier_definitions/"</B></I>
- <B>"%":</B> This one is simple, if its a percentage then add a percentage
- <B>"%%":</B> Not many use cases for this one, but if you are using a percentage modifier where 100% = 100 and not 1, use this one
- <B>"+/-":</B> This one is simple. If your modifier is <I>"good"</I> for you when its higher then use <B>"+"</B> and if its <I>"bad"</I> for you when its higher then use <B>"-"</B>

The end product should look something like the following 
```paradox_localisation
  wonder_modifiers_22:0 "$country_resource_food$: [?THIS.wonder_modifiers_values_real^22|+0=]\n"
```
Which will render as (for sake of the example the value of THIS.wonder_modifiers_values_real^22 is 300. The Example also wont render the colour of the text albeit it would be green) 
> "Food: +300"

With this all done, simply place it alongside the others in the loc file and you're good to move onto <b>part 3</b>

##### Part 3 - Adding them to the Modifier Block Loc-Key
This is a simple part. Simply take the "wonder_modifier_x_scripted" part from the defined text made in part 1 and paste it within \[brackets\] at the end of the "wonder_effects_tooltips" loc key, like the others before it with NO space between.

Now, the modifier will show up properly in the state tooltip.

And with that, its all done! your new modifier has been added 
## Current Wonders

| Wonder ID | Name                         | State | Starting Tag / Created by |
|:---------:|------------------------------|:-----:|:-------------------------:|
|     1     | Grand Katown Pyramid         |  509  |            KTW            |
|     2     | Lionsburg Riesigerwerks      |  173  |            PRL            |
|     3     | Great Shipyards of Auralia   |  116  |            AUR            |
|     4     | Himezulte Megairbase         |  220  |            HIM            |
|     5     | Purrlin Stock Exchange       |  192  |            PRL            |
|     6     | Südkatzelandisch Universität |  595  |            MEO            |
|     7     | Von Kattensbach Estates      |  13   |            SIL            |
|     8     | Frankfurr Institute          |  477  |            FRA            |
|     9     | Tailsbaden Borehole          |  84   |            TAI            |
|    10     | Stronien Logistical Hub      |  486  |            OST            |
|    11     | Punchiestadt Orchards        |  583  |            CLE            |
|    12     | Kiffrance Plants             |  644  |            MEC            |
|    13     | Grüyettburg Pharmaceutics    |  131  |            LIO            |
|    14     | Unterflusionian Monument     |  602  |            NEU            |
|    15     | Great City of Charles        |  349  |            TAK            |
|    16     | Rakvir Supercomputer         |  —    |            KUS            |
|    17     | Lutécie Tower                |  320  |            ROQ            |
|    18     | Steelloft                    |  726  |            MCF            |
|    19     | Katlantropa Dam              | 1324  |             —             |
|    20     | Great Lake Dam               | 1018  |             —             |
|    21     | Harelyne Spire               |  418  |            HAR            |
|    22     | Bunville Palace              |  406  |            PLR            |
|    23     | Great Missile Array          |  275  |            NEK            |

## The Wonder Output Modifier, Adding New/Updating Modifiers Midgame and Adding New Wonders Midgame
To begin with, any time a wonders modifier is updated by script ingame, its recommended you run the "apply_wonder_effects" scripted effect on the scope of whoever controls the state with the wonder in it. This would look like
```paradox_script
<STATE_ID>.contoller = { apply_wonder_effects = yes } 
```
This will immediately apply the effects of the wonder to the proper country (the controller of the wonder state).
### The Wonder Output Modifier
As of current theres a simple modifier dubbed "lok_wonder_output_mult" that can be added to a country via national spirits and such. The modifier allows up to 2 decimal precision and is added onto 1 and used as a multiplier in the calculator for the Wonder output. It works without issue
### Adding new/Updating Modifiers Midgame
Adding new modifiers or updating existing modifiers for a wonder midgame is an incredibly easy process, you simply need to scope to the state with the wonder and do the following
```paradox_script
<STATE_ID> = { 
    set_variable = { wonder_modifiers_values^<MODIFIER_ID> = <VALUE> }   
    # Other Variable maths are applicable here should you wish to use them. such as add and multiply. Just keep in mind what other changes are being made to the variables when using these non-set calculations on the variables
    controller = { apply_wonder_effects = yes }
}
```
<b>\<MODIFIER_ID>:</b> simply relates to the id of the modifier you want, found in [List of Modifiers](#list-of-modifiers)
<b>\<VALUE>:</b> refers to the value your modifier would have, please keep in mind the Precision of the modifier (Also found in [List of Modifiers](#list-of-modifiers))  
### Adding New Wonders Midgame
> <B>THIS DOES NOT COVER CREATION OF NEW WONDERS ENTIRELY! ONLY HOW TO IMPLEMENT PRE-CODED WONDERS TO STATES VIA SCRIPT!</B>
> 
> <I>For how to add a new wonder into the Code, see [Adding New Wonders](#guide-to-adding-new-wonders-)</I>

Midgame Wonder implementation is fairly simple to do via script. Code for it will look like the following
```paradox_script
<STATE_ID> = { 
    set_variable = { wonder = <WONDER_ID> }
    setup_wonder_array = yes
    #We Set variable wonder_modifiers_values^x relating to the wonder_modifier_x found in LOK_wonder_modifier
    set_variable = { wonder_modifiers_values^<WONDER_MODIFIER_ID_1> = <MODIFIER_VALUE_1> }
    set_variable = { wonder_modifiers_values^<WONDER_MODIFIER_ID_2> = <MODIFIER_VALUE_2> }
    set_variable = { wonder_modifiers_values^<WONDER_MODIFIER_ID_3> = <MODIFIER_VALUE_3> }
    #Apply the Wonder Effects
    controller = { apply_wonder_effects = yes }
}
```
<br></br>
<b>\<WONDER_ID>:</b> The ID of your Wonder, refer to the [List of Wonders](#current-wonders)<br>
<b>\<WONDER_MODIFIER_ID_X>:</b> The Index ID of the Modifier you wish to use in the Wonder, refer to the [List of Modifiers](#list-of-modifiers)<br>
<b>\<WONDER_VALUE_X>:</b> The value you wish your modifier to have, please keep in mind the Precision of the modifier (Also found in [List of Modifiers](#list-of-modifiers))
## Removing Wonders and Modifiers
### Removing Wonders
Wonders can be removed much easier than they are added, simply run the "remove_wonder" effect on the state with the wonder (or relative state effect scope should you wish to affect multiple!) and the wonder will disappear
### Removing Modifiers
For Removing modifiers, simply follow the same procedure as [Updating a Modifier](#adding-newupdating-modifiers-midgame) but set the value to 0
## Documentation Notes
As mentioned at the start, this Documentation used markdown formatting and is maintained by yours truly, DecentNameHere. Should you as a contributor add more wonders or modifiers i ask that you either ping me on the LOK mod discord or, if you are confident in adding with the Markdown format in this file, update the tables yourselves.
Additionally, if any further clarification is needed on how to use 
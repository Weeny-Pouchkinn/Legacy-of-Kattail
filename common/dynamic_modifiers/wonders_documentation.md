# Wonders
> ##### *Documentation Written and Maintained by DecentNameHere*

## Table of Contents
* [Adding New Wonders](#guide-to-adding-new-wonders-)
* [List of Modifers](#list-of-modifiers)
* [Current Wonders](#current-wonders)

## Guide to Adding New Wonders 
Wonder implementation is done in three steps
* Step 1: Defining the Wonders Modifiers
* Step 2: Adding Localization
* Step 3: Adding Graphics

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

\<MODIFIER_X_ID> is the index that your desired modifier is assigned to as found in [List of Modifiers](#list-of-modifiers) and \<MODIFIER_X_VALUE> is the value you want to give your modifier (please reference the List of modifiers for acceptable values/decimals)

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
> If you are following this and adding new modifiers, dont worry, that part will be covered in the [Adding New Modifiers](#adding-new-modifiers) Section

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

### Adding New Modifiers

## Current Wonders
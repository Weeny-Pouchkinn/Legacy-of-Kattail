# generate_lok_parliament_gui.py
#
# Run from the Legacy of Kattail mod root:
#     python generate_lok_parliament_gui.py
#
# Requires Pillow:
#     pip install pillow

from pathlib import Path
from PIL import Image, ImageDraw
import math

ROOT = Path(".")
SEATS = 200

# ============================================================
# helpers
# ============================================================

def write(path, text, bom=False):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig" if bom else "utf-8")

def make_positions(total=200, width=610, height=220):
    """
    Flaxbeard-style semicircular parliament geometry.
    Based on hoi4-parliament-diagram's row/radius algorithm.
    """

    ROW_TOTALS = [
        4,15,33,61,95,138,189,247,313,388,469,559,657,762,
        876,997,1126,1263,1408,1560,1722,1889,2066,2250,
        2442,2641,2850,3064,3289,3519,3759,4005,4261,4522,
        4794,5071,5358,5652,5953,6263,6581,6906,7239,7581,
        7929,8287,8650,9024,9404,9793,10187,10594,11003
    ]

    spread = 1.85
    hole = 5.7
    radius = 0.1

    rows = next(i + 1 for i, n in enumerate(ROW_TOTALS) if n >= total)
    pos = []

    for i in range(1, rows):
        n = int(
            total / ROW_TOTALS[rows - 1]
            * math.pi
            / (2 * math.asin(2 / (3 * rows + 4 * i - 2)))
        )

        r = (3 * hole + spread * i - 2) / 16

        for j in range(n):
            angle = (
                math.pi / 2 if n == 1 else
                j * (math.pi - 2 * math.sin(radius / r)) / (n - 1)
                + math.sin(radius / r)
            )
            pos.append((angle, r * math.cos(angle), r * math.sin(angle)))

    n = total - len(pos)
    r = (3 * hole + spread * rows - 2) / 16

    for j in range(n):
        angle = (
            math.pi / 2 if n == 1 else
            j * (math.pi - 2 * math.sin(radius / r)) / (n - 1)
            + math.sin(radius / r)
        )
        pos.append((angle, r * math.cos(angle), r * math.sin(angle)))

    # Important: party frame runs then fill seats left -> right.
    pos.sort(reverse=True, key=lambda x: x[0])

    xs = [p[1] for p in pos]
    ys = [p[2] for p in pos]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    scale = min(
        (width - 16) / (xmax - xmin),
        (height - 16) / (ymax - ymin)
    )

    return [
        (
            round((x - xmin) * scale + 8),
            round((ymax - y) * scale + 8)
        )
        for _, x, y in pos
    ]

coords = make_positions(SEATS)

# ============================================================
# placeholder graphics
# ============================================================

gfx = ROOT / "gfx/interface/LOK_parliament"
gfx.mkdir(parents=True, exist_ok=True)

# Nine horizontal seat frames.
colors = [
    (190,45,45,255),      # communist
    (222,73,105,255),     # socialist
    (214,116,179,255),    # socdem
    (92,190,215,255),     # soclib
    (218,190,73,255),     # democratic
    (67,120,194,255),     # soccon
    (44,79,130,255),      # authdem
    (135,135,135,255),    # neutrality
    (107,74,50,255),      # fascism
]

img = Image.new("RGBA", (90, 10))
d = ImageDraw.Draw(img)

for i, c in enumerate(colors):
    x = i * 10
    d.ellipse((x+1,1,x+8,8), fill=(10,10,10,255))
    d.ellipse((x+2,2,x+7,7), fill=c)

img.save(gfx / "LOK_parliament_seats.png")

def toggle(name, checked):
    img = Image.new("RGBA", (20,20))
    d = ImageDraw.Draw(img)
    d.rectangle(
        (2,2,17,17),
        fill=(42,46,57,255),
        outline=(205,190,142,255),
        width=2
    )
    if checked:
        d.line((5,10,9,14), fill=(230,220,175,255), width=2)
        d.line((9,14,16,5), fill=(230,220,175,255), width=2)
    img.save(gfx / name)

toggle("LOK_parliament_toggle_off.png", False)
toggle("LOK_parliament_toggle_on.png", True)

img = Image.new("RGBA", (28,28))
d = ImageDraw.Draw(img)
d.ellipse(
    (2,2,25,25),
    fill=(45,49,61,255),
    outline=(205,190,142,255),
    width=2
)
d.line((14,7,14,17), fill=(232,219,165,255), width=3)
d.ellipse((12,20,16,24), fill=(232,219,165,255))
img.save(gfx / "LOK_parliament_demands.png")

img = Image.new("RGBA", (52,52))
d = ImageDraw.Draw(img)
d.rounded_rectangle(
    (1,1,50,50),
    radius=6,
    fill=(35,39,51,245),
    outline=(194,170,94,255),
    width=2
)

for r,n in [(12,7),(17,10),(22,13)]:
    for i in range(n):
        a = math.pi - math.pi*i/(n-1)
        x = 26 + r*math.cos(a)
        y = 34 - r*math.sin(a)
        d.ellipse((x-2,y-2,x+2,y+2), fill=(224,208,150,255))

img.save(gfx / "LOK_parliament_launcher.png")

# ============================================================
# GFX
# ============================================================

write("interface/LOK_parliament_gui.gfx", r'''
spriteTypes = {
    spriteType = {
        name = "GFX_LOK_parliament_seat"
        texturefile = "gfx/interface/LOK_parliament/LOK_parliament_seats.png"
        noOfFrames = 9
    }

    spriteType = {
        name = "GFX_LOK_parliament_launcher"
        texturefile = "gfx/interface/LOK_parliament/LOK_parliament_launcher.png"
    }

    spriteType = {
        name = "GFX_LOK_parliament_toggle_off"
        texturefile = "gfx/interface/LOK_parliament/LOK_parliament_toggle_off.png"
    }

    spriteType = {
        name = "GFX_LOK_parliament_toggle_on"
        texturefile = "gfx/interface/LOK_parliament/LOK_parliament_toggle_on.png"
    }

    spriteType = {
        name = "GFX_LOK_parliament_demands"
        texturefile = "gfx/interface/LOK_parliament/LOK_parliament_demands.png"
    }
}
''')

# ============================================================
# interface
# ============================================================

write("interface/LOK_parliament_gui.gui", r'''
guiTypes = {

    # ========================================================
    # bottom-right launcher
    # ========================================================

    containerWindowType = {
        name = "LOK_parliament_launcher_gui"

        position = { x = -86 y = -205 }
        size = { width = 52 height = 52 }

        orientation = lower_right
        origo = lower_right

        buttonType = {
            name = "LOK_parliament_open_button"

            position = { x = 0 y = 0 }

            quadTextureSprite = "GFX_LOK_parliament_launcher"

            pdx_tooltip = "LOK_parliament_gui_open_tt"

            clicksound = click_default
        }
    }


    # ========================================================
    # main window
    # ========================================================

    containerWindowType = {
        name = "LOK_parliament_gui"

        position = { x = 0 y = 0 }

        size = {
            width = 760
            height = 720
        }

        orientation = center
        origo = center

        moveable = yes

        background = {
            name = "background"

            quadTextureSprite = "GFX_tiled_window_thin_border"
        }


        # ----------------------------------------------------
        # title
        # ----------------------------------------------------

        instantTextBoxType = {
            name = "LOK_parliament_title"

            position = { x = 70 y = 17 }

            font = "hoi_36header"

            text = "LOK_parliament_gui_title"

            maxWidth = 620
            maxHeight = 35

            fixedsize = yes

            format = center
        }


        buttonType = {
            name = "LOK_parliament_close_button"

            position = { x = -14 y = 12 }

            quadTextureSprite = "GFX_closebutton"

            orientation = upper_right

            shortcut = "ESCAPE"

            clicksound = click_close

            pdx_tooltip = "CLOSE"
        }


        # ----------------------------------------------------
        # parliament
        # ----------------------------------------------------

        containerWindowType = {
            name = "LOK_parliament_diagram_block"

            position = { x = 30 y = 58 }

            size = {
                width = 700
                height = 274
            }

            background = {
                name = "background"

                quadTextureSprite = "GFX_tiled_window_transparent"
            }


            gridboxtype = {
                name = "LOK_parliament_diagram"

                position = { x = 45 y = 12 }

                size = {
                    width = 620
                    height = 225
                }

                slotsize = {
                    width = 100%%
                    height = 0
                }

                max_slots_horizontal = 1

                add_horizontal = no
            }


            instantTextBoxType = {
                name = "LOK_parliament_government_support"

                position = { x = 90 y = 220 }

                font = "hoi_20b"

                text = "LOK_parliament_gui_government_support"

                maxWidth = 520
                maxHeight = 25

                fixedsize = yes

                format = center
            }
        }


        # ----------------------------------------------------
        # filters
        # ----------------------------------------------------

        containerWindowType = {
            name = "LOK_parliament_filters"

            position = { x = 35 y = 344 }

            size = {
                width = 690
                height = 34
            }


            instantTextBoxType = {
                name = "LOK_parliament_filters_label"

                position = { x = 0 y = 6 }

                font = "hoi_18mbs"

                text = "LOK_parliament_gui_filters"

                maxWidth = 55
                maxHeight = 20

                format = left
            }


            # banned filter

            buttonType = {
                name = "LOK_show_banned_off_button"

                position = { x = 65 y = 5 }

                quadTextureSprite = "GFX_LOK_parliament_toggle_off"

                pdx_tooltip = "LOK_parliament_gui_show_banned_tt"

                clicksound = click_default
            }

            buttonType = {
                name = "LOK_show_banned_on_button"

                position = { x = 65 y = 5 }

                quadTextureSprite = "GFX_LOK_parliament_toggle_on"

                pdx_tooltip = "LOK_parliament_gui_show_banned_tt"

                clicksound = click_default
            }

            instantTextBoxType = {
                name = "LOK_show_banned_label"

                position = { x = 91 y = 6 }

                font = "hoi_18mbs"

                text = "LOK_parliament_gui_show_banned"

                maxWidth = 205
                maxHeight = 20

                format = left
            }


            # zero-seat filter

            buttonType = {
                name = "LOK_show_zero_off_button"

                position = { x = 326 y = 5 }

                quadTextureSprite = "GFX_LOK_parliament_toggle_off"

                pdx_tooltip = "LOK_parliament_gui_show_zero_tt"

                clicksound = click_default
            }

            buttonType = {
                name = "LOK_show_zero_on_button"

                position = { x = 326 y = 5 }

                quadTextureSprite = "GFX_LOK_parliament_toggle_on"

                pdx_tooltip = "LOK_parliament_gui_show_zero_tt"

                clicksound = click_default
            }

            instantTextBoxType = {
                name = "LOK_show_zero_label"

                position = { x = 352 y = 6 }

                font = "hoi_18mbs"

                text = "LOK_parliament_gui_show_zero"

                maxWidth = 315
                maxHeight = 20

                format = left
            }
        }


        # ----------------------------------------------------
        # scrollable party list
        # ----------------------------------------------------

        containerWindowType = {
            name = "LOK_parliament_party_list_block"

            position = { x = 30 y = 382 }

            size = {
                width = 700
                height = 316
            }

            clipping = yes

            verticalScrollbar = "right_vertical_slider"

            vertical_scroll_step = 62
            scroll_wheel_factor = 62

            smooth_scrolling = yes

            margin = {
                top = 5
                left = 5
                bottom = 5
                right = 27
            }

            background = {
                name = "background"

                quadTextureSprite = "GFX_tiled_window_transparent"
            }


            gridBoxType = {
                name = "LOK_parliament_party_list"

                position = { x = 5 y = 5 }

                size = {
                    width = 660
                    height = 100%%
                }

                slotsize = {
                    width = 655
                    height = 62
                }

                max_slots_horizontal = 1

                format = "UPPER_LEFT"
            }
        }
    }


    # ========================================================
    # parliament seat dynamic-list entry
    # ========================================================

    containerWindowType = {
        name = "LOK_parliament_seat"

        size = {
            width = 10
            height = 10
        }

        iconType = {
            name = "LOK_parliament_seat_icon"

            quadTextureSprite = "GFX_LOK_parliament_seat"
        }
    }


    # ========================================================
    # party dynamic-list entry
    # ========================================================

    containerWindowType = {
        name = "LOK_parliament_party_entry"

        size = {
            width = 655
            height = 58
        }

        background = {
            name = "background"

            quadTextureSprite = "GFX_tiled_window_transparent"
        }


        instantTextBoxType = {
            name = "LOK_party_name"

            position = { x = 12 y = 6 }

            font = "hoi_20b"

            text = "LOK_parliament_gui_party_name"

            maxWidth = 365
            maxHeight = 22

            fixedsize = yes

            format = left
        }


        instantTextBoxType = {
            name = "LOK_party_ideology"

            position = { x = 12 y = 30 }

            font = "hoi_16mbs"

            text = "LOK_parliament_gui_party_ideology"

            maxWidth = 170
            maxHeight = 18

            fixedsize = yes

            format = left
        }


        instantTextBoxType = {
            name = "LOK_party_status"

            position = { x = 183 y = 30 }

            font = "hoi_16mbs"

            text = "LOK_parliament_gui_party_status"

            maxWidth = 90
            maxHeight = 18

            fixedsize = yes

            format = left
        }


        instantTextBoxType = {
            name = "LOK_party_share"

            position = { x = 283 y = 7 }

            font = "hoi_16mbs"

            text = "LOK_parliament_gui_party_share"

            maxWidth = 145
            maxHeight = 18

            fixedsize = yes

            format = left
        }


        instantTextBoxType = {
            name = "LOK_party_approval"

            position = { x = 283 y = 31 }

            font = "hoi_16mbs"

            text = "LOK_parliament_gui_party_approval"

            maxWidth = 145
            maxHeight = 18

            fixedsize = yes

            format = left
        }


        instantTextBoxType = {
            name = "LOK_party_approval_target"

            position = { x = 432 y = 31 }

            font = "hoi_16mbs"

            text = "LOK_parliament_gui_party_approval_target"

            maxWidth = 165
            maxHeight = 18

            fixedsize = yes

            format = left
        }


        buttonType = {
            name = "LOK_party_demands_button"

            position = { x = 610 y = 15 }

            quadTextureSprite = "GFX_LOK_parliament_demands"

            pdx_tooltip = "LOK_parliament_gui_demands_tt"
        }
    }
}
''')

# ============================================================
# scripted GUI
# ============================================================

write("common/scripted_guis/LOK_parliament_gui.txt", r'''
scripted_gui = {

    # ========================================================
    # launcher
    # ========================================================

    LOK_parliament_launcher_scripted_gui = {

        window_name = "LOK_parliament_launcher_gui"

        context_type = player_context


        visible = {
            has_country_flag = lok_parliament_initialized

            NOT = {
                has_country_flag = LOK_parliament_gui_open
            }
        }


        effects = {

            LOK_parliament_open_button_click = {
                LOK_parliament_gui_open = yes
            }
        }
    }


    # ========================================================
    # main parliament window
    # ========================================================

    LOK_parliament_scripted_gui = {

        window_name = "LOK_parliament_gui"

        context_type = player_context


        visible = {
            has_country_flag = LOK_parliament_gui_open
        }


        dirty = lok_parliament_gui_dirty


        dynamic_lists = {

            # Same X-array dynamic-list model as the TAI estate parliament.
            LOK_parliament_diagram = {

                array = lok_parliament_gui_seat_x

                change_scope = no

                entry_container = LOK_parliament_seat

                index = seat_idx
            }


            # Filtered list. party_idx is the actual ideology/party ID.
            LOK_parliament_party_list = {

                array = lok_parliament_gui_party_list

                value = party_idx

                index = party_list_idx

                change_scope = no

                entry_container = LOK_parliament_party_entry
            }
        }


        properties = {

            LOK_parliament_seat_icon = {

                x = lok_parliament_gui_seat_x^seat_idx

                y = lok_parliament_gui_seat_y^seat_idx

                frame = lok_parliament_gui_seat_frame^seat_idx
            }
        }


        effects = {

            LOK_parliament_close_button_click = {

                clr_country_flag = LOK_parliament_gui_open

                add_to_variable = {
                    lok_parliament_gui_dirty = 1
                }
            }


            LOK_show_banned_off_button_click = {
                LOK_parliament_gui_toggle_banned = yes
            }

            LOK_show_banned_on_button_click = {
                LOK_parliament_gui_toggle_banned = yes
            }


            LOK_show_zero_off_button_click = {
                LOK_parliament_gui_toggle_zero = yes
            }

            LOK_show_zero_on_button_click = {
                LOK_parliament_gui_toggle_zero = yes
            }
        }


        triggers = {

            LOK_show_banned_off_button_visible = {
                check_variable = {
                    lok_parliament_gui_show_banned = 0
                }
            }

            LOK_show_banned_on_button_visible = {
                check_variable = {
                    lok_parliament_gui_show_banned = 1
                }
            }


            LOK_show_zero_off_button_visible = {
                check_variable = {
                    lok_parliament_gui_show_zero = 0
                }
            }

            LOK_show_zero_on_button_visible = {
                check_variable = {
                    lok_parliament_gui_show_zero = 1
                }
            }
        }
    }
}
''')

# ============================================================
# party filtering
# ============================================================

filter_code = ""

for i in range(9):
    filter_code += f'''
    # Party {i}
    if = {{
        limit = {{
            OR = {{

                # banned: only include when first filter is enabled
                AND = {{
                    check_variable = {{
                        pol_party_array^{i} = 3
                    }}

                    check_variable = {{
                        lok_parliament_gui_show_banned = 1
                    }}
                }}


                # allowed parties
                AND = {{

                    NOT = {{
                        check_variable = {{
                            pol_party_array^{i} = 3
                        }}
                    }}

                    OR = {{

                        check_variable = {{
                            lok_parliament_party_share_array^{i} > 0
                        }}

                        AND = {{
                            check_variable = {{
                                lok_parliament_party_share_array^{i} = 0
                            }}

                            check_variable = {{
                                lok_parliament_gui_show_zero = 1
                            }}
                        }}
                    }}
                }}
            }}
        }}

        add_to_array = {{
            lok_parliament_gui_party_list = {i}
        }}
    }}
'''

# ============================================================
# cumulative seat allocation
# ============================================================

cum_code = '''
    set_variable = {
        lok_parliament_gui_cum_0 = lok_parliament_party_share_array^0
    }
'''

for i in range(1, 8):
    cum_code += f'''
    set_variable = {{
        lok_parliament_gui_cum_{i} = lok_parliament_gui_cum_{i-1}
    }}

    add_to_variable = {{
        lok_parliament_gui_cum_{i} = lok_parliament_party_share_array^{i}
    }}
'''

for i in range(8):
    cum_code += f'''
    multiply_variable = {{
        lok_parliament_gui_cum_{i} = {SEATS}
    }}

    round_variable = lok_parliament_gui_cum_{i}

    if = {{
        limit = {{
            check_variable = {{
                lok_parliament_gui_cum_{i} > {SEATS}
            }}
        }}

        set_variable = {{
            lok_parliament_gui_cum_{i} = {SEATS}
        }}
    }}
'''

resize_code = ""

for i in range(8):
    resize_code += f'''
    resize_array = {{
        array = lok_parliament_gui_seat_frame
        value = {i+1}
        size = lok_parliament_gui_cum_{i}
    }}
'''

resize_code += f'''
    resize_array = {{
        array = lok_parliament_gui_seat_frame
        value = 9
        size = {SEATS}
    }}
'''

position_code = ""

for x,y in coords:
    position_code += f'''
    add_to_array = {{ lok_parliament_gui_seat_x = {x} }}
    add_to_array = {{ lok_parliament_gui_seat_y = {y} }}
'''

effects = f'''
# ============================================================
# Parliament GUI support
# ============================================================

LOK_parliament_gui_open = {{

    set_country_flag = LOK_parliament_gui_open


    # Default filters are both disabled.
    if = {{
        limit = {{
            NOT = {{
                has_country_flag = LOK_parliament_gui_filters_initialized
            }}
        }}

        set_variable = {{
            lok_parliament_gui_show_banned = 0
        }}

        set_variable = {{
            lok_parliament_gui_show_zero = 0
        }}

        set_country_flag = LOK_parliament_gui_filters_initialized
    }}


    if = {{
        limit = {{
            NOT = {{
                has_country_flag = LOK_parliament_gui_positions_initialized
            }}
        }}

        LOK_parliament_gui_init_seat_positions = yes
    }}


    LOK_parliament_gui_refresh = yes
}



LOK_parliament_gui_toggle_banned = {{

    if = {{
        limit = {{
            check_variable = {{
                lok_parliament_gui_show_banned = 1
            }}
        }}

        set_variable = {{
            lok_parliament_gui_show_banned = 0
        }}
    }}

    else = {{

        set_variable = {{
            lok_parliament_gui_show_banned = 1
        }}
    }}


    LOK_parliament_gui_rebuild_party_list = yes

    add_to_variable = {{
        lok_parliament_gui_dirty = 1
    }}
}



LOK_parliament_gui_toggle_zero = {{

    if = {{
        limit = {{
            check_variable = {{
                lok_parliament_gui_show_zero = 1
            }}
        }}

        set_variable = {{
            lok_parliament_gui_show_zero = 0
        }}
    }}

    else = {{

        set_variable = {{
            lok_parliament_gui_show_zero = 1
        }}
    }}


    LOK_parliament_gui_rebuild_party_list = yes

    add_to_variable = {{
        lok_parliament_gui_dirty = 1
    }}
}



LOK_parliament_gui_refresh = {{

    LOK_parliament_gui_rebuild_party_list = yes

    LOK_parliament_gui_refresh_seats = yes

    add_to_variable = {{
        lok_parliament_gui_dirty = 1
    }}
}



# ============================================================
# Build the actually-visible list of parties.
#
# This is preferable to statically hiding one of nine rows:
# the gridbox reflows instead of leaving holes.
# ============================================================

LOK_parliament_gui_rebuild_party_list = {{

    clear_array = lok_parliament_gui_party_list

{filter_code}
}}



# ============================================================
# Turn normalized party shares into exactly 200 colored seats.
#
# Uses cumulative thresholds:
#
# share0
# share0 + share1
# share0 + share1 + share2
# ...
#
# This avoids separately rounding nine party seat counts.
# ============================================================

LOK_parliament_gui_refresh_seats = {{

{cum_code}

    clear_array = lok_parliament_gui_seat_frame

{resize_code}
}}



# ============================================================
# Static geometry.
#
# This only needs to run once per country that opens the GUI.
# ============================================================

LOK_parliament_gui_init_seat_positions = {{

    clear_array = lok_parliament_gui_seat_x

    clear_array = lok_parliament_gui_seat_y

{position_code}

    set_country_flag = LOK_parliament_gui_positions_initialized
}}
'''

write(
    "common/scripted_effects/LOK_parliament_gui_effects.txt",
    effects
)

# ============================================================
# scripted localisation
# ============================================================

party_names = [
    "LOK_parliament_gui_party_name_0",
    "LOK_parliament_gui_party_name_1",
    "LOK_parliament_gui_party_name_2",
    "LOK_parliament_gui_party_name_3",
    "LOK_parliament_gui_party_name_4",
    "LOK_parliament_gui_party_name_5",
    "LOK_parliament_gui_party_name_6",
    "LOK_parliament_gui_party_name_7",
    "LOK_parliament_gui_party_name_8",
]

party_ideologies = [
    "LOK_parliament_gui_party_ideology_0",
    "LOK_parliament_gui_party_ideology_1",
    "LOK_parliament_gui_party_ideology_2",
    "LOK_parliament_gui_party_ideology_3",
    "LOK_parliament_gui_party_ideology_4",
    "LOK_parliament_gui_party_ideology_5",
    "LOK_parliament_gui_party_ideology_6",
    "LOK_parliament_gui_party_ideology_7",
    "LOK_parliament_gui_party_ideology_8",
]

party_demands = [
    "LOK_parliament_gui_party_demands_0",
    "LOK_parliament_gui_party_demands_1",
    "LOK_parliament_gui_party_demands_2",
    "LOK_parliament_gui_party_demands_3",
    "LOK_parliament_gui_party_demands_4",
    "LOK_parliament_gui_party_demands_5",
    "LOK_parliament_gui_party_demands_6",
    "LOK_parliament_gui_party_demands_7",
    "LOK_parliament_gui_party_demands_8",
]

def defined_text(name, keys):
    out = f'''
defined_text = {{
    name = {name}
'''

    for i,key in enumerate(keys):
        out += f'''
    text = {{
        trigger = {{
            check_variable = {{
                party_idx = {i}
            }}
        }}

        localization_key = {key}
    }}
'''

    out += '''
    text = {
        localization_key = ""
    }
}
'''

    return out

scripted_loc = (
    defined_text(
        "LOK_GetParliamentGuiPartyName",
        party_names
    )
    +
    defined_text(
        "LOK_GetParliamentGuiPartyIdeology",
        party_ideologies
    )
    +
    defined_text(
        "LOK_GetParliamentGuiPartyDemands",
        party_demands
    )
    +
r'''

defined_text = {
    name = LOK_GetParliamentGuiPartyStatus

    text = {
        trigger = {
            check_variable = {
                pol_party_array^party_idx = 3
            }
        }

        localization_key = LOK_parliament_gui_status_banned
    }

    text = {
        localization_key = ""
    }
}
'''
)

write(
    "common/scripted_localisation/LOK_parliament_gui_scripted_localisation.txt",
    scripted_loc
)

# ============================================================
# localisation
# ============================================================

name_loc = [
    "§c[LOK_GetCommunismPartyName]§!",
    "§s[LOK_GetSocialismPartyName]§!",
    "§d[LOK_GetSocialDemocraticPartyName]§!",
    "§l[LOK_GetSocialLiberalPartyName]§!",
    "§m[LOK_GetDemocraticPartyName]§!",
    "§n[LOK_GetSocialConservativePartyName]§!",
    "§u[LOK_GetAuthoritarianDemocraticPartyName]§!",
    "§a[LOK_GetNeutralityPartyName]§!",
    "§f[LOK_GetFascismPartyName]§!",
]

ideology_loc = [
    "$communism$",
    "$socialism$",
    "$social_democratic$",
    "$social_liberal$",
    "$democratic$",
    "$social_conservative$",
    "$authoritarian_democratic$",
    "$neutrality$",
    "$fascism$",
]

loc = '''l_english:
 LOK_parliament_gui_title:0 "[LOK_GetParliamentName]"
 LOK_parliament_gui_open_tt:0 "Open §Y[LOK_GetParliamentName]§!"

 LOK_parliament_gui_government_support:0 "£lok_parliament_approval_icon£ Government Approval: §Y[?ROOT.lok_parliament_government_support|%0]§!"

 LOK_parliament_gui_filters:0 "Filters:"
 LOK_parliament_gui_show_banned:0 "Show banned parties"
 LOK_parliament_gui_show_banned_tt:0 "Show parties which are currently §Rbanned§!."
 LOK_parliament_gui_show_zero:0 "Show allowed parties with 0% seats"
 LOK_parliament_gui_show_zero_tt:0 "Show legal parties which currently have §Y0%§! of seats."

 LOK_parliament_gui_party_name:0 "[LOK_GetParliamentGuiPartyName]"
 LOK_parliament_gui_party_ideology:0 "[LOK_GetParliamentGuiPartyIdeology]"
 LOK_parliament_gui_party_status:0 "[LOK_GetParliamentGuiPartyStatus]"

 LOK_parliament_gui_party_share:0 "£lok_parliament_seats_icon£ §Y[?ROOT.lok_parliament_party_share_array^party_idx|%0]§!"
 LOK_parliament_gui_party_approval:0 "£lok_actor_opinion_icon£ §Y[?ROOT.lok_parliament_party_approval_array^party_idx|%0]§!"
 LOK_parliament_gui_party_approval_target:0 "£lok_actor_opinion_balance_icon£ §Y[?ROOT.lok_parliament_party_approval_target_array^party_idx|%0]§!"

 LOK_parliament_gui_status_banned:0 "§RBANNED§!"

 LOK_parliament_gui_demands_tt:0 "§Y[LOK_GetParliamentGuiPartyName]§!\\n§LDemands§!\\n[LOK_GetParliamentGuiPartyDemands]"
'''

for i in range(9):
    loc += f'''
 LOK_parliament_gui_party_name_{i}:0 "{name_loc[i]}"
 LOK_parliament_gui_party_ideology_{i}:0 "{ideology_loc[i]}"
 LOK_parliament_gui_party_demands_{i}:0 "$LOK_party_{i}_demands$"
'''

write(
    "localisation/english/LOK_parliament_gui_l_english.yml",
    loc,
    bom=True
)

# ============================================================
# refresh while open
# ============================================================

write("common/on_actions/LOK_parliament_gui_on_actions.txt", r'''
on_actions = {

    on_daily = {

        effect = {

            if = {

                limit = {
                    has_country_flag = LOK_parliament_gui_open
                }

                LOK_parliament_gui_refresh = yes
            }
        }
    }
}
''')

print("Generated Legacy of Kattail parliament GUI.")
print("200 parliament seats generated.")
"""Legacy of Kattail: state painter, source editor and tintable flag lab."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog, filedialog

from PIL import Image, ImageTk
from model import World, Emblems, FLAG_SIZES, child, default_paths, parse, scalar, value, walk
from demographics import Setup, set_local_draft, MapCatalogStore, MapDefinition, _catalog_decimal
from character_model import CharacterStore
from character_ui import CharacterWorkspace, DraftDialog
from select_ui import ChoiceBox, Choice, ChoiceIndex
from country_model import CountryStore
from country_ui import CountryWorkspace
from geography_model import GeographyStore, vp_color
from geography_ui import GeographyWorkspace


class Painter(ttk.Frame):
    def __init__(self, root, world, emblems):
        super().__init__(root)
        self.root, self.world, self.emblems = root, world, emblems
        self.character_store = CharacterStore(world)
        self.catalog_store = MapCatalogStore(world, self.character_store)
        self.country_store = CountryStore(world,self.character_store,self.catalog_store,emblems)
        self.geography_store = GeographyStore(world,self.character_store,self.catalog_store)
        self.geography_picker = None
        self._vp_seen = set()
        self.capital_picker = None
        self.world.docs.before_save = self.prepare_save
        self.current = None
        self.current_state = None
        self.rows = {}
        self.zoom = .25
        self.map_source = None
        self._map_job = None
        self._paint_feedback = None
        self._map_item = None
        self._drawn_view = None
        self.flag_drafts = {}
        self.flag_target = tk.StringVar(value='Unassigned draft')
        self.status = tk.StringVar()
        self.layer = tk.StringVar(value='Culture')
        self.brush = tk.StringVar(value='Culture')
        self.species_part = tk.StringVar(value='Majority')
        self.culture_operation = tk.StringVar(value='Set')
        self.wonder_operation = tk.StringVar(value='Move')
        self.palette_search = tk.StringVar()
        self.paint_selection = {}
        self.drag_seen = set()
        self.pick_only = False
        self.paint_scope = tk.StringVar(value='State')
        self.show_province_boundaries = tk.BooleanVar(value=False)
        self.show_state_boundaries = tk.BooleanVar(value=False)
        self.show_region_boundaries = tk.BooleanVar(value=False)
        self.last_painted = None
        self.background = tk.StringVar(value='#283c63')
        self.tint = tk.StringVar(value='#ffffff')
        self.symbol = tk.StringVar(value='')
        self.symbol_search = tk.StringVar()
        self.field_search = tk.StringVar()
        self.library_search = tk.StringVar()
        self.culture = tk.StringVar()
        self.species = tk.StringVar()
        self.minority = tk.StringVar()
        root.title('Legacy of Kattail Painter')
        root.geometry('1500x900')
        root.minsize(1050, 680)
        self.pack(fill='both', expand=True)
        self._build()
        self.world.normalise_demographics()
        self._library()
        self.refresh_palette()
        self._symbols()
        self._flag()
        self.refresh_map()
        root.protocol('WM_DELETE_WINDOW', self.close)
        self._status()
        root.bind('<Control-s>', lambda e: self.save())

    @staticmethod
    def numeric_id(text):
        return int(text.split(' · ', 1)[0].strip())

    def catalog(self, pattern):
        rows = []
        for key, label in self.world.localisation.items():
            match = re.fullmatch(pattern, key)
            if match:
                rows.append(Choice(match[1], label))
        return sorted(rows, key=lambda c: (c.name.casefold(), c.code))

    def _build(self):
        # Use the same native ttk appearance and compact workspace as the EU4 painter.
        style = ttk.Style(self.root)
        style.configure('Workspace.TNotebook.Tab', font=('Segoe UI', 13, 'bold'), padding=(12, 7))
        self.workspace = ttk.Notebook(self, style='Workspace.TNotebook')
        self.workspace.pack(fill='both', expand=True)
        self.map_workspace = ttk.Frame(self.workspace)
        self.character_workspace = ttk.Frame(self.workspace)
        self.workspace.add(self.map_workspace, text='MAP')
        self.workspace.add(self.character_workspace, text='CHARACTERS')
        self.country_workspace = ttk.Frame(self.workspace)
        self.workspace.add(self.country_workspace, text='COUNTRIES')
        top = ttk.Frame(self.map_workspace, padding=(8, 7))
        top.pack(fill='x')
        ttk.Button(top, text='Save', command=self.save).pack(side='left')
        ttk.Button(top, text='Undo', command=self.undo).pack(side='left', padx=(6, 0))
        ttk.Button(top, text='Redo', command=self.redo).pack(side='left', padx=(6, 0))
        ttk.Button(top, text='Discard drafts', command=self.discard).pack(side='left', padx=(6, 14))
        ttk.Label(top, text='Paint:').pack(side='left')
        brush = ChoiceBox(top, state='readonly', textvariable=self.brush,
                             values=['Inspect', 'Owner', 'Culture', 'Species', 'Wonder', 'VPs'], width=12)
        brush.pack(side='left', padx=(5, 14))
        brush.bind('<<ComboboxSelected>>', self.brush_changed)
        ttk.Label(top, text='View:').pack(side='left')
        layers = ChoiceBox(top, state='readonly', textvariable=self.layer,
                             values=['Owners', 'States', 'Strategic regions', 'VPs', 'Provinces', 'Terrain', 'Continents', 'Culture', 'Species', 'Minority', 'Wonder'], width=15)
        layers.pack(side='left', padx=(5, 14))
        layers.bind('<<ComboboxSelected>>', self.layer_changed)
        ttk.Button(top, text='Zoom -', command=lambda: self.change_zoom(.8)).pack(side='left')
        ttk.Button(top, text='Zoom +', command=lambda: self.change_zoom(1.25)).pack(side='left', padx=(5, 0))
        ttk.Button(top, text='Fit', command=self.fit_map).pack(side='left', padx=(5, 0))

        geography = ttk.Frame(self.map_workspace, padding=(8, 0, 8, 7))
        geography.pack(fill='x')
        ttk.Label(geography, text='Paint scope:').pack(side='left')
        ChoiceBox(geography, textvariable=self.paint_scope, values=['State', 'Strategic region'],
                     state='readonly', width=18).pack(side='left', padx=(5, 14))
        for label, variable in [('Province boundaries', self.show_province_boundaries),
                                ('State boundaries', self.show_state_boundaries),
                                ('Strategic region boundaries', self.show_region_boundaries)]:
            ttk.Checkbutton(geography, text=label, variable=variable,
                            command=self.draw_map).pack(side='left', padx=(0, 12))

        split = ttk.Panedwindow(self.map_workspace, orient='horizontal')
        split.pack(fill='both', expand=True)
        self.sidebar = ttk.Frame(split, padding=8, width=430)
        split.add(self.sidebar, weight=0)
        ttk.Label(self.sidebar, text='Legacy of Kattail', font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        self.sidebar_tabs = ttk.Notebook(self.sidebar)
        self.sidebar_tabs.pack(fill='both', expand=True, pady=(6, 0))
        library = ttk.Frame(self.sidebar_tabs, padding=(0, 6))
        self.state_tab = ttk.Frame(self.sidebar_tabs)
        self.palette_tab = ttk.Frame(self.sidebar_tabs, padding=(0, 6))
        self.sidebar_tabs.add(self.palette_tab, text='Paint')
        self.sidebar_tabs.add(self.state_tab, text='State setup')
        self.sidebar_tabs.add(library, text='Sources')
        self._palette_panel(self.palette_tab)
        ttk.Label(library, text='Source library').pack(anchor='w')
        search = self.library_search_entry = ttk.Entry(library, textvariable=self.library_search)
        search.pack(fill='x', pady=(6, 6))
        search.bind('<KeyRelease>', lambda e: self._library())
        self.library_kind = ChoiceBox(library, state='readonly', values=['Countries', 'States', 'All scripts'], width=23)
        self.library_kind.set('Countries')
        self.library_kind.pack(fill='x')
        self.library_kind.bind('<<ComboboxSelected>>', lambda e: self._library())
        listing = ttk.Frame(library)
        listing.pack(fill='both', expand=True, pady=(6, 0))
        self.library = ttk.Treeview(listing, show='tree', selectmode='browse')
        scroll = ttk.Scrollbar(listing, orient='vertical', command=self.library.yview)
        self.library.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.library.pack(side='left', fill='both', expand=True)
        self.library.bind('<<TreeviewSelect>>', self._library_select)
        self.library.bind('<Double-1>',self.edit_country_library)
        self.library.bind('<KeyPress>', lambda e: self.search_list(e, self.library_search, self.library_search_entry, self._library))
        ttk.Label(library, text=f'{len(self.world.states)} states / {len(self.world.countries)} countries\n{len(self.world.files)} script files\nSource: {self.world.root.name}', wraplength=400).pack(anchor='w', pady=(8, 0))
        self.tabs = ttk.Notebook(split)
        split.add(self.tabs, weight=1)
        map_tab, fields, flags = ttk.Frame(self.tabs), ttk.Frame(self.tabs), ttk.Frame(self.tabs)
        for frame, name in [(map_tab, 'Map'), (fields, 'All source fields'), (flags, 'Flag maker')]:
            self.tabs.add(frame, text=name)
        self._map_tab(map_tab)
        self.map_tab = map_tab
        self._state_panel(self.state_tab)
        self._fields_tab(fields)
        self._flags_tab(flags)
        definitions = ttk.Frame(self.tabs)
        self.tabs.add(definitions, text='Map definitions')
        self.definitions_panel = MapDefinitions(definitions, self)
        geography_tab = ttk.Frame(self.tabs)
        self.tabs.add(geography_tab, text='States / regions / VPs')
        self.geography_panel = GeographyWorkspace(geography_tab, self)
        self.tabs.bind('<<NotebookTabChanged>>', lambda e: (self.definitions_panel.refresh(), self.geography_panel.refresh()))
        ttk.Label(self.sidebar, text='Click/drag to paint; Shift-click to pick.\nRight-drag to pan; wheel to zoom.', wraplength=400).pack(fill='x', pady=(8, 0))
        ttk.Label(self.map_workspace, textvariable=self.status, anchor='w', padding=(8, 4)).pack(fill='x')

        self.characters_panel = CharacterWorkspace(self.character_workspace, self)
        self.countries_panel = CountryWorkspace(self.country_workspace,self)
        self.workspace.bind('<<NotebookTabChanged>>', lambda e: (self.characters_panel.refresh(),self.countries_panel.refresh()))

    def _palette_panel(self, tab):
        self.palette_title = tk.StringVar()
        ttk.Label(tab, textvariable=self.palette_title, font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        self.species_controls = ttk.Frame(tab)
        for part in ('Majority', 'Minority'):
            ttk.Radiobutton(self.species_controls, text=part, value=part, variable=self.species_part,
                            command=self.refresh_palette).pack(side='left', padx=(0, 8))
        self.culture_controls = ttk.Frame(tab)
        ttk.Label(self.culture_controls, text='Operation:').pack(side='left')
        ChoiceBox(self.culture_controls, textvariable=self.culture_operation,
                     values=['Set', 'Add', 'Remove'], state='readonly', width=10).pack(side='left', padx=6)
        self.wonder_controls = ttk.Frame(tab)
        ChoiceBox(self.wonder_controls, textvariable=self.wonder_operation,
                  values=['Move', 'Place copies'], width=18).pack(side='left')
        edit = ttk.Frame(tab); edit.pack(fill='x', pady=4)
        self.new_definition_button = ttk.Button(edit, text='New definition', command=lambda: self.open_definition(True))
        self.new_definition_button.pack(side='left')
        ttk.Button(edit, text='Edit selected', command=self.open_definition).pack(side='left', padx=6)
        ttk.Button(edit, text='Database', command=self.open_database).pack(side='left')
        self.palette_filter = ttk.Entry(tab, textvariable=self.palette_search)
        self.palette_filter.pack(fill='x', pady=6)
        self.palette_filter.bind('<KeyRelease>', lambda e: self.refresh_palette())
        listing = ttk.Frame(tab)
        listing.pack(fill='both', expand=True)
        self.palette = ttk.Treeview(listing, show='tree', selectmode='browse')
        scrollbar = ttk.Scrollbar(listing, orient='vertical', command=self.palette.yview)
        self.palette.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.palette.pack(side='left', fill='both', expand=True)
        self.palette.bind('<<TreeviewSelect>>', self.palette_selected)
        self.palette.bind('<Double-1>',lambda e:self.open_definition())
        self.palette.bind('<KeyPress>', lambda e: self.search_list(e, self.palette_search, self.palette_filter, self.refresh_palette))
        self.paint_label = tk.StringVar(value='Select something to paint.')
        ttk.Label(tab, textvariable=self.paint_label, wraplength=390).pack(fill='x', pady=(8, 0))

    def palette_key(self):
        brush = self.brush.get()
        if brush == 'Species':
            return 'Species' if self.species_part.get() == 'Majority' else 'Minority'
        if brush == 'Inspect':
            return self.layer.get() if self.layer.get() in {'Culture', 'Species', 'Minority', 'Wonder', 'States', 'Strategic regions', 'VPs'} else 'Owner'
        return brush

    def layer_changed(self, event=None):
        if self.layer.get() == 'VPs': self.brush.set('VPs')
        elif self.layer.get() in {'States','Strategic regions'} or self.brush.get() == 'VPs': self.brush.set('Inspect')
        self.palette_search.set(''); self.refresh_palette(); self.refresh_map()

    def open_database(self):
        mode = self.palette_key()
        if mode == 'Owner': self.workspace.select(self.country_workspace)
        elif mode in {'States','Strategic regions','VPs'}:
            self.geography_panel.kind.set(mode); self.tabs.select(self.geography_panel.master); self.geography_panel.refresh()
        else: self.tabs.select(self.definitions_panel.master)

    def brush_changed(self, event=None):
        mode = self.brush.get()
        if mode != 'Inspect':
            self.layer.set('Species' if mode == 'Minority' else 'Owners' if mode == 'Owner' else mode)
        self.palette_search.set('')
        self.sidebar_tabs.select(self.palette_tab)
        self.refresh_palette()
        self.refresh_map()

    def refresh_palette(self):
        mode = self.palette_key()
        self.palette_title.set({'Owner': 'Countries', 'Culture': 'Cultures',
                                'Species': 'Majority species', 'Minority': 'Minority species', 'Wonder': 'Wonders',
                                'States':'States', 'Strategic regions':'Strategic regions', 'VPs':'Victory points'}[mode])
        self.new_definition_button.configure(state='disabled' if mode in {'States','Strategic regions'} else 'normal', text='New VP on map' if mode=='VPs' else 'New definition')
        self.species_controls.pack_forget()
        self.culture_controls.pack_forget()
        self.wonder_controls.pack_forget()
        if self.brush.get() == 'Species':
            self.species_controls.pack(fill='x', pady=(6, 0), before=self.palette_filter)
        if mode == 'Culture':
            self.culture_controls.pack(fill='x', pady=(6, 0), before=self.palette_filter)
        if mode == 'Wonder':
            self.wonder_controls.pack(fill='x', pady=6, before=self.palette_filter)
        if mode == 'Owner':
            colours = self.world.country_colours()
            entries = [(tag, self.world.label(tag), colours.get(tag, (128, 128, 128)))
                       for tag in sorted(self.world.country_paths)]
        elif mode == 'Wonder':
            entries = [(0, 'No wonder (erase)', (90, 94, 100))] + [(r.key, r.name, (190, 155, 70)) for r in self.catalog_store.wonder_records().values()]
        elif mode == 'States':
            entries = [(sid,self.world.label(s.name),(100,150,190)) for sid,s in self.world.states.items()]
        elif mode == 'Strategic regions':
            entries = [(rid,self.world.label(r['name']),(100,150,190)) for rid,r in self.world.regions.items()]
        elif mode == 'VPs':
            records=self.geography_store.victory_points();maximum=max((r['value'] for r in records.values()),default=1)
            entries=[(pid,f'{r["name"]} — {r["value"]} VP',vp_color(r['value'],maximum)) for pid,r in records.items()]
        else:
            colours = self.world.culture_colours if mode == 'Culture' else (
                self.world.species_colours if mode == 'Species' else self.world.minority_colours)
            names = self.world.culture_names if mode == 'Culture' else self.world.species_names
            keys = set(colours) | set(names) if mode == 'Culture' else set(colours)
            entries = [(key, names.get(key, str(key)) + (' (no defined colour)' if key not in colours else ''),
                        colours.get(key, (128, 128, 128))) for key in sorted(keys)]
            if mode == 'Minority':
                entries.insert(0, (1000, 'No minority', (255, 255, 255)))
        self.palette.delete(*self.palette.get_children())
        self.palette_values, self.palette_images = {}, []
        selected = self.paint_selection.get(mode)
        rows = {str(key): (key, label, rgb) for key, label, rgb in entries}
        index = ChoiceIndex(Choice(str(key), label) for key, label, _ in entries)
        for choice in index.matching(self.palette_search.get()):
            key, label, rgb = rows[choice.code]
            text = choice.label
            icon = ImageTk.PhotoImage(Image.new('RGB', (16, 16), rgb))
            self.palette_images.append(icon)
            item = self.palette.insert('', 'end', text=text, image=icon)
            self.palette_values[item] = key
            if key == selected:
                self.palette.selection_set(item)
                self.palette.see(item)
        self.paint_label.set(f'Selected {mode.lower()}: {selected}' if selected is not None else 'Select something to paint.')
        if mode=='VPs': self.paint_label.set(f'Click any land province to add/edit a VP. Blue → red: 1–{maximum} VP. Names and values appear when zoomed in.')

    def open_definition(self, create=False):
        mode = self.palette_key()
        if mode in {'States','Strategic regions','VPs'}:
            if mode=='VPs' and create: self.geography_panel.new_vp()
            else:
                key=self.paint_selection.get(mode)
                if key is not None: {'States':self.geography_panel.open_state,'Strategic regions':self.geography_panel.open_region,'VPs':self.geography_panel.open_vp}[mode](key)
            return
        if mode=='Owner':
            self.countries_panel.open(None if create else self.paint_selection.get('Owner'))
            return
        kind = {'Culture': 'Cultures', 'Species': 'Species', 'Minority': 'Species', 'Wonder': 'Wonders'}.get(mode)
        if kind:
            self.definitions_panel.open(kind, None if create else self.paint_selection.get(mode))

    def palette_selected(self, event=None):
        selected = self.palette.selection()
        if selected and selected[0] in self.palette_values:
            mode = self.palette_key()
            self.paint_selection[mode] = self.palette_values[selected[0]]
            self.paint_label.set(self.palette.item(selected[0], 'text'))

    def paint_press(self, event):
        self.drag_seen.clear()
        self._vp_seen.clear()
        self.pick_only = bool(event.state & 1)
        self.pick(event)

    def paint_release(self, event=None):
        self.flush_map()
        self.drag_seen.clear()
        self.pick_only = False
        self.last_painted = None

    def _map_tab(self, tab):
        area = ttk.Frame(tab)
        area.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(area, bg='#1e1e1e', highlightthickness=0)
        xs = ttk.Scrollbar(area, orient='horizontal', command=lambda *args: self.scroll_map('x', *args))
        ys = ttk.Scrollbar(area, orient='vertical', command=lambda *args: self.scroll_map('y', *args))
        self.canvas.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        ys.grid(row=0, column=1, sticky='ns')
        xs.grid(row=1, column=0, sticky='ew')
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self.canvas.bind('<Button-1>', self.paint_press)
        self.canvas.bind('<B1-Motion>', self.pick)
        self.canvas.bind('<ButtonRelease-1>', self.paint_release)
        self.canvas.bind('<Button-3>', lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind('<B3-Motion>', self.pan_map)
        self.canvas.bind('<Configure>', lambda e: self.view_moved())
        self.canvas.bind('<MouseWheel>', lambda e: self.change_zoom(1.2 if e.delta > 0 else 1/1.2))
        self.canvas.bind('<Double-1>', self.edit_map_geography)

    def _state_panel(self, tab):
        # Scroll the form so every field remains reachable at the minimum window size.
        self.state_panel_canvas = tk.Canvas(tab, highlightthickness=0,
                                            background=ttk.Style().lookup('TFrame', 'background'))
        scroll = ttk.Scrollbar(tab, orient='vertical', command=self.state_panel_canvas.yview)
        self.state_panel_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.state_panel_canvas.pack(side='left', fill='both', expand=True)
        inspector = ttk.Frame(self.state_panel_canvas, padding=(0, 8, 8, 8))
        form = self.state_panel_canvas.create_window(0, 0, anchor='nw', window=inspector)
        inspector.bind('<Configure>', lambda e: self.state_panel_canvas.configure(
            scrollregion=self.state_panel_canvas.bbox('all')))
        self.state_panel_canvas.bind('<Configure>', lambda e: self.state_panel_canvas.itemconfigure(form, width=e.width))
        self.state_title = tk.StringVar(value='Select a state on the map')
        self.state_details = tk.StringVar(value='')
        ttk.Label(inspector, textvariable=self.state_title, font=('Segoe UI', 12, 'bold'), wraplength=380).pack(anchor='w')
        ttk.Label(inspector, textvariable=self.state_details, wraplength=380).pack(anchor='w', pady=8)
        ttk.Button(inspector,text='Edit state',command=lambda:self.geography_panel.open_state(self.current_state)).pack(fill='x',pady=3)
        ttk.Button(inspector,text='Edit strategic region',command=self.edit_current_region).pack(fill='x',pady=3)
        ttk.Separator(inspector).pack(fill='x', pady=8)
        ttk.Label(inspector, text='State demographics · DRAFT').pack(anchor='w')
        self.demographic_boxes = []
        species_choices = self.catalog(r'var_species_(\d+)')
        for label, var in [('Cultures (ordered numeric IDs)', self.culture), ('Majority species ID', self.species), ('Minority species ID (1000 = none)', self.minority)]:
            ttk.Label(inspector, text=label).pack(anchor='w', pady=(8, 0))
            if var is self.culture:
                ttk.Entry(inspector, textvariable=var).pack(fill='x')
            else:
                choices = species_choices + ([Choice('1000', 'No minority')] if var is self.minority else [])
                box = ChoiceBox(inspector, textvariable=var, values=choices)
                self.demographic_boxes.append(box); box.pack(fill='x')
        ttk.Label(inspector, text='Add a named culture').pack(anchor='w', pady=(8, 0))
        culture_choice = ChoiceBox(inspector, values=self.catalog(r'culture_(\d+)_name'), state='readonly')
        culture_choice.pack(fill='x')
        culture_choice.bind('<<ComboboxSelected>>', lambda e: self.culture.set((self.culture.get() + ' ' + str(self.numeric_id(culture_choice.get()))).strip()))
        ttk.Button(inspector, text='Apply state changes', command=self.apply_demographics).pack(fill='x', pady=10)
        ttk.Label(inspector, text='Culture and species changes are stored in the state history. Use Save to write your changes.', wraplength=380, foreground='#555').pack(anchor='w')
        ttk.Button(inspector, text='Inspect every state field', command=self.state_fields).pack(fill='x', pady=(16, 5))
        ttk.Button(inspector, text='Inspect owner history', command=self.owner_fields).pack(fill='x')
        self.owner_draft = tk.StringVar()
        ttk.Label(inspector, text='Draft owner tag').pack(anchor='w', pady=(18, 0))
        self.owner_box = ChoiceBox(inspector, textvariable=self.owner_draft, values=self.character_store.choices('countries'))
        self.owner_box.pack(fill='x')
        ttk.Button(inspector, text='Apply owner change', command=self.apply_owner).pack(fill='x', pady=5)

    def _fields_tab(self, tab):
        self.path_label = tk.StringVar(value='Select a country, state, or script from the library')
        ttk.Label(tab, textvariable=self.path_label, wraplength=1100).pack(anchor='w', padx=8, pady=8)
        bar = ttk.Frame(tab)
        bar.pack(fill='x', padx=8)
        ttk.Label(bar, text='Filter field paths').pack(side='left')
        entry = ttk.Entry(bar, textvariable=self.field_search)
        entry.pack(side='left', fill='x', expand=True, padx=8)
        entry.bind('<KeyRelease>', lambda e: self.populate_fields())
        ttk.Button(bar, text='Add custom field / block', command=self.add_field).pack(side='right')
        self.fields = ttk.Treeview(tab, columns=('value', 'line'), show='tree headings', selectmode='browse')
        self.fields.heading('#0', text='Full scope / field (repeated fields keep separate indices)')
        self.fields.heading('value', text='Source value')
        self.fields.heading('line', text='Line')
        self.fields.column('#0', width=520)
        self.fields.column('value', width=320)
        self.fields.column('line', width=60, stretch=False)
        self.fields.pack(fill='both', expand=True, padx=8, pady=8)
        fields_scroll = ttk.Scrollbar(self.fields, orient='vertical', command=self.fields.yview)
        fields_scroll.pack(side='right', fill='y')
        self.fields.configure(yscrollcommand=fields_scroll.set)
        self.fields.bind('<<TreeviewSelect>>', self._field_select)
        self.fields.bind('<Double-1>', lambda e: self.field_editor.focus_set())
        ttk.Label(tab, text='Selected value / block · edit text, then apply to memory').pack(anchor='w', padx=8)
        self.field_editor = tk.Text(tab, height=5, undo=True)
        self.field_editor.pack(fill='x', padx=8, pady=5)
        ttk.Button(tab, text='Apply selected value to draft', command=self.apply_field).pack(anchor='e', padx=8)
        ttk.Label(tab, text='Whole source draft · comments and unedited text are preserved').pack(anchor='w', padx=8, pady=(8, 0))
        self.source_editor = tk.Text(tab, height=7, undo=True)
        self.source_editor.pack(fill='x', padx=8, pady=5)
        ttk.Button(tab, text='Apply whole source to draft', command=self.apply_source).pack(anchor='e', padx=8, pady=(0, 8))

    def _flags_tab(self, tab):
        split = ttk.Panedwindow(tab, orient='horizontal')
        split.pack(fill='both', expand=True, padx=12, pady=12)
        options, preview = ttk.Frame(split), ttk.Frame(split)
        split.add(options, weight=1)
        split.add(preview, weight=1)
        ttk.Label(options, text='Flag design', font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=8)
        for label, var in [('Background colour', self.background), ('Emblem colour', self.tint)]:
            row = ttk.Frame(options)
            row.pack(fill='x', pady=7)
            ttk.Label(row, text=label).pack(anchor='w')
            controls = ttk.Frame(row)
            controls.pack(fill='x', pady=(3, 0))
            e = ttk.Entry(controls, textvariable=var, width=12)
            e.pack(side='left', padx=(0, 5))
            e.bind('<Return>', lambda e: self._flag())
            ttk.Button(controls, text='Choose…', command=lambda v=var: self.choose_colour(v)).pack(side='left')
        ttk.Button(options, text='Refresh colours', command=self._flag).pack(anchor='w')
        ttk.Label(options, text=f'{len(self.emblems.sources)} flat white masks · recoloured with the emblem colour\nGold / gilded textures are never loaded.', wraplength=420, foreground='#555').pack(anchor='w', pady=10)
        entry = self.symbol_search_entry = ttk.Entry(options, textvariable=self.symbol_search)
        entry.pack(fill='x', pady=5)
        entry.bind('<KeyRelease>', lambda e: self._symbols())
        self.symbols = tk.Listbox(options, exportselection=False)
        self.symbols.bind('<KeyPress>', self.search_symbol)
        self.symbols.pack(fill='both', expand=True)
        self.symbols.bind('<<ListboxSelect>>', self.select_symbol)
        ttk.Button(options, text='No emblem', command=lambda: (self.symbol.set(''), self._flag())).pack(anchor='w', pady=6)
        ttk.Label(preview, text='HOI4 flag preview', font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=8)
        self.flag_canvas = tk.Canvas(preview, width=492, height=312, bg='#1e1e1e', highlightthickness=0)
        self.flag_canvas.pack(fill='x', pady=8)
        self.flag_canvas.bind('<Configure>', self._draw_flag_preview)
        self.flag_sizes = ttk.Label(preview)
        self.flag_sizes.pack(anchor='w', pady=8)
        self.size_images = ttk.Frame(preview)
        self.size_images.pack(anchor='w')
        ttk.Label(preview, text='Large 82 × 52 · Medium 41 × 26 · Small 10 × 7\nPreview enlarged up to 6 times; native sizes shown below.', wraplength=460).pack(anchor='w', pady=12)
        ttk.Label(preview, text='Country / ideology draft label').pack(anchor='w')
        self.flag_target_box = ChoiceBox(preview, textvariable=self.flag_target, values=[Choice('Unassigned draft', 'Unassigned draft')] + list(self.character_store.choices('countries')))
        self.flag_target_box.pack(fill='x', pady=5)
        ttk.Button(preview, text='Keep flag in session', command=self.keep_flag).pack(anchor='w', pady=5)
        ttk.Button(preview, text='Restore selected session flag', command=self.restore_flag).pack(anchor='w')
        ttk.Label(preview, text='This panel keeps session sketches. Use Countries > Flags for native flag import, editable patterns, reusable emblems and ideology variants.', wraplength=460, foreground='#555').pack(anchor='w', pady=14)
        ttk.Button(preview,text='Edit country flags',command=lambda:self.countries_panel.open(self.flag_target.get() if self.flag_target.get() in self.world.country_paths else None)).pack(anchor='w')

    def search_list(self, event, variable, entry, refresh):
        if event.char and event.char.isprintable():
            variable.set(event.char); refresh()
            entry.focus_set(); entry.icursor('end')
            return 'break'

    def _library(self):
        self.library.delete(*self.library.get_children())
        q, kind = self.library_search.get(), self.library_kind.get()
        self.library_paths = {}
        cache = getattr(self, '_library_indices', {})
        if kind not in cache:
            if kind == 'Countries':
                rows = [(Choice(tag, self.world.label(tag)).label, path) for tag, path in self.world.countries.items()]
            elif kind == 'States':
                rows = [(Choice(str(sid), self.world.label(s.name)).label, s.path) for sid, s in self.world.states.items()]
            else:
                rows = [(p, p) for p in self.world.files]
            cache[kind] = ChoiceIndex(Choice(path, label) for label, path in rows)
            self._library_indices = cache
        for choice in cache[kind].matching(q):
            item = self.library.insert('', 'end', text=choice.name)
            self.library_paths[item] = choice.code

    def _library_select(self, event=None):
        sel = self.library.selection()
        if sel:
            rel = self.library_paths[sel[0]]
            self.open_document(rel)
            for sid, s in self.world.states.items():
                if s.path == rel:
                    self.inspect_state(sid)
                    break
            self.tabs.select(1)

    def edit_country_library(self,event=None):
        rows=self.library.selection()
        if rows:
            path=self.library_paths.get(rows[0])
            for sid,state in self.world.states.items():
                if state.path==path:self.geography_panel.open_state(sid);return
            for tag,history in self.world.countries.items():
                if history==path:self.countries_panel.open(tag);return

    def open_document(self, relative):
        self.current = relative
        self.field_search.set('')
        self.populate_fields()

    def populate_fields(self):
        self.fields.delete(*self.fields.get_children())
        self.rows.clear()
        if self.current is None:
            return
        text = self.world.docs.text(self.current)
        self.path_label.set(self.current + ('  · DRAFT' if self.current in self.world.docs.changed else ''))
        self.source_editor.delete('1.0', 'end')
        self.source_editor.insert('1.0', text)
        try:
            nodes = parse(text)
        except ValueError as exc:
            self.path_label.set(self.current + ' · parser limitation: ' + str(exc) + ' · raw text remains available')
            return
        q = self.field_search.get().lower()
        for path, node in walk(nodes):
            raw = value(text, node)
            if q and q not in (path + ' ' + raw[:100]).lower():
                continue
            line = text.count('\n', 0, node.start) + 1
            short = raw.replace('\n', ' ').replace('\r', ' ')[:140]
            item = self.fields.insert('', 'end', text=path, values=(short, line))
            self.rows[item] = node

    def _field_select(self, event=None):
        sel = self.fields.selection()
        if sel and sel[0] in self.rows:
            self.field_editor.delete('1.0', 'end')
            self.field_editor.insert('1.0', value(self.world.docs.text(self.current), self.rows[sel[0]]))

    def apply_field(self):
        sel = self.fields.selection()
        if not sel:
            return
        try:
            with self.world.docs.grouped():
                self.world.docs.edit(self.current, self.rows[sel[0]], self.field_editor.get('1.0', 'end-1c'))
                self.world.normalise_demographics()
            self.populate_fields()
            self.refresh_map()
            self._status('Field updated in memory')
        except ValueError as exc:
            messagebox.showerror('Invalid draft', str(exc), parent=self.root)

    def apply_source(self):
        if self.current:
            try:
                with self.world.docs.grouped():
                    self.world.docs.replace(self.current, self.source_editor.get('1.0', 'end-1c'))
                    self.world.normalise_demographics()
                self.populate_fields()
                self.refresh_map()
                self._status('Source updated in memory; this does not execute script effects')
            except ValueError as exc:
                messagebox.showerror('Invalid draft', str(exc), parent=self.root)

    def add_field(self):
        if not self.current:
            return
        snippet = simpledialog.askstring('Custom field', 'Enter key = value or key = { ... }.\nAppended inside the selected block, otherwise at file root.', parent=self.root)
        if not snippet:
            return
        try:
            parse(snippet)
            text = self.world.docs.text(self.current)
            sel = self.fields.selection()
            n = self.rows.get(sel[0]) if sel else None
            at = n.end - 1 if n and n.children is not None else len(text)
            with self.world.docs.grouped():
                self.world.docs.replace(self.current, text[:at] + '\n\t' + snippet + '\n' + text[at:])
                self.world.normalise_demographics()
            self.populate_fields()
            self.refresh_map()
            self._status('Custom field added to memory')
        except ValueError as exc:
            messagebox.showerror('Invalid draft', str(exc), parent=self.root)

    def refresh_map(self):
        self.cancel_map_job()
        self.catalog_store.sync_world()
        self.geography_store.sync_world()
        self.draw_map()

    def cancel_map_job(self):
        if self._map_job is not None:
            self.root.after_cancel(self._map_job); self._map_job = None

    def schedule_map(self):
        # Throttle, rather than debounce: long drags still get regular frames.
        if self._map_job is None: self._map_job = self.root.after(25, self.flush_map)

    def flush_map(self):
        pending = self._map_job is not None
        self.cancel_map_job()
        feedback, self._paint_feedback = self._paint_feedback, None
        if feedback:
            sid, detail = feedback
            self.inspect_state(sid, reveal=False); self._status(detail)
        if pending or feedback: self.refresh_map()

    def visible_box(self, size, margin=128):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width <= 1 or height <= 1: return (0, 0, *size)
        left, top = int(self.canvas.canvasx(0)), int(self.canvas.canvasy(0))
        x0, y0 = max(0, min(size[0]-1, left-margin)), max(0, min(size[1]-1, top-margin))
        return x0, y0, max(x0+1, min(size[0], left+width+margin)), max(y0+1, min(size[1], top+height+margin))

    def view_moved(self):
        if self.world.map_ids is None or self._drawn_view is None: return
        size, drawn = self._drawn_view; box = self.visible_box(size, 0)
        if not (drawn[0] <= box[0] and drawn[1] <= box[1] and box[2] <= drawn[2] and box[3] <= drawn[3]): self.schedule_map()

    def scroll_map(self, axis, *args):
        (self.canvas.xview if axis == 'x' else self.canvas.yview)(*args); self.view_moved()

    def pan_map(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1); self.view_moved()

    def draw_map(self):
        self.world.load_map()
        height, width = self.world.map_ids.shape
        size = max(1, round(width*self.zoom)), max(1, round(height*self.zoom))
        self.canvas.configure(scrollregion=(0, 0, *size))
        box = self.visible_box(size)
        image = self.world.map_image(self.layer.get(), size, box)
        image = self.world.boundary_overlay(image, self.show_province_boundaries.get(),
                                            self.show_state_boundaries.get(), self.show_region_boundaries.get(), size, box)
        self.map_source = image
        current = getattr(self, 'map_photo', None)
        if current is not None and (current.width(), current.height()) == image.size:
            current.paste(image)
        else:
            self.map_photo = ImageTk.PhotoImage(image)
            if self._map_item is not None: self.canvas.itemconfigure(self._map_item, image=self.map_photo)
        if self._map_item is None:
            self._map_item = self.canvas.create_image(box[0], box[1], anchor='nw', image=self.map_photo, tags='map')
        else: self.canvas.coords(self._map_item, box[0], box[1])
        self._drawn_view = size, box
        self.canvas.tag_lower('map')
        self.canvas.delete('wonder')
        self.canvas.delete('vp')
        if self.layer.get() == 'Wonder':
            self.draw_wonders()
        elif self.layer.get() == 'VPs': self.draw_victory_points()

    def draw_victory_points(self):
        points=self.geography_store.province_points();records=self.geography_store.victory_points()
        maximum=max((r['value'] for r in records.values()),default=1);box=self._drawn_view[1]
        for pid,r in records.items():
            if pid not in points:continue
            x,y=points[pid];x*=self.zoom;y*=self.zoom
            if not (box[0]-160<=x<=box[2]+160 and box[1]-40<=y<=box[3]+40):continue
            colour='#%02x%02x%02x'%vp_color(r['value'],maximum);radius=3 if self.zoom<.65 else 5
            self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=colour,outline='#ffffff',tags='vp')
            if self.zoom>=.65:
                label=f'{r["name"]} ({r["value"]})'
                self.canvas.create_text(x+1,y-10,text=label,fill='#10141b',anchor='s',tags='vp')
                self.canvas.create_text(x,y-11,text=label,fill='#ffffff',anchor='s',tags='vp')

    def edit_current_region(self):
        if self.current_state is not None:
            pid=next(iter(self.world.states[self.current_state].provinces),None)
            self.geography_panel.open_region(self.world.province_regions.get(pid))

    def edit_map_geography(self,event):
        if self.brush.get()!='Inspect' or self.geography_picker:return
        x,y=int(self.canvas.canvasx(event.x)/self.zoom),int(self.canvas.canvasy(event.y)/self.zoom)
        ids=self.world.map_ids
        if 0<=y<ids.shape[0] and 0<=x<ids.shape[1]:
            pid=int(ids[y,x])
            if self.layer.get()=='Strategic regions':self.geography_panel.open_region(self.world.province_regions.get(pid))
            else:self.geography_panel.open_state(self.world.province_states.get(pid))
        return 'break'

    def begin_geography_pick(self,dialog,callback,kind,allowed=None):
        if self.geography_picker:self.finish_geography_pick()
        if dialog is not None:dialog.grab_release();dialog.withdraw()
        self.geography_picker=(dialog,callback,kind,allowed)
        self.workspace.select(self.map_workspace);self.tabs.select(self.map_tab)
        self._geography_escape=self.root.bind('<Escape>',lambda e:self.finish_geography_pick(),add='+')
        self._status(f'Pick a {kind} on the map. Escape cancels.')

    def finish_geography_pick(self,chosen=None):
        if not self.geography_picker:return
        dialog,callback,kind,allowed=self.geography_picker;self.geography_picker=None
        self.root.unbind('<Escape>',self._geography_escape)
        if dialog is not None and dialog.winfo_exists():dialog.deiconify();dialog.lift();dialog.grab_set()
        self._status()
        if chosen is not None:callback(chosen)

    def draw_wonders(self):
        if not hasattr(self, '_state_centers'):
            import numpy as np
            ids = self.world.map_ids[::4, ::4]
            lookup = np.zeros(max(self.world.provinces) + 1, dtype=np.int32)
            for pid, sid in self.world.province_states.items(): lookup[pid] = sid
            states = lookup[ids]; yy, xx = np.indices(states.shape)
            counts = np.bincount(states.ravel())
            xs = np.bincount(states.ravel(), weights=xx.ravel() * 4)
            ys = np.bincount(states.ravel(), weights=yy.ravel() * 4)
            self._state_centers = {s: (xs[s]/counts[s], ys[s]/counts[s]) for s in self.world.states if s < len(counts) and counts[s]}
        self.wonder_photos = []
        if not hasattr(self, '_wonder_photo_cache'): self._wonder_photo_cache = {}
        box = self._drawn_view[1]
        for sid, ident in self.catalog_store.wonder_sites().items():
            if not ident or sid not in self._state_centers: continue
            x, y = self._state_centers[sid]; x *= self.zoom; y *= self.zoom
            if not (box[0]-44 <= x <= box[2]+44 and box[1]-30 <= y <= box[3]+30): continue
            sprite = f'GFX_wonder_{ident}'; key = (sprite, self.character_store.image_token(sprite))
            if key not in self._wonder_photo_cache:
                source = self.character_store.image(sprite, (44, 30))
                if len(self._wonder_photo_cache) >= 128: self._wonder_photo_cache.clear()
                self._wonder_photo_cache[key] = ImageTk.PhotoImage(source) if source is not None else None
            icon = self._wonder_photo_cache[key]
            if icon is not None:
                self.wonder_photos.append(icon)
                self.canvas.create_image(x, y, image=icon, tags='wonder')
            else: self.canvas.create_text(x, y, text=str(ident), fill='#ffe0a0', tags='wonder')

    def change_zoom(self, multiplier):
        self.zoom = max(.12, min(2, self.zoom * multiplier))
        self.draw_map()

    def fit_map(self):
        height, width = self.world.map_ids.shape
        self.zoom = min(self.canvas.winfo_width() / width, self.canvas.winfo_height() / height)
        self.zoom = max(.12, self.zoom)
        self.draw_map()

    def pick(self, event):
        x, y = int(self.canvas.canvasx(event.x) / self.zoom), int(self.canvas.canvasy(event.y) / self.zoom)
        ids = self.world.map_ids
        if not (0 <= y < ids.shape[0] and 0 <= x < ids.shape[1]):
            return
        pid = int(ids[y, x])
        sid = self.world.province_states.get(pid)
        if self.geography_picker:
            dialog,callback,kind,allowed=self.geography_picker
            if allowed is not None and pid not in allowed:self._status('Choose a province inside the edited state');return
            chosen=sid if kind=='state' else self.world.province_regions.get(pid) if kind=='region' else pid
            if chosen is None or kind=='province' and (sid is None or self.world.provinces[pid]['type']!='land'):
                self._status('Choose a land province belonging to a state');return
            self.finish_geography_pick(chosen);return
        if getattr(self,'capital_picker',None) is not None:
            if sid is None:self._status('Choose a state for the capital');return
            dialog=self.capital_picker;self.capital_picker=None
            self.root.unbind('<Escape>',self._capital_escape)
            dialog.receive_capital(sid);self._status('Capital state selected')
            return
        if self.layer.get()=='Strategic regions' and self.brush.get()=='Inspect':
            self.paint_selection['Strategic regions']=self.world.province_regions.get(pid)
        if self.brush.get()=='VPs':
            if pid in self._vp_seen:return
            self._vp_seen.add(pid)
            if sid is not None and self.world.provinces[pid]['type']=='land':
                if self.pick_only:self.paint_selection['VPs']=pid;self.refresh_palette()
                else:self.geography_panel.open_vp(pid)
            return
        if sid is None:
            self._status(f'Province {pid}: no state assignment')
            return
        if sid in self.drag_seen: return
        if self.pick_only or getattr(event, 'state', 0) & 1:
            if self.drag_seen:
                return
            mode = self.palette_key()
            data = self.world.demographics[sid]
            if mode == 'Owner':
                text, nodes = self.world.state_nodes(sid)
                target = scalar(text, child(nodes, 'history').children, 'owner')
            elif mode == 'Culture':
                target = next(iter(data['culture']), None)
            elif mode == 'Wonder':
                target = self.catalog_store.wonder_sites().get(sid, 0)
            elif mode == 'States':target=sid
            elif mode == 'Strategic regions':target=self.world.province_regions.get(pid)
            else:
                target = data['species' if mode == 'Species' else 'minority']
            if target is not None:
                self.paint_selection[mode] = target
            self.palette_search.set('')
            self.sidebar_tabs.select(self.palette_tab)
            self.refresh_palette()
            self.drag_seen.add(sid)
            self._status(f'Picked {mode.lower()} from state {sid}')
            return
        if self.brush.get() == 'Inspect':
            if self.layer.get()=='States':self.paint_selection['States']=sid
            self.inspect_state(sid)
            self._status(f'Province {pid}: state {sid}')
            return
        mode = self.palette_key()
        target = self.paint_selection.get(mode)
        if target is None:
            self._status('Select a value in the Paint list first')
            return
        try:
            revision = self.world.docs.revision
            affected = self.world.paint(pid, self.paint_scope.get(), mode, target,
                                        self.wonder_operation.get() if mode == 'Wonder' else self.culture_operation.get(), exclude=self.drag_seen)
            if not affected:
                return
            self.drag_seen.update(affected)
            if self.world.docs.revision == revision: return
            self._paint_feedback = sid, f'Painted {len(affected)} state(s): {mode.lower()} {target}'
            self.schedule_map()
        except ValueError as exc:
            messagebox.showerror('Invalid brush value', str(exc), parent=self.root)

    def inspect_state(self, sid, reveal=True):
        if reveal:
            self.sidebar_tabs.select(self.state_tab)
        self.current_state = sid
        s = self.world.states[sid]
        t, ns = self.world.state_nodes(sid)
        hist = child(ns, 'history')
        owner = scalar(t, hist.children, 'owner') if hist else ''
        self.state_title.set(f'{sid} · {self.world.label(s.name)}')
        self.state_details.set(f'Owner: {owner} · {self.world.label(owner)}\nPopulation: {scalar(t, ns, "manpower")}\nCategory: {scalar(t, ns, "state_category")}\n{s.path}')
        d = self.world.demographics.get(sid, {})
        self.culture.set(' '.join(map(str, d.get('culture', []))))
        self.species.set(str(d.get('species', 0)))
        self.minority.set(str(d.get('minority', 1000)))
        self.owner_draft.set(owner)
        self.flag_target.set(owner or 'Unassigned draft')

    def begin_capital_pick(self,dialog):
        self.capital_picker=dialog;self.workspace.select(self.map_workspace);self.tabs.select(0)
        self._capital_escape=self.root.bind('<Escape>',lambda e:self.cancel_capital_pick(),add='+')
        self._status('Select the capital state on the map; Escape returns without changing it.')
        self.canvas.focus_set()

    def cancel_capital_pick(self):
        dialog,self.capital_picker=self.capital_picker,None
        self.root.unbind('<Escape>',self._capital_escape)
        if dialog is not None:dialog.receive_capital()
        self._status()

    def apply_demographics(self):
        if self.current_state is None:
            return
        try:
            for box in self.demographic_boxes: box.commit()
            cultures = [int(s) for s in self.culture.get().replace(',', ' ').split()]
            set_local_draft(self.world, self.current_state, cultures, self.numeric_id(self.species.get()), self.numeric_id(self.minority.get()))
            self.inspect_state(self.current_state, reveal=False)
            self.refresh_map()
            self._status('State demographics updated; Save writes the changes')
        except ValueError as exc:
            messagebox.showerror('Invalid demographics', str(exc), parent=self.root)

    def apply_owner(self, reveal=True):
        if self.current_state is None:
            return
        self.owner_box.commit()
        tag = self.owner_draft.get().upper().strip()
        try:
            self.world.set_owner_draft(self.current_state, tag)
            self.inspect_state(self.current_state, reveal=reveal)
            self.refresh_map()
            self._status('Owner draft updated; demographics remain attached to the state')
        except ValueError as exc:
            messagebox.showerror('Invalid owner', str(exc), parent=self.root)

    def state_fields(self):
        if self.current_state:
            self.open_document(self.world.states[self.current_state].path)
            self.tabs.select(1)

    def owner_fields(self):
        self.owner_box.commit()
        tag = self.owner_draft.get()
        if tag in self.world.countries:
            self.open_document(self.world.countries[tag])
            self.tabs.select(1)

    def _symbols(self):
        self.symbols.delete(0, 'end')
        if not hasattr(self, '_symbol_index'):
            self._symbol_index = ChoiceIndex(Choice(k, k.rsplit('/', 1)[-1].replace('_', ' ').title()) for k in self.emblems.sources)
        index = self._symbol_index
        self.symbol_keys = [choice.code for choice in index.matching(self.symbol_search.get())]
        for key in self.symbol_keys:
            self.symbols.insert('end', index.by_code[key].label)

    def search_symbol(self, event):
        if event.char and event.char.isprintable():
            self.symbol_search.set(event.char); self._symbols()
            self.symbol_search_entry.focus_set(); self.symbol_search_entry.icursor('end')
            return 'break'

    def select_symbol(self, event=None):
        selection = self.symbols.curselection()
        if selection:
            self.symbol.set(self.symbol_keys[selection[0]])
            self._flag()

    def choose_colour(self, var):
        selected = colorchooser.askcolor(var.get(), parent=self.root)[1]
        if selected:
            var.set(selected)
            self._flag()

    def _flag(self):
        try:
            images = {name: self.emblems.render(self.symbol.get(), self.background.get(), self.tint.get(), size) for name, size in FLAG_SIZES.items()}
        except (ValueError, KeyError, OSError) as exc:
            messagebox.showerror('Flag preview', str(exc), parent=self.root)
            return False
        self.preview_source = images['large']
        self._draw_flag_preview()
        self.flag_sizes.configure(text=self.symbol.get() or 'Solid colour · no emblem')
        for item in self.size_images.winfo_children():
            item.destroy()
        self.native_photos = []
        for name, im in images.items():
            photo = ImageTk.PhotoImage(im)
            self.native_photos.append(photo)
            f = ttk.Frame(self.size_images, padding=6)
            f.pack(side='left', anchor='n')
            ttk.Label(f, text=name.title()).pack()
            ttk.Label(f, image=photo).pack(pady=6)
        return True

    def _draw_flag_preview(self, event=None):
        if not hasattr(self, 'preview_source'):
            return
        available = self.flag_canvas.winfo_width()
        width = min(492, available) if available > 1 else 492
        height = round(width * self.preview_source.height / self.preview_source.width)
        self.flag_canvas.configure(height=height)
        self.preview_image = ImageTk.PhotoImage(self.preview_source.resize((width, height), Image.Resampling.NEAREST))
        self.flag_canvas.delete('all')
        self.flag_canvas.create_image(0, 0, anchor='nw', image=self.preview_image)

    def keep_flag(self):
        self.flag_target_box.commit()
        if self._flag():
            self.flag_drafts[self.flag_target.get()] = (self.symbol.get(), self.background.get(), self.tint.get())
            self._status('Flag kept in session; no flag file was written')

    def restore_flag(self):
        self.flag_target_box.commit()
        draft = self.flag_drafts.get(self.flag_target.get())
        if draft:
            self.symbol.set(draft[0]); self.background.set(draft[1]); self.tint.set(draft[2])
            self._flag()

    def _sync(self):
        self._paint_feedback = None
        self.world.refresh_countries()
        self.character_store._cache.pop('choices:countries',None)
        self.world.localisation=self.character_store.localisations()
        self._library_indices={}
        self._library()
        self.world.normalise_demographics()
        self.catalog_store.sync_world()
        self.geography_store.sync_world()
        self.refresh_palette()
        self.definitions_panel.refresh()
        self.geography_panel.refresh()
        self.populate_fields()
        self.refresh_map()
        if self.current_state:
            self.inspect_state(self.current_state, reveal=False)
        self._status()
        self.characters_panel.refresh()
        self.countries_panel.refresh()
        self.owner_box.configure(values=self.character_store.choices('countries'))
        self.flag_target_box.configure(values=[Choice('Unassigned draft','Unassigned draft')]+list(self.character_store.choices('countries')))

    def prepare_save(self):
        self.geography_store.validate_save()
        self.world.normalise_demographics()
        self.character_store.prepare_save()

    def undo(self):
        self.world.docs.undo()
        self._sync()

    def redo(self):
        self.world.docs.redo()
        self._sync()

    def discard(self):
        if messagebox.askyesno('Discard session', 'Discard all unsaved source changes and session flag drafts?', parent=self.root):
            self.world.docs.reset()
            self.flag_drafts.clear()
            self._sync()

    def _status(self, detail=''):
        self.status.set(f'{len(self.world.docs.changed)} unsaved files · {len(self.flag_drafts)} session flag drafts' + ('  |  ' + detail if detail else ''))

    def save(self):
        try:
            self.world.normalise_demographics()
            setup = Setup(self.world)
            setup.load()
            if setup.selected and self.world.docs.changed:
                raise ValueError('Move startup demographics into state histories before saving. '
                                 'Run migrate_state_setup.py to stage and apply the migration.')
            count, backup = self.world.docs.save()
            self._sync()
            self._status(f'Saved {count} files' + (f'; backups: {backup.name}' if backup else ''))
        except (ValueError, OSError, UnicodeError) as exc:
            messagebox.showerror('Save failed', str(exc), parent=self.root)

    def close(self):
        if self.world.docs.changed or self.flag_drafts:
            if not messagebox.askyesno('Discard drafts and close?', 'Discard unsaved source changes and session flags, then close?', parent=self.root):
                return
        self.cancel_map_job()
        self.root.destroy()


class MapDefinitions(ttk.Frame):
    KINDS = ('Cultures', 'Culture groups', 'Species', 'Species traits', 'Wonders')

    def __init__(self, parent, app):
        super().__init__(parent, padding=10); self.pack(fill='both', expand=True)
        self.app = app; self.store = app.catalog_store
        self.kind = tk.StringVar(value='Cultures'); self.query = tk.StringVar(); self.rows = {}
        bar = ttk.Frame(self); bar.pack(fill='x')
        box = ChoiceBox(bar, textvariable=self.kind, values=self.KINDS, width=20); box.pack(side='left')
        box.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        ttk.Button(bar, text='New', command=lambda: self.open(self.kind.get())).pack(side='left', padx=8)
        ttk.Button(bar, text='Edit selected', command=self.edit).pack(side='left')
        ttk.Label(bar, text='Search name or ID:').pack(side='left', padx=(20, 6))
        search = ttk.Entry(bar, textvariable=self.query); search.pack(side='left', fill='x', expand=True)
        search.bind('<KeyRelease>', lambda e: self.refresh())
        self.search = search
        self.table = ttk.Treeview(self, columns=('detail',), show='tree headings', selectmode='browse')
        self.table.heading('#0', text='Localized name (ID)'); self.table.heading('detail', text='Group / traits / placements')
        self.table.column('#0', width=420); self.table.column('detail', width=500)
        scroll = ttk.Scrollbar(self, command=self.table.yview); self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y', pady=10); self.table.pack(fill='both', expand=True, pady=10)
        self.table.bind('<Double-1>', lambda e: self.edit()); self.table.bind('<Return>', lambda e: self.edit())
        self.table.bind('<KeyPress>', lambda e: app.search_list(e, self.query, self.search, self.refresh))
        ttk.Label(self, text='Apply creates a draft. Save writes the existing native definitions, localisation, triggers and GFX. Imported icons go into native gfx folders.', wraplength=1000).pack(anchor='w')

    def records(self, kind=None):
        return {'Cultures': self.store.cultures, 'Culture groups': self.store.groups,
                'Species': self.store.species, 'Species traits': self.store.species_traits,
                'Wonders': self.store.wonder_records}[kind or self.kind.get()]()

    def refresh(self):
        if not self.winfo_viewable(): return
        records = self.records(); kind = self.kind.get()
        selected = self.rows.get(next(iter(self.table.selection()), ''))
        self.table.delete(*self.table.get_children()); self.rows = {}
        index = ChoiceIndex(Choice(str(k), r.name) for k, r in records.items()); keys = {str(k): k for k in records}
        groups = self.store.groups() if kind == 'Cultures' else {}
        for choice in index.matching(self.query.get()):
            key = keys[choice.code]; record = records[key]
            detail = ''
            if kind == 'Cultures': detail = Choice(str(record.group), groups[record.group].name).label if record.group in groups else 'No culture group'
            elif kind == 'Species': detail = ', '.join(self.store.species_traits().get(t, MapDefinition(t, t)).name for t in record.traits)
            elif kind == 'Wonders': detail = 'States: ' + ', '.join(str(s) for s, w in self.store.wonder_sites().items() if w == key)
            item = self.table.insert('', 'end', text=choice.label, values=(detail,)); self.rows[item] = key
            if key == selected: self.table.selection_set(item)

    def edit(self):
        selected = self.table.selection()
        if selected: self.open(self.kind.get(), self.rows[selected[0]])

    def open(self, kind, key=None):
        records = self.records(kind)
        if key == 0 and kind == 'Wonders': return
        try:
            dialog = MapDefinitionDialog(self, self.store, kind, records.get(key) if key is not None else None)
            self.wait_window(dialog)
            self.app._sync()
            if dialog.result is not None:
                mode = {'Cultures': 'Culture', 'Species': 'Species', 'Wonders': 'Wonder'}.get(kind)
                if mode:
                    self.app.brush.set(mode); self.app.paint_selection[mode] = dialog.result
                    self.app.brush_changed()
        except (ValueError, OSError) as exc: messagebox.showerror('Map definition', str(exc), parent=self)


class MapDefinitionDialog(DraftDialog):
    def __init__(self, parent, store, kind, record=None):
        super().__init__(parent, store.characters, kind + ' — ' + ('Edit' if record else 'New'))
        self.catalog = store; self.kind = kind; self.new = record is None
        if record and kind == 'Wonders': record = store.wonder_detail(record.key)
        self.record = record; self.geometry('1030x850'); self.minsize(850, 700)
        records = {'Cultures': store.cultures, 'Culture groups': store.groups, 'Species': store.species,
                   'Species traits': store.species_traits, 'Wonders': store.wonder_records}[kind]()
        ident = record.key if record else 'lok_species__trait_modifier' if kind == 'Species traits' else max(records, default=0) + 1
        self.ident = tk.StringVar(value=str(ident)); self.name = tk.StringVar(value=record.name if record else '')
        self.name_color = tk.StringVar(value=record.name_color if record else '')
        self.group = tk.StringVar(value=str(record.group) if record and record.group else '')
        self.color = tk.StringVar(value=self.hex_color(record.color if record else None))
        self.minor_color = tk.StringVar(value=self.hex_color(record.minority_color if record else None))
        self.icon_path = tk.StringVar(); self.effects = dict(record.effects) if record else {}; self.percent_keys = set()
        self.selected_traits = list(record.traits) if record else []
        self.update_scripts = tk.BooleanVar(value=False)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True, padx=12, pady=12)
        details = ttk.Frame(self.tabs, padding=10); self.tabs.add(details, text='Definition')
        details.columnconfigure(1, weight=1)
        row = 0
        for label, variable in [('Native ID', self.ident), ('Localized name', self.name)]:
            ttk.Label(details, text=label).grid(row=row, column=0, sticky='w', pady=5)
            entry = ttk.Entry(details, textvariable=variable); entry.grid(row=row, column=1, sticky='ew', padx=10)
            if row == 0 and record: entry.configure(state='disabled')
            row += 1
        if kind in {'Cultures', 'Species', 'Culture groups'}:
            ttk.Label(details, text='Name color').grid(row=row, column=0, sticky='w', pady=5)
            colors = [Choice('', 'None'), Choice('W', 'White'), Choice('R', 'Red'), Choice('G', 'Green'), Choice('B', 'Blue'),
                      Choice('Y', 'Yellow'), Choice('C', 'Cyan'), Choice('O', 'Orange'), Choice('L', 'Grey'), Choice('H', 'Highlight')]
            # Native mods may define additional one-character colors.
            ChoiceBox(details, textvariable=self.name_color, values=colors, allow_custom=True).grid(row=row, column=1, sticky='ew', padx=10); row += 1
        if kind in {'Cultures', 'Species'}:
            for label, variable in [('Map color', self.color)] + ([('Minority stripe color', self.minor_color)] if kind == 'Species' else []):
                ttk.Label(details, text=label).grid(row=row, column=0, sticky='w', pady=5)
                line = ttk.Frame(details); line.grid(row=row, column=1, sticky='ew', padx=10)
                ttk.Entry(line, textvariable=variable, width=14).pack(side='left')
                ttk.Button(line, text='Choose color', command=lambda v=variable: self.pick_color(v)).pack(side='left', padx=8)
                row += 1
        if kind == 'Cultures':
            ttk.Label(details, text='Culture group').grid(row=row, column=0, sticky='w', pady=5)
            line = ttk.Frame(details); line.grid(row=row, column=1, sticky='ew', padx=10)
            self.group_box = ChoiceBox(line, textvariable=self.group, values=[Choice(str(k), r.name) for k, r in store.groups().items()])
            self.group_box.pack(side='left', fill='x', expand=True)
            ttk.Button(line, text='New group', command=self.new_group).pack(side='left', padx=6); row += 1
        if kind in {'Species', 'Species traits', 'Wonders'}:
            ttk.Label(details, text='Icon').grid(row=row, column=0, sticky='w', pady=5)
            line = ttk.Frame(details); line.grid(row=row, column=1, sticky='ew', padx=10)
            ttk.Entry(line, textvariable=self.icon_path).pack(side='left', fill='x', expand=True)
            ttk.Button(line, text='Import…', command=self.pick_icon).pack(side='left', padx=6)
            self.icon_preview = ttk.Label(line); self.icon_preview.pack(side='left')
            if record: self.preview(store.characters.image(record.sprite))
            row += 1
        ttk.Label(details, text='Description').grid(row=row, column=0, sticky='nw', pady=7)
        self.description = tk.Text(details, height=6, wrap='word', undo=True)
        self.description.grid(row=row, column=1, sticky='nsew', padx=10, pady=7)
        self.description.insert('1.0', record.description if record else ''); details.rowconfigure(row, weight=1); row += 1
        if kind == 'Species':
            ttk.Label(details, text='State species traits').grid(row=row, column=0, sticky='nw', pady=7)
            traits = ttk.Frame(details); traits.grid(row=row, column=1, sticky='ew', padx=10)
            self.trait = tk.StringVar()
            self.trait_box = ChoiceBox(traits, textvariable=self.trait, values=[Choice(k, r.name) for k, r in store.species_traits().items()])
            self.trait_box.pack(fill='x')
            line = ttk.Frame(traits); line.pack(fill='x', pady=5)
            for text, command in [('Add', self.add_trait), ('Remove selected', self.remove_trait), ('New trait', self.new_trait), ('Edit chosen trait', self.edit_trait)]:
                ttk.Button(line, text=text, command=command).pack(side='left', padx=(0, 5))
            self.traits = ttk.Treeview(traits, show='tree', height=5, selectmode='browse'); self.traits.pack(fill='x'); self.refresh_traits()
            row += 1
        if kind == 'Wonders':
            ttk.Checkbutton(details, text='Also update event/focus/decision scripted variants of this wonder', variable=self.update_scripts).grid(row=row, column=0, columnspan=2, sticky='w', pady=8); row += 1
            ttk.Label(details, text='Values are regular base effects. The native script doubles them in a capital and halves them in a noncore state. Editing updates all starting placements; optional scripted variants may have intentionally different values.', wraplength=850).grid(row=row, column=0, columnspan=2, sticky='w', pady=8)
        if kind in {'Species traits', 'Wonders'}: self.build_modifiers()
        bottom = ttk.Frame(self, padding=12); bottom.pack(fill='x')
        ttk.Label(bottom, text='Apply stages changes. Save writes native sources with backups.').pack(side='left')
        ttk.Button(bottom, text='Cancel', command=self.cancel).pack(side='right')
        ttk.Button(bottom, text='Apply definition', command=self.ok).pack(side='right', padx=8)

    @staticmethod
    def hex_color(rgb): return '#' + ''.join(f'{v:02x}' for v in (rgb or (128, 128, 128)))

    def pick_color(self, variable):
        color = colorchooser.askcolor(variable.get(), parent=self)[1]
        if color: variable.set(color)

    def preview(self, source):
        if source is not None:
            source = source.copy(); source.thumbnail((100, 61), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(source); self.icon_preview.configure(image=self.photo)

    def pick_icon(self):
        path = filedialog.askopenfilename(parent=self, title='Import native icon', filetypes=[('Images', '*.png *.dds *.tga *.bmp *.jpg *.jpeg'), ('All files', '*.*')])
        if path:
            try:
                with Image.open(path) as source: self.preview(source)
                self.icon_path.set(path)
            except (OSError, ValueError) as exc: messagebox.showerror('Icon', str(exc), parent=self)

    def new_group(self):
        dialog = MapDefinitionDialog(self, self.catalog, 'Culture groups'); self.wait_window(dialog); self.grab_set()
        self.group_box.configure(values=[Choice(str(k), r.name) for k, r in self.catalog.groups().items()])
        if dialog.result is not None: self.group.set(str(dialog.result))

    def refresh_traits(self):
        self.traits.delete(*self.traits.get_children())
        records = self.catalog.species_traits()
        for key in sorted(self.selected_traits, key=lambda k: records[k].name.casefold()):
            self.traits.insert('', 'end', iid=key, text=Choice(key, records[key].name).label)
        self.trait_box.configure(values=[Choice(k, r.name) for k, r in records.items()])

    def add_trait(self):
        self.trait_box.commit(); key = self.trait.get()
        if key in self.catalog.species_traits() and key not in self.selected_traits: self.selected_traits.append(key); self.refresh_traits()

    def remove_trait(self):
        for key in self.traits.selection(): self.selected_traits.remove(key)
        self.refresh_traits()

    def new_trait(self): self.trait_dialog()
    def edit_trait(self):
        self.trait_box.commit()
        key = next(iter(self.traits.selection()), self.trait.get())
        if key in self.catalog.species_traits(): self.trait_dialog(self.catalog.species_traits()[key])

    def trait_dialog(self, record=None):
        dialog = MapDefinitionDialog(self, self.catalog, 'Species traits', record); self.wait_window(dialog); self.grab_set()
        if dialog.result is not None and dialog.result not in self.selected_traits: self.selected_traits.append(dialog.result)
        self.refresh_traits()

    def build_modifiers(self):
        form = ttk.Frame(self.tabs, padding=10); self.tabs.add(form, text='State modifiers' if self.kind == 'Species traits' else 'Regular wonder effects')
        self.modifiers = ttk.Treeview(form, columns=('value', 'format'), show='tree headings', selectmode='browse')
        self.modifiers.heading('#0', text='Localized modifier (ID)'); self.modifiers.heading('value', text='Base value'); self.modifiers.heading('format', text='New tooltip format')
        self.modifiers.column('#0', width=580); self.modifiers.column('value', width=100); self.modifiers.column('format', width=140)
        scroll = ttk.Scrollbar(form, command=self.modifiers.yview); self.modifiers.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.modifiers.pack(fill='both', expand=True)
        line = ttk.Frame(form); line.pack(fill='x', pady=10)
        self.modifier = tk.StringVar(); self.amount = tk.StringVar(value='0.1'); self.is_percent = tk.BooleanVar(value=True)
        choices = list(self.catalog.characters.trait_store.modifier_choices()); known = {c.code for c in choices}
        choices += [Choice(k, k) for k in self.effects if k not in known]
        self.modifier_box = ChoiceBox(line, textvariable=self.modifier, values=choices, width=50); self.modifier_box.pack(side='left', fill='x', expand=True)
        self.modifier_box.bind('<<ComboboxSelected>>', lambda e: self.modifier_help())
        ttk.Entry(line, textvariable=self.amount, width=12).pack(side='left', padx=8)
        ttk.Button(line, text='Add / update', command=self.add_modifier).pack(side='left')
        ttk.Button(line, text='Remove', command=self.remove_modifier).pack(side='left', padx=8)
        if self.kind == 'Wonders': ttk.Checkbutton(form, text='Percentage tooltip for a newly registered modifier (0.1 = 10%)', variable=self.is_percent).pack(anchor='w')
        self.modifier_info = ttk.Label(form, text='Values use game units. Existing tooltip formats are preserved. Select a modifier to see its supported scopes.', wraplength=900); self.modifier_info.pack(anchor='w', pady=8)
        self.modifiers.bind('<<TreeviewSelect>>', self.pick_modifier)
        self.modifiers.bind('<KeyPress>', lambda e: self.search_modifier(e))
        self.refresh_modifiers()

    def search_modifier(self, event):
        if event.char and event.char.isprintable():
            self.modifier_box.focus_set(); self.modifier_box.display.set(event.char); self.modifier_box.typed(); return 'break'

    def modifier_help(self):
        info = self.catalog.characters.trait_store.modifier_catalog().get(self.modifier.get(), {})
        self.modifier_info.configure(text='Native scopes: ' + ', '.join(sorted(info.get('categories', ()))) + '. Values use game units.')

    def refresh_modifiers(self):
        self.modifiers.delete(*self.modifiers.get_children())
        known = self.catalog.characters.trait_store.modifier_catalog()
        registry = self.catalog.wonder_registry() if self.kind == 'Wonders' else {}
        for key in sorted(self.effects, key=lambda k: known.get(k, {}).get('choice', Choice(k, k)).name.casefold()):
            choice = known.get(key, {}).get('choice', Choice(key, key))
            fmt = 'Existing native format' if key in registry else 'Percent' if key in self.percent_keys else 'Number'
            self.modifiers.insert('', 'end', iid=key, text=choice.label, values=(self.effects[key], fmt if self.kind == 'Wonders' else ''))

    def pick_modifier(self, event=None):
        if (keys := self.modifiers.selection()):
            key = keys[0]; self.modifier.set(key); self.amount.set(self.effects[key]); self.is_percent.set(key in self.percent_keys); self.modifier_help()

    def add_modifier(self):
        try:
            self.modifier_box.commit(); key = self.modifier.get()
            if key not in self.modifier_box.index.by_code: raise ValueError('Choose a defined modifier')
            self.effects[key] = _catalog_decimal(self.amount.get())
            if self.is_percent.get(): self.percent_keys.add(key)
            else: self.percent_keys.discard(key)
            self.refresh_modifiers()
        except ValueError as exc: messagebox.showerror('Modifier', str(exc), parent=self)

    def remove_modifier(self):
        for key in self.modifiers.selection(): self.effects.pop(key, None); self.percent_keys.discard(key)
        self.refresh_modifiers()

    def ok(self):
        docs = self.catalog.docs
        snapshot = (dict(docs.drafts), list(docs.undo_stack), list(docs.redo_stack))
        try:
            ident = self.ident.get().strip() if self.kind == 'Species traits' else int(self.ident.get())
            name = self.name.get().strip(); desc = self.description.get('1.0', 'end-1c')
            if self.kind in {'Cultures', 'Species', 'Culture groups'}:
                # Commit typed choices before validating native IDs/color codes.
                for box in self.tabs.winfo_children()[0].winfo_children():
                    if isinstance(box, ChoiceBox): box.commit()
            if self.kind == 'Cultures':
                self.group_box.commit()
                self.catalog.edit_culture(ident, name, desc, self.color.get(), self.name_color.get(), int(self.group.get()), self.new)
            elif self.kind == 'Culture groups': self.catalog.edit_group(ident, name, desc, self.name_color.get(), self.new)
            elif self.kind == 'Species': self.catalog.edit_species(ident, name, desc, self.color.get(), self.minor_color.get(), self.name_color.get(), self.selected_traits, self.icon_path.get() or None, self.new)
            elif self.kind == 'Species traits': self.catalog.edit_species_trait(ident, name, desc, self.effects, self.icon_path.get() or None, self.new)
            elif self.kind == 'Wonders': self.catalog.edit_wonder(ident, name, desc, self.effects, self.icon_path.get() or None, self.new, self.percent_keys, self.update_scripts.get())
            self.accept(ident)
        except (ValueError, OSError, UnicodeError, StopIteration, KeyError) as exc:
            docs.drafts, docs.undo_stack, docs.redo_stack = snapshot; docs.revision += 1
            self.catalog.sync_world()
            messagebox.showerror('Invalid definition', str(exc), parent=self)


def main():
    defaults = default_paths()
    ap = argparse.ArgumentParser(description=__doc__)
    parent = Path(__file__).resolve().parent.parent
    ap.add_argument('--mod', type=Path, default=parent if (parent / 'descriptor.mod').exists() else defaults['mod'])
    ap.add_argument('--eu4-painter', type=Path, default=defaults['painter'])
    ap.add_argument('--stellaris', type=Path, default=defaults['stellaris'])
    ap.add_argument('--gigastructures', type=Path, default=defaults['giga'])
    args = ap.parse_args()
    root = tk.Tk()
    root.withdraw()
    try:
        if not (args.mod / 'history/states').is_dir():
            chosen = filedialog.askdirectory(title='Choose the Legacy of Kattail mod folder', parent=root)
            if not chosen:
                root.destroy(); return
            args.mod = Path(chosen)
        world = World(args.mod)
        world.demographics = Setup(world).load()
        app = Painter(root, world, Emblems(args.eu4_painter, args.stellaris, args.gigastructures))
        root.deiconify()
        if world.warnings:
            messagebox.showwarning('Source loading warnings', '\n'.join(world.warnings), parent=root)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror('Painter startup failed', str(exc), parent=root)
        root.destroy()
        raise


if __name__ == '__main__':
    main()

"""Legacy of Kattail: state painter, source editor and tintable flag lab."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog, filedialog

from PIL import Image, ImageTk
from model import World, Emblems, FLAG_SIZES, child, default_paths, parse, scalar, value, walk
from demographics import Setup, set_local_draft


class Painter(ttk.Frame):
    def __init__(self, root, world, emblems):
        super().__init__(root)
        self.root, self.world, self.emblems = root, world, emblems
        self.current = None
        self.current_state = None
        self.rows = {}
        self.zoom = .25
        self.map_source = None
        self.flag_drafts = {}
        self.flag_target = tk.StringVar(value='Unassigned draft')
        self.status = tk.StringVar()
        self.layer = tk.StringVar(value='Culture')
        self.brush = tk.StringVar(value='Culture')
        self.species_part = tk.StringVar(value='Majority')
        self.culture_operation = tk.StringVar(value='Set')
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
                rows.append((int(match[1]), re.sub('§.', '', label)))
        return [f'{i} · {label}' for i, label in sorted(rows)]

    def _build(self):
        # Use the same native ttk appearance and compact workspace as the EU4 painter.
        top = ttk.Frame(self, padding=(8, 7))
        top.pack(fill='x')
        ttk.Button(top, text='Save', command=self.save).pack(side='left')
        ttk.Button(top, text='Undo', command=self.undo).pack(side='left', padx=(6, 0))
        ttk.Button(top, text='Redo', command=self.redo).pack(side='left', padx=(6, 0))
        ttk.Button(top, text='Discard drafts', command=self.discard).pack(side='left', padx=(6, 14))
        ttk.Label(top, text='Paint:').pack(side='left')
        brush = ttk.Combobox(top, state='readonly', textvariable=self.brush,
                             values=['Inspect', 'Owner', 'Culture', 'Species'], width=12)
        brush.pack(side='left', padx=(5, 14))
        brush.bind('<<ComboboxSelected>>', self.brush_changed)
        ttk.Label(top, text='View:').pack(side='left')
        layers = ttk.Combobox(top, state='readonly', textvariable=self.layer,
                             values=['Owners', 'States', 'Provinces', 'Terrain', 'Continents', 'Culture', 'Species', 'Minority'], width=15)
        layers.pack(side='left', padx=(5, 14))
        layers.bind('<<ComboboxSelected>>', lambda e: (self.refresh_palette(), self.refresh_map()))
        ttk.Button(top, text='Zoom -', command=lambda: self.change_zoom(.8)).pack(side='left')
        ttk.Button(top, text='Zoom +', command=lambda: self.change_zoom(1.25)).pack(side='left', padx=(5, 0))
        ttk.Button(top, text='Fit', command=self.fit_map).pack(side='left', padx=(5, 0))

        geography = ttk.Frame(self, padding=(8, 0, 8, 7))
        geography.pack(fill='x')
        ttk.Label(geography, text='Paint scope:').pack(side='left')
        ttk.Combobox(geography, textvariable=self.paint_scope, values=['State', 'Strategic region'],
                     state='readonly', width=18).pack(side='left', padx=(5, 14))
        for label, variable in [('Province boundaries', self.show_province_boundaries),
                                ('State boundaries', self.show_state_boundaries),
                                ('Strategic region boundaries', self.show_region_boundaries)]:
            ttk.Checkbutton(geography, text=label, variable=variable,
                            command=self.draw_map).pack(side='left', padx=(0, 12))

        split = ttk.Panedwindow(self, orient='horizontal')
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
        search = ttk.Entry(library, textvariable=self.library_search)
        search.pack(fill='x', pady=(6, 6))
        search.bind('<KeyRelease>', lambda e: self._library())
        self.library_kind = ttk.Combobox(library, state='readonly', values=['Countries', 'States', 'All scripts'], width=23)
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
        ttk.Label(library, text=f'{len(self.world.states)} states / {len(self.world.countries)} countries\n{len(self.world.files)} script files\nSource: {self.world.root.name}', wraplength=400).pack(anchor='w', pady=(8, 0))
        self.tabs = ttk.Notebook(split)
        split.add(self.tabs, weight=1)
        map_tab, fields, flags = ttk.Frame(self.tabs), ttk.Frame(self.tabs), ttk.Frame(self.tabs)
        for frame, name in [(map_tab, 'Map'), (fields, 'All source fields'), (flags, 'Flag maker')]:
            self.tabs.add(frame, text=name)
        self._map_tab(map_tab)
        self._state_panel(self.state_tab)
        self._fields_tab(fields)
        self._flags_tab(flags)
        ttk.Label(self.sidebar, text='Click/drag to paint; Shift-click to pick.\nRight-drag to pan; wheel to zoom.', wraplength=400).pack(fill='x', pady=(8, 0))
        ttk.Label(self, textvariable=self.status, anchor='w', padding=(8, 4)).pack(fill='x')

    def _palette_panel(self, tab):
        self.palette_title = tk.StringVar()
        ttk.Label(tab, textvariable=self.palette_title, font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        self.species_controls = ttk.Frame(tab)
        for part in ('Majority', 'Minority'):
            ttk.Radiobutton(self.species_controls, text=part, value=part, variable=self.species_part,
                            command=self.refresh_palette).pack(side='left', padx=(0, 8))
        self.culture_controls = ttk.Frame(tab)
        ttk.Label(self.culture_controls, text='Operation:').pack(side='left')
        ttk.Combobox(self.culture_controls, textvariable=self.culture_operation,
                     values=['Set', 'Add', 'Remove'], state='readonly', width=10).pack(side='left', padx=6)
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
        self.paint_label = tk.StringVar(value='Select something to paint.')
        ttk.Label(tab, textvariable=self.paint_label, wraplength=390).pack(fill='x', pady=(8, 0))

    def palette_key(self):
        brush = self.brush.get()
        if brush == 'Species':
            return 'Species' if self.species_part.get() == 'Majority' else 'Minority'
        if brush == 'Inspect':
            return self.layer.get() if self.layer.get() in {'Culture', 'Species', 'Minority'} else 'Owner'
        return brush

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
                                'Species': 'Majority species', 'Minority': 'Minority species'}[mode])
        self.species_controls.pack_forget()
        self.culture_controls.pack_forget()
        if self.brush.get() == 'Species':
            self.species_controls.pack(fill='x', pady=(6, 0), before=self.palette_filter)
        if mode == 'Culture':
            self.culture_controls.pack(fill='x', pady=(6, 0), before=self.palette_filter)
        if mode == 'Owner':
            colours = self.world.country_colours()
            entries = [(tag, self.world.label(tag), colours.get(tag, (128, 128, 128)))
                       for tag in sorted(self.world.country_paths)]
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
        query = self.palette_search.get().casefold()
        selected = self.paint_selection.get(mode)
        for key, label, rgb in entries:
            text = f'{key} · {label}'
            if query not in text.casefold():
                continue
            icon = ImageTk.PhotoImage(Image.new('RGB', (16, 16), rgb))
            self.palette_images.append(icon)
            item = self.palette.insert('', 'end', text=text, image=icon)
            self.palette_values[item] = key
            if key == selected:
                self.palette.selection_set(item)
                self.palette.see(item)
        self.paint_label.set(f'Selected {mode.lower()}: {selected}' if selected is not None else 'Select something to paint.')

    def palette_selected(self, event=None):
        selected = self.palette.selection()
        if selected and selected[0] in self.palette_values:
            mode = self.palette_key()
            self.paint_selection[mode] = self.palette_values[selected[0]]
            self.paint_label.set(self.palette.item(selected[0], 'text'))

    def paint_press(self, event):
        self.drag_seen.clear()
        self.pick_only = bool(event.state & 1)
        self.pick(event)

    def paint_release(self, event=None):
        self.drag_seen.clear()
        self.pick_only = False
        self.last_painted = None

    def _map_tab(self, tab):
        area = ttk.Frame(tab)
        area.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(area, bg='#1e1e1e', highlightthickness=0)
        xs = ttk.Scrollbar(area, orient='horizontal', command=self.canvas.xview)
        ys = ttk.Scrollbar(area, orient='vertical', command=self.canvas.yview)
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
        self.canvas.bind('<B3-Motion>', lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind('<MouseWheel>', lambda e: self.change_zoom(1.2 if e.delta > 0 else 1/1.2))

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
        ttk.Separator(inspector).pack(fill='x', pady=8)
        ttk.Label(inspector, text='State demographics · DRAFT').pack(anchor='w')
        species_choices = self.catalog(r'var_species_(\d+)')
        for label, var in [('Cultures (ordered numeric IDs)', self.culture), ('Majority species ID', self.species), ('Minority species ID (1000 = none)', self.minority)]:
            ttk.Label(inspector, text=label).pack(anchor='w', pady=(8, 0))
            if var is self.culture:
                ttk.Entry(inspector, textvariable=var).pack(fill='x')
            else:
                choices = species_choices + (['1000 · No minority'] if var is self.minority else [])
                ttk.Combobox(inspector, textvariable=var, values=choices).pack(fill='x')
        ttk.Label(inspector, text='Add a named culture').pack(anchor='w', pady=(8, 0))
        culture_choice = ttk.Combobox(inspector, values=self.catalog(r'culture_(\d+)_name'), state='readonly')
        culture_choice.pack(fill='x')
        culture_choice.bind('<<ComboboxSelected>>', lambda e: self.culture.set((self.culture.get() + ' ' + str(self.numeric_id(culture_choice.get()))).strip()))
        ttk.Button(inspector, text='Apply state changes', command=self.apply_demographics).pack(fill='x', pady=10)
        ttk.Label(inspector, text='Culture and species changes are stored in the state history. Use Save to write your changes.', wraplength=380, foreground='#555').pack(anchor='w')
        ttk.Button(inspector, text='Inspect every state field', command=self.state_fields).pack(fill='x', pady=(16, 5))
        ttk.Button(inspector, text='Inspect owner history', command=self.owner_fields).pack(fill='x')
        self.owner_draft = tk.StringVar()
        ttk.Label(inspector, text='Draft owner tag').pack(anchor='w', pady=(18, 0))
        ttk.Combobox(inspector, textvariable=self.owner_draft, values=sorted(self.world.countries)).pack(fill='x')
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
        entry = ttk.Entry(options, textvariable=self.symbol_search)
        entry.pack(fill='x', pady=5)
        entry.bind('<KeyRelease>', lambda e: self._symbols())
        self.symbols = tk.Listbox(options, exportselection=False)
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
        ttk.Combobox(preview, textvariable=self.flag_target, values=['Unassigned draft'] + sorted(self.world.countries)).pack(fill='x', pady=5)
        ttk.Button(preview, text='Keep flag in session', command=self.keep_flag).pack(anchor='w', pady=5)
        ttk.Button(preview, text='Restore selected session flag', command=self.restore_flag).pack(anchor='w')
        ttk.Label(preview, text='Flags are session prototypes. There is no image export or overwrite of existing flags in this version.', wraplength=460, foreground='#555').pack(anchor='w', pady=14)

    def _library(self):
        self.library.delete(*self.library.get_children())
        q, kind = self.library_search.get().lower(), self.library_kind.get()
        self.library_paths = {}
        if kind == 'Countries':
            rows = [(tag + ' · ' + self.world.label(tag), path) for tag, path in sorted(self.world.countries.items())]
        elif kind == 'States':
            rows = [(str(sid) + ' · ' + self.world.label(s.name), s.path) for sid, s in sorted(self.world.states.items())]
        else:
            rows = [(p, p) for p in self.world.files]
        for label, path in rows:
            if q in (label + ' ' + path).lower():
                item = self.library.insert('', 'end', text=label)
                self.library_paths[item] = path

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
        self.map_source = self.world.map_image(self.layer.get())
        self.draw_map()

    def draw_map(self):
        image = self.map_source.resize((round(self.map_source.width * self.zoom), round(self.map_source.height * self.zoom)), Image.Resampling.NEAREST)
        image = self.world.boundary_overlay(image, self.show_province_boundaries.get(),
                                            self.show_state_boundaries.get(), self.show_region_boundaries.get())
        self.map_photo = ImageTk.PhotoImage(image)
        self.canvas.delete('map')
        self.canvas.create_image(0, 0, anchor='nw', image=self.map_photo, tags='map')
        self.canvas.tag_lower('map')
        self.canvas.configure(scrollregion=(0, 0, image.width, image.height))

    def change_zoom(self, multiplier):
        self.zoom = max(.12, min(2, self.zoom * multiplier))
        self.draw_map()

    def fit_map(self):
        self.zoom = min(self.canvas.winfo_width() / self.map_source.width, self.canvas.winfo_height() / self.map_source.height)
        self.zoom = max(.12, self.zoom)
        self.draw_map()

    def pick(self, event):
        x, y = int(self.canvas.canvasx(event.x) / self.zoom), int(self.canvas.canvasy(event.y) / self.zoom)
        ids = self.world.map_ids
        if not (0 <= y < ids.shape[0] and 0 <= x < ids.shape[1]):
            return
        pid = int(ids[y, x])
        sid = self.world.province_states.get(pid)
        if sid is None:
            self._status(f'Province {pid}: no state assignment')
            return
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
            self.inspect_state(sid)
            self._status(f'Province {pid}: state {sid}')
            return
        mode = self.palette_key()
        target = self.paint_selection.get(mode)
        if target is None:
            self._status('Select a value in the Paint list first')
            return
        try:
            affected = self.world.paint(pid, self.paint_scope.get(), mode, target,
                                        self.culture_operation.get(), exclude=self.drag_seen)
            if not affected:
                return
            self.drag_seen.update(affected)
            self.inspect_state(sid, reveal=False)
            self.refresh_map()
            self._status(f'Painted {len(affected)} state(s): {mode.lower()} {target}')
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

    def apply_demographics(self):
        if self.current_state is None:
            return
        try:
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
        tag = self.owner_draft.get()
        if tag in self.world.countries:
            self.open_document(self.world.countries[tag])
            self.tabs.select(1)

    def _symbols(self):
        q = self.symbol_search.get().lower()
        self.symbols.delete(0, 'end')
        for key in sorted(self.emblems.sources):
            if q in key.lower():
                self.symbols.insert('end', key)

    def select_symbol(self, event=None):
        selection = self.symbols.curselection()
        if selection:
            self.symbol.set(self.symbols.get(selection[0]))
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
        if self._flag():
            self.flag_drafts[self.flag_target.get()] = (self.symbol.get(), self.background.get(), self.tint.get())
            self._status('Flag kept in session; no flag file was written')

    def restore_flag(self):
        draft = self.flag_drafts.get(self.flag_target.get())
        if draft:
            self.symbol.set(draft[0]); self.background.set(draft[1]); self.tint.set(draft[2])
            self._flag()

    def _sync(self):
        self.world.normalise_demographics()
        self.populate_fields()
        self.refresh_map()
        if self.current_state:
            self.inspect_state(self.current_state, reveal=False)
        self._status()

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
        self.root.destroy()


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

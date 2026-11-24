"""Traits subtab and native modifier editor over the shared guarded draft store."""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from character_ui import DraftDialog
from character_model import atom, patch_field, sort_name
from model import parse, value
from select_ui import Choice, ChoiceBox, ChoiceIndex
from trait_model import TRAIT_TYPES, MODIFIER_BLOCKS, Trait, _number

GROUPS = ('Generals', 'Admirals', 'Political advisors', 'Other unit traits')


class TraitWorkspace(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app; self.store = app.character_store.trait_store
        self.query = tk.StringVar(); self.origin = tk.StringVar(value='All')
        self.overridden = tk.BooleanVar(value=False); self._job = None
        bar = ttk.Frame(self, padding=8); bar.pack(fill='x')
        ttk.Button(bar, text='New trait', command=self.new).pack(side='left')
        ttk.Button(bar, text='Edit / inspect', command=self.edit).pack(side='left', padx=6)
        ttk.Button(bar, text='Clone with new ID', command=self.clone).pack(side='left')
        ttk.Label(bar, text='Search:').pack(side='left', padx=(12, 4))
        self.search = ttk.Entry(bar, textvariable=self.query, width=26); self.search.pack(side='left')
        self.search.bind('<KeyRelease>', self.search_changed)
        box = ChoiceBox(bar, textvariable=self.origin, values=['All', 'Mod', 'Vanilla'], width=10)
        box.pack(side='left', padx=6); box.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        ttk.Checkbutton(bar, text='Show overridden vanilla', variable=self.overridden, command=self.refresh).pack(side='left')
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True)
        self.tables = {}
        for group in GROUPS:
            frame = ttk.Frame(self.tabs); self.tabs.add(frame, text=group)
            table = ttk.Treeview(frame, columns=('source', 'status', 'type'), show='tree headings', selectmode='browse')
            for key, label in [('#0', 'Localized name (trait ID)'), ('source', 'Source file'), ('status', 'Definition'), ('type', 'Trait type')]:
                table.heading(key, text=label); table.column(key, width=430 if key == '#0' else 310 if key == 'source' else 140)
            scroll = ttk.Scrollbar(frame, command=table.yview); table.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right', fill='y'); table.pack(fill='both', expand=True)
            table.bind('<Double-1>', lambda e: self.edit()); table.bind('<Return>', lambda e: self.edit())
            table.bind('<KeyPress>', self.type_in_list)
            self.tables[group] = table
        self.tabs.bind('<<NotebookTabChanged>>', lambda e: self.refresh())
        self.status = ttk.Label(self, padding=8, text='New traits and edits remain drafts until Save. Vanilla definitions can be cloned.')
        self.status.pack(fill='x')
        self.rows = {}; self._records = None; self._group_rows = {}

    def search_changed(self, event=None):
        if self._job: self.after_cancel(self._job)
        self._job = self.after(100, self.refresh)

    def type_in_list(self, event):
        if event.char and event.char.isprintable():
            self.query.set(event.char); self.search.focus_set(); self.search.icursor('end'); self.search_changed(); return 'break'

    def current_group(self):
        return self.tabs.tab(self.tabs.select(), 'text')

    def refresh(self):
        self._job = None
        if not self.winfo_viewable(): return
        records = self.store.records()
        signature = (id(records), id(self.store.names()), self.current_group(), self.query.get(), self.origin.get(), self.overridden.get())
        if signature == getattr(self, '_view_signature', None): return
        self._view_signature = signature
        if records is not self._records or getattr(self, '_names', None) is not self.store.names():
            self._records = records; self._names = self.store.names()
            self._index = ChoiceIndex(Choice(str(i), self.store.name(t.key) + ' ' + t.key) for i, t in enumerate(records))
        table = self.tables[self.current_group()]
        selected = self.selected()
        table.delete(*table.get_children()); self.rows = {}
        self._group_rows[self.current_group()] = self.rows
        matches = {int(c.code) for c in self._index.matching(self.query.get())}
        ordered = sorted((i for i in matches if self.current_group() in records[i].groups),
                         key=lambda i: (sort_name(self.store.name(records[i].key)), records[i].key, records[i].origin, records[i].path))
        for i in ordered:
            t = records[i]
            if self.origin.get() != 'All' and t.origin != self.origin.get(): continue
            if not self.overridden.get() and not t.active: continue
            item = table.insert('', 'end', text=Choice(t.key, self.store.name(t.key)).label,
                                values=(t.path, t.origin + (' — active' if t.active else ' — overridden'), t.trait_type or t.unit_type))
            self.rows[item] = t
            if selected and (t.key, t.path, t.origin) == (selected.key, selected.path, selected.origin): table.selection_set(item)
        self.status.configure(text=f'{len(self.rows)} definitions. Changes are drafts until Save. Political advisors includes country-leader traits from their shared native database.')

    def selected(self):
        table = self.tables[self.current_group()]; selected = table.selection()
        return self._group_rows.get(self.current_group(), {}).get(selected[0]) if selected else None

    def open(self, trait=None, clone=False):
        try:
            dialog = TraitDialog(self, self.store, trait, clone=clone,
                                 group=self.current_group())
            self.wait_window(dialog); self.refresh(); self.app._status()
        except (ValueError, OSError) as exc: messagebox.showerror('Trait', str(exc), parent=self)

    def new(self): self.open()
    def edit(self):
        if (trait := self.selected()): self.open(trait)
    def clone(self):
        if (trait := self.selected()): self.open(trait, True)


class TraitDialog(DraftDialog):
    def __init__(self, parent, store, trait=None, clone=False, group='Generals'):
        super().__init__(parent, store.characters, 'Trait definition')
        self.trait_store = store; self.trait = trait; self.new = trait is None or clone
        self.read_only = bool(trait and trait.origin == 'Vanilla' and not clone)
        self.geometry('1050x820'); self.minsize(900, 700)
        family = trait.family if trait else 'country' if group == 'Political advisors' else 'unit'
        self.family = tk.StringVar(value=family)
        self.ident = tk.StringVar(value=trait.key + ('_copy' if clone else '') if trait else '')
        self.name = tk.StringVar(value=store.name(trait.key) if trait else '')
        self.unit_type = tk.StringVar(value=trait.unit_type if trait and family == 'unit' else 'navy' if group == 'Admirals' else 'land')
        self.trait_type = tk.StringVar(value=trait.trait_type if trait else 'personality_trait')
        top = ttk.Frame(self, padding=10); top.pack(fill='x'); top.columnconfigure(1, weight=1)
        self.controls = []
        for row, (label, variable) in enumerate([('Trait ID', self.ident), ('Localized name', self.name)]):
            ttk.Label(top, text=label).grid(row=row, column=0, sticky='w', pady=4)
            entry = ttk.Entry(top, textvariable=variable); entry.grid(row=row, column=1, sticky='ew', padx=8)
            if self.read_only or row == 0 and not self.new: entry.configure(state='disabled')
            self.controls.append(entry)
        ttk.Label(top, text='Database').grid(row=2, column=0, sticky='w', pady=4)
        self.family_box = ChoiceBox(top, textvariable=self.family, values=[Choice('unit', 'Military'), Choice('country', 'Political advisor / country leader')],
                                    state='normal' if self.new and trait is None else 'disabled')
        self.family_box.grid(row=2, column=1, sticky='ew', padx=8); self.family_box.bind('<<ComboboxSelected>>', lambda e: self.family_changed())
        kinds = ttk.Frame(top); kinds.grid(row=3, column=0, columnspan=2, sticky='ew', pady=4)
        ttk.Label(kinds, text='Unit type').pack(side='left')
        self.unit_box = ChoiceBox(kinds, textvariable=self.unit_type, values=[Choice('', 'Default (unspecified)')] + [Choice(t, t.replace('_', ' ').title()) for t in ('land', 'corps_commander', 'field_marshal', 'navy', 'all', 'operative')])
        self.unit_box.pack(side='left', padx=8)
        ttk.Label(kinds, text='Trait category').pack(side='left')
        self.category_box = ChoiceBox(kinds, textvariable=self.trait_type, values=[Choice('', 'Default (unspecified)')] + [Choice(t, t.replace('_', ' ').title()) for t in TRAIT_TYPES])
        self.category_box.pack(side='left', padx=8)
        ttk.Label(top, text='Description').grid(row=4, column=0, sticky='nw', pady=4)
        self.description = tk.Text(top, height=3, wrap='word'); self.description.grid(row=4, column=1, sticky='ew', padx=8)
        self.description.insert('1.0', store.names().get(trait.key + '_desc', '') if trait else '')
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True, padx=10)
        form = ttk.Frame(self.tabs, padding=8); advanced = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(form, text='Modifiers'); self.tabs.add(advanced, text='Other fields and conditions')
        self.modifiers = ttk.Treeview(form, columns=('context', 'value'), show='tree headings', selectmode='browse')
        for field, label in [('#0', 'Localized modifier (ID)'), ('context', 'Modifier block'), ('value', 'Value')]:
            self.modifiers.heading(field, text=label); self.modifiers.column(field, width=530 if field == '#0' else 170)
        scroll = ttk.Scrollbar(form, command=self.modifiers.yview); self.modifiers.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.modifiers.pack(fill='both', expand=True)
        self.modifiers.bind('<<TreeviewSelect>>', self.pick_modifier)
        self.modifiers.bind('<KeyPress>', self.search_modifiers)
        edit = ttk.Frame(form); edit.pack(fill='x', pady=8)
        self.context = tk.StringVar(value='root' if family == 'country' else 'modifier')
        self.context_box = ChoiceBox(edit, textvariable=self.context, width=23)
        self.context_box.pack(side='left', padx=(0, 6))
        self.modifier = tk.StringVar(); self.modifier_box = ChoiceBox(edit, textvariable=self.modifier, values=store.modifier_choices(), width=42)
        self.modifier_box.pack(side='left', fill='x', expand=True)
        self.modifier_box.bind('<<ComboboxSelected>>', lambda e: self.modifier_help())
        self.amount = tk.StringVar(value='0.1'); self.amount_entry = ttk.Entry(edit, textvariable=self.amount, width=12)
        self.amount_entry.pack(side='left', padx=6)
        self.add_button = ttk.Button(edit, text='Add / update', command=self.add_modifier); self.add_button.pack(side='left')
        self.remove_button = ttk.Button(form, text='Remove selected modifier', command=self.remove_modifier); self.remove_button.pack(anchor='w')
        self.help = ttk.Label(form, text='Values use game units: 0.1 is 10% for percentage modifiers; yes/no is accepted for flags.', wraplength=950)
        self.help.pack(anchor='w', pady=8)
        ttk.Label(advanced, text='Native trait body. Basic type fields above take precedence. Nested conditions, icons, effects and special modifier blocks are preserved.', wraplength=950).pack(anchor='w')
        self.raw = ScrolledText(advanced, undo=True, wrap='none'); self.raw.pack(fill='both', expand=True, pady=6)
        body = store.body(trait, clone=clone) if trait else self.default_body(family)
        self.raw.insert('1.0', body)
        self.raw.bind('<FocusOut>', lambda e: self.refresh_modifiers())
        self.tabs.bind('<<NotebookTabChanged>>', lambda e: self.refresh_modifiers())
        bottom = ttk.Frame(self, padding=10); bottom.pack(fill='x')
        ttk.Label(bottom, text='Vanilla is read-only; use Clone with new ID.' if self.read_only else 'Apply stages a draft. Save writes the trait and English localisation with backups.').pack(side='left')
        ttk.Button(bottom, text='Close' if self.read_only else 'Cancel', command=self.cancel).pack(side='right')
        if not self.read_only: ttk.Button(bottom, text='Apply trait', command=self.ok).pack(side='right', padx=8)
        self.configure_family(); self.refresh_modifiers()
        if self.read_only:
            self.description.configure(state='disabled'); self.raw.configure(state='disabled')
            self.add_button.configure(state='disabled'); self.remove_button.configure(state='disabled'); self.amount_entry.configure(state='disabled')

    def default_body(self, family):
        return '\t\trandom = no\n' if family == 'country' else '\t\ttype = ' + (self.unit_type.get() or 'land') + '\n\t\ttrait_type = personality_trait\n\t\tmodifier = {\n\t\t}\n\t\tnew_commander_weight = { factor = 0 }\n'

    def configure_family(self):
        military = self.family.get() == 'unit'
        for box in (self.unit_box, self.category_box): box.configure(state='normal' if military and not self.read_only else 'disabled')
        contexts = [Choice('root', 'Country modifiers')] if not military else [Choice(k, k.replace('_', ' ').title()) for k in MODIFIER_BLOCKS] + [Choice('root', 'Trait stat bonuses')]
        self.context_box.configure(values=contexts)
        if self.context.get() not in self.context_box.index.by_code: self.context.set('modifier' if military else 'root')

    def family_changed(self):
        self.configure_family()
        if self.new and self.trait is None:
            self.raw.delete('1.0', 'end'); self.raw.insert('1.0', self.default_body(self.family.get())); self.refresh_modifiers()

    def parsed_body(self):
        text = 'trait = {\n' + self.raw.get('1.0', 'end-1c') + '\n}'
        return text, parse(text)[0]

    def refresh_modifiers(self):
        try:
            text, node = self.parsed_body()
            trait = Trait(self.ident.get(), self.family.get(), '', text, node, 'Mod')
            rows = self.trait_store.modifier_rows(trait)
        except ValueError: return
        self.modifiers.delete(*self.modifiers.get_children()); self.rows = {}
        catalog = self.trait_store.modifier_catalog()
        for context, key, amount in sorted(rows, key=lambda r: sort_name(catalog.get(r[1], {}).get('choice', Choice(r[1], r[1])).name)):
            label = catalog.get(key, {}).get('choice', Choice(key, key)).label
            item = self.modifiers.insert('', 'end', text=label, values=(context, amount)); self.rows[item] = (context, key, amount)

    def pick_modifier(self, event=None):
        selected = self.modifiers.selection()
        if selected and selected[0] in self.rows:
            context, key, amount = self.rows[selected[0]]; self.context.set(context); self.modifier.set(key); self.amount.set(amount); self.modifier_help()

    def search_modifiers(self, event):
        if event.char and event.char.isprintable():
            self.modifier_box.focus_set(); self.modifier_box.display.set(event.char); self.modifier_box.typed(); return 'break'

    def modifier_help(self):
        info = self.trait_store.modifier_catalog().get(self.modifier.get())
        if info: self.help.configure(text=info['choice'].label + ' — categories: ' + ', '.join(sorted(info['categories'])) + '. ' + info['source'])

    def add_modifier(self):
        if self.read_only: return
        try:
            self.context_box.commit(); self.modifier_box.commit()
            key = self.modifier.get(); context = self.context.get()
            if key not in self.trait_store.modifier_catalog(): raise ValueError('Choose a defined modifier')
            stat = key.endswith(('_skill', '_skill_factor'))
            if self.family.get() == 'country' and stat: raise ValueError('Trait skill bonuses belong on military traits')
            if self.family.get() == 'unit' and context == 'root' and not stat: raise ValueError('Place ordinary military modifiers in a modifier block')
            if self.family.get() == 'unit' and context != 'root' and stat: raise ValueError('Trait skill bonuses belong in Trait stat bonuses')
            raw = _number(self.amount.get()); text, root = self.parsed_body()
            if context == 'root': text = patch_field(text, root, key, raw)
            else:
                parent = next((n for n in root.children if n.key == context and n.children is not None), None)
                if parent is None:
                    text = patch_field(text, root, context, '{\n\t\t\t' + key + ' = ' + raw + '\n\t\t}')
                else: text = patch_field(text, parent, key, raw)
            body = value(text, parse(text)[0])[1:-1]
            self.raw.delete('1.0', 'end'); self.raw.insert('1.0', body); self.refresh_modifiers()
        except ValueError as exc: messagebox.showerror('Modifier', str(exc), parent=self)

    def remove_modifier(self):
        if self.read_only: return
        selected = self.modifiers.selection()
        if not selected: return
        context, key, _ = self.rows[selected[0]]; text, root = self.parsed_body()
        parent = root if context == 'root' else next(n for n in root.children if n.key == context)
        nodes = [n for n in parent.children if n.key == key]
        for node in reversed(nodes): text = text[:node.start] + text[node.end:]
        self.raw.delete('1.0', 'end'); self.raw.insert('1.0', value(text, parse(text)[0])[1:-1]); self.refresh_modifiers()

    def ok(self):
        try:
            self.family_box.commit(); self.unit_box.commit(); self.category_box.commit()
            text, root = self.parsed_body()
            if self.family.get() == 'unit':
                for key, raw in [('type', self.unit_type.get()), ('trait_type', self.trait_type.get())]:
                    root = parse(text)[0]
                    if raw: text = patch_field(text, root, key, raw)
                    else:
                        for node in reversed([n for n in root.children if n.key == key]):
                            text = text[:node.start] + text[node.end:]
            body = value(text, parse(text)[0])[1:-1]
            self.trait_store.edit(self.ident.get().strip(), self.family.get(), self.name.get(),
                                 self.description.get('1.0', 'end-1c'), body, create=self.new,
                                 source=self.trait.path if self.trait and not self.new else None)
            self.accept(self.ident.get().strip())
        except (ValueError, OSError) as exc: messagebox.showerror('Trait', str(exc), parent=self)

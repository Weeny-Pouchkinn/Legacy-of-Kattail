"""Full-width character/portrait galleries and native role editors."""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, ImageOps
from small_portrait import generate_small_portrait

from character_model import LARGE_SIZE, SMALL_SIZE, ROLES, PORTRAIT_SLOTS, atom, block, quote, sort_name
from model import parse, value
from select_ui import ChoiceBox, Choice, ChoiceIndex, TraitChoices


class DraftDialog(tk.Toplevel):
    def __init__(self, parent, store, title):
        super().__init__(parent)
        self.store, self.result = store, None
        self.snapshot = (dict(store.docs.drafts), list(store.docs.undo_stack), list(store.docs.redo_stack))
        self.title(title)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.bind('<Escape>', lambda e: self.cancel())

    def cancel(self):
        docs = self.store.docs
        docs.drafts, docs.undo_stack, docs.redo_stack = self.snapshot
        docs.revision += 1
        self.destroy()

    def accept(self, result=True):
        docs = self.store.docs
        start = len(self.snapshot[1])
        records = [r for entry in docs.undo_stack[start:] for r in (entry if isinstance(entry, list) else [entry])]
        if len(records) > 1:
            docs.undo_stack[start:] = [records]
        self.result = result
        self.destroy()


class Gallery(ttk.Frame):
    """Virtualised cards: large portraits for visible rows, no thumbnail wall in RAM."""
    def __init__(self, parent, panel, portraits=False):
        super().__init__(parent)
        self.panel, self.store, self.portraits = panel, panel.app.character_store, portraits
        self.query, self.order, self.nation = tk.StringVar(), tk.StringVar(value='Name'), tk.StringVar(value='All')
        self.photos = OrderedDict()
        self.revision = -1
        self.records, self.cards, self.headers = [], [], []
        self._search_job = None
        top = ttk.Frame(self, padding=8); top.pack(fill='x')
        ttk.Button(top, text='New portrait pair' if portraits else 'New character', command=self.new).pack(side='left')
        ttk.Label(top, text='Search:').pack(side='left', padx=(14, 4))
        entry = ttk.Entry(top, textvariable=self.query, width=30); entry.pack(side='left')
        entry.bind('<KeyRelease>', self.search_changed)
        ttk.Label(top, text='Sort:').pack(side='left', padx=(14, 4))
        order = ChoiceBox(top, textvariable=self.order, values=['Name', 'Tag' if portraits else 'Nation'], width=10)
        order.pack(side='left'); order.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        self.filter_box = ChoiceBox(top, textvariable=self.nation, width=33)
        self.filter_box.pack(side='left', padx=12); self.filter_box.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        self.count = ttk.Label(top); self.count.pack(side='right')
        body = ttk.Frame(self); body.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(body, background='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self.scroll)
        scrollbar.pack(side='right', fill='y'); self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.layout())
        self.canvas.bind('<MouseWheel>', self.wheel)
        self.canvas.bind('<Button-4>', lambda e: self.scroll('scroll', -2, 'units'))
        self.canvas.bind('<Button-5>', lambda e: self.scroll('scroll', 2, 'units'))

    def wheel(self, event):
        self.scroll('scroll', -1 if event.delta > 0 else 1, 'units')

    def search_changed(self, event=None):
        if self._search_job: self.after_cancel(self._search_job)
        self._search_job = self.after(100, self.refresh)

    def scroll(self, *args):
        self.canvas.yview(*args)
        self.draw()

    def refresh(self):
        self._search_job = None
        if not self.winfo_viewable():
            return
        self.revision = self.store.docs.revision
        selected = self.nation.get()
        if self.portraits:
            records = list(self.store.portraits().values())
            tags = sorted({p.tag for p in records})
            self.filter_box.configure(values=[Choice('All', 'All')] + [Choice(tag, self.store.neutral_name(tag)) for tag in tags])
            options = self.store.choices('portraits')
            self.labels = {c.code: c for c in options}
            if getattr(self, '_options', None) is not options:
                self._options = options; self.search_index = ChoiceIndex(options)
            matches = {c.code for c in self.search_index.matching(self.query.get())}
            records = [p for p in records if (selected == 'All' or p.tag == selected) and p.key in matches]
            self.records = sorted(records, key=lambda p: ((sort_name(self.store.neutral_name(p.tag)), p.tag) if self.order.get() == 'Tag' else ('', ''), sort_name(self.labels[p.key].name), p.key))
        else:
            self.filter_box.configure(values=[Choice('All', 'All'), Choice('UNASSIGNED', 'Not recruited at start')] + list(self.store.choices('countries')))
            self.records = self.store.ordered(self.order.get() == 'Nation', '' if selected == 'All' else selected, self.query.get())
        self.count.configure(text=f'{len(self.records)} entries')
        self.layout()

    def layout(self):
        if not self.winfo_viewable():
            return
        width = max(240, self.canvas.winfo_width())
        columns = max(1, width // 250)
        card_width = width / columns
        height = 400 if self.portraits else 350
        self.cards, self.headers = [], []
        group, col, y = None, 0, 8
        loc = self.store.localisations() if self.records else {}
        for i, record in enumerate(self.records):
            current = record.tag if self.portraits else record.countries[0] if record.countries else 'UNASSIGNED'
            if self.order.get() != 'Name' and current != group:
                if col:
                    y += height; col = 0
                title = 'Not recruited at start' if current == 'UNASSIGNED' else Choice(current, self.store.neutral_name(current, loc)).label
                self.headers.append((y, title)); y += 35; group = current
            self.cards.append((col * card_width + 8, y, card_width - 16, height - 12, i))
            col += 1
            if col == columns:
                col = 0; y += height
        total = y + (height if col else 0) + 8
        self.canvas.configure(scrollregion=(0, 0, width, max(total, self.canvas.winfo_height())))
        self.draw()

    def photo(self, reference, size):
        key = (reference, self.store.image_token(reference), size)
        if key not in self.photos:
            try:
                image = self.store.image(reference, size)
            except (ValueError, OSError):
                image = None
            self.photos[key] = ImageTk.PhotoImage(image) if image else None
            if len(self.photos) > 128:
                self.photos.popitem(last=False)
        else: self.photos.move_to_end(key)
        return self.photos[key]

    def draw(self):
        self.canvas.delete('all')
        self.visible_photos = []
        top = self.canvas.canvasy(0); bottom = top + self.canvas.winfo_height()
        for y, title in self.headers:
            if top - 35 < y < bottom:
                self.canvas.create_text(12, y + 15, text=title, anchor='w', font=('Segoe UI', 14, 'bold'))
        for x, y, width, height, index in self.cards:
            if y + height < top or y > bottom:
                continue
            record = self.records[index]; tag = f'card_{index}'
            self.canvas.create_rectangle(x, y, x + width, y + height, fill='white', outline='#c4c4c4', tags=tag)
            reference = record.large if self.portraits else self.store.portrait_for_character(record)
            photo = self.photo(reference, LARGE_SIZE)
            if photo:
                self.visible_photos.append(photo)
                self.canvas.create_image(x + width / 2, y + 8, anchor='n', image=photo, tags=tag)
            else:
                self.canvas.create_text(x + width / 2, y + 95, text='No large portrait', fill='#666', tags=tag)
            name = self.labels[record.key].label if self.portraits else Choice(record.key, record.name).label
            self.canvas.create_text(x + width / 2, y + 224, text=name, width=width - 12,
                                    font=('Segoe UI', 10, 'bold'), anchor='n', tags=tag)
            if self.portraits:
                small = self.photo(record.small, SMALL_SIZE) if record.small else None
                if small:
                    self.visible_photos.append(small)
                    self.canvas.create_image(x + 12, y + 312, anchor='nw', image=small, tags=tag)
                self.canvas.create_text(x + width - 12, y + 350, text=record.tag, anchor='ne', tags=tag)
            else:
                self.canvas.create_text(x + width / 2, y + 306,
                                        text=', '.join(Choice(tag, self.store.neutral_name(tag)).label for tag in record.countries) or 'Not recruited at start', width=width - 12, tags=tag)
            self.canvas.tag_bind(tag, '<Button-1>', lambda e, key=record.key: self.edit(key))

    def edit(self, key):
        dialog = PortraitDialog(self, self.store, key) if self.portraits else CharacterDialog(self, self.store, key)
        self.wait_window(dialog); self.panel.refresh(); self.panel.app._status()

    def new(self):
        dialog = PortraitDialog(self, self.store) if self.portraits else CharacterDialog(self, self.store)
        self.wait_window(dialog); self.panel.refresh(); self.panel.app._status()


class CharacterWorkspace(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill='both', expand=True)
        actions = ttk.Frame(self, padding=8); actions.pack(fill='x')
        for label, command in [('Save', app.save), ('Undo', app.undo), ('Redo', app.redo), ('Discard drafts', app.discard)]:
            ttk.Button(actions, text=label, command=command).pack(side='left', padx=(0, 6))
        ttk.Label(actions, text='Click a portrait card to edit. Changes are drafts until Save.').pack(side='left', padx=15)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True)
        self.characters = Gallery(self.tabs, self)
        self.portraits = Gallery(self.tabs, self, True)
        self.tabs.add(self.characters, text='Characters'); self.tabs.add(self.portraits, text='Portrait definitions')
        from generic_portrait_ui import GenericPortraitWorkspace
        self.generic_portraits = GenericPortraitWorkspace(self.tabs, app)
        self.tabs.add(self.generic_portraits, text='Generic Portrait Groups')
        from trait_ui import TraitWorkspace
        self.traits = TraitWorkspace(self.tabs, app)
        self.tabs.add(self.traits, text='Trait database')
        self.tabs.bind('<<NotebookTabChanged>>', lambda e: self.refresh())

    def refresh(self):
        selected = self.tabs.select()
        if selected:
            self.nametowidget(selected).refresh()


class CharacterDialog(DraftDialog):
    def __init__(self, parent, store, key=None):
        super().__init__(parent, store, 'Edit character' if key else 'New character')
        self.geometry('850x760'); self.minsize(720, 600)
        self.key, self.new = key, key is None
        c = store.characters().get(key)
        self.ident = tk.StringVar(value=key or '')
        self.name = tk.StringVar(value=c.name if c else '')
        self.country = tk.StringVar(value=c.countries[0] if c and c.countries else '')
        self.gender = tk.StringVar(value=atom(c.text, c.node.children, 'gender', 'male') if c else 'male')
        self.art = tk.StringVar(value=c.art_source if c else '')
        self._applied_identity = (key, c.name, c.description, c.art_source, self.country.get(), self.gender.get()) if c else None
        notebook = ttk.Notebook(self); notebook.pack(fill='both', expand=True, padx=10, pady=10)
        identity, roles, portraits = (ttk.Frame(notebook, padding=10) for _ in range(3))
        for frame, label in [(identity, 'Identity & description'), (roles, 'Roles, traits & stats'), (portraits, 'Portrait assignments')]:
            notebook.add(frame, text=label)
        identity.columnconfigure(1, weight=1)
        fields = [('Character ID', self.ident), ('Display name', self.name), ('Recruited by at start (blank = none)', self.country),
                  ('Gender', self.gender), ('Art source / credit', self.art)]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(identity, text=label).grid(row=row, column=0, sticky='w', pady=5)
            if variable is self.country:
                widget = self.country_box = ChoiceBox(identity, textvariable=variable, values=[Choice('', 'Not recruited at start')] + list(store.choices('countries')))
            elif variable is self.gender:
                widget = self.gender_box = ChoiceBox(identity, textvariable=variable, values=[Choice('male', 'Male'), Choice('female', 'Female')])
            else:
                widget = ttk.Entry(identity, textvariable=variable)
            widget.grid(row=row, column=1, sticky='ew', padx=(12, 0), pady=5)
            if variable is self.ident:
                self.id_entry = widget
                if not self.new: widget.configure(state='disabled')
        ttk.Label(identity, text='Description').grid(row=5, column=0, sticky='nw', pady=5)
        self.description = tk.Text(identity, height=14, wrap='word'); self.description.grid(row=5, column=1, sticky='nsew', padx=(12, 0), pady=5)
        self.description.insert('1.0', c.description if c else ''); identity.rowconfigure(5, weight=1)
        ttk.Button(identity, text='Apply identity to draft', command=self.apply_identity).grid(row=6, column=1, sticky='e', pady=8)
        self.roles = ttk.Treeview(roles, columns=('traits', 'stats'), show='tree headings', selectmode='browse')
        self.roles.heading('#0', text='Role'); self.roles.heading('traits', text='Traits'); self.roles.heading('stats', text='Stats')
        self.roles.column('#0', width=150); self.roles.column('traits', width=310); self.roles.column('stats', width=230)
        self.roles.pack(fill='both', expand=True)
        self.roles.bind('<Double-1>', lambda e: self.edit_role())
        buttons = ttk.Frame(roles); buttons.pack(fill='x', pady=8)
        ttk.Button(buttons, text='Add role', command=lambda: self.edit_role(True)).pack(side='left')
        ttk.Button(buttons, text='Edit selected role', command=self.edit_role).pack(side='left', padx=6)
        ttk.Button(buttons, text='Remove selected role', command=self.remove_role).pack(side='left')
        self.assignments = ttk.Treeview(portraits, columns=('large', 'small'), show='tree headings', height=6)
        for column, label in [('#0', 'Portrait slot'), ('large', 'Large sprite'), ('small', 'Small sprite')]:
            self.assignments.heading(column, text=label); self.assignments.column(column, width=130 if column == '#0' else 290)
        self.assignments.pack(fill='x', pady=6)
        self.slot = tk.StringVar(value='army'); self.pair = tk.StringVar()
        ttk.Label(portraits, text='Slot and portrait definition').pack(anchor='w', pady=(16, 4))
        self.slot_box = ChoiceBox(portraits, textvariable=self.slot, values=[Choice(s, s.title()) for s in PORTRAIT_SLOTS]); self.slot_box.pack(fill='x')
        self.pair_box = ChoiceBox(portraits, textvariable=self.pair); self.pair_box.pack(fill='x', pady=6)
        ttk.Button(portraits, text='Assign existing portrait pair', command=self.assign).pack(anchor='w', pady=4)
        ttk.Button(portraits, text='Create a portrait pair and assign it…', command=self.new_pair).pack(anchor='w', pady=4)
        ttk.Button(portraits, text='Link selected pair as an additional variant', command=self.link_variant).pack(anchor='w', pady=4)
        ttk.Label(portraits, text='Portrait variants linked to this character').pack(anchor='w', pady=(10, 4))
        self.variant_list = tk.Listbox(portraits, height=4, exportselection=False)
        self.variant_list.pack(fill='x')
        self.variant_list.bind('<<ListboxSelect>>', lambda e: self.pair.set(self.variant_keys[self.variant_list.curselection()[0]]) if self.variant_list.curselection() else None)
        self.variant_list.bind('<KeyPress>', self.search_variants)
        ttk.Label(portraits, text='Each slot can use a different portrait definition. Portraits are shared assets; editing a definition updates all characters using it.', wraplength=750).pack(anchor='w', pady=14)
        bottom = ttk.Frame(self, padding=10); bottom.pack(fill='x')
        ttk.Button(bottom, text='Cancel', command=self.cancel).pack(side='right')
        ttk.Button(bottom, text='Apply character to drafts', command=self.done).pack(side='right', padx=6)
        self.refresh()

    def apply_identity(self):
        try:
            self.country_box.commit(); self.gender_box.commit()
            key = self.ident.get().strip()
            current = (key, self.name.get(), self.description.get('1.0', 'end-1c'), self.art.get(), self.country.get(), self.gender.get())
            if not self.new and current == self._applied_identity:
                return True
            self.store.edit_character(key, self.name.get(), self.description.get('1.0', 'end-1c'),
                                       self.art.get(), self.country.get(), self.gender.get(), create=self.new)
            self.key, self.new = key, False
            self._applied_identity = current
            self.id_entry.configure(state='disabled'); self.refresh()
            return True
        except (ValueError, OSError) as exc:
            messagebox.showerror('Character', str(exc), parent=self)
            return False

    def refresh(self):
        self.roles.delete(*self.roles.get_children()); self.assignments.delete(*self.assignments.get_children())
        self.pair_box.configure(values=self.store.choices('portraits'))
        c = self.store.characters().get(self.key)
        if not c: return
        self.variant_list.delete(0, 'end')
        choices = self.pair_box.index.by_code
        self.variant_keys = sorted(self.store.variants(self.key), key=lambda key: sort_name(choices.get(key, Choice(key, key)).name))
        for variant in self.variant_keys:
            self.variant_list.insert('end', choices.get(variant, Choice(variant, variant)).label)
        for i, role in enumerate(c.roles):
            traits = block(role.children, 'traits')
            self.roles.insert('', 'end', iid=str(i), text=Choice(role.key, role.key.replace('_', ' ').title()).label,
                              values=(' '.join(n.key for n in traits.children) if traits else '',
                                      ', '.join(n.key + '=' + value(c.text, n) for n in role.children if n.key.endswith('skill'))))
        container = block(c.node.children, 'portraits')
        for slot in container.children if container else []:
            if slot.children:
                self.assignments.insert('', 'end', text=slot.key,
                                        values=(atom(c.text, slot.children, 'large'), atom(c.text, slot.children, 'small')))

    def edit_role(self, new=False):
        if not self.apply_identity(): return
        selected = self.roles.selection()
        if not new and not selected: return
        dialog = RoleDialog(self, self.store, self.key, None if new else int(selected[0]))
        self.wait_window(dialog); self.grab_set(); self.refresh()

    def remove_role(self):
        selected = self.roles.selection()
        if selected and messagebox.askyesno('Remove role', 'Remove this role from the character draft?', parent=self):
            self.store.remove_role(self.key, int(selected[0])); self.refresh()

    def assign(self):
        if not self.apply_identity(): return
        try:
            self.slot_box.commit(); self.pair_box.commit()
            self.store.assign_portrait(self.key, self.slot.get(), self.pair.get())
            self.refresh()
        except (KeyError, ValueError) as exc:
            messagebox.showerror('Portrait assignment', str(exc), parent=self)

    def new_pair(self):
        if not self.apply_identity(): return
        tag = self.country.get() or (self.key[:3] if re.fullmatch('[A-Z]{3}', self.key[:3]) else 'GEN')
        dialog = PortraitDialog(self, self.store, initial_tag=tag, initial_key='GFX_portrait_' + re.sub(r'[^A-Za-z0-9_]', '_', self.key))
        self.wait_window(dialog); self.grab_set()
        if dialog.result:
            self.pair.set(dialog.result); self.assign()

    def link_variant(self):
        if not self.apply_identity(): return
        try:
            self.pair_box.commit()
            self.store.link_variant(self.key, self.pair.get()); self.refresh()
        except ValueError as exc:
            messagebox.showerror('Portrait variant', str(exc), parent=self)

    def search_variants(self, event):
        if event.char and event.char.isprintable():
            self.pair_box.focus_set(); self.pair_box.display.set(event.char); self.pair_box.typed(); return 'break'

    def done(self):
        if self.apply_identity(): self.accept(self.key)


class RoleDialog(DraftDialog):
    def __init__(self, parent, store, key, index=None):
        super().__init__(parent, store, 'Role, traits and stats')
        self.geometry('780x780'); self.key, self.index = key, index
        c = store.characters()[key]; role = c.roles[index] if index is not None else None
        self.kind = tk.StringVar(value=role.key.casefold() if role else 'country_leader')
        top = ttk.Frame(self, padding=10); top.pack(fill='x')
        ttk.Label(top, text='Role type').pack(side='left')
        choice = self.kind_box = ChoiceBox(top, textvariable=self.kind, values=[Choice(r, r.replace('_', ' ').title()) for r in ROLES], state='disabled' if role else 'normal'); choice.pack(side='left', padx=10)
        choice.bind('<<ComboboxSelected>>', lambda e: self.build_fields())
        self.form = ttk.Frame(self, padding=10); self.form.pack(fill='x')
        self.random_actions = ttk.Frame(self, padding=(10, 0))
        ttk.Button(self.random_actions, text='Randomize skills from current level', command=self.randomize_skills).pack(side='left')
        self.random_count = tk.StringVar(value='3'); self.random_mode = tk.StringVar(value='Replace vanilla')
        ttk.Label(self.random_actions, text='Vanilla traits:').pack(side='left', padx=(12, 4))
        ttk.Spinbox(self.random_actions, from_=0, to=10, width=3, textvariable=self.random_count).pack(side='left')
        self.random_mode_box = ChoiceBox(self.random_actions, textvariable=self.random_mode, values=['Replace vanilla', 'Add'], width=16)
        self.random_mode_box.pack(side='left', padx=4)
        ttk.Button(self.random_actions, text='Roll traits', command=self.randomize_traits).pack(side='left')
        self.random_status = ttk.Label(self, wraplength=740)
        ttk.Label(self, text='Traits: type a name or ID to add; select a trait to remove').pack(anchor='w', padx=10)
        traits = block(role.children, 'traits') if role else None
        self.traits = tk.StringVar(value=' '.join(n.key for n in traits.children) if traits else '')
        self.trait_choices = TraitChoices(self, self.traits, store.trait_store.choices_for_role(self.kind.get()))
        self.trait_choices.pack(fill='x', padx=10, pady=4)
        self.use_raw = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text='Also edit complete role script below (preserves unsupported/custom fields)', variable=self.use_raw).pack(anchor='w', padx=10, pady=(12, 0))
        self.raw = tk.Text(self, height=9, wrap='none'); self.raw.pack(fill='both', expand=True, padx=10, pady=6)
        if role: self.raw.insert('1.0', value(c.text, role)[1:-1])
        bottom = ttk.Frame(self, padding=10); bottom.pack(fill='x')
        ttk.Button(bottom, text='Cancel', command=self.cancel).pack(side='right')
        ttk.Button(bottom, text='Apply role', command=self.ok).pack(side='right', padx=6)
        self.build_fields()

    def build_fields(self):
        for widget in self.form.winfo_children(): widget.destroy()
        c = self.store.characters()[self.key]; role = c.roles[self.index] if self.index is not None else None
        kind = self.kind.get()
        from trait_model import MILITARY
        self.trait_choices.picker.configure(values=self.store.trait_store.choices_for_role(kind))
        self.trait_choices.refresh()
        if kind in MILITARY:
            self.random_actions.pack(fill='x', after=self.form)
            self.random_status.pack(fill='x', padx=10, pady=4, after=self.random_actions)
            self.random_status.configure(text='Rolls stay in this dialog until Apply. Custom and scripted/status traits are retained.')
        else:
            self.random_actions.pack_forget(); self.random_status.pack_forget()
        fields = ['ideology', 'expire', 'desc'] if kind == 'country_leader' else ['slot', 'idea_token', 'ledger', 'cost'] if kind == 'advisor' else ['desc', 'skills'] if kind == 'scientist' else ['skill', 'attack_skill', 'defense_skill', 'maneuvering_skill', 'coordination_skill'] if kind == 'navy_leader' else ['skill', 'attack_skill', 'defense_skill', 'planning_skill', 'logistics_skill']
        self.variables = {}
        self.form.columnconfigure(1, weight=1)
        for row, field in enumerate(fields):
            node = next((n for n in role.children if n.key == field), None) if role else None
            default = c.description_key if field == 'desc' else '1965.1.1' if field == 'expire' else 'political_advisor' if field == 'slot' else self.key + '_advisor' if field == 'idea_token' else '1' if field.endswith('skill') else ''
            if field == 'idea_token' and node is None:
                occupied = {atom(person.text, r.children, 'idea_token') for person in self.store.characters().values() for r in person.roles}
                suffix = 2
                while default in occupied:
                    default = self.key + '_advisor_' + str(suffix); suffix += 1
            if field == 'cost' and node is None:
                default = '150'
            raw = value(c.text, node) if node else default
            if node and node.children is None: raw = raw.strip('"')
            variable = tk.StringVar(value=raw); self.variables[field] = variable
            ttk.Label(self.form, text=field.replace('_', ' ')).grid(row=row, column=0, sticky='w', pady=3)
            widget = ChoiceBox(self.form, textvariable=variable, values=self.store.choices('ideologies')) if field == 'ideology' else ttk.Entry(self.form, textvariable=variable)
            widget.grid(row=row, column=1, sticky='ew', padx=(12, 0), pady=3)

    def randomize_skills(self):
        try:
            self.kind_box.commit()
            result = self.store.trait_store.random_skills(self.kind.get(), self.variables['skill'].get())
            for field, amount in result.items(): self.variables[field].set(str(amount))
            self.random_status.configure(text='Current level kept. Base skills: ' + ', '.join(f'{k.replace("_skill", "")} {v}' for k, v in result.items()) + '. This base roll excludes trait bonuses.')
        except (ValueError, KeyError) as exc: messagebox.showerror('Skills', str(exc), parent=self)

    def randomize_traits(self):
        try:
            self.kind_box.commit(); self.random_mode_box.commit()
            result = self.store.trait_store.random_traits(self.kind.get(), self.traits.get().split(), int(self.random_count.get()),
                                                        replace=self.random_mode.get() == 'Replace vanilla')
            self.traits.set(' '.join(result))
            self.random_status.configure(text='Rolled generic vanilla traits; custom and restricted/scripted traits kept. Apply to keep this draft.')
        except ValueError as exc: messagebox.showerror('Traits', str(exc), parent=self)

    def ok(self):
        try:
            self.kind_box.commit()
            for widget in self.form.winfo_children():
                if isinstance(widget, ChoiceBox): widget.commit()
            fields = {key: var.get().strip() for key, var in self.variables.items()}
            for key, raw in fields.items():
                if (key.endswith('skill') or key == 'cost') and raw and (not raw.isdigit()):
                    raise ValueError(key + ' must be a nonnegative whole number')
                if raw: parse(key + ' = ' + (quote(raw) if key == 'expire' else raw))
            if self.kind.get() == 'country_leader' and not fields.get('ideology'):
                raise ValueError('Choose a defined sub-ideology for this country leader')
            if fields.get('expire'): fields['expire'] = quote(fields['expire'])
            self.store.edit_role(self.key, self.index, self.kind.get(), fields, self.traits.get().split(),
                                  self.raw.get('1.0', 'end-1c') if self.use_raw.get() else None)
            self.accept()
        except (ValueError, KeyError) as exc:
            messagebox.showerror('Role', str(exc), parent=self)


class PortraitDialog(DraftDialog):
    def __init__(self, parent, store, key=None, initial_tag='GEN', initial_key=''):
        super().__init__(parent, store, 'Edit portrait pair' if key else 'New portrait pair')
        self.geometry('820x660'); self.new = key is None
        record = store.portraits().get(key)
        self.ident = tk.StringVar(value=key or initial_key or 'GFX_portrait_')
        self.tag = tk.StringVar(value=record.tag if record else initial_tag)
        self.art = tk.StringVar(value=record.art_source if record else '')
        self.generate = tk.BooleanVar(value=self.new)
        self.large_file = self.small_file = None
        outer = ttk.Frame(self, padding=12); outer.pack(fill='both', expand=True); outer.columnconfigure(1, weight=1)
        for row, (label, variable) in enumerate([('Portrait ID', self.ident), ('Three-letter tag', self.tag), ('Art source / credit', self.art)]):
            ttk.Label(outer, text=label).grid(row=row, column=0, sticky='w', pady=4)
            if variable is self.tag:
                tags = sorted({p.tag for p in store.portraits().values()} | set(store.world.countries))
                entry = self.tag_box = ChoiceBox(outer, textvariable=variable, values=[Choice(t, store.neutral_name(t)) for t in tags], allow_custom=True)
            else:
                entry = ttk.Entry(outer, textvariable=variable)
            entry.grid(row=row, column=1, sticky='ew', padx=10, pady=4)
            if row == 0 and not self.new: entry.configure(state='disabled')
        images = ttk.Frame(outer); images.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
        self.large_preview = ttk.Label(images); self.large_preview.pack(side='left', padx=20)
        self.small_preview = ttk.Label(images); self.small_preview.pack(side='left', padx=20)
        buttons = ttk.Frame(outer); buttons.grid(row=4, column=0, columnspan=2, sticky='w')
        ttk.Button(buttons, text='Choose large image…', command=lambda: self.choose(True)).pack(side='left')
        ttk.Button(buttons, text='Choose small image…', command=lambda: self.choose(False)).pack(side='left', padx=8)
        ttk.Button(buttons, text='Generate small portrait', command=self.make_small).pack(side='left', padx=8)
        ttk.Checkbutton(outer, text='Use generated small portrait (Ministermaker)', variable=self.generate,
                        command=self.show_images).grid(row=5, column=0, columnspan=2, sticky='w', pady=8)
        ttk.Label(outer, text='Generate small portrait uses Ministermaker’s tilted, bordered 65 × 67 output. The preview becomes a draft on Apply; Save writes it with backups. Replacing an animated texture with a regular image makes that portrait static.', wraplength=760).grid(row=6, column=0, columnspan=2, sticky='w')
        ttk.Label(outer, text='Portrait notes / description').grid(row=7, column=0, sticky='nw', pady=8)
        self.description = tk.Text(outer, height=4, wrap='word'); self.description.grid(row=7, column=1, sticky='nsew', padx=10, pady=8)
        self.description.insert('1.0', record.description if record else ''); outer.rowconfigure(7, weight=1)
        bottom = ttk.Frame(outer); bottom.grid(row=8, column=0, columnspan=2, sticky='ew')
        ttk.Button(bottom, text='Cancel', command=self.cancel).pack(side='right')
        ttk.Button(bottom, text='Apply portrait pair', command=self.ok).pack(side='right', padx=6)
        self.show_images()

    def current_large(self):
        record = self.store.portraits().get(self.ident.get())
        if self.large_file:
            with Image.open(self.large_file) as image:
                fitted = ImageOps.contain(image.convert('RGBA'), LARGE_SIZE, Image.Resampling.LANCZOS)
                canvas = Image.new('RGBA', LARGE_SIZE)
                canvas.alpha_composite(fitted, ((LARGE_SIZE[0] - fitted.width) // 2, (LARGE_SIZE[1] - fitted.height) // 2))
                return canvas
        return self.store.image(record.large) if record else None

    def make_small(self):
        try:
            if self.current_large() is None:
                raise ValueError('Choose a valid large portrait first')
            self.small_file = None
            self.generate.set(True)
            self.show_images()
        except (OSError, ValueError) as exc:
            messagebox.showerror('Small portrait', str(exc), parent=self)

    def show_images(self):
        record = self.store.portraits().get(self.ident.get())
        self.photos = []
        try:
            large_image = self.current_large()
        except (OSError, ValueError):
            large_image = None
        for large, label, source, size in [(True, self.large_preview, self.large_file, LARGE_SIZE), (False, self.small_preview, self.small_file, SMALL_SIZE)]:
            try:
                if large:
                    image = ImageOps.contain(large_image, size, Image.Resampling.LANCZOS) if large_image else None
                elif self.generate.get() and large_image is not None:
                    image = generate_small_portrait(large_image)
                elif source:
                    with Image.open(source) as opened:
                        image = opened.convert('RGBA'); image.thumbnail(size)
                else:
                    image = self.store.image(record.large if large else record.small, size) if record else None
                if image:
                    photo = ImageTk.PhotoImage(image); self.photos.append(photo); label.configure(image=photo, text='')
                else: label.configure(image='', text='No large image' if large else 'No small image')
            except (OSError, ValueError) as exc:
                label.configure(image='', text=str(exc))

    def choose(self, large):
        selected = filedialog.askopenfilename(parent=self, title='Choose portrait image', filetypes=[('Images', '*.tga *.dds *.png *.jpg *.jpeg *.webp *.bmp'), ('All files', '*.*')])
        if not selected: return
        try:
            with Image.open(selected) as image: image.verify()
            if large: self.large_file = selected
            else: self.small_file = selected; self.generate.set(False)
            self.show_images()
        except OSError as exc: messagebox.showerror('Portrait', str(exc), parent=self)

    def ok(self):
        try:
            self.tag_box.commit()
            key = self.ident.get().strip()
            self.store.edit_portrait(key, self.tag.get().strip(), self.art.get(), self.description.get('1.0', 'end-1c'),
                                     self.large_file, self.small_file, create=self.new, generate_small=self.generate.get())
            self.accept(key)
        except (ValueError, OSError, KeyError) as exc:
            messagebox.showerror('Portrait', str(exc), parent=self)

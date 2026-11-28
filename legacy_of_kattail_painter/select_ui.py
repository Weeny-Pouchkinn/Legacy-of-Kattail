"""Searchable, localized choices. Display labels never become script IDs."""
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
import re
import tkinter as tk
from tkinter import ttk
import unicodedata


def normalized(text):
    return _normalized(str(text))


@lru_cache(maxsize=32768)
def _normalized(text):
    text = re.sub('[\x15§].', '', str(text))
    return ''.join(c for c in unicodedata.normalize('NFKD', text).casefold()
                   if not unicodedata.combining(c))


@dataclass(frozen=True)
class Choice:
    code: str
    name: str

    @property
    def label(self):
        name = re.sub('[\x15§].', '', self.name).replace('\n', ' ')
        return f'{name} ({self.code})' if name and self.code and name != self.code else name or self.code


class ChoiceIndex:
    def __init__(self, values=()):
        self.source = tuple(values)
        self.choices = tuple(sorted((v if isinstance(v, Choice) else Choice(str(v), str(v)) for v in self.source),
                                    key=lambda c: (normalized(c.name), normalized(c.code))))
        self.by_code = {c.code: c for c in self.choices}
        self.exact = {normalized(c.label): c.code for c in self.choices}
        self.exact.update({normalized(c.code): c.code for c in self.choices})
        by_name = {}
        for c in self.choices: by_name.setdefault(normalized(c.name), []).append(c.code)
        for name, codes in by_name.items():
            if len(codes) == 1: self.exact.setdefault(name, codes[0])
        self.search = [(c, normalized(c.name), normalized(c.code)) for c in self.choices]

    def resolve(self, text):
        if text in self.by_code:
            return text
        return self.exact.get(normalized(text))

    def preferred(self, text, matches):
        exact = self.resolve(text)
        if exact is not None: return exact
        if not matches: return None
        query = normalized(text)
        return max(matches, key=lambda c: max(SequenceMatcher(None, query, normalized(c.name)).ratio(),
                                              SequenceMatcher(None, query, normalized(c.code)).ratio())).code

    def matching(self, text='', limit=None):
        query = normalized(text).strip()
        if not query:
            return list(self.choices[:limit] if limit else self.choices)
        words = query.split()
        direct = [c for c, name, code in self.search if all(w in name + ' ' + code for w in words)]
        if not direct:
            # Narrow before fuzzy matching; every comparison still checks both names.
            candidates = [(c, name, code) for c, name, code in self.search
                          if query[0] in name or query[0] in code]
            def score(text):
                match=SequenceMatcher(None,query,text)
                # These are upper bounds: pruning cannot change any result
                # accepted by the existing 0.45 similarity threshold.
                if match.real_quick_ratio()<.45 or match.quick_ratio()<.45:return 0
                return match.ratio()
            scored = [(max(score(name),score(code)),c) for c,name,code in candidates]
            direct = [c for score, c in sorted(scored, key=lambda row: -row[0]) if score >= .45][:12]
            direct.sort(key=lambda c: (normalized(c.name), normalized(c.code)))
        return direct[:limit] if limit else direct


class ChoiceBox(ttk.Frame):
    """Keeps typing focus in the entry while a bounded suggestion popup is open."""
    def __init__(self, master, values=(), textvariable=None, state='normal', width=24, allow_custom=False, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = textvariable if textvariable is not None else tk.StringVar(self)
        self.display = tk.StringVar(self)
        self.index = ChoiceIndex(values)
        self.allow_custom = allow_custom
        self.popup = self.listbox = None
        self._job = None
        self._matches = []
        self.entry = ttk.Entry(self, textvariable=self.display, width=width)
        self.entry.pack(side='left', fill='x', expand=True)
        self.arrow = ttk.Button(self, text='▾', width=2, command=self.toggle)
        self.arrow.pack(side='right')
        self.entry.bind('<KeyRelease>', self.typed)
        self.entry.bind('<Down>', self.down)
        self.entry.bind('<Up>', self.up)
        self.entry.bind('<Return>', self.enter)
        self.entry.bind('<Escape>', self.escape)
        self.entry.bind('<FocusOut>', self.focus_out)
        self.entry.bind('<FocusIn>', lambda event: self.after_idle(self.select_all))
        self.entry.bind('<Tab>', self.tab)
        self._trace = self.variable.trace_add('write', self.sync)
        self.bind('<Destroy>', self.destroyed, add='+')
        self._disabled = state == 'disabled'
        self.configure(state=state)
        self.sync()

    def sync(self, *args):
        code = self.variable.get()
        choice = self.index.by_code.get(code)
        self.display.set(choice.label if choice else code)

    def get(self):
        return self.variable.get()

    def set(self, code):
        self.variable.set(code)

    def configure(self, cnf=None, **kwargs):
        if cnf: kwargs.update(cnf)
        if 'values' in kwargs:
            values = tuple(kwargs.pop('values'))
            if values != self.index.source:
                self.index = ChoiceIndex(values); self.sync()
        if 'width' in kwargs: self.entry.configure(width=kwargs.pop('width'))
        if 'state' in kwargs:
            self._disabled = kwargs.pop('state') == 'disabled'
            for widget in (self.entry, self.arrow): widget.configure(state='disabled' if self._disabled else 'normal')
        if kwargs: return super().configure(**kwargs)

    config = configure

    def cget(self, key):
        if key == 'values': return tuple(c.label for c in self.index.choices)
        if key == 'state': return 'disabled' if self._disabled else 'normal'
        return super().cget(key)

    def focus_set(self):
        self.entry.focus_set()

    def select_all(self):
        if self.winfo_exists() and self.focus_get() == self.entry:
            self.entry.selection_range(0, 'end'); self.entry.icursor('end')

    def typed(self, event=None):
        if event and event.keysym in {'Up', 'Down', 'Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R'}: return
        if self._job: self.after_cancel(self._job)
        self._job = self.after(70, lambda: self.show(self.display.get()))

    def show(self, query=''):
        self._job = None
        if self._disabled: return
        self._matches = self.index.matching(query)
        if not self._matches:
            self.hide(); return
        if not self.popup:
            self.popup = tk.Toplevel(self)
            self.popup.withdraw(); self.popup.overrideredirect(True)
            self.popup.attributes('-alpha', self.winfo_toplevel().attributes('-alpha'))
            self.popup.transient(self.winfo_toplevel())
            body = ttk.Frame(self.popup, relief='solid', borderwidth=1); body.pack(fill='both', expand=True)
            self.listbox = tk.Listbox(body, exportselection=False, activestyle='dotbox')
            scrollbar = ttk.Scrollbar(body, command=self.listbox.yview)
            self.listbox.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side='right', fill='y'); self.listbox.pack(fill='both', expand=True)
            self.listbox.bind('<ButtonRelease-1>', self.choose)
            self.listbox.bind('<Return>', self.choose)
            self.listbox.bind('<Escape>', self.escape)
            self.popup.bind('<FocusOut>', self.focus_out)
        self.listbox.delete(0, 'end')
        self.listbox.insert('end', *(choice.label for choice in self._matches))
        self.listbox.configure(height=min(9, len(self._matches)))
        preferred = self.index.preferred(query, self._matches) if query else self.variable.get()
        selected = next((i for i, choice in enumerate(self._matches) if choice.code == preferred), 0)
        self.listbox.selection_set(selected); self.listbox.activate(selected); self.listbox.see(selected)
        self.popup.update_idletasks()
        width = max(self.winfo_width(), min(650, max(len(c.label) for c in self._matches) * 8 + 30))
        height = self.popup.winfo_reqheight()
        x = min(self.winfo_rootx(), self.winfo_screenwidth() - width)
        y = self.winfo_rooty() + self.winfo_height()
        if y + height > self.winfo_screenheight(): y = self.winfo_rooty() - height
        self.popup.geometry(f'{width}x{height}+{max(0, x)}+{max(0, y)}')
        self.popup.deiconify(); self.popup.lift()

    def toggle(self):
        if self.popup and self.popup.winfo_viewable(): self.hide()
        else: self.entry.focus_set(); self.show('')

    def hide(self):
        if self._job: self.after_cancel(self._job); self._job = None
        if self.popup and self.popup.winfo_exists(): self.popup.withdraw()

    def choose(self, event=None):
        selected = self.listbox.curselection() if self.listbox else ()
        if selected and self._matches:
            self.variable.set(self._matches[selected[0]].code)
            self.hide(); self.entry.focus_set()
            self.select_all()
            self.event_generate('<<ComboboxSelected>>')
        return 'break'

    def down(self, event=None):
        if not self.popup or not self.popup.winfo_viewable():
            text = self.display.get()
            self.show('' if self.index.resolve(text) == self.variable.get() else text)
        else: self.move(1)
        return 'break'

    def up(self, event=None):
        if not self.popup or not self.popup.winfo_viewable(): self.show('')
        else: self.move(-1)
        return 'break'

    def move(self, offset):
        if self.listbox and self._matches:
            selected = self.listbox.curselection()
            index = max(0, min(len(self._matches) - 1, (selected[0] if selected else 0) + offset))
            self.listbox.selection_clear(0, 'end'); self.listbox.selection_set(index)
            self.listbox.activate(index); self.listbox.see(index)

    def enter(self, event=None):
        if self._job: self.after_cancel(self._job); self._job = None; self.show(self.display.get())
        if self.popup and self.popup.winfo_viewable(): return self.choose()
        code = self.index.resolve(self.display.get())
        if code is not None:
            self.variable.set(code); self.event_generate('<<ComboboxSelected>>')
        elif self.allow_custom: self.commit()
        else: self.show(self.display.get())
        return 'break'

    def tab(self, event=None):
        self.commit()

    def commit(self):
        code = self.index.resolve(self.display.get())
        if code is None and self.allow_custom: code = self.display.get().strip()
        if code is not None:
            changed = code != self.variable.get()
            self.variable.set(code)
            if changed: self.event_generate('<<ComboboxSelected>>')
        else: self.sync()
        self.hide()
        return self.variable.get()

    def escape(self, event=None):
        if self.popup and self.popup.winfo_viewable():
            self.hide(); self.sync(); return 'break'

    def focus_out(self, event=None):
        self.after_idle(self.check_focus)

    def check_focus(self):
        if not self.winfo_exists(): return
        focus = self.focus_get()
        if focus is not None and (focus == self.entry or (self.popup and str(focus).startswith(str(self.popup)))): return
        self.tab()

    def destroyed(self, event):
        if event.widget is self:
            self.hide(); self.variable.trace_remove('write', self._trace)


class TextColorChoiceBox(ChoiceBox):
    def __init__(self,master,colors,**kwargs):
        self.colors=colors
        super().__init__(master,values=[Choice('','None')]+[Choice(k,d['name']) for k,d in colors.items()],allow_custom=True,**kwargs)

    def show(self,query=''):
        super().show(query)
        if self.listbox:
            for i,c in enumerate(self._matches):
                rgb=self.colors.get(c.code,{}).get('color')
                if rgb:
                    color='#%02x%02x%02x'%rgb;contrast='#000000' if sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))>145 else '#ffffff'
                    self.listbox.itemconfigure(i,background=color,foreground=contrast,selectbackground=color,selectforeground=contrast)


class TextColorPicker(ttk.Frame):
    """Search native codes by name/ID, with live swatch and actual-name preview."""
    def __init__(self,master,colors,textvariable,samplevariable):
        super().__init__(master)
        self.colors,self.variable,self.samplevariable=colors,textvariable,samplevariable
        self.box=TextColorChoiceBox(self,colors,textvariable=textvariable);self.box.pack(fill='x')
        line=ttk.Frame(self);line.pack(fill='x',pady=(4,0))
        self.swatch=tk.Label(line,width=3,relief='solid',borderwidth=1);self.swatch.pack(side='left',padx=(0,6))
        self.preview=tk.Label(line,anchor='w',padx=6,font=('Segoe UI',11,'bold'));self.preview.pack(side='left',fill='x',expand=True)
        self._traces=[(var,var.trace_add('write',self.refresh)) for var in (textvariable,samplevariable,self.box.display)]
        self.bind('<Destroy>',self.destroyed,add='+');self.refresh()

    def commit(self):return self.box.commit()

    def refresh(self,*args):
        code=self.box.index.resolve(self.box.display.get())
        rgb=self.colors.get(code,{}).get('color');color='#%02x%02x%02x'%rgb if rgb else '#d0d0d0'
        self.swatch.configure(background=color)
        background='#f4f4f4' if rgb and sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))<100 else '#20242c'
        sample=self.samplevariable.get() or 'Text preview'
        self.preview.configure(text=sample if rgb else sample+' (default)' if code=='' else 'Unknown color code',foreground=color,background=background)

    def destroyed(self,event):
        if event.widget is self:
            for var,trace in self._traces:var.trace_remove('write',trace)


class TraitChoices(ttk.Frame):
    """Localized multi-selection, retaining only IDs in the role's variable."""
    def __init__(self, master, variable, values):
        super().__init__(master)
        self.variable = variable
        self.picker = ChoiceBox(self, values=values)
        self.picker.pack(fill='x'); self.picker.bind('<<ComboboxSelected>>', self.add)
        self.listbox = tk.Listbox(self, height=4, exportselection=False)
        self.listbox.pack(fill='x', pady=4)
        self.listbox.bind('<Delete>', self.remove)
        self.listbox.bind('<KeyPress>', self.type_in_list)
        ttk.Button(self, text='Remove selected trait', command=self.remove).pack(anchor='w')
        self._trace = variable.trace_add('write', self.refresh)
        self.bind('<Destroy>', self.destroyed, add='+'); self.refresh()

    def refresh(self, *args):
        self.selected = sorted(self.variable.get().split(), key=lambda code: normalized(self.picker.index.by_code.get(code, Choice(code, code)).name))
        self.listbox.delete(0, 'end')
        for code in self.selected: self.listbox.insert('end', self.picker.index.by_code.get(code, Choice(code, code)).label)

    def add(self, event=None):
        code = self.picker.get(); values = self.variable.get().split()
        if code and code not in values: self.variable.set(' '.join(values + [code]))
        self.picker.set('')

    def remove(self, event=None):
        remove = {self.selected[i] for i in self.listbox.curselection()}
        self.variable.set(' '.join(c for c in self.variable.get().split() if c not in remove))
        return 'break'

    def type_in_list(self, event):
        if event.char and event.char.isprintable():
            self.picker.focus_set(); self.picker.display.set(event.char); self.picker.typed(); return 'break'

    def destroyed(self, event):
        if event.widget is self: self.variable.trace_remove('write', self._trace)

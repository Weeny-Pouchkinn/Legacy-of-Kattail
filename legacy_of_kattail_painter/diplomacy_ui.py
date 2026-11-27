"""Diplomacy declarations and directed country relationships in country setup."""
import tkinter as tk
from tkinter import ttk,messagebox

from character_ui import DraftDialog
from diplomacy_model import DiplomacyStore,Relation,KINDS
from select_ui import Choice,ChoiceBox,ChoiceIndex


class DiplomacyPanel(ttk.Frame):
    def __init__(self,parent,country):
        super().__init__(parent);self.pack(fill='both',expand=True)
        self.country=country;self.app=country.app
        self.store=getattr(self.app,'diplomacy_store',None) or DiplomacyStore(self.app.world,country.store)
        self.show_all=tk.BooleanVar(value=False);self.query=tk.StringVar();self.summary=tk.StringVar()
        bar=ttk.Frame(self);bar.pack(fill='x',pady=5)
        for label,callback in [('Add relation',self.add),('Edit selected',self.edit),('Remove selected',self.remove),('Refresh',self.refresh)]:ttk.Button(bar,text=label,command=callback).pack(side='left',padx=(0,7))
        ttk.Checkbutton(bar,text='Show all countries',variable=self.show_all,command=self.refresh).pack(side='left',padx=8)
        ttk.Label(self,textvariable=self.summary).pack(anchor='w',pady=5)
        search=ttk.Entry(self,textvariable=self.query);search.pack(fill='x',pady=5);search.bind('<KeyRelease>',lambda e:self.refresh())
        body=ttk.Frame(self);body.pack(fill='both',expand=True)
        columns=('actor','target','detail','context','source')
        self.rows=ttk.Treeview(body,columns=columns,show='tree headings',selectmode='browse',height=15)
        self.rows.heading('#0',text='Relation');self.rows.column('#0',width=165)
        for key,label,width in [('actor','Source country',180),('target','Target country',180),('detail','Name / level / goal',190),('context','Conditions / date',210),('source','Source file',270)]:self.rows.heading(key,text=label);self.rows.column(key,width=width)
        vertical=ttk.Scrollbar(body,orient='vertical',command=self.rows.yview);vertical.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(body,orient='horizontal',command=self.rows.xview);horizontal.pack(side='bottom',fill='x')
        self.rows.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set);self.rows.pack(fill='both',expand=True)
        self.rows.bind('<Double-1>',lambda e:self.edit());self.rows.bind('<Return>',lambda e:self.edit())
        ttk.Label(self,text='Source leads the faction, is the overlord/aggressor, or grants the listed access/guarantee. Incoming and outgoing relations are both shown. Conditional, dated and shared declarations show their source; the list does not simulate engine events.',wraplength=1030).pack(anchor='w',pady=8)
        self.values={}

    def choices(self):
        chars=self.store.characters;loc=chars.localisations()
        return ChoiceIndex(Choice(tag,chars.neutral_name(tag,loc)) for tag in self.app.world.country_paths).choices

    def refresh(self):
        tag=self.country.tag.get().strip();records=self.store.records();factions=self.store.faction_map(records)
        names={c.code:c.label for c in self.choices()};loc=self.store.characters.localisations()
        self.rows.delete(*self.rows.get_children());self.values={};query=self.query.get().casefold()
        for r in records:
            if not self.show_all.get() and tag not in (r.actor,r.target) and not (r.kind=='faction' and tag in factions.get(r.actor,set())):continue
            detail=loc.get(r.detail,r.detail);context='; '.join(r.context) or 'Base setup'
            if r.group:context='Group declaration; '+context
            if not r.active:context='Cancellation; '+context
            if not r.editable:context='Source edit required; '+context
            target=names.get(r.target,r.target+(' (unregistered)' if r.target and r.target not in self.app.world.country_paths else ''))
            values=(names.get(r.actor,r.actor),target,detail,context,f'{r.path}:{r.line}')
            if query and query not in (' '.join((r.description,*values))).casefold():continue
            iid=self.rows.insert('','end',text=r.description,values=values);self.values[iid]=r
        self.summary.set(f'{len(self.values)} diplomatic declarations'+(' for all countries' if self.show_all.get() else f' involving {names.get(tag,tag or "this draft country")}'))

    def selected(self):return self.values.get(next(iter(self.rows.selection()),''))

    def add(self):
        if not self.country.ensure_country():return
        self.open()

    def edit(self):
        if relation:=self.selected():self.open(relation)

    def open(self,relation=None):
        try:
            dialog=RelationDialog(self,self.store,self.country.tag.get().strip(),self.choices(),relation)
            self.wait_window(dialog);self.country.grab_set();self.refresh()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Diplomacy',str(exc),parent=self)

    def remove(self):
        if not (relation:=self.selected()):return
        try:self.store.change(relation);self.refresh()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Diplomacy',str(exc),parent=self)


class RelationDialog(DraftDialog):
    def __init__(self,parent,store,tag,choices,relation=None):
        super().__init__(parent,store.characters,'Edit diplomacy' if relation else 'Add diplomacy')
        self.diplomacy=store;self.original=relation;self.geometry('790x610');self.minsize(680,530)
        current=relation or Relation('war',tag,detail='annex_everything')
        self.kind=tk.StringVar(value=current.kind);self.actor=tk.StringVar(value=current.actor);self.target=tk.StringVar(value=current.target)
        self.detail=tk.StringVar(value=current.detail);self.freedom=tk.StringVar(value=current.freedom);self.active=tk.BooleanVar(value=current.active)
        form=ttk.Frame(self,padding=12);form.pack(fill='x');form.columnconfigure(1,weight=1)
        self.boxes=[]
        for row,(label,var,options) in enumerate([('Relation',self.kind,[Choice(k,v) for k,v in KINDS.items()]),('Source country',self.actor,choices),('Target country',self.target,choices)]):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=6)
            box=ChoiceBox(form,textvariable=var,values=options);box.grid(row=row,column=1,sticky='ew',padx=8);self.boxes.append(box)
        if relation:
            self.boxes[0].configure(state='disabled');self.boxes[1].configure(state='disabled')
        self.detail_label=ttk.Label(form);self.detail_label.grid(row=3,column=0,sticky='w',pady=6)
        self.detail_box=ChoiceBox(form,textvariable=self.detail,values=[]);self.detail_box.grid(row=3,column=1,sticky='ew',padx=8)
        self.name_entry=ttk.Entry(form,textvariable=self.detail);self.name_entry.grid(row=3,column=1,sticky='ew',padx=8)
        self.freedom_label=ttk.Label(form,text='Freedom level (optional, 0–1)');self.freedom_label.grid(row=4,column=0,sticky='w',pady=6)
        self.freedom_entry=ttk.Entry(form,textvariable=self.freedom);self.freedom_entry.grid(row=4,column=1,sticky='ew',padx=8)
        self.active_check=ttk.Checkbutton(form,text='Active relation (off writes a cancellation)',variable=self.active);self.active_check.grid(row=5,column=1,sticky='w',padx=8)
        self.direction=tk.StringVar();ttk.Label(form,textvariable=self.direction,wraplength=720).grid(row=6,column=0,columnspan=2,sticky='w',pady=12)
        self.boxes[0].bind('<<ComboboxSelected>>',lambda e:self.configure_kind(True));self.configure_kind()
        if relation:
            context='\n'.join(relation.context) or 'Base setup'
            message=f'{relation.path}:{relation.line}\n{context}\n\n{relation.raw}'
            if relation.group:message+='\n\nOnly this country\'s instance will change; the other group members keep the original declaration.'
        else:message='New declarations use native country history. Subject setup is placed before the subject\'s politics; it preserves existing wars and subordinate subjects. Creating a faction precedes its memberships.'
        preview=tk.Text(self,height=10,wrap='word');preview.pack(fill='both',expand=True,padx=12,pady=8);preview.insert('1.0',message);preview.configure(state='disabled')
        bar=ttk.Frame(self,padding=12);bar.pack(fill='x');ttk.Button(bar,text='Cancel',command=self.cancel).pack(side='right');ttk.Button(bar,text='Apply relation',command=self.ok,state='normal' if not relation or relation.editable else 'disabled').pack(side='right',padx=8)

    def configure_kind(self,reset=False):
        kind=self.kind.get();loc=self.store.trait_store.names()
        self.name_entry.grid_remove();self.detail_box.grid_remove();self.detail_label.grid_remove()
        if kind=='faction':self.detail_label.configure(text='Faction name or localisation key');self.detail_label.grid();self.name_entry.grid()
        elif kind in {'subject','war'}:
            options=self.diplomacy.autonomies() if kind=='subject' else self.diplomacy.wargoals()
            self.detail_box.configure(values=[Choice(k,loc.get(k,k)) for k in sorted(options)]);self.detail_box.grid();self.detail_label.grid()
            self.detail_label.configure(text='Autonomy level' if kind=='subject' else 'War goal')
            if reset:self.detail.set('autonomy_puppet' if kind=='subject' else 'annex_everything')
        elif reset:self.detail.set('')
        for widget in (self.freedom_label,self.freedom_entry):widget.grid() if kind=='subject' else widget.grid_remove()
        self.boxes[2].configure(state='disabled' if kind=='faction' else 'normal')
        if kind in {'military_access','non_aggression_pact'}:self.active_check.grid()
        else:self.active_check.grid_remove()
        self.direction.set({'faction':'Source country becomes the faction leader. Enter your faction name.',
                            'member':'Source is a country already in the faction; target joins that faction.',
                            'subject':'Source is the overlord; target becomes its subject at the selected autonomy level.',
                            'war':'Source is the attacker; target is the defender.',
                            'guarantee':'Source guarantees the target country.',
                            'military_access':'Source grants target permission to move troops through its territory.',
                            'market_access':'Source and target gain mutual equipment-market access.',
                            'non_aggression_pact':'Source and target enter a mutual non-aggression pact.'}.get(kind,''))

    def ok(self):
        try:
            for box in self.boxes:box.commit()
            if self.kind.get() in {'subject','war'}:self.detail_box.commit()
            new=Relation(self.kind.get(),self.actor.get(),'' if self.kind.get()=='faction' else self.target.get(),self.detail.get().strip(),self.freedom.get().strip() if self.kind.get()=='subject' else '',self.active.get())
            if self.original:self.diplomacy.change(self.original,new)
            else:self.diplomacy.add(new)
            self.accept(True)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Diplomacy',str(exc),parent=self)

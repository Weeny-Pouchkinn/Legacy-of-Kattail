"""State, strategic-region/weather and victory-point forms over native drafts."""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk, messagebox

from character_ui import DraftDialog
from character_model import inherited_localisations, atom
from country_ui import table, buttons, choose_color
from select_ui import Choice, ChoiceBox, ChoiceIndex
from geography_model import CLIMATES, WEATHER_FIELDS, WeatherPeriod, climate_preset, numeric
from imperium_model import CATALOG as IMPERIUM_CATALOG, LAYER as IMPERIUM_LAYER
from imperium_ui import ImperiumElementDialog


def type_search(event,entry,variable,refresh):
    if event.char and event.char.isprintable():variable.set(event.char);entry.focus_set();entry.icursor('end');refresh();return 'break'


class ValueEditor(ttk.Frame):
    def __init__(self,parent,values,choices,label='Value',integer=False):
        super().__init__(parent);self.pack(fill='both',expand=True);self.values=dict(values);self.choices=choices;self.integer=integer
        self.rows=table(self,[('amount',label,140)]);self.key=tk.StringVar();self.amount=tk.StringVar(value='1')
        line=ttk.Frame(self);line.pack(fill='x',pady=8)
        self.box=ChoiceBox(line,textvariable=self.key,values=choices);self.box.pack(side='left',fill='x',expand=True)
        ttk.Entry(line,textvariable=self.amount,width=14).pack(side='left',padx=6)
        ttk.Button(line,text='Add / update',command=self.add).pack(side='left');ttk.Button(line,text='Remove selected',command=self.remove).pack(side='left',padx=6)
        self.rows.bind('<<TreeviewSelect>>',self.pick)
        self.rows.bind('<KeyPress>',lambda e:type_search(e,self.box.entry,self.box.display,lambda:self.box.show(self.box.display.get())))
        self.refresh()

    def refresh(self):
        self.rows.delete(*self.rows.get_children());names={c.code:c.name for c in self.choices}
        for c in ChoiceIndex(Choice(k,names.get(k,k)) for k in self.values).choices:self.rows.insert('','end',iid=c.code,text=c.label,values=(self.values[c.code],))

    def add(self):
        try:
            self.box.commit();key=self.key.get()
            if key not in self.box.index.by_code:raise ValueError('Choose a defined entry')
            self.values[key]=numeric(self.amount.get(),0,self.integer);self.refresh()
        except ValueError as exc:messagebox.showerror('Value',str(exc),parent=self)

    def remove(self):
        for key in self.rows.selection():self.values.pop(key,None)
        self.refresh()

    def pick(self,event=None):
        if rows:=self.rows.selection():self.key.set(rows[0]);self.amount.set(self.values[rows[0]])


class TagSetEditor(ttk.Frame):
    def __init__(self,parent,values,choices):
        super().__init__(parent);self.pack(fill='both',expand=True);self.values=set(values);self.choices=choices
        self.rows=table(self,height=5);self.key=tk.StringVar();self.box=ChoiceBox(self,textvariable=self.key,values=choices);self.box.pack(fill='x',pady=5)
        buttons(self,[('Add',self.add),('Remove selected',self.remove)]);self.refresh()

    def refresh(self):
        self.rows.delete(*self.rows.get_children());names={c.code:c.name for c in self.choices}
        for c in ChoiceIndex(Choice(k,names.get(k,k)) for k in self.values).choices:self.rows.insert('','end',iid=c.code,text=c.label)

    def add(self):
        self.box.commit()
        if self.key.get() in self.box.index.by_code:self.values.add(self.key.get());self.refresh()

    def remove(self):
        self.values.difference_update(self.rows.selection());self.refresh()


class GeographyWorkspace(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,padding=8);self.pack(fill='both',expand=True);self.app=app;self.store=app.geography_store
        self.kind=tk.StringVar(value='States');self.query=tk.StringVar();self._signature=None
        bar=buttons(self,[('Edit selected',self.edit),('New category',lambda:self.open_category(None)),('New Imperium element',lambda:self.open_imperium_element(None)),('New VP on map',self.new_vp),('Save',app.save),('Undo',app.undo),('Redo',app.redo)])
        box=ChoiceBox(bar,textvariable=self.kind,values=['States','State categories','Strategic regions','VPs',IMPERIUM_CATALOG],width=23);box.pack(side='left',padx=8);box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        self.search=ttk.Entry(bar,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True);self.search.bind('<KeyRelease>',lambda e:self.refresh())
        self.rows=table(self,[('detail','Details',470)]);self.rows.bind('<Double-1>',lambda e:self.edit());self.rows.bind('<Return>',lambda e:self.edit())
        self.rows.bind('<KeyPress>',lambda e:type_search(e,self.search,self.query,self.refresh))
        ttk.Label(self,text='State shapes are fixed. Region membership transfers whole states; native sources are written only by Save.').pack(anchor='w',pady=8)
        self.bind('<Map>',lambda e:self.after_idle(self.refresh))

    def refresh(self):
        if not self.winfo_viewable():return
        signature=(self.app.world.docs.revision,self.kind.get(),self.query.get())
        if signature==self._signature:return
        self._signature=signature;kind=self.kind.get();selected=next(iter(self.rows.selection()),'');self.rows.delete(*self.rows.get_children());self.entries={}
        if kind=='States':
            choices=[Choice(str(sid),self.app.world.label(s.name)) for sid,s in self.app.world.states.items()]
            details={str(sid):'Regions: '+', '.join(map(str,sorted({self.app.world.province_regions.get(p) for p in s.provinces}))) for sid,s in self.app.world.states.items()}
        elif kind=='Strategic regions':
            choices=[Choice(str(rid),self.app.world.label(r['name'])) for rid,r in self.app.world.regions.items()]
            details={str(rid):f'{len(self.app.world.region_states[rid])} states / {len(r["provinces"])} provinces' for rid,r in self.app.world.regions.items()}
        elif kind==IMPERIUM_CATALOG:
            records=self.app.imperium_store.elements();counts={}
            for ident in self.app.imperium_store.state_assignments().values():counts[ident]=counts.get(ident,0)+1
            choices=[Choice(str(key),d.name) for key,d in records.items()];details={str(key):f'{counts.get(key,0)} states / #%02x%02x%02x'%d.color for key,d in records.items()}
        elif kind=='State categories':
            records=self.store.categories();choices=[Choice(k,d['name']) for k,d in records.items()];details={k:f'{d["slots"]} base slots / {d["path"]}' for k,d in records.items()}
        else:
            records=self.store.victory_points();choices=[Choice(str(pid),d['name']) for pid,d in records.items()];details={str(pid):f'{d["value"]} VP — state {d["state"]}' for pid,d in records.items()}
        for c in ChoiceIndex(choices).matching(self.query.get()):self.rows.insert('','end',iid=c.code,text=c.label,values=(details[c.code],));self.entries[c.code]=c.code
        if selected and self.rows.exists(selected):self.rows.selection_set(selected)

    def edit(self):
        if rows:=self.rows.selection():
            key=rows[0] if self.kind.get()=='State categories' else int(rows[0]);{'States':self.open_state,'State categories':self.open_category,'Strategic regions':self.open_region,'VPs':self.open_vp,IMPERIUM_CATALOG:self.open_imperium_element}[self.kind.get()](key)

    def open(self,dialog_type,key):
        try:
            dialog=dialog_type(self,self.app,key);self.wait_window(dialog)
            if dialog_type is ImperiumElementDialog and dialog.result is not None:self.app.paint_selection[IMPERIUM_LAYER]=dialog.result
            self.app._sync();self.refresh()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Geography editor',str(exc),parent=self)

    def open_state(self,sid):
        if sid is not None:self.open(StateDialog,sid)
    def open_region(self,rid):
        if rid is not None:self.open(RegionDialog,rid)
    def open_vp(self,pid):
        if pid is not None:self.open(VictoryPointDialog,pid)

    def open_category(self,key=None):self.open(CategoryDialog,key)

    def open_imperium_element(self,key=None):self.open(ImperiumElementDialog,key)

    def new_vp(self):self.app.begin_geography_pick(None,lambda pid:self.open_vp(pid),'province')


class CategoryDialog(DraftDialog):
    def __init__(self,parent,app,key=None):
        data=app.geography_store.categories().get(key)
        super().__init__(parent,app.character_store,'Edit state category' if data else 'New state category')
        self.app,self.geo,self.new=app,app.geography_store,data is None;self.geometry('820x640');self.minsize(700,540)
        files=self.geo.characters.files('common/state_category','.txt')
        self.ident=tk.StringVar(value=key or '');self.name=tk.StringVar(value=data['name'] if data else '');self.slots=tk.StringVar(value=str(data['slots']) if data else '4')
        self.color=tk.StringVar(value='#%02x%02x%02x'%(data['color'] if data else (128,128,128)));self.path=tk.StringVar(value=data['path'] if data else files[0])
        form=ttk.Frame(self,padding=12);form.pack(fill='x');form.columnconfigure(1,weight=1)
        for row,(label,var) in enumerate([('Category ID',self.ident),('Localized name',self.name),('Base shared building slots',self.slots),('Map color',self.color),('Native source file',self.path)]):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=6)
            if var is self.path:
                self.path_box=ChoiceBox(form,textvariable=var,values=files,state='normal' if self.new else 'disabled');widget=self.path_box
            else:widget=ttk.Entry(form,textvariable=var,state='disabled' if var is self.ident and not self.new else 'normal')
            widget.grid(row=row,column=1,sticky='ew',padx=8)
            if var is self.color:ttk.Button(form,text='Choose',command=lambda:choose_color(self,self.color)).grid(row=row,column=2)
        ttk.Label(self,text='Additional native fields (modifiers, buildings_max_level, comments). Color and slots use the fields above.',wraplength=760).pack(anchor='w',padx=12,pady=6)
        self.extra=tk.Text(self,height=12,wrap='none');self.extra.pack(fill='both',expand=True,padx=12);self.extra.insert('1.0',data['extra'] if data else '')
        buttons(self,[('Apply category',self.ok),('Cancel',self.cancel)])

    def ok(self):
        try:
            self.path_box.commit();self.geo.edit_category(self.ident.get().strip(),self.name.get(),self.slots.get(),self.color.get(),self.path.get(),self.extra.get('1.0','end-1c'),self.new);self.accept(self.ident.get())
        except (ValueError,OSError) as exc:messagebox.showerror('State category',str(exc),parent=self)


class StateDialog(DraftDialog):
    def __init__(self,parent,app,sid):
        data=app.geography_store.state(sid)
        super().__init__(parent,app.character_store,f'State {sid}')
        self.app,self.geo,self.sid,self.data=app,app.geography_store,sid,data;self.geometry('1050x820');self.minsize(900,700)
        self.name=tk.StringVar(value=data['name']);top=ttk.Frame(self,padding=10);top.pack(fill='x');ttk.Label(top,text='State name').pack(side='left');ttk.Entry(top,textvariable=self.name).pack(side='left',fill='x',expand=True,padx=8)
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=10)
        frames={}
        for key,label in [('attributes','Attributes'),('resources','Resources'),('buildings','Buildings'),('ownership','Owner / cores / claims'),('demographics','Culture / species'),('vps','Victory points')]:
            f=ttk.Frame(self.tabs,padding=10);self.tabs.add(f,text=label);frames[key]=f
        self.frames=frames;form=frames['attributes'];form.columnconfigure(1,weight=1);self.attribute_values={};self.boxes=[]
        labels={'manpower':'Population','state_category':'State category','buildings_max_level_factor':'Building slot multiplier','local_supplies':'Local supplies','impassable':'Impassable'}
        defaults={'manpower':'0','state_category':'rural','buildings_max_level_factor':'1','local_supplies':'0','impassable':'no'}
        for row,key in enumerate(dict.fromkeys([*labels,*data['attributes']])):
            variable=tk.StringVar(value=data['attributes'].get(key,defaults.get(key,'')));self.attribute_values[key]=variable
            ttk.Label(form,text=labels.get(key,key)).grid(row=row,column=0,sticky='w',pady=9)
            if key=='state_category':widget=ChoiceBox(form,textvariable=variable,values=self.geo.choices('categories'));self.boxes.append(widget)
            elif key=='impassable':widget=ChoiceBox(form,textvariable=variable,values=['yes','no']);self.boxes.append(widget)
            else:widget=ttk.Entry(form,textvariable=variable)
            widget.grid(row=row,column=1,sticky='ew',padx=10)
        ttk.Label(form,text=f'{len(app.world.states[sid].provinces)} provinces. Province membership and shapes cannot be changed here.',wraplength=850).grid(row=len(self.attribute_values),column=0,columnspan=2,sticky='w',pady=20)
        self.resources=ValueEditor(frames['resources'],data['resources'],self.geo.choices('resources'),'Amount')
        self.build_buildings(frames['buildings']);self.build_ownership(frames['ownership'])
        demo=app.world.demographics[sid];self.cultures=tk.StringVar(value=' '.join(map(str,demo['culture'])));self.species=tk.StringVar(value=str(demo['species']));self.minority=tk.StringVar(value=str(demo['minority']))
        for row,(label,var) in enumerate([('Culture IDs (ordered, separated by spaces)',self.cultures),('Majority species',self.species),('Minority species',self.minority)]):
            ttk.Label(frames['demographics'],text=label).grid(row=row,column=0,sticky='w',pady=8)
            if var is self.cultures:widget=ttk.Entry(frames['demographics'],textvariable=var,width=55)
            else:
                choices=[Choice(str(k),r.name) for k,r in app.catalog_store.species().items()]
                if var is self.minority:choices.append(Choice('1000','No minority'))
                widget=ChoiceBox(frames['demographics'],textvariable=var,values=choices);self.boxes.append(widget)
            widget.grid(row=row,column=1,sticky='ew',padx=8)
        self.culture_choice=ChoiceBox(frames['demographics'],values=[Choice(str(k),r.name) for k,r in app.catalog_store.cultures().items()]);self.culture_choice.grid(row=3,column=1,sticky='ew',padx=8)
        ttk.Button(frames['demographics'],text='Append named culture',command=self.add_culture).grid(row=3,column=0,pady=8)
        self.vps=table(frames['vps'],[('value','VP value',120)]);self.vps.bind('<Double-1>',lambda e:self.edit_vp())
        buttons(frames['vps'],[('Edit selected VP',self.edit_vp),('New VP: pick province on map',lambda:app.begin_geography_pick(self,self.edit_vp,'province',set(app.world.states[sid].provinces)))])
        self.refresh_vps();buttons(self,[('Apply state',self.ok),('Cancel',self.cancel)])

    def build_ownership(self,frame):
        choices=[Choice(tag,self.app.character_store.neutral_name(tag)) for tag in self.app.world.country_paths];self.owner=tk.StringVar(value=self.data['owner']);self.controller=tk.StringVar(value=self.data['controller'])
        for label,var in [('Owner',self.owner),('Controller (blank = owner)',self.controller)]:
            line=ttk.Frame(frame);line.pack(fill='x',pady=6);ttk.Label(line,text=label,width=30).pack(side='left');box=ChoiceBox(line,textvariable=var,values=[Choice('','Unspecified')]+choices);box.pack(side='left',fill='x',expand=True);self.boxes.append(box)
        self.transfer_cores=getattr(self.app,'transfer_cores',None) or tk.BooleanVar(value=True)
        ttk.Checkbutton(frame,text='Transfer Cores',variable=self.transfer_cores).pack(anchor='w')
        split=ttk.Panedwindow(frame,orient='horizontal');split.pack(fill='both',expand=True,pady=10)
        core=ttk.LabelFrame(split,text='Cores',padding=6);claim=ttk.LabelFrame(split,text='Claims',padding=6);split.add(core,weight=1);split.add(claim,weight=1)
        self.cores=TagSetEditor(core,self.data['cores'],choices);self.claims=TagSetEditor(claim,self.data['claims'],choices)

    def build_buildings(self,frame):
        self.building_values=dict(self.data['buildings']);self.building_rows=table(frame,[('scope','Placement',170),('amount','Level',90),('type','Building type',170)])
        self.building_rows.bind('<<TreeviewSelect>>',self.pick_building);self.building_keys={}
        line=ttk.Frame(frame);line.pack(fill='x',pady=6);self.building=tk.StringVar();self.building_level=tk.StringVar(value='1');self.province=tk.StringVar()
        defs=self.geo.buildings();choices=[c for c in self.geo.choices('buildings') if not defs[c.code]['network']]
        self.building_box=ChoiceBox(line,textvariable=self.building,values=choices,width=35);self.building_box.pack(side='left',fill='x',expand=True);self.building_box.bind('<<ComboboxSelected>>',lambda e:self.building_help())
        self.province_box=ChoiceBox(line,textvariable=self.province,values=[Choice('','State')]+[Choice(str(p),f'Province {p}') for p in self.app.world.states[self.sid].provinces],width=19);self.province_box.pack(side='left',padx=6)
        ttk.Entry(line,textvariable=self.building_level,width=8).pack(side='left');ttk.Button(line,text='Add / update',command=self.add_building).pack(side='left',padx=6)
        buttons(frame,[('Remove selected',self.remove_building),('Pick province on map',lambda:self.app.begin_geography_pick(self,lambda p:self.province.set(str(p)),'province',set(self.app.world.states[self.sid].provinces)))])
        self.building_note=ttk.Label(frame,wraplength=950);self.building_note.pack(anchor='w',pady=6)
        ttk.Label(frame,text='Shared-slot, nonshared state and province buildings are separate. Supply nodes use their native map file. Railway routes are not edited here.',wraplength=950).pack(anchor='w',pady=6)
        self.refresh_buildings()

    def refresh_buildings(self):
        self.building_rows.delete(*self.building_rows.get_children());self.building_keys={};names={c.code:c.name for c in self.geo.choices('buildings')};defs=self.geo.buildings()
        for i,((pid,key),amount) in enumerate(sorted(self.building_values.items(),key=lambda r:(names.get(r[0][1],r[0][1]).casefold(),r[0][0] or 0))):
            d=defs.get(key,{});kind='Shared slots' if d.get('shared') else 'Province' if d.get('province') else 'Nonshared state'
            item=self.building_rows.insert('','end',text=Choice(key,names.get(key,key)).label,values=(f'Province {pid}' if pid is not None else 'State',amount,kind));self.building_keys[item]=(pid,key)

    def building_help(self):
        d=self.geo.buildings().get(self.building.get(),{})
        if d.get('province'):
            self.province_box.configure(state='normal')
            if not self.province.get():self.province.set(str(self.app.world.states[self.sid].provinces[0]))
        else:self.province.set('');self.province_box.configure(state='disabled')
        self.building_note.configure(text='Native limits: '+', '.join(k+'='+str(v) for k,v in [('state',d.get('state_max')),('province',d.get('province_max')),('facility group',d.get('group'))] if v is not None and v!='')+('. Coastal location required.' if d.get('coastal') else ''))

    def add_building(self):
        try:
            self.building_box.commit();self.province_box.commit();key=self.building.get();d=self.geo.buildings().get(key)
            if d is None:raise ValueError('Choose a defined building')
            pid=int(self.province.get()) if d['province'] else None
            self.building_values[(pid,key)]=numeric(self.building_level.get(),0,True);self.refresh_buildings()
        except ValueError as exc:messagebox.showerror('Building',str(exc),parent=self)

    def remove_building(self):
        for item in self.building_rows.selection():self.building_values.pop(self.building_keys[item],None)
        self.refresh_buildings()

    def pick_building(self,event=None):
        if rows:=self.building_rows.selection():
            pid,key=self.building_keys[rows[0]];self.building.set(key);self.province.set(str(pid) if pid is not None else '');self.building_level.set(self.building_values[(pid,key)]);self.building_help()

    def add_culture(self):
        self.culture_choice.commit();key=self.culture_choice.get()
        if key:self.cultures.set((self.cultures.get()+' '+key).strip())

    def refresh_vps(self):
        self.vps.delete(*self.vps.get_children())
        records=self.geo.victory_points()
        for c in ChoiceIndex(Choice(str(p),d['name']) for p,d in records.items() if d['state']==self.sid).choices:
            self.vps.insert('','end',iid=c.code,text=c.label,values=(records[int(c.code)]['value'],))

    def edit_vp(self,pid=None):
        if pid is None:pid=int(next(iter(self.vps.selection()),'0'))
        if not pid:return
        dialog=VictoryPointDialog(self,self.app,pid);self.wait_window(dialog);self.grab_set();self.refresh_vps()

    def ok(self):
        docs=self.geo.docs
        try:
            for box in self.boxes:box.commit()
            with docs.grouped():
                self.geo.edit_state(self.sid,self.name.get(),{k:v.get() for k,v in self.attribute_values.items()},self.resources.values,self.building_values,self.owner.get(),self.controller.get(),self.cores.values,self.claims.values,transfer_cores=self.transfer_cores.get())
                cultures=[int(x) for x in self.cultures.get().replace(',',' ').split()];species=int(self.species.get());minority=int(self.minority.get())
                old=self.app.world.demographics[self.sid]
                if (cultures,species,minority)!=(old['culture'],old['species'],old['minority']):
                    from demographics import set_local_draft
                    set_local_draft(self.app.world,self.sid,cultures,species,minority)
            self.accept(self.sid)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('State',str(exc),parent=self)


class RegionDialog(DraftDialog):
    def __init__(self,parent,app,rid):
        data=app.geography_store.region(rid)
        super().__init__(parent,app.character_store,f'Strategic region {rid}')
        self.app,self.geo,self.rid,self.data=app,app.geography_store,rid,data;self.geometry('1180x850');self.minsize(1030,730)
        self.transfers={};self.periods=deepcopy(data['weather']);self.name=tk.StringVar(value=data['name']);self.terrain=tk.StringVar(value=data['terrain'])
        form=ttk.Frame(self,padding=10);form.pack(fill='x');ttk.Label(form,text='Region name').pack(side='left');ttk.Entry(form,textvariable=self.name).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Label(form,text='Terrain for sea provinces').pack(side='left');self.terrain_box=ChoiceBox(form,textvariable=self.terrain,values=[Choice('','Default / none')]+self.geo.choices('terrain'),width=26);self.terrain_box.pack(side='left',padx=8)
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=10);membership=ttk.Frame(self.tabs,padding=10);weather=ttk.Frame(self.tabs,padding=10)
        self.tabs.add(membership,text='Whole-state membership');self.tabs.add(weather,text='Weather / climate')
        self.build_membership(membership);self.build_weather(weather);buttons(self,[('Apply region',self.ok),('Cancel',self.cancel)])

    def region_choices(self):return [Choice(str(r),self.app.world.label(d['name'])) for r,d in self.app.world.regions.items()]

    def build_membership(self,frame):
        self.member_rows=table(frame,[('from','Original region',180)]);self.state=tk.StringVar();self.destination=tk.StringVar()
        line=ttk.Frame(frame);line.pack(fill='x',pady=7);self.state_box=ChoiceBox(line,textvariable=self.state,values=[Choice(str(s),self.app.world.label(d.name)) for s,d in self.app.world.states.items()]);self.state_box.pack(side='left',fill='x',expand=True)
        ttk.Button(line,text='Add / move into this region',command=self.add_state).pack(side='left',padx=6)
        ttk.Button(line,text='Pick state on map',command=lambda:self.app.begin_geography_pick(self,lambda sid:self.add_state(sid),'state')).pack(side='left')
        line=ttk.Frame(frame);line.pack(fill='x',pady=7);ttk.Label(line,text='Remove selected state by transferring to:').pack(side='left')
        self.destination_box=ChoiceBox(line,textvariable=self.destination,values=[c for c in self.region_choices() if int(c.code)!=self.rid]);self.destination_box.pack(side='left',fill='x',expand=True,padx=7)
        ttk.Button(line,text='Transfer selected',command=self.remove_state).pack(side='left')
        self.transfer_note=ttk.Label(frame,wraplength=1000);self.transfer_note.pack(anchor='w',pady=10)
        ttk.Label(frame,text='Each state moves with every one of its provinces. Removing a state always needs a destination; sea provinces stay in their existing region.',wraplength=1000).pack(anchor='w');self.refresh_members()

    def refresh_members(self):
        self.member_rows.delete(*self.member_rows.get_children());members=set(self.data['states'])
        for sid,rid in self.transfers.items():
            if rid==self.rid:members.add(sid)
            else:members.discard(sid)
        for c in ChoiceIndex(Choice(str(s),self.app.world.label(self.app.world.states[s].name)) for s in members).choices:
            sid=int(c.code);regions={self.app.world.province_regions.get(p) for p in self.app.world.states[sid].provinces};self.member_rows.insert('','end',iid=c.code,text=c.label,values=(', '.join(map(str,regions)),))
        self.transfer_note.configure(text=f'{len(members)} states after Apply; {len(self.transfers)} pending transfers.')

    def add_state(self,sid=None):
        try:
            if sid is None:self.state_box.commit();sid=int(self.state.get())
            if sid not in self.app.world.states:raise ValueError('Choose a defined state')
            self.transfers[sid]=self.rid;self.refresh_members()
        except ValueError as exc:messagebox.showerror('Region membership',str(exc),parent=self)

    def remove_state(self):
        try:
            selected=self.member_rows.selection()
            if not selected:return
            self.destination_box.commit();destination=int(self.destination.get())
            if destination==self.rid or destination not in self.app.world.regions:raise ValueError('Choose a different destination region')
            self.transfers[int(selected[0])]=destination;self.refresh_members()
        except ValueError as exc:messagebox.showerror('Region membership',str(exc),parent=self)

    def build_weather(self,frame):
        top=ttk.Frame(frame);top.pack(fill='x');self.climate=tk.StringVar(value='Cfb')
        self.climate_box=ChoiceBox(top,textvariable=self.climate,values=[Choice(k,n) for k,n in CLIMATES.items()],width=38);self.climate_box.pack(side='left')
        self.latitude=tk.BooleanVar(value=self.app.koppen_latitude.get() if hasattr(self.app,'koppen_latitude') else True)
        ttk.Checkbutton(top,text='Account for latitude',variable=self.latitude).pack(side='left',padx=6)
        ttk.Button(top,text='Apply climate preset',command=self.preset).pack(side='left')
        self.vanilla=tk.StringVar();self.flip=tk.BooleanVar();self.import_terrain=tk.BooleanVar(value=False)
        line=ttk.Frame(frame);line.pack(fill='x',pady=6);ttk.Label(line,text='Vanilla region:').pack(side='left')
        loc=inherited_localisations(str(self.app.character_store.game_root));choices=[]
        for rid,(path,text,node) in self.geo.vanilla_regions().items():choices.append(Choice(str(rid),loc.get(atom(text,node.children,'name'),path.stem)))
        self.vanilla_box=ChoiceBox(line,textvariable=self.vanilla,values=choices,width=42);self.vanilla_box.pack(side='left',fill='x',expand=True,padx=6)
        ttk.Checkbutton(line,text='Shift seasons 6 months',variable=self.flip).pack(side='left');ttk.Button(line,text='Import weather',command=self.import_weather).pack(side='left',padx=6)
        ttk.Checkbutton(frame,text='Also import naval terrain (affects sea provinces)',variable=self.import_terrain).pack(anchor='w')
        self.weather_rows=table(frame,[('dates','Dates',180),('temp','Temperature °C',190)],height=10);self.weather_rows.bind('<<TreeviewSelect>>',self.pick_period)
        form=ttk.Frame(frame);form.pack(fill='x',pady=8);self.start=tk.StringVar();self.end=tk.StringVar();self.low=tk.StringVar();self.high=tk.StringVar()
        for label,var in [('Start day.month',self.start),('End day.month',self.end),('Min °C',self.low),('Max °C',self.high)]:ttk.Label(form,text=label).pack(side='left',padx=3);ttk.Entry(form,textvariable=var,width=9).pack(side='left',padx=3)
        weights=ttk.Frame(frame);weights.pack(fill='x');self.weights={}
        for i,k in enumerate(WEATHER_FIELDS):
            variable=tk.StringVar(value='0');self.weights[k]=variable;ttk.Label(weights,text=k).grid(row=(i//3)*2,column=i%3*2,sticky='w',padx=4)
            ttk.Entry(weights,textvariable=variable,width=9).grid(row=(i//3)*2,column=i%3*2+1,padx=4,pady=3)
        buttons(frame,[('Update selected period',self.update_period),('Add period',self.add_period),('Remove selected period',self.remove_period)])
        ttk.Label(frame,text='Dates are game day.month, both zero-based (0.0 = 1 January). Weather values are weights, not probabilities summing to 100%. Presets are editable Köppen-inspired approximations.',wraplength=1050).pack(anchor='w',pady=4)
        self.refresh_weather()

    def refresh_weather(self):
        self.weather_rows.delete(*self.weather_rows.get_children())
        for i,p in enumerate(self.periods):self.weather_rows.insert('','end',iid=str(i),text=f'Period {i+1}',values=(p.start+' — '+p.end,p.low+' to '+p.high))

    def pick_period(self,event=None):
        if rows:=self.weather_rows.selection():
            p=self.periods[int(rows[0])];self.start.set(p.start);self.end.set(p.end);self.low.set(p.low);self.high.set(p.high)
            for k,v in self.weights.items():v.set(p.weights.get(k,'0'))

    def update_period(self):
        try:
            if not (rows:=self.weather_rows.selection()):return
            old=self.periods[int(rows[0])];p=deepcopy(old);p.start=self.start.get();p.end=self.end.get();p.low=self.low.get();p.high=self.high.get();p.weights.update({k:v.get() for k,v in self.weights.items()});p.validate();self.periods[int(rows[0])]=p;self.refresh_weather()
        except ValueError as exc:messagebox.showerror('Weather',str(exc),parent=self)

    def add_period(self):self.periods.append(WeatherPeriod('0.0','30.0','0','20',{k:'0' for k in WEATHER_FIELDS}));self.refresh_weather()
    def remove_period(self):
        for i in sorted(map(int,self.weather_rows.selection()),reverse=True):self.periods.pop(i)
        self.refresh_weather()

    def preset(self):
        try:self.climate_box.commit();self.periods=self.geo.climate_at_region(self.rid,self.climate.get(),self.latitude.get());self.refresh_weather()
        except ValueError as exc:messagebox.showerror('Climate preset',str(exc),parent=self)

    def import_weather(self):
        try:
            self.vanilla_box.commit();periods,terrain=self.geo.import_weather(int(self.vanilla.get()),self.flip.get());self.periods=periods
            if self.import_terrain.get():self.terrain.set(terrain)
            self.refresh_weather()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Vanilla weather',str(exc),parent=self)

    def ok(self):
        try:
            self.terrain_box.commit();self.geo.edit_region(self.rid,self.name.get(),self.terrain.get(),self.periods,self.transfers);self.accept(self.rid)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Strategic region',str(exc),parent=self)


class VictoryPointDialog(DraftDialog):
    def __init__(self,parent,app,pid):
        if pid not in app.world.province_states or app.world.provinces[pid]['type']!='land':raise ValueError('Choose a land province belonging to a state')
        super().__init__(parent,app.character_store,f'Victory point — province {pid}')
        self.app,self.geo,self.pid=app,app.geography_store,pid;self.geometry('650x330');self.minsize(550,300)
        current=self.geo.victory_points().get(pid);self.name=tk.StringVar(value=current['name'] if current else '');self.amount=tk.StringVar(value=str(current['value']) if current else '1')
        form=ttk.Frame(self,padding=15);form.pack(fill='both',expand=True);form.columnconfigure(1,weight=1)
        sid=app.world.province_states[pid];ttk.Label(form,text=f'Province {pid} / state {sid} — {app.world.label(app.world.states[sid].name)}',wraplength=600).grid(row=0,column=0,columnspan=2,sticky='w',pady=8)
        for row,(label,var) in enumerate([('VP name',self.name),('VP value',self.amount)],1):ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=10);ttk.Entry(form,textvariable=var).grid(row=row,column=1,sticky='ew',padx=10)
        ttk.Label(form,text='Name is stored in victory_points_l_english.yml, sorted by localized place name. Values are stored in this province’s state history.',wraplength=600).grid(row=3,column=0,columnspan=2,sticky='w',pady=10)
        entries=[('Apply VP',self.ok),('Cancel',self.cancel)]
        if current:entries.insert(1,('Remove VP',self.remove))
        buttons(self,entries)

    def ok(self):
        try:self.geo.set_vp(self.pid,self.name.get(),self.amount.get());self.accept(self.pid)
        except (ValueError,OSError) as exc:messagebox.showerror('Victory point',str(exc),parent=self)

    def remove(self):
        try:self.geo.set_vp(self.pid,'',None);self.accept(self.pid)
        except (ValueError,OSError) as exc:messagebox.showerror('Victory point',str(exc),parent=self)

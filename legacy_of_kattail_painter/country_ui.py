"""Country workspace and modal native-data editors over the shared draft store."""
from copy import deepcopy
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser

from PIL import Image, ImageTk, ImageOps

from character_model import atom, block
from character_ui import DraftDialog, CharacterDialog
from country_model import Country, CountrySourceExists, PATTERNS, render_flag, number, copy_ideology_names, definite_name, distribute_popularities, flag_rgb
from model import parse, value, child
from select_ui import Choice, ChoiceBox, ChoiceIndex
from flag_designer import FlagDesigner


def buttons(parent, entries):
    bar=ttk.Frame(parent);bar.pack(fill='x',pady=6)
    for text, command in entries:ttk.Button(bar,text=text,command=command).pack(side='left',padx=(0,6))
    return bar


@lru_cache(maxsize=4)
def eaw_badge(size):
    with Image.open(Path(__file__).parent/'assets/eaw_sun.png') as image:
        return ImageOps.contain(image.convert('RGBA'),(size,size),Image.Resampling.LANCZOS)


def spirit_icon_preview(store,key,size=(40,40)):
    """UI-only attribution in a separate margin, never in the game texture."""
    image=store.icon_image(key,size)
    if image is None:return None
    badge_size=16;gap=4;left=badge_size+gap
    preview=Image.new('RGBA',(size[0]+left,size[1]+gap))
    preview.alpha_composite(image,(left+(size[0]-image.width)//2,0))
    if store.icon_catalog()[key]['origin']=='EaW':
        preview.alpha_composite(eaw_badge(badge_size),(0,preview.height-badge_size))
    return preview


def spirit_icon_choices(store):
    sources=getattr(store,'spirit_icon_sources',{})
    return [row['choice'] for row in store.spirit_icon_catalog().values() if sources.get(row['origin'],True)]


def import_spirit_icon(parent,store):
    source=filedialog.askopenfilename(parent=parent,title='Import national spirit icon',
        filetypes=[('Icon images','*.png *.jpg *.jpeg *.dds *.tga *.bmp *.webp'),('All files','*.*')])
    if not source:return None
    try:
        key=store.import_spirit_icon(source)
        origin=store.icon_catalog()[key]['origin']
        store.spirit_icon_sources={**getattr(store,'spirit_icon_sources',{}),origin:True}
        return key
    except (ValueError,OSError) as exc:messagebox.showerror('Import icon',str(exc),parent=parent)


def choose_color(parent,variable):
    try:initial='#%02x%02x%02x'%flag_rgb(variable.get())
    except ValueError:initial='#ffffff'
    selected=colorchooser.askcolor(initial,parent=parent)[1]
    if selected:variable.set(selected)


def table(parent,columns=(),height=12):
    frame=ttk.Frame(parent);frame.pack(fill='both',expand=True)
    tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show='tree headings',height=height,selectmode='browse')
    tree.heading('#0',text='Localized name (ID)');tree.column('#0',width=360)
    for key,label,width in columns:tree.heading(key,text=label);tree.column(key,width=width)
    scroll=ttk.Scrollbar(frame,command=tree.yview);tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
    return tree


class CountryWorkspace(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,padding=10);self.pack(fill='both',expand=True)
        self.app=app;self.store=app.country_store;self.query=tk.StringVar()
        bar=buttons(self,[('New country',lambda:self.open()),('Edit selected',self.edit),('Paint on map',self.paint),('Save',app.save),('Undo',app.undo),('Redo',app.redo),('Discard drafts',app.discard)])
        ttk.Label(bar,text='Search name or tag:').pack(side='left',padx=(14,5))
        self.search=ttk.Entry(bar,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True)
        self.search.bind('<KeyRelease>',lambda e:self.refresh())
        self.rows=table(self,[('history','Country history',420)])
        self.rows.bind('<Double-1>',lambda e:self.edit());self.rows.bind('<Return>',lambda e:self.edit())
        self.rows.bind('<KeyPress>',lambda e:app.search_list(e,self.query,self.search,self.refresh))
        ttk.Label(self,text='Edits stay in drafts until Save. Country setup, ideological names, flags and spirits use native game files.').pack(anchor='w',pady=8)
        self._signature=None
        self.bind('<Map>',lambda event:self.after_idle(self.refresh))

    def refresh(self):
        if not self.winfo_viewable():return
        loc=self.store.characters.localisations();signature=(id(loc),tuple(self.app.world.country_paths),tuple(self.app.world.countries.items()),self.query.get())
        if signature==self._signature:return
        self._signature=signature
        selected=next(iter(self.rows.selection()),None);self.rows.delete(*self.rows.get_children())
        index=ChoiceIndex(Choice(tag,self.store.characters.neutral_name(tag,loc)) for tag in self.app.world.country_paths)
        for choice in index.matching(self.query.get()):
            self.rows.insert('','end',iid=choice.code,text=choice.label,values=(self.app.world.countries.get(choice.code,'No history yet'),))
        if selected and self.rows.exists(selected):self.rows.selection_set(selected)

    def edit(self):
        if selected:=self.rows.selection():self.open(selected[0])

    def paint(self):
        if selected:=self.rows.selection():
            self.app.paint_selection['Owner']=selected[0];self.app.brush.set('Owner')
            self.app.workspace.select(self.app.map_workspace);self.app.tabs.select(0);self.app.brush_changed()

    def open(self,tag=None):
        try:
            dialog=CountryDialog(self,self.app,tag);self.wait_window(dialog);self.app._sync();self._signature=None;self.refresh()
            if dialog.result:
                self.app.paint_selection['Owner']=dialog.result
                if self.rows.exists(dialog.result):self.rows.selection_set(dialog.result);self.rows.see(dialog.result)
        except (ValueError,OSError,KeyError,InvalidOperation) as exc:messagebox.showerror('Country editor',str(exc),parent=self)


class CountryDialog(DraftDialog):
    def __init__(self,parent,app,tag=None):
        super().__init__(parent,app.character_store,'Edit country' if tag else 'New country')
        self.app=app;self.countries=app.country_store;self.new=tag is None
        self.geometry('1180x850');self.minsize(1000,730)
        ideologies=self.countries.ideologies();ruling='neutrality' if 'neutrality' in ideologies else next(iter(ideologies))
        self.data=self.countries.read(tag) if tag else Country('', '', '',ruling=ruling,popularities={i:('100' if i==ruling else '0') for i in ideologies},laws={'mobilization_laws':'volunteer_only','economy':'civilian_economy','specialty':'specialty_nothing','species':'var_species_0'},names={i:{'name':None,'def':None} for i in ('',*ideologies)})
        self.names=deepcopy(self.data.names);self.flags={};self._flag_photos=[];self._names_row='';self._loading_name=False
        self.tag=tk.StringVar(value=tag or '');self.base_name=tk.StringVar(value=self.names['']['name'] or '')
        self.color=tk.StringVar(value=self.hex(app.world.country_colours().get(tag,(70,120,180))))
        self.capital=tk.StringVar(value=self.data.capital);self.stability=tk.StringVar(value=self.data.stability);self.war=tk.StringVar(value=self.data.war_support)
        self.ruling=tk.StringVar(value=self.data.ruling);self.laws={k:tk.StringVar(value=self.data.laws.get(k,'')) for k in ('mobilization_laws','economy','economy_laws','specialty','species')}
        self.portrait_group=tk.StringVar(value=self.data.portrait_group if self.data.portrait_group is not None else '__keep__')
        self.auto_portrait_group=self.new
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=10,pady=10)
        self.frames={}
        for key,label in [('setup','Setup'),('summary','Summary'),('politics','Parties & popularity'),('names','Ideology names'),('flags','Flags'),('leaders','Leaders'),('tech','Starting technologies'),('spirits','National spirits')]:
            frame=ttk.Frame(self.tabs,padding=10);self.tabs.add(frame,text=label);self.frames[key]=frame
        self.build_setup();self.build_summary();self.build_politics();self.build_names();self.build_flags();self.build_leaders();self.build_tech();self.build_spirits()
        self.tabs.bind('<<NotebookTabChanged>>',self.tab_changed)
        bottom=ttk.Frame(self,padding=10);bottom.pack(fill='x')
        ttk.Label(bottom,text='Apply stages native sources. Save in the main window writes them with backups.').pack(side='left')
        ttk.Button(bottom,text='Cancel',command=self.cancel).pack(side='right');ttk.Button(bottom,text='Apply country',command=self.ok).pack(side='right',padx=8)

    @staticmethod
    def hex(rgb):return '#'+''.join(f'{v:02x}' for v in rgb)

    def ideology_choices(self,base=False):
        names=self.countries.characters.trait_store.names()
        return ([Choice('','Base / fallback')] if base else [])+[Choice(i,names.get(i,i)) for i in self.countries.ideologies()]

    def build_setup(self):
        frame=self.frames['setup'];frame.columnconfigure(1,weight=1);self.boxes=[]
        entries=[('Country tag',self.tag),('Base name',self.base_name),('Map color',self.color),('Capital state',self.capital),('Starting stability (%)',self.stability),('Starting war support (%)',self.war)]
        for row,(label,variable) in enumerate(entries):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',pady=9)
            line=ttk.Frame(frame);line.grid(row=row,column=1,sticky='ew',padx=10)
            if variable is self.capital:
                box=ChoiceBox(line,textvariable=variable,values=[Choice(str(s),self.app.world.label(d.name)) for s,d in self.app.world.states.items()],width=48)
                box.pack(side='left',fill='x',expand=True);self.boxes.append(box)
                ttk.Button(line,text='Pick on map',command=self.pick_capital).pack(side='left',padx=8)
            else:
                entry=ttk.Entry(line,textvariable=variable);entry.pack(side='left',fill='x',expand=True)
                if variable is self.tag:
                    self.tag_entry=entry
                    if not self.new:entry.configure(state='disabled')
                if variable is self.color:ttk.Button(line,text='Choose',command=lambda:choose_color(self,self.color)).pack(side='left',padx=8)
        labels={'mobilization_laws':'Mobilization law','economy':'Economy law','economy_laws':'National economic model','specialty':'National attribute','species':'National species'}
        for row,(category,variable) in enumerate(self.laws.items(),len(entries)):
            ttk.Label(frame,text=labels[category]).grid(row=row,column=0,sticky='w',pady=9)
            values=list(self.countries.choices(category))
            if category=='economy_laws':values.insert(0,Choice('','Unspecified'))
            box=ChoiceBox(frame,textvariable=variable,values=values);box.grid(row=row,column=1,sticky='ew',padx=10);self.boxes.append(box)
        row=len(entries)+len(self.laws)
        ttk.Label(frame,text='Generic portrait group').grid(row=row,column=0,sticky='w',pady=9)
        line=ttk.Frame(frame);line.grid(row=row,column=1,sticky='ew',padx=10)
        groups=self.store.generic_portraits.groups()
        values=[Choice('__keep__','Keep existing / native default'),Choice('','Default (remove country-specific pools)')]+[Choice(k,g.name) for k,g in groups.items()]
        self.portrait_group_box=ChoiceBox(line,textvariable=self.portrait_group,values=values)
        self.portrait_group_box.pack(side='left',fill='x',expand=True);self.boxes.append(self.portrait_group_box)
        self.portrait_group_box.bind('<<ComboboxSelected>>',lambda e:setattr(self,'auto_portrait_group',False))
        ttk.Button(line,text='Use national species',command=self.use_species_portraits).pack(side='left',padx=6)
        self.laws['species'].trace_add('write',lambda *args:self.suggest_species_portraits())
        self.suggest_species_portraits()
        ttk.Label(frame,text='Capital selection does not change state ownership. Use the Owner brush to assign territory to a new country.',wraplength=1000).grid(row=row+1,column=0,columnspan=2,sticky='w',pady=15)

    def suggest_species_portraits(self):
        if self.auto_portrait_group:
            key='Species_'+self.laws['species'].get().removeprefix('var_species_')
            if key in self.store.generic_portraits.groups():self.portrait_group.set(key)

    def use_species_portraits(self):
        self.auto_portrait_group=True;self.suggest_species_portraits()

    def pick_capital(self):
        self.grab_release();self.withdraw();self.app.begin_capital_pick(self)

    def receive_capital(self,sid=None):
        if sid is not None:self.capital.set(str(sid))
        self.deiconify();self.lift();self.grab_set()

    def build_summary(self):
        frame=self.frames['summary'];self.summary_title=tk.StringVar();ttk.Label(frame,textvariable=self.summary_title,font=('Segoe UI',13,'bold')).pack(anchor='w',pady=8)
        self.summary_population=tk.StringVar();ttk.Label(frame,textvariable=self.summary_population).pack(anchor='w',pady=8)
        self.summary_factories=table(frame,[('total','Total',150)],height=5)
        ttk.Label(frame,text='Resources').pack(anchor='w',pady=(12,5));self.summary_resources=table(frame,[('total','Total',150)],height=10)
        ttk.Label(frame,text='Read-only totals of owned states in the current starting-setup drafts. Runtime effects and foreign-controlled factories are not simulated.',wraplength=1000).pack(anchor='w',pady=8)

    def refresh_summary(self):
        tag=self.tag.get().strip();data=self.countries.summary(tag);names=self.store.trait_store.names()
        self.summary_title.set(f'{self.base_name.get() or tag} ({tag}) — {data["states"]} owned states')
        self.summary_population.set(f'Population: {int(data["population"]):,}')
        self.summary_factories.delete(*self.summary_factories.get_children())
        for kind,amount in data['factories'].items():self.summary_factories.insert('','end',text=Choice(kind,names.get(kind,kind.replace('_',' ').title())).label,values=(f'{amount:,}',))
        self.summary_factories.insert('','end',text='Civilian + military factories',values=(f'{data["factories"]["industrial_complex"]+data["factories"]["arms_factory"]:,}',))
        self.summary_factories.insert('','end',text='Factories + dockyards',values=(f'{sum(data["factories"].values()):,}',))
        self.summary_resources.delete(*self.summary_resources.get_children())
        keys=set(data['resources'])|set(self.countries.definitions('common/resources','resources'))
        for c in ChoiceIndex(Choice(k,names.get('PRODUCTION_MATERIALS_'+k.upper(),names.get(k,k.replace('_',' ').title()))) for k in keys).choices:
            self.summary_resources.insert('','end',text=c.label,values=(format(Decimal(data['resources'].get(c.code,0)).normalize(),'f'),))

    def build_politics(self):
        frame=self.frames['politics'];left=ttk.Frame(frame);left.pack(side='left',fill='y',padx=(0,25))
        ttk.Label(left,text='Ruling ideology').grid(row=0,column=0,sticky='w',pady=8)
        self.ruling_box=ChoiceBox(left,textvariable=self.ruling,values=self.ideology_choices(),width=34);self.ruling_box.grid(row=0,column=1,sticky='ew');self.boxes.append(self.ruling_box)
        self.pop={}
        for row,choice in enumerate(ChoiceIndex(self.ideology_choices()).choices,1):
            ttk.Label(left,text=choice.label).grid(row=row,column=0,sticky='w',pady=5)
            variable=tk.StringVar(value=self.data.popularities.get(choice.code,'0'));self.pop[choice.code]=variable
            entry=ttk.Entry(left,textvariable=variable,width=12);entry.grid(row=row,column=1,sticky='w',padx=10)
            variable.trace_add('write',lambda *args:self.draw_pie())
        self.total=tk.StringVar();ttk.Label(left,textvariable=self.total).grid(row=len(self.pop)+1,column=0,columnspan=2,sticky='w',pady=12)
        ttk.Button(left,text='Assign random weights to remaining ideologies',command=lambda:self.adjust_popularities(True)).grid(row=len(self.pop)+2,column=0,columnspan=2,sticky='ew',pady=3)
        ttk.Button(left,text='Normalize to 100',command=self.adjust_popularities).grid(row=len(self.pop)+3,column=0,columnspan=2,sticky='ew',pady=3)
        ttk.Label(left,text='Random fills non-Gestalt blank/zero entries. Normalize rescales weights. Apply saves exact totals at 0.001% precision; Gestalt is set manually.',wraplength=410).grid(row=len(self.pop)+4,column=0,columnspan=2,sticky='w',pady=8)
        self.pie=tk.Canvas(frame,width=430,height=470,highlightthickness=0);self.pie.pack(side='left',fill='both',expand=True)
        self.pie.bind('<Configure>',lambda e:self.draw_pie());self.draw_pie()

    def adjust_popularities(self,remaining=False):
        try:values=distribute_popularities({i:v.get() for i,v in self.pop.items()},remaining)
        except ValueError as exc:messagebox.showerror('Party popularity',str(exc),parent=self);return
        self._updating_pop=True
        try:
            for i,v in values.items():self.pop[i].set(v)
        finally:self._updating_pop=False
        self.draw_pie()

    def draw_pie(self):
        if not hasattr(self,'pie') or getattr(self,'_updating_pop',False):return
        self.pie.delete('all')
        try:
            precise={i:Decimal(number(v.get(),0,100)) for i,v in self.pop.items()};exact=sum(precise.values())
            values={i:float(v) for i,v in precise.items()};total=float(exact);self.total.set('Total: '+format(exact.normalize(),'f')+'% (must equal 100%)')
        except ValueError:self.total.set('Enter popularity values between 0 and 100.');return
        width=self.pie.winfo_width() if self.pie.winfo_width()>1 else 430
        height=self.pie.winfo_height() if self.pie.winfo_height()>1 else 470
        diameter=max(90,min(310,width-40,height-sum(bool(v) for v in values.values())*21-65));box=(20,20,20+diameter,20+diameter);start=90
        names={c.code:c.name for c in self.ideology_choices()}
        for i,v in values.items():
            if not v or not total:continue
            extent=v/total*360;color=self.hex(self.countries.ideologies()[i]['color'])
            if extent>=359.999:self.pie.create_oval(*box,fill=color,outline='white')
            else:self.pie.create_arc(*box,start=start,extent=-extent,fill=color,outline='white');start-=extent
        for n,(i,v) in enumerate((i,v) for i,v in values.items() if v):
            y=diameter+46+n*21;color=self.hex(self.countries.ideologies()[i]['color']);self.pie.create_rectangle(20,y-5,32,y+7,fill=color,outline='');self.pie.create_text(40,y+1,anchor='w',text=f'{names[i]}: {format(precise[i].normalize(),"f")}%')

    def build_names(self):
        frame=self.frames['names'];self.names_table=table(frame,[('name','Normal name',300),('def','Definite name',300)],height=11)
        self.names_table.bind('<<TreeviewSelect>>',self.load_name)
        form=ttk.Frame(frame);form.pack(fill='x',pady=8);self.name_value=tk.StringVar();self.def_value=tk.StringVar()
        for label,var in [('Normal',self.name_value),('DEF',self.def_value)]:
            ttk.Label(form,text=label).pack(side='left',padx=5);ttk.Entry(form,textvariable=var,width=43).pack(side='left',fill='x',expand=True)
        buttons(frame,[('Apply to all ideologies',lambda:self.bulk_names(False)),('Apply to all undefined ideologies',lambda:self.bulk_names(True)),('Inherit base names',self.inherit_names)])
        buttons(frame,[('Duplicate normal to DEF + “the”',lambda:self.duplicate_def(True)),('Duplicate normal to DEF without “the”',lambda:self.duplicate_def(False))])
        ttk.Label(frame,text='Select an ideology to edit. Missing overrides inherit the base country name; bulk “undefined” preserves existing translations, including explicit empty strings.').pack(anchor='w',pady=5)
        self.name_value.trace_add('write',lambda *args:self.name_edited('name'));self.def_value.trace_add('write',lambda *args:self.name_edited('def'));self.refresh_names();self.names_table.selection_set('base');self.load_name()

    def refresh_names(self):
        self.names_table.delete(*self.names_table.get_children())
        for choice in ChoiceIndex(self.ideology_choices(True)).choices:
            row=self.names[choice.code];self.names_table.insert('','end',iid=choice.code or 'base',text=choice.label,values=tuple(row[k] if row[k] is not None else '(inherits base)' for k in ('name','def')))

    def load_name(self,event=None):
        rows=self.names_table.selection()
        if not rows:return
        self._loading_name=True;self._names_row='' if rows[0]=='base' else rows[0];row=self.names[self._names_row]
        self.name_value.set(row['name'] if row['name'] is not None else '');self.def_value.set(row['def'] if row['def'] is not None else '');self._loading_name=False

    def name_edited(self,field):
        if self._loading_name:return
        self.names[self._names_row][field]=(self.name_value if field=='name' else self.def_value).get()
        if self._names_row=='' and field=='name':self.base_name.set(self.name_value.get())
        iid=self._names_row or 'base';self.names_table.item(iid,values=tuple(self.names[self._names_row][k] if self.names[self._names_row][k] is not None else '(inherits base)' for k in ('name','def')))

    def bulk_names(self,undefined):
        copy_ideology_names(self.names,self._names_row,self.countries.ideologies(),undefined)
        self.refresh_names();self.names_table.selection_set(self._names_row or 'base')

    def duplicate_def(self,article):
        text=self.names[self._names_row]['name']
        if text is None:text=self.base_name.get()
        self.def_value.set(definite_name(text,article))

    def inherit_names(self):
        if not self._names_row:return
        self.names[self._names_row]={'name':None,'def':None};self.refresh_names();self.names_table.selection_set(self._names_row);self.load_name()

    def build_flags(self):
        frame=self.frames['flags'];top=ttk.Frame(frame);top.pack(fill='x')
        self.flag_ideology=tk.StringVar(value='');box=ChoiceBox(top,textvariable=self.flag_ideology,values=self.ideology_choices(True),width=35);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.flag_preview())
        self.flag_box=box
        ttk.Button(top,text='Import flag…',command=self.import_flag).pack(side='left',padx=8)
        ttk.Button(top,text='Apply to all ideologies',command=lambda:self.bulk_flags(False)).pack(side='left',padx=5)
        ttk.Button(top,text='Apply to all undefined ideologies',command=lambda:self.bulk_flags(True)).pack(side='left',padx=5)
        self.flag_status=ttk.Label(frame);self.flag_status.pack(anchor='w',pady=6)
        split=ttk.Panedwindow(frame,orient='horizontal');split.pack(fill='both',expand=True)
        design=ttk.Frame(split);preview=ttk.Frame(split);split.add(design,weight=3);split.add(preview,weight=2)
        self.designer=FlagDesigner(design,self.countries,self.use_design);self.designer.pack(fill='both',expand=True)
        ttk.Label(preview,text='Selected country / ideology flag').pack(anchor='w',pady=8)
        self.flag_image=ttk.Label(preview);self.flag_image.pack(pady=15)
        ttk.Label(preview,text='Saved as native 82×52, 41×26 and 10×7 TGA flags. All color choices and the emblem tint remain editable while designing.',wraplength=330).pack(anchor='w',pady=10)
        self.flag_preview()

    def current_flag(self,ideology=None):
        ideology=self.flag_ideology.get() if ideology is None else ideology
        return self.flags.get(ideology) or self.countries.flag(self.tag.get(),ideology,False) or self.flags.get('') or self.countries.flag(self.tag.get(),'')

    def flag_preview(self):
        self.flag_box.commit();ideology=self.flag_ideology.get();image=self.current_flag(ideology)
        explicit=ideology in self.flags or self.countries.flag(self.tag.get(),ideology,False) is not None
        self.flag_status.configure(text=('Defined for this ideology' if explicit else 'Uses base flag fallback')+(' — draft' if ideology in self.flags else ''))
        if image is not None:
            image=image.resize((328,208),Image.Resampling.NEAREST);photo=ImageTk.PhotoImage(image);self._flag_photos=[photo];self.flag_image.configure(image=photo)
        else:self.flag_image.configure(image='',text='No flag yet. Import one or use a design.')

    def import_flag(self):
        path=filedialog.askopenfilename(parent=self,title='Import flag',filetypes=[('Images','*.tga *.png *.dds *.jpg *.jpeg *.bmp'),('All files','*.*')])
        if path:
            try:
                with Image.open(path) as image:self.flags[self.flag_ideology.get()]=image.convert('RGB')
                self.flag_preview()
            except OSError as exc:messagebox.showerror('Flag',str(exc),parent=self)

    def use_design(self,image):self.flags[self.flag_ideology.get()]=image;self.flag_preview()

    def bulk_flags(self,undefined):
        image=self.current_flag()
        if image is None:messagebox.showerror('Flag','Import or create a flag first.',parent=self);return
        for i in self.countries.ideologies():
            if not undefined or i not in self.flags and self.countries.flag(self.tag.get(),i,False) is None:self.flags[i]=image.copy()
        self.flag_preview()

    def build_leaders(self):
        frame=self.frames['leaders'];self.leader_rows=table(frame,[('leader','Active / last promoted leader',340),('others','Other recruited candidates',290)])
        buttons(frame,[('Assign / quickly create leader',self.add_leader),('Open in character database',self.edit_character)])
        ttk.Label(frame,text='Leaders are native character definitions. Assignment recruits the character and explicitly promotes the selected subideology; other roles and countries remain intact.').pack(anchor='w',pady=8)
        self.leaders_loaded=False

    def refresh_leaders(self):
        self.leader_rows.delete(*self.leader_rows.get_children());people=self.store.characters();self.leader_map=self.countries.leaders(self.tag.get())
        for choice in ChoiceIndex(self.ideology_choices()).choices:
            rows=self.leader_map.get(choice.code,[]);labels=[Choice(k,people[k].name).label for k,_ in rows]
            self.leader_rows.insert('','end',iid=choice.code,text=choice.label,values=(labels[-1] if labels else 'No defined leader',', '.join(labels[:-1])))
        self.leaders_loaded=True

    def add_leader(self):
        if not self.ensure_country():return
        selected=next(iter(self.leader_rows.selection()),self.ruling.get())
        dialog=LeaderDialog(self,self.countries,self.tag.get(),selected);self.wait_window(dialog);self.grab_set();self.refresh_leaders()

    def edit_character(self):
        selected=self.leader_rows.selection()
        if not selected:return
        rows=self.leader_map.get(selected[0],[])
        if not rows:return
        dialog=CharacterDialog(self,self.store,rows[-1][0]);self.wait_window(dialog);self.grab_set();self.refresh_leaders()

    def build_tech(self):
        frame=self.frames['tech'];self.tech_values=dict(self.data.technologies)
        self.tech_rows=table(frame,[('level','Level',120)])
        line=ttk.Frame(frame);line.pack(fill='x',pady=8);self.tech=tk.StringVar();self.tech_level=tk.StringVar(value='1')
        self.tech_box=ChoiceBox(line,textvariable=self.tech,values=self.countries.choices('technologies'),width=65);self.tech_box.pack(side='left',fill='x',expand=True)
        ttk.Entry(line,textvariable=self.tech_level,width=10).pack(side='left',padx=8)
        ttk.Button(line,text='Add / update',command=self.add_tech).pack(side='left');ttk.Button(line,text='Remove selected',command=self.remove_tech).pack(side='left',padx=6)
        self.tech_rows.bind('<<TreeviewSelect>>',self.pick_tech)
        self.tech_rows.bind('<KeyPress>',lambda e:self.type_choice(e,self.tech_box))
        ttk.Label(frame,text='These are unconditional starting technologies. Existing dated and DLC/conditional technology scripts are preserved.').pack(anchor='w',pady=8);self.refresh_tech()

    def refresh_tech(self):
        self.tech_rows.delete(*self.tech_rows.get_children());loc=self.store.trait_store.names()
        for choice in ChoiceIndex(Choice(k,loc.get(k,k)) for k in self.tech_values).choices:self.tech_rows.insert('','end',iid=choice.code,text=choice.label,values=(self.tech_values[choice.code],))

    def add_tech(self):
        try:
            self.tech_box.commit();key=self.tech.get()
            if key not in self.countries.technologies():raise ValueError('Choose a defined technology')
            self.tech_values[key]=number(self.tech_level.get(),0,100);self.refresh_tech()
        except ValueError as exc:messagebox.showerror('Technology',str(exc),parent=self)

    def remove_tech(self):
        for key in self.tech_rows.selection():self.tech_values.pop(key,None)
        self.refresh_tech()

    def pick_tech(self,event=None):
        if rows:=self.tech_rows.selection():self.tech.set(rows[0]);self.tech_level.set(self.tech_values[rows[0]])

    def build_spirits(self):
        frame=self.frames['spirits'];self.spirit_values=set(self.data.ideas);self.spirit_rows=table(frame)
        line=ttk.Frame(frame);line.pack(fill='x',pady=8);self.spirit=tk.StringVar();self.spirit_box=ChoiceBox(line,textvariable=self.spirit,values=self.countries.choices('spirits'));self.spirit_box.pack(side='left',fill='x',expand=True)
        for text,command in [('Add',self.add_spirit),('Remove selected',self.remove_spirit),('New spirit',lambda:self.spirit_dialog()),('Edit definition',self.edit_spirit)]:ttk.Button(line,text=text,command=command).pack(side='left',padx=5)
        self.spirit_rows.bind('<<TreeviewSelect>>',lambda e:self.spirit.set(next(iter(self.spirit_rows.selection()),'')))
        self.spirit_rows.bind('<Double-1>',lambda e:self.edit_spirit());self.spirit_rows.bind('<KeyPress>',lambda e:self.type_choice(e,self.spirit_box))
        ttk.Label(frame,text='Editing a spirit changes its shared native definition for every country using it. Create a new spirit for a country-specific effect.').pack(anchor='w',pady=8);self.refresh_spirits()

    def refresh_spirits(self):
        self.spirit_rows.delete(*self.spirit_rows.get_children());loc=self.store.localisations()
        for choice in ChoiceIndex(Choice(k,loc.get(k,k)) for k in self.spirit_values).choices:self.spirit_rows.insert('','end',iid=choice.code,text=choice.label)
        self.spirit_box.configure(values=self.countries.choices('spirits'))

    def add_spirit(self):
        self.spirit_box.commit();key=self.spirit.get()
        if key in self.countries.ideas():self.spirit_values.add(key);self.refresh_spirits()

    def remove_spirit(self):
        for key in self.spirit_rows.selection():self.spirit_values.discard(key)
        self.refresh_spirits()

    def edit_spirit(self):
        key=next(iter(self.spirit_rows.selection()),self.spirit.get())
        if key in self.countries.ideas():self.spirit_dialog(key)

    def spirit_dialog(self,key=None):
        dialog=SpiritDialog(self,self.countries,key);self.wait_window(dialog);self.grab_set()
        if dialog.result:self.spirit_values.add(dialog.result)
        self.refresh_spirits()

    @staticmethod
    def type_choice(event,box):
        if event.char and event.char.isprintable():box.focus_set();box.display.set(event.char);box.typed();return 'break'

    def tab_changed(self,event=None):
        if not hasattr(self,'leader_rows'):return
        if self.tabs.select()==str(self.frames['summary']):self.refresh_summary()
        if self.tabs.select()==str(self.frames['leaders']) and not self.leaders_loaded:self.refresh_leaders()
        if self.tabs.select()==str(self.frames['names']):
            if (self.names['']['name'] or '')!=self.base_name.get():self.names['']['name']=self.base_name.get();self.refresh_names();self.names_table.selection_set('base');self.load_name()

    def collect(self):
        for box in self.boxes:box.commit()
        if (self.names['']['name'] or '')!=self.base_name.get():self.names['']['name']=self.base_name.get()
        self.data.tag=self.tag.get().strip();self.data.capital=self.capital.get();self.data.stability=self.stability.get();self.data.war_support=self.war.get();self.data.ruling=self.ruling.get()
        self.data.popularities={i:v.get() for i,v in self.pop.items()};self.data.technologies=dict(self.tech_values);self.data.ideas=set(self.spirit_values);self.data.laws={k:v.get() for k,v in self.laws.items()}
        self.data.portrait_group=None if self.portrait_group.get()=='__keep__' else self.portrait_group.get()
        return self.data

    def apply_country(self):
        data=self.collect()
        try:self.countries.apply(data,self.color.get(),self.names,self.flags,self.new)
        except CountrySourceExists as exc:
            if not messagebox.askyesno('Overwrite country sources?',
                'These country files already exist:\n\n'+'\n'.join(exc.paths)+'\n\nOverwrite their country setup with the values in this form? Unrelated and dated script is preserved. Changes remain drafts until Save, which creates backups.',parent=self,default='no'):return False
            self.countries.apply(data,self.color.get(),self.names,self.flags,self.new,overwrite=True)
        self.new=False;self.tag_entry.configure(state='disabled')
        applied=self.countries.read(data.tag)
        self._updating_pop=True
        try:
            for ideology,var in self.pop.items():var.set(applied.popularities.get(ideology,'0'))
        finally:self._updating_pop=False
        self.color.set(self.hex(self.app.world.country_colours().get(data.tag,(70,120,180))))
        self.draw_pie()
        return True

    def ensure_country(self):
        if not self.new:return True
        try:return self.apply_country()
        except (ValueError,OSError,InvalidOperation) as exc:messagebox.showerror('Country setup',str(exc),parent=self);return False

    def ok(self):
        try:
            if self.apply_country():self.accept(self.tag.get())
        except (ValueError,OSError,InvalidOperation,KeyError) as exc:messagebox.showerror('Country',str(exc),parent=self)


class FlagLibraryPicker(tk.Toplevel):
    """Read-only, virtual thumbnail grid; selection applies only on acceptance."""
    TILE_W, TILE_H = 164, 126
    THUMB = (144,92)
    BATCH = 6

    def __init__(self,designer,kind):
        # Validate colors before creating a modal window, avoiding stranded grabs.
        colors=[v.get() for v in designer.colors];tint=designer.tint.get()
        scale=float(number(designer.scale.get(),Decimal('.05'),Decimal('1.5')))
        # A 1x1 probe collapses small checkerboard cells into inverted rectangles.
        render_flag(designer.pattern.get(),colors,None,tint,self.THUMB,scale)
        symbols=designer.symbol_specs(skip_index=designer.active_symbol_index() if kind=='emblem' else None)
        previous=designer.grab_current()
        super().__init__(designer)
        self._previous_grab=previous
        self.designer,self.kind=designer,kind;self.result=None
        self.colors,self.tint,self.scale=colors,tint,scale
        self.symbols,self.active=symbols,designer.active_symbol_index()
        self.pattern=designer.pattern.get();self.emblem=designer.emblem.get()
        self.selected=self.pattern if kind=='background' else self.emblem
        choices=[Choice(p,p) for p in PATTERNS] if kind=='background' else designer.store.emblem_choices()
        self.index=ChoiceIndex(choices);self.by_code=self.index.by_code
        self.query=tk.StringVar();self.group=tk.StringVar(value='All')
        self.photos=OrderedDict();self.masks=OrderedDict();self.failures={}
        self._render_job=self._search_job=None;self._queue=[];self._items={};self._first_view=True
        self.title('Flag backgrounds' if kind=='background' else 'Flag emblems')
        self.geometry('1100x760');self.minsize(800,560)
        self.transient(designer.winfo_toplevel());self.grab_set();self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.bind('<Escape>',lambda event:self.destroy())
        top=ttk.Frame(self,padding=10);top.pack(fill='x')
        ttk.Label(top,text='Search name or code:').pack(side='left')
        self.search=ttk.Entry(top,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True,padx=8)
        self.search.bind('<KeyRelease>',self.schedule_search);self.search.bind('<Return>',self.search_accept)
        if kind=='emblem':
            self.group_box=ChoiceBox(top,textvariable=self.group,values=['All','Stellaris masks','Native imports','EU4 imports','No emblem'],width=18)
            self.group_box.pack(side='left');self.group_box.bind('<<ComboboxSelected>>',lambda event:self.refresh())
        ttk.Label(self,text='Click a thumbnail to preview. Double-click, press Enter, or use the selection button to apply.',padding=(10,0,10,8)).pack(anchor='w')
        body=ttk.Frame(self,padding=(10,0,10,10));body.pack(fill='both',expand=True)
        gallery=ttk.Frame(body);gallery.pack(side='left',fill='both',expand=True)
        self.canvas=tk.Canvas(gallery,background='#e9e9e9',highlightthickness=0,yscrollincrement=self.TILE_H//3,takefocus=True)
        scroll=ttk.Scrollbar(gallery,command=self.scroll);self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda event:self.layout())
        self.canvas.bind('<Button-1>',self.click);self.canvas.bind('<Double-1>',self.double_click)
        for key,delta in [('<Left>',-1),('<Right>',1),('<Up>',-100),('<Down>',100)]:self.canvas.bind(key,lambda event,d=delta:self.step(d))
        self.canvas.bind('<Return>',lambda event:self.accept())
        self.canvas.bind('<KeyPress>',self.type_search,add='+')
        self.bind('<MouseWheel>',self.wheel);self.bind('<Button-4>',self.wheel);self.bind('<Button-5>',self.wheel)
        side=ttk.Frame(body,padding=(12,0,0,0),width=286);side.pack(side='right',fill='y')
        ttk.Label(side,text='Flag preview',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,10))
        self.preview_label=ttk.Label(side);self.preview_label.pack()
        self.selection_label=ttk.Label(side,wraplength=270,justify='left');self.selection_label.pack(fill='x',pady=12)
        ttk.Label(side,text='Previews use your current background colors, emblem tint and emblem size.',wraplength=270).pack(anchor='w',pady=(0,12))
        self.use_button=ttk.Button(side,text='Use selected background' if kind=='background' else 'Use selected emblem',command=self.accept);self.use_button.pack(fill='x',pady=4)
        ttk.Button(side,text='Cancel',command=self.destroy).pack(fill='x',pady=4)
        self.count=ttk.Label(self,padding=(10,0,10,8));self.count.pack(anchor='w')
        self.columns=1;self.matches=[];self.refresh();self.update_preview()
        self.search.focus_set()

    @staticmethod
    def source(code):
        if not code:return 'No emblem'
        if code.startswith('mask:'):return 'Stellaris masks'
        if code.startswith('file:'):return 'EU4 imports'
        return 'Native imports'

    def mask(self,code):
        if not code:return None
        if code not in self.masks:
            mask=self.designer.store.emblem_mask(code)
            if mask is not None:
                mask=mask.copy();mask.thumbnail((384,384),Image.Resampling.LANCZOS)
            self.masks[code]=mask
            if len(self.masks)>96:self.masks.popitem(last=False)
        self.masks.move_to_end(code)
        return self.masks[code]

    def flag_image(self,code,size):
        pattern=code if self.kind=='background' else self.pattern
        symbols=[dict(s) for s in self.symbols]
        if self.kind=='emblem':symbols[self.active]['mask']=self.mask(code)
        return render_flag(pattern,self.colors,size=size,symbols=symbols)

    def schedule_search(self,event=None):
        if event is not None and event.keysym in {'Return','Escape','Up','Down','Left','Right'}:return
        if self._search_job is not None:self.after_cancel(self._search_job)
        self._search_job=self.after(100,self.refresh)

    def refresh(self):
        if self._search_job is not None:self.after_cancel(self._search_job);self._search_job=None
        self.matches=[c for c in self.index.matching(self.query.get()) if self.kind=='background' or self.group.get()=='All' or self.source(c.code)==self.group.get()]
        self.canvas.yview_moveto(0);self.layout()
        self.count.configure(text=f'{len(self.matches)} '+('backgrounds' if self.kind=='background' else 'emblems'))

    def layout(self):
        self.columns=max(1,self.canvas.winfo_width()//self.TILE_W)
        height=max(1,((len(self.matches)+self.columns-1)//self.columns)*self.TILE_H)
        self.canvas.configure(scrollregion=(0,0,self.columns*self.TILE_W,height))
        if self._first_view and self.canvas.winfo_height()>1:
            self._first_view=False;self.reveal_selected()
        self.schedule_visible()

    def schedule_visible(self):
        if self._render_job is not None:self.after_cancel(self._render_job)
        self._render_job=self.after_idle(self.draw_visible)

    def draw_visible(self):
        self._render_job=None;self._queue=[];self._items={};self.canvas.delete('tile')
        first=max(0,int(self.canvas.canvasy(0))//self.TILE_H-1)*self.columns
        rows=self.canvas.winfo_height()//self.TILE_H+3
        stop=min(len(self.matches),first+rows*self.columns)
        for index in range(first,stop):
            choice=self.matches[index];x=(index%self.columns)*self.TILE_W+8;y=(index//self.columns)*self.TILE_H+6
            border='#2678c4' if choice.code==self.selected else '#c6c6c6'
            self.canvas.create_rectangle(x-3,y-3,x+149,y+116,fill='#dcecff' if choice.code==self.selected else '#f7f7f7',outline=border,width=2,tags='tile')
            image=self.canvas.create_image(x+72,y+46,tags='tile')
            label=self.canvas.create_text(x+72,y+102,text=self.tile_label(choice),width=148,font=('Segoe UI',9),tags='tile')
            self._items[choice.code]=(image,label)
            if choice.code in self.photos:
                self.photos.move_to_end(choice.code);self.canvas.itemconfigure(image,image=self.photos[choice.code])
            elif choice.code in self.failures:self.canvas.itemconfigure(label,text=self.tile_label(choice,True),fill='#a33030')
            else:self._queue.append(choice.code)
        if not self.matches:self.canvas.create_text(16,20,anchor='nw',text='No matching images.',tags='tile')
        if self._queue:self._render_job=self.after(1,self.render_batch)

    def render_batch(self):
        self._render_job=None
        batch,self._queue=self._queue[:self.BATCH],self._queue[self.BATCH:]
        for code in batch:
            try:
                photo=ImageTk.PhotoImage(self.flag_image(code,self.THUMB));self.photos[code]=photo
                if len(self.photos)>128:self.photos.popitem(last=False)
                self.canvas.itemconfigure(self._items[code][0],image=photo)
            except (OSError,ValueError,KeyError) as exc:
                self.failures[code]=str(exc);self.canvas.itemconfigure(self._items[code][1],text=self.tile_label(self.by_code[code],True),fill='#a33030')
        if self._queue:self._render_job=self.after(1,self.render_batch)

    @staticmethod
    def tile_label(choice,unavailable=False):
        text=choice.name.replace('\n',' ')
        if unavailable:return text[:20]+'\n(unavailable)'
        return text if len(text)<=34 else text[:31]+'…'

    def update_preview(self):
        choice=self.by_code.get(self.selected)
        if choice is None:self.use_button.configure(state='disabled');return
        label=choice.name+'\nEU4 import: '+Path(choice.code[5:]).name if choice.code.startswith('file:') else choice.label
        self.selection_label.configure(text=label)
        try:
            self.preview_photo=ImageTk.PhotoImage(self.flag_image(choice.code,(268,170)))
            self.preview_label.configure(image=self.preview_photo,text='');self.use_button.configure(state='normal')
        except (OSError,ValueError,KeyError) as exc:
            self.preview_label.configure(image='',text='Image unavailable');self.selection_label.configure(text=label+'\n'+str(exc));self.use_button.configure(state='disabled')

    def select(self,code):
        if code not in self.by_code:return
        self.selected=code;self.update_preview();self.schedule_visible()

    def index_at(self,event):
        index=int(self.canvas.canvasy(event.y))//self.TILE_H*self.columns+int(self.canvas.canvasx(event.x))//self.TILE_W
        return index if 0<=index<len(self.matches) and 0<=event.x<self.columns*self.TILE_W else None

    def click(self,event):
        index=self.index_at(event)
        if index is not None:self.select(self.matches[index].code);self.canvas.focus_set()

    def double_click(self,event):
        if self.index_at(event) is not None:self.click(event);self.accept()

    def reveal_selected(self):
        index=next((i for i,c in enumerate(self.matches) if c.code==self.selected),None)
        if index is None:return
        top=index//self.columns*self.TILE_H;visible=self.canvas.canvasy(0);height=self.canvas.winfo_height()
        if top<visible or top+self.TILE_H>visible+height:
            total=max(self.TILE_H,((len(self.matches)+self.columns-1)//self.columns)*self.TILE_H)
            self.canvas.yview_moveto(top/total)

    def step(self,delta):
        if not self.matches:return 'break'
        if abs(delta)==100:delta=self.columns*(1 if delta>0 else -1)
        index=next((i for i,c in enumerate(self.matches) if c.code==self.selected),0)
        self.select(self.matches[max(0,min(len(self.matches)-1,index+delta))].code);self.reveal_selected()
        return 'break'

    def type_search(self,event):
        if event.char and event.char.isprintable():self.query.set(event.char);self.search.focus_set();self.search.icursor('end');self.schedule_search();return 'break'

    def search_accept(self,event=None):
        self.refresh()
        code=self.index.preferred(self.query.get(),self.matches) if self.query.get() else self.selected
        if code in {c.code for c in self.matches}:self.select(code);self.accept()
        return 'break'

    def scroll(self,*args):self.canvas.yview(*args);self.schedule_visible()

    def wheel(self,event):
        delta=-1 if getattr(event,'delta',0)>0 or getattr(event,'num',None)==4 else 1
        self.canvas.yview_scroll(delta*3,'units');self.schedule_visible();return 'break'

    def accept(self):
        if self.selected in self.by_code and str(self.use_button.cget('state'))!='disabled':self.result=self.selected;self.destroy()

    def destroy(self):
        for job in (self._render_job,self._search_job):
            if job is not None:self.after_cancel(job)
        self._render_job=self._search_job=None
        super().destroy()
        try:
            if self._previous_grab is not None and self._previous_grab.winfo_exists() and self._previous_grab.winfo_viewable():self._previous_grab.grab_set()
        except tk.TclError:pass  # The owning window may itself be closing.


class LeaderDialog(DraftDialog):
    def __init__(self,parent,store,tag,group):
        super().__init__(parent,store.characters,'Assign or create party leader');self.country_store=store;self.tag=tag
        self.geometry('850x570');self.mode=tk.StringVar(value='Existing character');self.key=tk.StringVar();self.name=tk.StringVar();self.subtype=tk.StringVar(value=next(iter(store.ideologies()[group]['types']),''));self.portrait=tk.StringVar()
        form=ttk.Frame(self,padding=12);form.pack(fill='both',expand=True);form.columnconfigure(1,weight=1)
        for row,(label,var) in enumerate([('Action',self.mode),('Existing character',self.key),('New character name',self.name),('Leader subideology',self.subtype),('Portrait pair (optional)',self.portrait)]):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=8)
            if var is self.mode:widget=ChoiceBox(form,textvariable=var,values=['Existing character','Create new character'])
            elif var is self.key:widget=ChoiceBox(form,textvariable=var,values=[Choice(k,c.name) for k,c in store.characters.characters().items()],allow_custom=True)
            elif var is self.subtype:widget=ChoiceBox(form,textvariable=var,values=[Choice(k,store.characters.trait_store.names().get(k,k)) for k in store.ideologies()[group]['types']])
            elif var is self.portrait:widget=ChoiceBox(form,textvariable=var,values=[Choice('','Keep current / none')]+[Choice(k,k) for k in store.characters.portraits()])
            else:widget=ttk.Entry(form,textvariable=var)
            widget.grid(row=row,column=1,sticky='ew',padx=10)
        ttk.Label(form,text='For a new character, type its unique code in the character field above.').grid(row=5,column=0,columnspan=2,sticky='w')
        ttk.Label(form,text='Description').grid(row=6,column=0,sticky='nw',pady=8);self.desc=tk.Text(form,height=7);self.desc.grid(row=6,column=1,sticky='nsew',padx=10);form.rowconfigure(6,weight=1)
        buttons(self,[('Assign leader',self.ok),('Cancel',self.cancel)])

    def ok(self):
        try:
            for widget in self.winfo_children()[0].winfo_children():
                if isinstance(widget,ChoiceBox):widget.commit()
            self.country_store.set_leader(self.tag,self.key.get(),self.subtype.get(),self.name.get() if self.mode.get()=='Create new character' else None,self.desc.get('1.0','end-1c'),self.portrait.get())
            self.accept(self.key.get())
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Leader',str(exc),parent=self)


class IconPicker(DraftDialog):
    def __init__(self,parent,store):
        super().__init__(parent,store.characters,'National spirit icons: mod, vanilla and EaW');self.country_store=store
        self.geometry('900x700');self.query=tk.StringVar();self.photos={};self._job=None
        bar=ttk.Frame(self,padding=10);bar.pack(fill='x');ttk.Label(bar,text='Search name / sprite / source:').pack(side='left')
        search=ttk.Entry(bar,textvariable=self.query);search.pack(side='left',fill='x',expand=True,padx=8);search.bind('<KeyRelease>',lambda e:self.refresh())
        filters=ttk.Frame(self,padding=(10,0,10,6));filters.pack(fill='x');self.sources={};self.source_checks={}
        for source in ('Mod','Vanilla','EaW'):
            self.sources[source]=tk.BooleanVar(value=getattr(store,'spirit_icon_sources',{}).get(source,True))
            button=ttk.Checkbutton(filters,text=source,variable=self.sources[source],command=self.filter_sources)
            button.pack(side='left',padx=(0,12));self.source_checks[source]=button
        self.count=tk.StringVar();ttk.Label(filters,textvariable=self.count).pack(side='right')
        ttk.Style(self).configure('CountryIcons.Treeview',rowheight=48)
        self.tree=table(self,[('origin','Source',100),('texture','Texture',340)]);self.tree.configure(style='CountryIcons.Treeview')
        self.tree.bind('<Double-1>',lambda e:self.ok());self.tree.bind('<Configure>',lambda e:self.schedule_images())
        self.tree.bind('<MouseWheel>',lambda e:self.schedule_images(),add='+')
        self.search=search;self.tree.bind('<KeyPress>',self.type_search)
        original=self.tree.cget('yscrollcommand');self.tree.configure(yscrollcommand=lambda a,b:(self.tk.call(original,a,b),self.schedule_images()))
        buttons(self,[('Import icon…',self.import_icon),('Use selected icon',self.ok),('Cancel',self.cancel)]);self.refresh()

    def import_icon(self):
        key=import_spirit_icon(self,self.country_store)
        if key is not None:
            self.sources[self.country_store.icon_catalog()[key]['origin']].set(True);self.query.set('');self.refresh()
            self.tree.selection_set(key);self.tree.see(key);self.schedule_images()

    def refresh(self):
        self.tree.delete(*self.tree.get_children());self.photos={};catalog=self.country_store.spirit_icon_catalog()
        catalog={k:v for k,v in catalog.items() if self.sources[v['origin']].get()}
        index=ChoiceIndex(Choice(k,v['choice'].name+' '+v['origin']) for k,v in catalog.items())
        for choice in index.matching(self.query.get()):
            item=catalog[choice.code];self.tree.insert('','end',iid=choice.code,text=item['choice'].label,values=(item['origin'],item['texture']))
        self.count.set(str(len(self.tree.get_children()))+' icons')
        self.schedule_images()

    def filter_sources(self):
        self.country_store.spirit_icon_sources={source:variable.get() for source,variable in self.sources.items()}
        self.refresh()

    def schedule_images(self):
        if self._job is None:self._job=self.after(35,self.load_images)

    def type_search(self,event):
        if event.char and event.char.isprintable():self.query.set(event.char);self.search.focus_set();self.search.icursor('end');self.refresh();return 'break'

    def destroy(self):
        if self._job is not None:self.after_cancel(self._job);self._job=None
        super().destroy()

    def load_images(self):
        self._job=None;seen=set()
        for y in range(0,self.tree.winfo_height(),22):
            key=self.tree.identify_row(y)
            if not key or key in seen:continue
            seen.add(key)
            if key not in self.photos:
                image=spirit_icon_preview(self.country_store,key)
                if image is not None:self.photos[key]=ImageTk.PhotoImage(image);self.tree.item(key,image=self.photos[key])
        if len(self.photos)>160:
            for key in list(self.photos):
                if key not in seen:self.tree.item(key,image='');self.photos.pop(key)

    def ok(self):
        if rows:=self.tree.selection():self.accept(rows[0])


class SpiritDialog(DraftDialog):
    def __init__(self,parent,store,key=None):
        super().__init__(parent,store.characters,'National spirit');self.countries=store;self.new=key is None;self.geometry('1000x760')
        self.key=tk.StringVar(value=key or '');self.name=tk.StringVar(value=store.characters.localisations().get(key,key or ''));self.icon=tk.StringVar()
        self.effects={};self.percent=None
        description=''
        if key:
            category,path,text,node=store.ideas()[key];description=store.characters.localisations().get(key+'_desc','');picture=atom(text,node.children,'picture',key);candidate='GFX_idea_'+picture
            self.icon.set(candidate if candidate in store.icon_catalog() else 'vanilla:'+candidate if 'vanilla:'+candidate in store.icon_catalog() else '')
            modifier=block(node.children,'modifier');self.effects={c.key:value(text,c) for c in modifier.children if c.children is None} if modifier else {}
        form=ttk.Frame(self,padding=10);form.pack(fill='x');form.columnconfigure(1,weight=1)
        for row,(label,var) in enumerate([('Native spirit ID',self.key),('Localized name',self.name),('Icon sprite',self.icon)]):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=5)
            if var is self.icon:
                box=ChoiceBox(form,textvariable=var,values=spirit_icon_choices(store));box.grid(row=row,column=1,sticky='ew',padx=8);self.icon_box=box
                ttk.Button(form,text='Browse all icons…',command=self.pick_icon).grid(row=row,column=2)
                ttk.Button(form,text='Import icon…',command=self.import_icon).grid(row=row,column=3,padx=(6,0))
            else:
                entry=ttk.Entry(form,textvariable=var);entry.grid(row=row,column=1,sticky='ew',padx=8)
                if var is self.key and not self.new:entry.configure(state='disabled')
        self.icon_preview=ttk.Label(form);self.icon_preview.grid(row=3,column=2,padx=5)
        self.icon.trace_add('write',lambda *args:self.preview_icon());self.preview_icon()
        ttk.Label(form,text='Description').grid(row=3,column=0,sticky='nw',pady=5);self.desc=tk.Text(form,height=4,wrap='word');self.desc.grid(row=3,column=1,sticky='ew',padx=8);self.desc.insert('1.0',description)
        self.research_bonuses,self.equipment_bonuses=store.spirit_bonuses(key)
        self.bonus_tabs=ttk.Notebook(self);self.bonus_tabs.pack(fill='both',expand=True,padx=10,pady=8)
        modifier_tab=ttk.Frame(self.bonus_tabs);research_tab=ttk.Frame(self.bonus_tabs);equipment_tab=ttk.Frame(self.bonus_tabs)
        for frame,label in [(modifier_tab,'Modifiers'),(research_tab,'Research bonuses'),(equipment_tab,'Equipment bonuses')]:self.bonus_tabs.add(frame,text=label)
        self.rows=table(modifier_tab,[('value','Value (game units)',170)])
        line=ttk.Frame(modifier_tab,padding=10);line.pack(fill='x');self.modifier=tk.StringVar();self.amount=tk.StringVar(value='.1')
        self.modifier_box=ChoiceBox(line,textvariable=self.modifier,values=store.characters.trait_store.spirit_modifier_choices());self.modifier_box.pack(side='left',fill='x',expand=True)
        ttk.Entry(line,textvariable=self.amount,width=12).pack(side='left',padx=6);ttk.Button(line,text='Add / update',command=self.add_modifier).pack(side='left');ttk.Button(line,text='Remove',command=self.remove_modifier).pack(side='left',padx=6)
        self.rows.bind('<<TreeviewSelect>>',self.pick_modifier);self.rows.bind('<KeyPress>',lambda e:CountryDialog.type_choice(e,self.modifier_box))
        ttk.Label(modifier_tab,text='Modifier values use game units (usually 0.1 = 10%; Boolean modifiers also accept yes/no). Existing conditions, on-add effects and nested modifier blocks are preserved.',wraplength=950,padding=10).pack(anchor='w')
        self.build_bonus_tabs(research_tab,equipment_tab)
        buttons(self,[('Apply spirit',self.ok),('Cancel',self.cancel)]);self.refresh()

    def build_bonus_tabs(self,research_tab,equipment_tab):
        self.research_key=tk.StringVar();self.research_amount=tk.StringVar(value='.1')
        self.research_rows=table(research_tab,[('value','Research bonus (game units)',180)])
        self.research_rows.bind('<<TreeviewSelect>>',self.pick_research_bonus)
        line=ttk.Frame(research_tab,padding=10);line.pack(fill='x')
        choices=list(self.countries.bonus_choices('research'));known={c.code for c in choices}
        choices.extend(Choice(k,k) for k in self.research_bonuses if k not in known)
        self.research_box=ChoiceBox(line,textvariable=self.research_key,values=choices);self.research_box.pack(side='left',fill='x',expand=True)
        ttk.Entry(line,textvariable=self.research_amount,width=12).pack(side='left',padx=6)
        ttk.Button(line,text='Add / update',command=self.add_research_bonus).pack(side='left');ttk.Button(line,text='Remove',command=self.remove_research_bonus).pack(side='left',padx=6)
        ttk.Label(research_tab,text='Choose a technology category. Use native values: 0.1 gives a 10% research bonus.',padding=10,wraplength=950).pack(anchor='w')
        self.equipment_key=tk.StringVar();self.equipment_stat=tk.StringVar();self.equipment_amount=tk.StringVar(value='.1');self.equipment_instant=tk.StringVar(value='yes')
        self.equipment_rows=table(equipment_tab,[('stat','Equipment stat',260),('value','Bonus (game units)',130),('instant','Apply immediately',140)])
        self.equipment_rows.bind('<<TreeviewSelect>>',self.pick_equipment_bonus)
        line=ttk.Frame(equipment_tab,padding=10);line.pack(fill='x')
        choices=list(self.countries.bonus_choices('equipment'));known={c.code for c in choices}
        choices.extend(Choice(k,k) for k in self.equipment_bonuses if k not in known)
        self.equipment_box=ChoiceBox(line,textvariable=self.equipment_key,values=choices,width=40);self.equipment_box.pack(side='left',fill='x',expand=True)
        choices=list(self.countries.bonus_choices('stats'));known={c.code for c in choices}
        existing={stat for fields in self.equipment_bonuses.values() for stat in fields if stat!='instant'}
        choices.extend(Choice(k,k) for k in existing if k not in known)
        self.equipment_stat_box=ChoiceBox(line,textvariable=self.equipment_stat,values=choices,width=30);self.equipment_stat_box.pack(side='left',fill='x',expand=True,padx=6)
        ttk.Entry(line,textvariable=self.equipment_amount,width=10).pack(side='left')
        line=ttk.Frame(equipment_tab,padding=(10,0,10,4));line.pack(fill='x')
        ttk.Label(line,text='When to apply:').pack(side='left',padx=(0,6))
        self.instant_box=ChoiceBox(line,textvariable=self.equipment_instant,values=[Choice('','Native default (new variants)'),Choice('yes','Immediately'),Choice('no','New variants only')],width=32);self.instant_box.pack(side='left')
        ttk.Button(line,text='Add / update',command=self.add_equipment_bonus).pack(side='left',padx=6);ttk.Button(line,text='Remove',command=self.remove_equipment_bonus).pack(side='left')
        self._equipment_target=None;self.equipment_key.trace_add('write',lambda *args:self.load_equipment_instant())
        ttk.Label(equipment_tab,text='Choose equipment and a stat. Values use native game units; negative build_cost_ic reduces cost. Without instant, bonuses apply when a new equipment variant is created.',padding=10,wraplength=950).pack(anchor='w')
        self.refresh_bonus_tables()

    def refresh_bonus_tables(self):
        self.research_rows.delete(*self.research_rows.get_children())
        for key,raw in sorted(self.research_bonuses.items()):
            choice=self.research_box.index.by_code.get(key,Choice(key,key))
            self.research_rows.insert('','end',iid=key,text=choice.label,values=(raw,))
        self.equipment_rows.delete(*self.equipment_rows.get_children());self.equipment_row_keys={}
        for eq,fields in sorted(self.equipment_bonuses.items()):
            for stat,raw in sorted(fields.items()):
                if stat=='instant':continue
                key=str(len(self.equipment_row_keys));self.equipment_row_keys[key]=(eq,stat)
                choice=self.equipment_box.index.by_code.get(eq,Choice(eq,eq));stat_choice=self.equipment_stat_box.index.by_code.get(stat,Choice(stat,stat))
                self.equipment_rows.insert('','end',iid=key,text=choice.label,values=(stat_choice.label,raw,fields.get('instant','Default')))

    def pick_research_bonus(self,event=None):
        if rows:=self.research_rows.selection():
            self.research_key.set(rows[0]);self.research_amount.set(self.research_bonuses[rows[0]])

    def add_research_bonus(self):
        try:
            self.research_box.commit();key=self.research_key.get()
            if key not in self.research_box.index.by_code:raise ValueError('Choose a research category')
            self.research_bonuses[key]=number(self.research_amount.get());self.refresh_bonus_tables()
        except ValueError as exc:messagebox.showerror('Research bonus',str(exc),parent=self)

    def remove_research_bonus(self):
        for key in self.research_rows.selection():self.research_bonuses.pop(key,None)
        self.refresh_bonus_tables()

    def load_equipment_instant(self,force=False):
        target=self.equipment_key.get()
        if not force and target==self._equipment_target:return
        self._equipment_target=target;fields=self.equipment_bonuses.get(target)
        self.equipment_instant.set(fields.get('instant','') if fields is not None else 'yes')

    def pick_equipment_bonus(self,event=None):
        if rows:=self.equipment_rows.selection():
            eq,stat=self.equipment_row_keys[rows[0]];self.equipment_key.set(eq);self.equipment_stat.set(stat)
            self.equipment_amount.set(self.equipment_bonuses[eq][stat]);self.load_equipment_instant(force=True)

    def add_equipment_bonus(self):
        try:
            for box in (self.equipment_box,self.equipment_stat_box,self.instant_box):box.commit()
            eq,stat=self.equipment_key.get(),self.equipment_stat.get()
            if eq not in self.equipment_box.index.by_code or stat not in self.equipment_stat_box.index.by_code:raise ValueError('Choose equipment and a stat')
            amount=number(self.equipment_amount.get());fields=dict(self.equipment_bonuses.get(eq,{}));fields[stat]=amount
            if self.equipment_instant.get():fields['instant']=self.equipment_instant.get()
            else:fields.pop('instant',None)
            self.equipment_bonuses[eq]=fields;self.refresh_bonus_tables()
        except ValueError as exc:messagebox.showerror('Equipment bonus',str(exc),parent=self)

    def remove_equipment_bonus(self):
        for row in self.equipment_rows.selection():
            eq,stat=self.equipment_row_keys[row];fields=self.equipment_bonuses[eq];fields.pop(stat,None)
            if not any(k!='instant' for k in fields):self.equipment_bonuses.pop(eq)
        self.refresh_bonus_tables()

    def refresh(self):
        self.rows.delete(*self.rows.get_children());catalog=self.countries.characters.trait_store.modifier_catalog()
        for choice in ChoiceIndex(catalog.get(k,{}).get('choice',Choice(k,k)) for k in self.effects).choices:self.rows.insert('','end',iid=choice.code,text=choice.label,values=(self.effects[choice.code],))

    def preview_icon(self):
        if self.icon.get() in self.countries.icon_catalog():
            image=spirit_icon_preview(self.countries,self.icon.get(),(64,64))
            if image is not None:self.photo=ImageTk.PhotoImage(image);self.icon_preview.configure(image=self.photo);return
        self.icon_preview.configure(image='')

    def add_modifier(self):
        try:
            self.modifier_box.commit();key=self.modifier.get()
            if key not in self.countries.characters.trait_store.modifier_catalog():raise ValueError('Choose a defined modifier')
            self.effects[key]=self.countries.characters.trait_store.modifier_value(key,self.amount.get());self.refresh()
        except ValueError as exc:messagebox.showerror('Modifier',str(exc),parent=self)

    def remove_modifier(self):
        for key in self.rows.selection():self.effects.pop(key,None)
        self.refresh()

    def pick_modifier(self,event=None):
        if rows:=self.rows.selection():self.modifier.set(rows[0]);self.amount.set(self.effects[rows[0]])

    def pick_icon(self):
        dialog=IconPicker(self,self.countries);self.wait_window(dialog);self.grab_set()
        self.icon_box.configure(values=spirit_icon_choices(self.countries))
        if dialog.result:self.icon.set(dialog.result)

    def import_icon(self):
        key=import_spirit_icon(self,self.countries)
        if key is not None:
            self.icon_box.configure(values=spirit_icon_choices(self.countries));self.icon.set(key)

    def ok(self):
        try:
            self.icon_box.commit();self.countries.edit_spirit(self.key.get(),self.name.get(),self.desc.get('1.0','end-1c'),self.icon.get(),self.effects,self.new,research_bonuses=self.research_bonuses,equipment_bonuses=self.equipment_bonuses);self.accept(self.key.get())
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Spirit',str(exc),parent=self)

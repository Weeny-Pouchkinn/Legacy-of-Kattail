"""Land template designer, copy dialog and province division-name editing."""
import tkinter as tk
from tkinter import ttk,messagebox

from character_ui import DraftDialog
from country_ui import table,buttons
from select_ui import Choice,ChoiceBox,ChoiceIndex
from land_oob_model import LAYER


class LandOobControls(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent);self.app=app;self.store=app.land_oob_store
        self.country=tk.StringVar();self.path=tk.StringVar();self.global_view=tk.BooleanVar(value=False)
        self._source_identity=None
        self.action=tk.StringVar(value='Place divisions');self.amount=tk.StringVar(value='1')
        ttk.Label(self,text='Country').pack(anchor='w');self.country_box=ChoiceBox(self,textvariable=self.country,values=self.countries());self.country_box.pack(fill='x')
        self.country_box.bind('<<ComboboxSelected>>',self.country_changed)
        self.source_box=ChoiceBox(self,textvariable=self.path);self.source_box.pack(fill='x',pady=4);self.source_box.bind('<<ComboboxSelected>>',lambda e:self.changed())
        ttk.Checkbutton(self,text='Global view: all nations and templates',variable=self.global_view,command=self.changed).pack(anchor='w')
        for label in ('Place divisions','Edit division names'):ttk.Radiobutton(self,text=label,value=label,variable=self.action,command=self.changed).pack(anchor='w')
        line=ttk.Frame(self);line.pack(fill='x',pady=4);ttk.Label(line,text='Divisions per click').pack(side='left');ttk.Spinbox(line,from_=1,to=1000,textvariable=self.amount,width=7).pack(side='left',padx=8)
        buttons(self,[('Copy template…',self.copy),('Division list…',self.divisions)])
        self.country.set(next((tag for tag in sorted(app.world.country_paths) if self.store.source(tag)),next(iter(app.world.country_paths),'')))
        self.refresh_sources()

    def countries(self):
        chars=self.app.character_store;loc=chars.localisations()
        return ChoiceIndex(Choice(tag,chars.neutral_name(tag,loc)) for tag in self.app.world.country_paths).choices

    def refresh_sources(self):
        self.country_box.configure(values=self.countries())
        if self.country.get() not in self.app.world.country_paths:self.country.set(next(iter(self.app.world.country_paths),''))
        rows=self.store.sources(self.country.get());paths={r.path for r in rows}
        if self.path.get() not in paths:
            previous=next((r for r in rows if (self.country.get(),r.start,r.context)==self._source_identity),None)
            default=previous or self.store.source(self.country.get());self.path.set(default.path if default else rows[0].path if rows else '')
        selected=next((r for r in rows if r.path==self.path.get()),None)
        self._source_identity=(self.country.get(),selected.start,selected.context) if selected else None
        choices=[Choice(r.path,r.path.removeprefix('history/units/')+(' — '+', '.join(r.context) if r.context else '')) for r in rows]
        self.source_box.configure(values=choices,state='normal' if len(paths)>1 else 'disabled')

    def country_changed(self,event=None):
        self.path.set('');self._source_identity=None;self.app.paint_selection[LAYER]='__all__';self.changed()

    def changed(self):
        self.refresh_sources();self.app.refresh_palette();self.app.refresh_map()

    def edit(self,create=False):
        selected=self.app.paint_selection.get(LAYER)
        if not create and (not selected or selected=='__all__'):self.app._status('Select a template to edit');return
        self.open(TemplateDialog,self.country.get(),None if create else selected,self.path.get())

    def copy(self):self.open(CopyTemplateDialog,self.country.get(),self.path.get())

    def divisions(self,province=None):
        self.open(DivisionsDialog,'' if self.global_view.get() else self.country.get(),province,self.path.get())

    def open(self,dialog_type,*args):
        try:
            dialog=dialog_type(self.app.root,self.store,*args);self.wait_window(dialog)
            self.refresh_sources();self.app._sync()
            if dialog.result and isinstance(dialog.result,str):self.app.paint_selection[LAYER]=dialog.result;self.app.refresh_palette();self.app.refresh_map()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Land OOB',str(exc),parent=self.app.root)


class TemplateDialog(DraftDialog):
    def __init__(self,parent,store,tag,name=None,path=''):
        super().__init__(parent,store.characters,'Edit land template' if name else 'New land template')
        self.oob=store;self.tag=tag;self.old_name=name;self.path=path;self.geometry('900x730')
        current=store.templates(tag,path).get(name) if name else None
        self.name=tk.StringVar(value=current.name if current else '');self.short=tk.StringVar(value=current.short if current else '')
        self.values={'regiments':list(current.regiments) if current else [],'support':list(current.support) if current else []}
        frame=ttk.Frame(self,padding=10);frame.pack(fill='x');frame.columnconfigure(1,weight=1)
        for row,(label,var) in enumerate([('Template name',self.name),('Shortened name for divisions',self.short)]):ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',pady=5);ttk.Entry(frame,textvariable=var).grid(row=row,column=1,sticky='ew',padx=8)
        ttk.Label(frame,text='New placements use “1st [state name] [shortened name]”. Existing division names stay unchanged.',wraplength=850).grid(row=2,column=0,columnspan=2,sticky='w',pady=7)
        tabs=ttk.Notebook(self);tabs.pack(fill='both',expand=True,padx=10);self.editors={};units=store.subunits();loc=store.characters.trait_store.names();cw,ch,sw,sh=store.dimensions()
        for key,label,width,height in [('regiments','Combat battalions',cw,ch),('support','Support companies',sw,sh)]:
            page=ttk.Frame(tabs,padding=10);tabs.add(page,text=label);rows=table(page,[('x','Column',90),('y','Row',90)],height=12)
            line=ttk.Frame(page);line.pack(fill='x',pady=7);unit=tk.StringVar();x=tk.StringVar(value='0');y=tk.StringVar(value='0')
            box=ChoiceBox(line,textvariable=unit,values=[Choice(k,loc.get(k,k)) for k,row in units.items() if row['support']==(key=='support')]);box.pack(side='left',fill='x',expand=True)
            for text,var,maximum in [('Column',x,width),('Row',y,height)]:ttk.Label(line,text=text).pack(side='left',padx=5);ttk.Spinbox(line,from_=0,to=maximum-1,textvariable=var,width=4).pack(side='left')
            buttons(page,[('Set cell',lambda key=key:self.set_cell(key)),('Remove selected cell',lambda key=key:self.remove_cell(key))])
            rows.bind('<<TreeviewSelect>>',lambda e,key=key:self.pick_cell(key));self.editors[key]=(rows,box,unit,x,y)
        buttons(self,[('Apply template',self.ok),('Cancel',self.cancel)]);self.refresh()

    def refresh(self):
        loc=self.store.trait_store.names()
        for key,(rows,box,unit,x,y) in self.editors.items():
            rows.delete(*rows.get_children())
            for index,(kind,cx,cy) in enumerate(self.values[key]):rows.insert('','end',iid=str(index),text=Choice(kind,loc.get(kind,kind)).label,values=(cx,cy))

    def pick_cell(self,key):
        rows,box,unit,x,y=self.editors[key]
        if selected:=rows.selection():kind,cx,cy=self.values[key][int(selected[0])];unit.set(kind);x.set(str(cx));y.set(str(cy))

    def set_cell(self,key):
        try:
            rows,box,unit,x,y=self.editors[key];box.commit();cx=int(x.get());cy=int(y.get())
            candidate=[v for v in self.values[key] if v[1:]!=(cx,cy)]+[(unit.get(),cx,cy)]
            # Full validation is also performed when applying the template.
            if unit.get() not in self.oob.subunits():raise ValueError('Choose a defined land subunit')
            self.values[key]=sorted(candidate,key=lambda c:(c[1],c[2]));self.refresh()
        except (ValueError,KeyError) as exc:messagebox.showerror('Template cell',str(exc),parent=self)

    def remove_cell(self,key):
        rows=self.editors[key][0]
        for selected in rows.selection():self.values[key].pop(int(selected))
        self.refresh()

    def ok(self):
        try:
            name=self.oob.edit_template(self.tag,self.name.get().strip(),self.short.get().strip(),self.values['regiments'],self.values['support'],self.old_name,self.path);self.accept(name)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Land template',str(exc),parent=self)


class CopyTemplateDialog(DraftDialog):
    def __init__(self,parent,store,target,path=''):
        super().__init__(parent,store.characters,'Copy land template');self.oob=store;self.target=target;self.path=path;self.geometry('650x330')
        self.country=tk.StringVar();self.source_path=tk.StringVar();self.template=tk.StringVar();self.name=tk.StringVar();self.short=tk.StringVar()
        frame=ttk.Frame(self,padding=12);frame.pack(fill='both',expand=True);frame.columnconfigure(1,weight=1)
        loc=store.characters.localisations();choices=[Choice(tag,store.characters.neutral_name(tag,loc)) for tag in store.world.country_paths]
        for row,(label,var) in enumerate([('Source country',self.country),('Source OOB',self.source_path),('Source template',self.template),('New template name',self.name),('Shortened name',self.short)]):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',pady=7)
            if row<3:
                box=ChoiceBox(frame,textvariable=var,values=choices if row==0 else []);box.grid(row=row,column=1,sticky='ew',padx=8)
                if row==0:self.country_box=box;box.bind('<<ComboboxSelected>>',lambda e:self.country_changed())
                elif row==1:self.source_box=box;box.bind('<<ComboboxSelected>>',lambda e:self.source_changed())
                else:self.template_box=box;box.bind('<<ComboboxSelected>>',lambda e:self.template_changed())
            else:ttk.Entry(frame,textvariable=var).grid(row=row,column=1,sticky='ew',padx=8)
        buttons(self,[('Copy template',self.ok),('Cancel',self.cancel)])

    def country_changed(self):
        sources=self.oob.sources(self.country.get());default=self.oob.source(self.country.get())
        self.source_box.configure(values=[Choice(r.path,r.path.removeprefix('history/units/')+(' — '+', '.join(r.context) if r.context else '')) for r in sources])
        self.source_path.set(default.path if default else sources[0].path if sources else '');self.source_changed()

    def source_changed(self):
        rows=self.oob.templates(self.country.get(),self.source_path.get());self.template_box.configure(values=[Choice(k,k) for k in rows]);self.template.set(next(iter(rows),''));self.template_changed()

    def template_changed(self):
        row=self.oob.templates(self.country.get(),self.source_path.get()).get(self.template.get());self.name.set(row.name if row else '');self.short.set(row.short if row else '')

    def ok(self):
        try:
            self.country_box.commit();self.source_box.commit();self.template_box.commit()
            name=self.oob.copy_template(self.country.get(),self.template.get(),self.target,self.name.get().strip(),self.short.get().strip(),source_path=self.source_path.get(),target_path=self.path);self.accept(name)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Copy template',str(exc),parent=self)


class DivisionsDialog(DraftDialog):
    def __init__(self,parent,store,tag='',province=None,path=''):
        super().__init__(parent,store.characters,'Division names'+(f' — province {province}' if province else ''))
        self.oob=store;self.tag=tag;self.province=province;self.path=path;self.geometry('1050x650');self.name=tk.StringVar()
        source=store.source(tag,path) if tag else None;self.source_identity=(source.start,source.context) if source else None
        self.rows=table(self,[('nation','Country',90),('template','Template',240),('province','Province',85),('state','State',220)],height=17);self.rows.bind('<<TreeviewSelect>>',self.pick)
        line=ttk.Frame(self,padding=10);line.pack(fill='x');ttk.Label(line,text='Division name').pack(side='left');ttk.Entry(line,textvariable=self.name).pack(side='left',fill='x',expand=True,padx=8)
        buttons(self,[('Apply name',self.rename),('Generate name',lambda:self.rename(True)),('Remove selected division',self.remove),('Done',self.accept),('Cancel',self.cancel)]);self.refresh()

    def refresh(self):
        self.rows.delete(*self.rows.get_children());self.values={};loc=self.store.localisations()
        if self.tag and self.path and self.path not in {r.path for r in self.oob.sources(self.tag)}:
            selected=next((r for r in self.oob.sources(self.tag) if (r.start,r.context)==self.source_identity),None)
            self.path=selected.path if selected else ''
        for tag in self.oob.world.countries if not self.tag else [self.tag]:
            for row in self.oob.divisions(tag,self.path if self.tag else ''):
                if self.province is not None and row.province!=self.province:continue
                sid=self.oob.world.province_states.get(row.province);state=self.oob.world.states.get(sid);label=loc.get(state.name,state.name) if state else 'Unknown state'
                iid=self.rows.insert('','end',text=row.name or '(Game-generated name)',values=(tag,row.template,row.province,label));self.values[iid]=(tag,row)

    def selected(self):return self.values.get(next(iter(self.rows.selection()),''))

    def pick(self,event=None):
        if selected:=self.selected():self.name.set(selected[1].name)

    def rename(self,generated=False):
        if not (selected:=self.selected()):return
        tag,row=selected
        try:self.oob.rename(tag,row.index,self.name.get(),row.path,generated=generated);self.refresh()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Division name',str(exc),parent=self)

    def remove(self):
        if not (selected:=self.selected()):return
        tag,row=selected
        try:self.oob.delete_division(tag,row.index,row.path);self.refresh()
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Division',str(exc),parent=self)

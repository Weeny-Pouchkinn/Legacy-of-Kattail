"""Shared generic portrait pools, role/gender selection and image uploads."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import ImageTk

from character_ui import DraftDialog
from country_ui import table, buttons
from select_ui import Choice, ChoiceBox, ChoiceIndex
from generic_portrait_model import ROLES, IDEOLOGIES


class GenericPortraitWorkspace(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,padding=10)
        self.app=app; self.store=app.character_store.generic_portraits
        self.query=tk.StringVar(); self.signature=None
        bar=buttons(self,[('Edit selected group',self.edit)])
        ttk.Label(bar,text='Search species or group:').pack(side='left',padx=10)
        self.search=ttk.Entry(bar,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True)
        self.search.bind('<KeyRelease>',lambda e:self.refresh())
        self.rows=table(self,[('countries','Country tags',600)])
        self.rows.bind('<Double-1>',lambda e:self.edit());self.rows.bind('<Return>',lambda e:self.edit())
        self.rows.bind('<KeyPress>',lambda e:app.search_list(e,self.query,self.search,self.refresh))
        ttk.Label(self,text='Species slots stay available before assignment. Editing shared art updates every country in that group.',wraplength=1000).pack(anchor='w',pady=10)
        self.bind('<Map>',lambda e:self.after_idle(self.refresh))

    def refresh(self):
        if not self.winfo_viewable(): return
        signature=(self.store.docs.revision,self.query.get())
        if signature==self.signature:return
        self.signature=signature
        selected=next(iter(self.rows.selection()),None);self.rows.delete(*self.rows.get_children())
        groups=self.store.groups()
        for choice in ChoiceIndex(Choice(k,g.name) for k,g in groups.items()).matching(self.query.get()):
            self.rows.insert('','end',iid=choice.code,text=choice.label,values=(', '.join(groups[choice.code].tags) or 'No countries assigned',))
        if selected and self.rows.exists(selected):self.rows.selection_set(selected)

    def edit(self):
        if not (selected:=self.rows.selection()):return
        try:
            dialog=GenericPortraitDialog(self,self.app,selected[0]);self.wait_window(dialog)
            self.app._sync();self.signature=None;self.refresh()
        except (ValueError,OSError) as exc:messagebox.showerror('Generic Portrait Groups',str(exc),parent=self)


class GenericPortraitDialog(DraftDialog):
    def __init__(self,parent,app,key):
        super().__init__(parent,app.character_store,'Generic Portrait Group: '+key)
        self.app=app;self.groups=app.character_store.generic_portraits;self.key=key
        record=self.groups.groups()[key]
        self.geometry('1100x780');self.minsize(850,650)
        self.pool=tk.StringVar(value=next(iter(record.pools),'army/male'));self.photos=[]
        header=ttk.Frame(self,padding=10);header.pack(fill='x')
        ttk.Label(header,text=record.name+' ('+key+')',font=('Segoe UI',13,'bold')).pack(anchor='w')
        ttk.Label(header,text='Countries: '+(', '.join(record.tags) or 'No countries assigned'),wraplength=1000).pack(anchor='w',pady=7)
        ttk.Label(header,text='Role / ideology / gender').pack(anchor='w')
        paths=set(record.pools)|{role+'/'+gender for role in ROLES for gender in ('male','female')}
        ideologies=set(IDEOLOGIES)|set(app.country_store.ideologies())
        paths|={'political/'+ideology+'/'+gender for ideology in ideologies for gender in ('male','female')}
        self.pool_box=ChoiceBox(header,textvariable=self.pool,values=[Choice(p,p.replace('/',' / ')) for p in sorted(paths)],width=65)
        self.pool_box.pack(fill='x');self.pool_box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        body=ttk.Frame(self,padding=10);body.pack(fill='both',expand=True)
        left=ttk.Frame(body);left.pack(side='left',fill='both',expand=True)
        self.rows=table(left,[('texture','Large texture',400)])
        self.rows.bind('<<TreeviewSelect>>',lambda e:self.preview())
        right=ttk.Frame(body);right.pack(side='left',padx=15)
        self.large=ttk.Label(right);self.large.pack();self.small=ttk.Label(right);self.small.pack(pady=10)
        self.status=tk.StringVar();ttk.Label(self,textvariable=self.status,wraplength=1020).pack(anchor='w',padx=10)
        buttons(self,[('Add images to pool',self.add),('Replace selected image',self.replace),('Remove from this pool',self.remove)])
        ttk.Label(self,text='Uploads generate large and small TGA portraits automatically. Shared sprites can appear in several pools; replacing one updates all its uses. Changes remain drafts until Save.',wraplength=1020).pack(anchor='w',padx=10,pady=10)
        buttons(self,[('Apply group',lambda:self.accept(self.key)),('Cancel',self.cancel)])
        self.refresh()

    def refresh(self):
        self.pool_box.commit();refs=self.groups.groups()[self.key].pools.get(self.pool.get(),())
        selected=next(iter(self.rows.selection()),None);self.rows.delete(*self.rows.get_children())
        for ref in refs:
            entries=self.store.sprite_entries(ref);texture=entries[0]['texture'] if entries else 'Missing sprite'
            self.rows.insert('','end',iid=ref,text=ref,values=(texture,))
        if selected and self.rows.exists(selected):self.rows.selection_set(selected)
        elif refs:self.rows.selection_set(refs[0])
        self.status.set(f'{len(refs)} portraits in {self.pool.get()}. '+('Add an image to enable this pool.' if not refs else ''))
        self.preview()

    def preview(self):
        self.photos=[]
        ref=next(iter(self.rows.selection()),None)
        small=next((s for s in self.store.sprites() if ref and s.casefold()==(ref+'_small').casefold()),None)
        for widget,sprite,size in ((self.large,ref,(156,210)),(self.small,small,(65,67))):
            image=self.store.image(sprite,size) if sprite else None
            if image is None:widget.configure(image='',text='No preview')
            else:
                photo=ImageTk.PhotoImage(image,master=self);self.photos.append(photo);widget.configure(image=photo,text='')

    def import_files(self,files,replace=None):
        if not files:return
        self.pool_box.commit();refs=self.groups.upload(self.key,self.pool.get(),files,replace);self.refresh()
        selected=replace or refs[-1];self.rows.selection_set(selected);self.rows.see(selected);self.preview()

    def add(self):
        files=filedialog.askopenfilenames(parent=self,title='Add generic portraits',filetypes=[('Portrait images','*.png *.tga *.dds *.jpg *.jpeg *.bmp *.webp'),('All files','*.*')])
        try:self.import_files(files)
        except (ValueError,OSError) as exc:messagebox.showerror('Generic portraits',str(exc),parent=self)

    def replace(self):
        if not (selected:=self.rows.selection()):return
        file=filedialog.askopenfilename(parent=self,title='Replace portrait and generate its small portrait',filetypes=[('Portrait images','*.png *.tga *.dds *.jpg *.jpeg *.bmp *.webp'),('All files','*.*')])
        try:self.import_files([file] if file else [],selected[0])
        except (ValueError,OSError) as exc:messagebox.showerror('Generic portraits',str(exc),parent=self)

    def remove(self):
        if not (selected:=self.rows.selection()):return
        try:
            refs=self.groups.groups()[self.key].pools[self.pool.get()]
            self.groups.set_pool(self.key,self.pool.get(),[r for r in refs if r!=selected[0]]);self.refresh()
        except (ValueError,OSError) as exc:messagebox.showerror('Generic portraits',str(exc),parent=self)

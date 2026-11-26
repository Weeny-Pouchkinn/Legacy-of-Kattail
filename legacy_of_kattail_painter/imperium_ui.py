"""Reusable Imperium element forms and immediate/delayed map hover previews."""
import tkinter as tk
from tkinter import ttk,messagebox

from character_ui import DraftDialog
from country_ui import choose_color,buttons
from imperium_model import LAYER,CATALOG
from model import colour


class ImperiumElementDialog(DraftDialog):
    def __init__(self,parent,app,ident=None):
        super().__init__(parent,app.character_store,'Edit Imperium element' if ident else 'New Imperium element')
        self.app,self.elements=app,app.imperium_store;record=self.elements.elements().get(ident);self.new=record is None
        next_id=max(self.elements.elements(),default=0)+1
        self.ident=tk.StringVar(value=str(record.key if record else next_id));self.name=tk.StringVar(value=record.name if record else '')
        self.color=tk.StringVar(value='#%02x%02x%02x'%(record.color if record else colour('imperium_'+str(next_id))))
        self.geometry('870x730');self.minsize(700,600)
        form=ttk.Frame(self,padding=12);form.pack(fill='x');form.columnconfigure(1,weight=1)
        for row,(label,var) in enumerate([('Element ID',self.ident),('Name',self.name),('Map color',self.color)]):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky='w',pady=6)
            ttk.Entry(form,textvariable=var,state='disabled' if var is self.ident and record else 'normal').grid(row=row,column=1,sticky='ew',padx=8)
            if var is self.color:ttk.Button(form,text='Choose color',command=lambda:choose_color(self,self.color)).grid(row=row,column=2)
        ttk.Label(self,text='Use [FROM.GetName] for the hovered state’s name. Both tooltip texts are yours to write; Enter adds a new line.',wraplength=780).pack(anchor='w',padx=12,pady=8)
        ttk.Label(self,text='Immediate tooltip').pack(anchor='w',padx=12)
        self.immediate=tk.Text(self,height=4,wrap='word',undo=True);self.immediate.pack(fill='x',padx=12,pady=(4,12));self.immediate.insert('1.0',record.immediate if record else '')
        ttk.Label(self,text='Delayed tooltip').pack(anchor='w',padx=12)
        self.delayed=tk.Text(self,height=10,wrap='word',undo=True);self.delayed.pack(fill='both',expand=True,padx=12,pady=4);self.delayed.insert('1.0',record.delayed if record else '')
        buttons(self,[('Apply element',self.ok),('Cancel',self.cancel)])

    def ok(self):
        try:
            ident=int(self.ident.get())
            self.elements.edit_element(ident,self.name.get(),self.color.get(),self.immediate.get('1.0','end-1c'),self.delayed.get('1.0','end-1c'),self.new)
            self.accept(ident)
        except (ValueError,OSError) as exc:messagebox.showerror(CATALOG,str(exc),parent=self)


class ImperiumHover:
    DELAY_MS=650

    def __init__(self,app):
        self.app=app;self.canvas=app.canvas;self.window=None;self.label=None;self.job=None;self.key=None;self.position=(0,0);self.short='';self.long=''
        self.canvas.bind('<Motion>',self.motion,add='+');self.canvas.bind('<Leave>',lambda e:self.hide(),add='+')
        for sequence in ('<ButtonPress-1>','<ButtonPress-2>','<ButtonPress-3>'):self.canvas.bind(sequence,lambda e:self.hide(),add='+')
        self.canvas.bind('<Destroy>',lambda e:self.hide(),add='+')

    def hide(self):
        if self.job is not None:
            try:self.canvas.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
        if self.window is not None:
            try:self.window.destroy()
            except tk.TclError:pass
            self.window=None;self.label=None
        self.key=None

    def show(self,delayed=False):
        text=self.short+('\n\n' if self.short and self.long and delayed else '')+(self.long if delayed else '')
        if not text:return
        if self.window is None:
            self.window=tk.Toplevel(self.canvas);self.window.wm_overrideredirect(True)
            self.label=tk.Label(self.window,text=text,justify='left',wraplength=420,padx=9,pady=7,bg='#fffbd9',fg='#111111',relief='solid',borderwidth=1)
            self.label.pack()
        else:self.label.configure(text=text)
        x,y=self.position;self.window.geometry(f'{x+16:+d}{y+20:+d}')

    def reveal(self):
        self.job=None
        if self.key is not None:self.show(True)

    def motion(self,event):
        app=self.app
        if app.palette_key()!=LAYER or getattr(event,'state',0)&0x700:self.hide();return
        ids=app.world.map_ids
        if ids is None:self.hide();return
        x,y=int(self.canvas.canvasx(event.x)/app.zoom),int(self.canvas.canvasy(event.y)/app.zoom)
        if not 0<=x<ids.shape[1] or not 0<=y<ids.shape[0]:self.hide();return
        sid=app.world.province_states.get(int(ids[y,x]))
        if sid is None:self.hide();return
        self.position=(event.x_root,event.y_root);key=(sid,app.world.docs.revision)
        if key!=self.key:
            self.hide();self.key=key;self.short,self.long=app.imperium_store.hover_text(sid)
            self.show();self.job=self.canvas.after(self.DELAY_MS,self.reveal)
        elif self.window is not None:
            px,py=self.position;self.window.geometry(f'{px+16:+d}{py+20:+d}')

"""Seed-province selection for a new user-named state."""
import tkinter as tk
from tkinter import ttk,messagebox

from character_ui import DraftDialog
from country_ui import buttons


class NewStateDialog(DraftDialog):
    def __init__(self,parent,app):
        super().__init__(parent,app.character_store,'Create state')
        self.app=app;self.seed=None;self.name=tk.StringVar();self.seed_label=tk.StringVar(value='No initial province selected')
        self.geometry('550x260')
        frame=ttk.Frame(self,padding=12);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='New state name').pack(anchor='w')
        ttk.Entry(frame,textvariable=self.name).pack(fill='x',pady=6)
        ttk.Button(frame,text='Choose initial province on map',command=self.pick_seed).pack(anchor='w',pady=6)
        ttk.Label(frame,textvariable=self.seed_label).pack(anchor='w')
        ttk.Label(frame,text='Owner, cores, category and demographics inherit from the seed state. The donor must retain a province. Paint further provinces into the new state after creating it.',wraplength=510).pack(anchor='w',pady=8)
        buttons(frame,[('Create state',self.ok),('Cancel',self.cancel)])

    def pick_seed(self):
        self.app.begin_geography_pick(self,self.receive_seed,'province')

    def receive_seed(self,pid):
        self.seed=pid;sid=self.app.world.province_states[pid]
        self.seed_label.set(f'Province {pid}, from state {sid}')

    def ok(self):
        try:
            if self.seed is None:raise ValueError('Choose the initial province on the map')
            sid,result=self.app.state_boundary_store.create_state(self.name.get(),self.seed,self.app.state_boundary_options())
            self.accept(sid)
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('Create state',str(exc),parent=self)

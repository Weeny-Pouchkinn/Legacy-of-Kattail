"""Live, eight-layer flag design; only flattened native flags are saved."""
import tkinter as tk
from collections import OrderedDict
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
from select_ui import ChoiceBox
from country_model import PATTERNS, render_flag, flag_rgb, symbol_alpha, number


class FlagDesigner(ttk.Frame):
    def __init__(self,parent,store,on_use):
        super().__init__(parent,padding=(0,8));self.store=store;self.on_use=on_use
        self.symbols=[];self._preview_job=None;self._rendering=False;self._drag=None;self._traces=[];self.color_controls=[];self._masks=OrderedDict()
        self.pattern=tk.StringVar(value='Horizontal tricolor');self.colors=[tk.StringVar(value=c) for c in ('#283c63','#ffffff','#b33232','#e9c45c')]
        self.mask_mode=tk.StringVar(value='Alpha')
        area=ttk.Frame(self);area.pack(fill='both',expand=True)
        self.controls_canvas=tk.Canvas(area,highlightthickness=0,height=340,background=ttk.Style().lookup('TFrame','background'))
        scrollbar=ttk.Scrollbar(area,command=self.controls_canvas.yview);self.controls_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');self.controls_canvas.pack(side='left',fill='both',expand=True)
        self.controls=ttk.Frame(self.controls_canvas);window=self.controls_canvas.create_window(0,0,anchor='nw',window=self.controls)
        self.controls.bind('<Configure>',lambda e:self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox('all')))
        self.controls_canvas.bind('<Configure>',lambda e:self.controls_canvas.itemconfigure(window,width=e.width))
        self._scroll_tag='FlagControls'+str(id(self));self.bind_class(self._scroll_tag,'<MouseWheel>',self.scroll_controls)
        row=ttk.Frame(self.controls);row.pack(fill='x')
        self.pattern_box=ChoiceBox(row,textvariable=self.pattern,values=PATTERNS);self.pattern_box.pack(side='left',fill='x',expand=True)
        self.pattern_box.arrow.configure(command=lambda:self.browse('background'))
        self.pattern_box.entry.bind('<Double-1>',lambda e:self.browse('background'))
        ttk.Button(row,text='Browse backgrounds…',command=lambda:self.browse('background')).pack(side='left',padx=(6,0))
        palette=ttk.Frame(self.controls);palette.pack(fill='x',pady=4)
        for i,var in enumerate(self.colors):
            line=ttk.Frame(palette);line.grid(row=i//2,column=i%2,sticky='w',padx=(0,8),pady=2);self.color_field(line,var,f'Color {i+1}')
        line=ttk.Frame(self.controls);line.pack(fill='x',pady=4);ChoiceBox(line,textvariable=self.mask_mode,values=['Alpha','White on dark','Dark on light'],width=18).pack(side='left')
        ttk.Button(line,text='Import reusable emblem…',command=self.import_emblem).pack(side='left',padx=6)
        line=ttk.Frame(self.controls);line.pack(fill='x',pady=4)
        self.add_button=ttk.Button(line,text='Add symbol',command=self.add_symbol);self.add_button.pack(side='left')
        ttk.Button(line,text='Remove selected symbol',command=self.remove_symbol).pack(side='left',padx=6)
        self.symbol_tabs=ttk.Notebook(self.controls);self.symbol_tabs.pack(fill='both',expand=True)
        self.symbol_tabs.bind('<<NotebookTabChanged>>',lambda e:self.schedule_preview())
        self.preview_canvas=tk.Canvas(self,height=164,highlightthickness=0,background=ttk.Style().lookup('TFrame','background'))
        self.preview_canvas.pack(fill='x',pady=(6,0));self.preview_canvas.bind('<Configure>',lambda e:self.schedule_preview())
        self.preview_canvas.bind('<Button-1>',self.drag_start);self.preview_canvas.bind('<B1-Motion>',self.drag_move);self.preview_canvas.bind('<ButtonRelease-1>',self.drag_end)
        ttk.Label(self,text='Drag a symbol to select/move it. Later tabs draw on top.',wraplength=520).pack(anchor='w')
        bar=ttk.Frame(self);bar.pack(fill='x',pady=6);ttk.Button(bar,text='Preview design',command=self.preview).pack(side='left')
        self.use_button=ttk.Button(bar,text='Use design for selected ideology',command=self.use);self.use_button.pack(side='left',padx=6)
        self.watch(self.pattern)
        for var in self.colors:self.watch(var)
        self.add_symbol();self.tag_scroll(self.controls);self.preview()

    def watch(self,var,callback=None):
        token=var.trace_add('write',callback or self.schedule_preview);self._traces.append((var,token))

    def color_field(self,parent,var,label):
        ttk.Label(parent,text=label).pack(side='left',padx=(0,5))
        entry=ttk.Entry(parent,textvariable=var,width=10);entry.pack(side='left');entry.bind('<Return>',lambda e:self.preview())
        swatch=tk.Canvas(parent,width=18,height=18,highlightthickness=1,highlightbackground='#777777');swatch.pack(side='left',padx=4)
        self.color_controls.append((var,swatch,entry));ttk.Button(parent,text='Choose',width=7,command=lambda:self.color_pick(var)).pack(side='left')

    def color_pick(self,var):
        try:initial='#%02x%02x%02x'%flag_rgb(var.get())
        except ValueError:initial='#ffffff'
        chosen=colorchooser.askcolor(initial,parent=self)[1]
        if chosen:var.set(chosen)

    def numeric_control(self,parent,row,label,var,low,high):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',padx=(0,8),pady=2)
        slider=tk.DoubleVar(value=float(var.get()))
        scale=ttk.Scale(parent,from_=low,to=high,variable=slider,command=lambda raw:var.set(f'{float(raw):.3f}'.rstrip('0').rstrip('.')))
        scale.grid(row=row,column=1,sticky='ew')
        entry=ttk.Entry(parent,textvariable=var,width=9);entry.grid(row=row,column=2,padx=6);entry.bind('<Return>',lambda e:self.preview())
        def sync(*args):
            try:slider.set(float(number(var.get(),low,high)))
            except ValueError:pass
        self.watch(var,sync);return scale,entry

    def add_symbol(self):
        if len(self.symbols)>=8:return
        frame=ttk.Frame(self.symbol_tabs,padding=6)
        defaults={'emblem':'','tint':'#ffffff','scale':'.65','x':'.5','y':'.5','stretch_x':'1','stretch_y':'1','angle':'0','outline_width':'1','outline_color':'#000000'}
        layer={k:tk.StringVar(value=v) for k,v in defaults.items()};layer['outline']=tk.BooleanVar(value=False);layer['frame']=frame;layer['numeric']={}
        self.symbols.append(layer);self.symbol_tabs.add(frame,text=f'Symbol {len(self.symbols)}');self.symbol_tabs.select(frame)
        row=ttk.Frame(frame);row.pack(fill='x')
        layer['box']=ChoiceBox(row,textvariable=layer['emblem'],values=self.store.emblem_choices());layer['box'].pack(side='left',fill='x',expand=True)
        layer['box'].arrow.configure(command=lambda:self.browse('emblem'));layer['box'].entry.bind('<Double-1>',lambda e:self.browse('emblem'))
        ttk.Button(row,text='Browse symbols…',command=lambda:self.browse('emblem')).pack(side='left',padx=6)
        row=ttk.Frame(frame);row.pack(fill='x',pady=4);self.color_field(row,layer['tint'],'Symbol color')
        row=ttk.Frame(frame);row.pack(fill='x',pady=4);ttk.Checkbutton(row,text='Outline for symbol',variable=layer['outline']).pack(side='left',padx=(0,8));self.color_field(row,layer['outline_color'],'Color')
        form=ttk.Frame(frame);form.pack(fill='x');form.columnconfigure(1,weight=1)
        controls=[('scale','Size (fraction of flag height)',.05,1.5),('x','Horizontal position (0–1)',-.5,1.5),('y','Vertical position (0–1)',-.5,1.5),('stretch_x','Horizontal stretch (×)',.1,3),('stretch_y','Vertical stretch (×)',.1,3),('angle','Tilt (degrees, clockwise)',-180,180),('outline_width','Outline thickness (82×52 px)',0,8)]
        for row,(key,label,low,high) in enumerate(controls):layer['numeric'][key]=self.numeric_control(form,row,label,layer[key],low,high)
        for key in (*defaults,'outline'):self.watch(layer[key])
        self.add_button.configure(state='disabled' if len(self.symbols)>=8 else 'normal');self.tag_scroll(frame);self.schedule_preview()

    def remove_symbol(self):
        index=self.active_symbol_index()
        if len(self.symbols)==1:self.symbols[0]['emblem'].set('');return
        layer=self.symbols.pop(index);self.symbol_tabs.forget(layer['frame']);layer['frame'].destroy()
        variables=[v for v in layer.values() if isinstance(v,tk.Variable)]
        for var,token in list(self._traces):
            if any(var is candidate for candidate in variables):var.trace_remove('write',token);self._traces.remove((var,token))
        self.color_controls=[r for r in self.color_controls if r[1].winfo_exists()]
        for i,layer in enumerate(self.symbols,1):self.symbol_tabs.tab(layer['frame'],text=f'Symbol {i}')
        self.add_button.configure(state='normal');self.schedule_preview()

    def active_symbol_index(self):
        selected=self.symbol_tabs.select()
        return next((i for i,r in enumerate(self.symbols) if str(r['frame'])==selected),0)

    @property
    def emblem(self):return self.symbols[self.active_symbol_index()]['emblem']
    @property
    def tint(self):return self.symbols[self.active_symbol_index()]['tint']
    @property
    def scale(self):return self.symbols[self.active_symbol_index()]['scale']
    @property
    def emblem_box(self):return self.symbols[self.active_symbol_index()]['box']

    def symbol_specs(self,skip_index=None):
        layers=[]
        limits={'scale':(.05,1.5),'x':(-.5,1.5),'y':(-.5,1.5),'stretch_x':(.1,3),'stretch_y':(.1,3),'angle':(-180,180),'outline_width':(0,8)}
        for i,layer in enumerate(self.symbols):
            spec={k:float(number(layer[k].get(),*bounds)) for k,bounds in limits.items()}
            spec.update(tint='#%02x%02x%02x'%flag_rgb(layer['tint'].get()),outline_color='#%02x%02x%02x'%flag_rgb(layer['outline_color'].get()))
            if not layer['outline'].get():spec['outline_width']=0
            spec['code']=layer['emblem'].get();spec['mask']=None if i==skip_index else self.mask(spec['code'])
            layers.append(spec)
        return layers

    def mask(self,code):
        if not code:return None
        token=(code,getattr(getattr(self.store,'docs',None),'revision',0))
        if token not in self._masks:
            image=self.store.emblem_mask(code)
            if image is not None:image=image.convert('L');image.thumbnail((256,256),Image.Resampling.LANCZOS)
            self._masks[token]=image
            if len(self._masks)>16:self._masks.popitem(last=False)
        self._masks.move_to_end(token);return self._masks[token]

    def update_swatches(self):
        for var,swatch,entry in self.color_controls:
            swatch.delete('all')
            try:swatch.configure(background='#%02x%02x%02x'%flag_rgb(var.get()))
            except ValueError:
                swatch.configure(background='#eeeeee');swatch.create_line(2,2,16,16,fill='#b03030',width=2);swatch.create_line(2,16,16,2,fill='#b03030',width=2)

    def schedule_preview(self,*args):
        if self._rendering:return
        self.update_swatches()
        if self._drag is not None:
            if self._preview_job is None:self._preview_job=self.after(16,lambda:self.preview(commit=False))
            return
        if self._preview_job is not None:self.after_cancel(self._preview_job)
        self._preview_job=self.after(80,lambda:self.preview(commit=False))

    def tag_scroll(self,widget):
        if self._scroll_tag not in widget.bindtags():widget.bindtags((*widget.bindtags(),self._scroll_tag))
        for c in widget.winfo_children():self.tag_scroll(c)

    def scroll_controls(self,event):
        self.controls_canvas.yview_scroll(-3 if event.delta>0 else 3,'units');return 'break'

    def browse(self,kind):
        from country_ui import FlagLibraryPicker
        previous=self.grab_current();self.pattern_box.hide();self.emblem_box.hide()
        try:
            self.pattern_box.commit();self.emblem_box.commit()
            dialog=FlagLibraryPicker(self,kind);self.wait_window(dialog)
            if dialog.result is not None:(self.pattern if kind=='background' else self.emblem).set(dialog.result);self.preview()
        except (ValueError,OSError) as exc:messagebox.showerror('Flag library',str(exc),parent=self)
        finally:
            if previous is not None and previous.winfo_exists():previous.grab_set()

    def render(self,commit=True,size=(328,208)):
        if commit:
            self.pattern_box.commit()
            for layer in self.symbols:layer['box'].commit()
        self._latest_specs=self.symbol_specs()
        return render_flag(self.pattern.get(),[v.get() for v in self.colors],size=size,symbols=self._latest_specs)

    def preview(self,commit=True):
        if self._rendering:return False
        if self._preview_job is not None:self.after_cancel(self._preview_job);self._preview_job=None
        self._rendering=True;self.update_swatches();self.preview_canvas.delete('all')
        try:
            image=self.render(commit,size=(246,156));self.photo=ImageTk.PhotoImage(image);self.latest=image
            x=max(0,(self.preview_canvas.winfo_width()-246)/2);y=4;self._preview_origin=(x,y)
            self.preview_canvas.create_image(x,y,anchor='nw',image=self.photo)
            spec=self._latest_specs[self.active_symbol_index()];bounds=symbol_alpha(spec,(246,156)).getbbox()
            if bounds:self.preview_canvas.create_rectangle(x+bounds[0],y+bounds[1],x+bounds[2],y+bounds[3],outline='#ffcf40',dash=(3,3))
            self.use_button.configure(state='normal');return True
        except (ValueError,OSError,KeyError) as exc:
            self.latest=None;self.use_button.configure(state='disabled');self.preview_canvas.create_text(10,12,anchor='nw',text=str(exc),width=max(100,self.preview_canvas.winfo_width()-20));return False
        finally:self._rendering=False

    def drag_start(self,event):
        if self.latest is None:return
        x,y=self._preview_origin;px,py=int(event.x-x),int(event.y-y)
        if not (0<=px<246 and 0<=py<156):return
        for index in range(len(self._latest_specs)-1,-1,-1):
            if symbol_alpha(self._latest_specs[index],(246,156)).getpixel((px,py))>24:
                layer=self.symbols[index];self.symbol_tabs.select(layer['frame']);self._drag=(index,event.x,event.y,float(layer['x'].get()),float(layer['y'].get()));self.schedule_preview();break

    def drag_move(self,event):
        if self._drag is None:return
        index,x,y,ox,oy=self._drag;layer=self.symbols[index]
        layer['x'].set(f'{max(-.5,min(1.5,ox+(event.x-x)/246)):.4f}');layer['y'].set(f'{max(-.5,min(1.5,oy+(event.y-y)/156)):.4f}')

    def drag_end(self,event=None):
        if self._drag is not None:self._drag=None;self.preview(commit=False)

    def use(self):
        if self.preview():self.on_use(self.render(False))

    def import_emblem(self):
        path=filedialog.askopenfilename(parent=self,title='Import reusable emblem',filetypes=[('Images','*.png *.dds *.tga *.bmp'),('All files','*.*')])
        if path:
            try:
                key=self.store.import_emblem(path,self.mask_mode.get())
                for layer in self.symbols:layer['box'].configure(values=self.store.emblem_choices())
                self.emblem.set(key);self.preview()
            except (ValueError,OSError) as exc:messagebox.showerror('Emblem',str(exc),parent=self)

    def destroy(self):
        if self._preview_job is not None:self.after_cancel(self._preview_job);self._preview_job=None
        for var,token in self._traces:var.trace_remove('write',token)
        self._traces=[];self.unbind_class(self._scroll_tag,'<MouseWheel>');super().destroy()

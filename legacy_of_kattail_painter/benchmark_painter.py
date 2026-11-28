"""Repeatable native UI workloads; edits remain in memory and never Save."""
import argparse
import cProfile
import io
import json
from pathlib import Path
import pstats
import sys
import time
import tkinter as tk
from types import SimpleNamespace

from model import World,Emblems
from painter import Painter
from country_ui import IconPicker,SpiritDialog,spirit_icon_preview
from imperium_model import LAYER


def benchmark(mod,profile=False):
    timings={};profiler=cProfile.Profile();errors=[]
    def measure(key,callback):
        start=time.perf_counter()
        if profile:profiler.enable()
        result=callback()
        if profile:profiler.disable()
        timings[key]=round(time.perf_counter()-start,6)
        print(key,timings[key],file=sys.stderr,flush=True)
        return result
    world=measure('world_load',lambda:World(mod));root=tk.Tk();root.attributes('-alpha',0)
    root.report_callback_exception=lambda *exc:errors.append(str(exc))
    try:
        app=measure('painter_open',lambda:Painter(root,world,Emblems()));root.update()
        app.layer.set('States');app.layer_changed();app.state_mode.set(LAYER);app.map_mode_changed();root.update()
        ident=next(iter(app.imperium_store.elements()),0)
        app.paint_selection[LAYER]=ident
        for index,sid in enumerate(list(world.states)[:3]):
            if app.imperium_store.state_assignments().get(sid,0)==ident:
                app.paint_selection[LAYER]=0 if ident else next(iter(app.imperium_store.elements()),0)
            else:app.paint_selection[LAYER]=ident
            def stroke(sid=sid):
                app.pick_geography(world.states[sid].provinces[0],sid,SimpleNamespace(state=0));app.paint_release();root.update()
            measure('imperium_stroke_'+str(index+1),stroke)
        measure('warm_map_frame',app.refresh_map)
        catalog=measure('spirit_catalog_cold',app.country_store.spirit_icon_catalog)
        measure('spirit_catalog_warm',app.country_store.spirit_icon_catalog)
        picker=measure('icon_picker_open',lambda:IconPicker(root,app.country_store));picker.attributes('-alpha',0);root.update_idletasks()
        measure('icon_visible_images',picker.load_images);root.update()
        picker.query.set('axes');measure('icon_search',picker.refresh);root.update();picker.cancel()
        keys=list(catalog)[:6]
        measure('six_icon_previews',lambda:[spirit_icon_preview(app.country_store,key) for key in keys])
        measure('six_icon_previews_warm',lambda:[spirit_icon_preview(app.country_store,key) for key in keys])
        spirit=measure('spirit_editor_open',lambda:SpiritDialog(root,app.country_store));spirit.attributes('-alpha',0);root.update();spirit.cancel()
        measure('sync_after_cancel',app._sync)
        app.cancel_map_job();app.destroy()
    finally:root.update_idletasks();root.destroy()
    if errors:raise AssertionError(errors)
    checked=0;external_changes=[]
    for relative,original in world.docs.snapshots.items():
        path=world.root/relative
        if (path.read_bytes() if path.is_file() else None)!=original:external_changes.append(relative)
        checked+=1
    if profile:
        output=io.StringIO();pstats.Stats(profiler,stream=output).strip_dirs().sort_stats('cumulative').print_stats(32)
        print(output.getvalue(),file=sys.stderr)
    return {'seconds':timings,'icons':len(catalog),'sources_checked':checked,'source_writes':0,'external_changes_observed':len(external_changes),'profiled':profile}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mod',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--profile',action='store_true');args=parser.parse_args()
    print(json.dumps(benchmark(args.mod,args.profile),indent=2))

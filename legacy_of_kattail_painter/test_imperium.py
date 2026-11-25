"""Reusable native Imperium objects, state painting and two-stage hover."""
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from model import World,parse,child,value,walk,Emblems
from character_model import CharacterStore
from demographics import MapCatalogStore,CATALOG_PATHS
from imperium_model import (ImperiumStore,LAYER,CATALOG,VARIABLE,MAPMODE,MAP_PATH,
                            TEXT_PATH,LOC_PATH,FUNCTIONS,UNASSIGNED,loc_key)
import test_geography as geography_tests


class ImperiumTests(unittest.TestCase):
    write=geography_tests.GeographyTests.write
    def setUp(self):
        geography_tests.GeographyTests.setUp(self);self.store=ImperiumStore(self.world,self.c,self.g.catalogs)
        self.world.map_ids=np.array([[1,3,2,4],[1,3,2,4]],np.int32)
    tearDown=geography_tests.GeographyTests.tearDown

    def element(self,ident=1,**kw):
        values=dict(name='Schutzone Pegasien',color='#e68a21',immediate='[FROM.GetName] was part of the Schutzone Pegasien',delayed='Long text\nAuthored "details" and $tokens$.')
        values.update(kw);self.store.edit_element(ident,create=True,**values)

    def test_reusable_objects_have_manual_text_native_dispatch_and_unique_colors(self):
        self.element();self.element(2,name='Second element',color='#1944af',immediate='Exact second text',delayed='')
        self.assertEqual(set(self.store.elements()),{1,2});self.assertEqual(self.store.elements()[1].color,(230,138,33))
        self.store.paint_state(1,1);self.store.paint_state(2,1)
        self.assertEqual(self.store.hover_text(1)[0],'First state was part of the Schutzone Pegasien')
        self.assertEqual(self.store.hover_text(2)[0],'Second state was part of the Schutzone Pegasien')
        self.store.edit_element(1,'Renamed','#23ad90','Manually changed [FROM.GetName]','Different delayed')
        self.assertEqual(self.store.hover_text(1),('Manually changed First state','Different delayed'))
        self.assertEqual(self.store.hover_text(2)[0],'Manually changed Second state')
        self.assertEqual(self.store.state_assignments(),{1:1,2:1});self.store.validate_save()
        text=self.world.docs.text(LOC_PATH)
        self.assertIn('[FROM.GetKatzenartigImperiumTooltip]',text);self.assertIn('[FROM.GetKatzenartigImperiumTooltipDelayed]',text)
        for function in FUNCTIONS:self.assertIn(function,self.world.docs.text(TEXT_PATH))

    def test_paint_changes_only_owned_base_history_and_keeps_dates_and_other_fields(self):
        self.element();path=self.world.states[1].path
        original=self.world.docs.text(path)
        text=original.replace('history = {','history = { set_variable={ '+VARIABLE+'=2 other=7 }',1)
        text=text.replace('1940.1.1 = {','1940.1.1 = { set_variable={ '+VARIABLE+'=99 }')
        self.world.docs.replace(path,text)
        self.store.paint_state(1,1)
        changed=self.world.docs.text(path)
        self.assertEqual(changed,text.replace(VARIABLE+'=2',VARIABLE+'=1'))
        self.assertEqual(self.store.state_assignments(),{1:1})
        self.store.paint_state(1,0);self.assertEqual(self.store.state_assignments(),{1:0})
        self.world.docs.undo();self.assertEqual(self.store.state_assignments(),{1:1})
        self.world.docs.redo();self.assertEqual(self.store.state_assignments(),{1:0})
        self.assertFalse(self.store.paint_state(2,0))

    def test_new_state_history_assignment_rgb_save_reload_and_clear(self):
        self.element();original={sid:self.world.docs.text(s.path) for sid,s in self.world.states.items()}
        self.store.paint_state(1,1)
        self.assertEqual(self.world.map_image(LAYER).getpixel((0,0)),(230,138,33))
        self.assertEqual(self.world.map_image(LAYER).getpixel((2,0)),UNASSIGNED)
        self.assertEqual(self.world.map_image(LAYER).getpixel((3,0)),(26,43,60))
        self.assertEqual(self.world.docs.text(self.world.states[2].path),original[2])
        self.store.validate_save();self.world.docs.save()
        self.assertTrue((self.root/LOC_PATH).read_bytes().startswith(b'\xef\xbb\xbf'))
        w=World(self.root);c=CharacterStore(w);catalog=MapCatalogStore(w,c);fresh=ImperiumStore(w,c,catalog)
        self.assertEqual(fresh.state_assignments(),{1:1});self.assertEqual(fresh.elements()[1].delayed,'Long text\nAuthored "details" and $tokens$.')
        self.assertEqual(fresh.hover_text(1)[0],'First state was part of the Schutzone Pegasien');fresh.validate_save()
        fresh.paint_state(1,0);self.assertEqual(fresh.state_assignments(),{1:0})

    def test_definition_failures_are_atomic_and_no_id_or_color_collisions(self):
        self.element();before=dict(self.world.docs.drafts)
        for ident,kw in [(1,{}),(2,{'color':'#e68a21'}),(2,{'color':'#41454e'}),(0,{'color':'#123456'}),(2,{'name':'  ','color':'#123456'})]:
            with self.assertRaises(ValueError):self.element(ident,**kw)
            self.assertEqual(self.world.docs.drafts,before)
        self.world.docs.replace(TEXT_PATH,'defined_text={name=wrong text={localization_key=missing}}');before=dict(self.world.docs.drafts)
        with self.assertRaises(ValueError):self.element(2,color='#123456')
        self.assertEqual(self.world.docs.drafts,before)

    def test_undefined_state_reference_and_broken_tooltip_are_rejected(self):
        self.element();self.store.paint_state(1,1)
        path=self.world.states[1].path;self.world.docs.replace(path,self.world.docs.text(path).replace(VARIABLE+' = 1',VARIABLE+' = 999'))
        with self.assertRaisesRegex(ValueError,'undefined'):self.store.validate_save()
        self.world.docs.undo();self.store.validate_save()
        self.world.docs.replace(TEXT_PATH,self.world.docs.text(TEXT_PATH).replace(loc_key(1,'tooltip_delayed'),'wrong_key'))
        with self.assertRaisesRegex(ValueError,'tooltip branch'):self.store.validate_save()

    def test_long_form_variable_and_history_creation(self):
        self.element();path=self.world.states[1].path
        self.world.docs.replace(path,'state={id=1 name=ONE provinces={1 3} history={set_variable={var='+VARIABLE+' value=1}}}')
        self.assertEqual(self.store.state_assignments(),{1:1})
        self.store.paint_state(1,0);self.assertIn('value=0',self.world.docs.text(path))
        other=self.world.states[2].path;self.world.docs.replace(other,'state={id=2 name=TWO provinces={2}}')
        self.store.paint_state(2,1);self.assertEqual(self.store.state_assignments()[2],1)


class ImperiumFormTests(unittest.TestCase):
    write=geography_tests.GeographyTests.write
    element=ImperiumTests.element
    def setUp(self):
        ImperiumTests.setUp(self);self.root_widget=tk.Tk();self.root_widget.withdraw();self.root_widget.attributes('-alpha',0)
        self.errors=[];self.root_widget.report_callback_exception=lambda typ,val,tb:self.errors.append(str(val))
        errors=patch('imperium_ui.messagebox.showerror',side_effect=AssertionError('Unexpected element dialog error'));errors.start();self.addCleanup(errors.stop)
    def tearDown(self):
        self.root_widget.destroy();geography_tests.GeographyTests.tearDown(self)

    def app(self):
        from painter import Painter
        for rel in set(CATALOG_PATHS.values()):
            if not (self.root/rel).exists():self.write(rel,'l_english:\n' if rel.endswith('.yml') else '',rel.endswith('.yml'))
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        with patch('character_model.default_paths',return_value={'game':self.c.game_root}):app=Painter(self.root_widget,self.world,Emblems())
        self.root_widget.deiconify();self.root_widget.update();app.layer.set('States');app.layer_changed();app.state_mode.set(LAYER);app.map_mode_changed();self.root_widget.update()
        return app

    def test_object_dialog_create_edit_cancel_and_palette_state_gestures(self):
        from imperium_ui import ImperiumElementDialog
        app=self.app();self.assertEqual(app.map_config().layer,LAYER);self.assertEqual(set(app.palette_values.values()),{0})
        d=ImperiumElementDialog(self.root_widget,app);d.attributes('-alpha',0);self.root_widget.update()
        d.name.set('Schutzone Pegasien');d.color.set('#e68a21');d.immediate.insert('1.0','[FROM.GetName] was part of the Schutzone Pegasien');d.delayed.insert('1.0','Long manual text');d.ok()
        app.refresh_palette();self.assertEqual(set(app.palette_values.values()),{0,1});app.paint_selection[LAYER]=1;app.refresh_palette();self.root_widget.update()
        app.zoom=10;app.draw_map();self.root_widget.update();app.canvas.xview_moveto(0);app.canvas.yview_moveto(0)
        app.paint_press(SimpleNamespace(x=0,y=0,state=0));app.paint_release();self.assertEqual(app.imperium_store.state_assignments()[1],1)
        app.paint_press(SimpleNamespace(x=0,y=0,state=1));app.paint_release();self.assertEqual(app.paint_selection[LAYER],1)
        app.right_press(SimpleNamespace(x=0,y=0,state=0));app.paint_release();self.assertEqual(app.imperium_store.state_assignments()[1],0)
        app.undo();self.assertEqual(app.imperium_store.state_assignments()[1],1)
        d=ImperiumElementDialog(self.root_widget,app,1);d.attributes('-alpha',0);d.color.set('#123456');d.cancel();self.assertEqual(app.imperium_store.elements()[1].color,(230,138,33))
        app.save_overlay();self.assertEqual(app.overlay_config.layer,LAYER)
        self.assertFalse(self.errors);app.cancel_map_job();app.destroy()

    def test_hover_has_immediate_and_delayed_authored_text_and_cleans_up(self):
        app=self.app();self.element();app.paint_selection[LAYER]=1;app.imperium_store.paint_state(1,1);app.zoom=10;app.draw_map();self.root_widget.update()
        hover=app.imperium_hover;hover.motion(SimpleNamespace(x=0,y=0,x_root=50,y_root=50,state=0))
        self.assertIsNotNone(hover.window);self.assertIn('First state was part',hover.label.cget('text'));self.assertNotIn('Long text',hover.label.cget('text'))
        self.root_widget.after(hover.DELAY_MS+40,self.root_widget.quit);self.root_widget.mainloop()
        self.assertIn('Long text',hover.label.cget('text'))
        hover.hide();self.assertIsNone(hover.window);self.assertIsNone(hover.job)
        app.state_mode.set('Population');app.map_mode_changed();self.root_widget.update();hover.motion(SimpleNamespace(x=0,y=0,x_root=50,y_root=50,state=0));self.assertIsNone(hover.window)
        self.assertFalse(self.errors);app.cancel_map_job();app.destroy()

    def test_definition_database_creates_reusable_object_and_selects_state_brush(self):
        from imperium_ui import ImperiumElementDialog
        app=self.app();app.open_database();self.root_widget.update()
        self.assertEqual(app.definitions_panel.kind.get(),CATALOG)
        def fill():
            d=next(c for c in app.definitions_panel.winfo_children() if isinstance(c,ImperiumElementDialog));d.attributes('-alpha',0)
            d.name.set('Schutzone Pegasien');d.color.set('#e68a21');d.immediate.insert('1.0','[FROM.GetName] was part of the Schutzone Pegasien');d.ok()
        self.root_widget.after(30,fill);app.definitions_panel.open(CATALOG);self.root_widget.update()
        self.assertEqual(app.brush.get(),'States');self.assertEqual(app.state_mode.get(),LAYER);self.assertEqual(app.paint_selection[LAYER],1)
        self.assertEqual(app.definitions_panel.records()[1].name,'Schutzone Pegasien')
        self.assertFalse(app.imperium_store.state_assignments());self.assertFalse(self.errors);app.cancel_map_job();app.destroy()


if __name__=='__main__':unittest.main()

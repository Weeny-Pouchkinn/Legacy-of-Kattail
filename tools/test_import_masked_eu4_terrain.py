"""Pixel-exact format and scope checks for the masked native map importer."""
import io
import struct
import unittest

import numpy as np
from PIL import Image

from import_masked_eu4_terrain import (patch_bmp,patch_colormap,image_array,inward_blend,
                                     half_mask,half_weight,province_types,terrain_tables)


class MaskedTerrainTests(unittest.TestCase):
    def bmp(self,mode):
        im=Image.new(mode,(8,6))
        if mode=='P':im.putpalette([v for i in range(256) for v in (i,255-i,i//2)])
        stream=io.BytesIO();im.save(stream,format='BMP');return stream.getvalue()

    def test_bmp_formats_keep_header_palette_exterior_and_orientation(self):
        mask=np.zeros((6,8),bool);mask[1:4,2:6]=True
        for mode in ('L','P','RGB'):
            blob=self.bmp(mode);pixels=image_array(blob);pixels[mask]=73 if pixels.ndim==2 else (17,83,155)
            out=patch_bmp(blob,pixels,mask);offset=struct.unpack_from('<I',blob,10)[0]
            self.assertEqual(blob[:offset],out[:offset]);self.assertEqual(len(blob),len(out))
            self.assertTrue(np.array_equal(image_array(out),pixels))
        with self.assertRaises(ValueError):patch_bmp(blob,pixels,np.zeros((5,8),bool))

    def test_colormap_keeps_header_alpha_and_exterior_bytes(self):
        im=Image.new('RGBA',(8,6),(10,20,30,77));stream=io.BytesIO();im.save(stream,format='DDS')
        blob=stream.getvalue();mask=np.zeros((6,8),bool);mask[2:4,3:5]=True
        rgb=np.full((6,8,3),(90,100,110),dtype=np.uint8)
        # Pillow emits RGBA; the active game DDS uses BGRA. Encode the fixture
        # with its actual native channel masks and bytes rather than converting
        # the production writer's format assumptions.
        raw=bytearray(blob);struct.pack_into('<4I',raw,92,0xff0000,0xff00,0xff,0xff000000)
        raw[128:]=bytes((30,20,10,77))*48;blob=bytes(raw)
        out=patch_colormap(blob,rgb,mask);a=image_array(out);b=image_array(blob)
        self.assertEqual(blob[:128],out[:128]);self.assertTrue(np.array_equal(a[~mask],b[~mask]))
        self.assertTrue(np.array_equal(a[:,:,3],b[:,:,3]));self.assertTrue(np.all(a[:,:,:3][mask]==rgb[mask]))
        with self.assertRaises(ValueError):patch_colormap(blob,b[:,:,:3],np.ones((5,8),bool))

    def test_blend_stays_inside_mask_and_half_pixels_require_full_coverage(self):
        mask=np.zeros((12,12),bool);mask[1:11,1:11]=True
        weight=inward_blend(mask,4)
        self.assertTrue(np.all(weight[~mask]==0));self.assertEqual(weight[1,1],.25);self.assertEqual(weight[5,5],1)
        mask[2,2]=False;small=half_mask(mask);self.assertFalse(small[1,1])
        self.assertEqual(half_weight(weight).shape,(6,6))

    def test_gameplay_terrain_uses_source_overrides_and_majority_coverage(self):
        source=np.array([[1,1,2,2],[1,1,2,2]],dtype=np.uint16)
        target=np.array([[3,3,4,4],[3,3,4,4]],dtype=np.uint16)
        terrain=np.zeros_like(source,dtype=np.uint8);mask=np.ones_like(source,bool);mask[:,2:]=False;mask[0,2]=True
        rows=province_types(source,terrain,target,mask,{0:'grasslands'},{1:'mountain',2:'forest'})
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['province'],3);self.assertEqual(rows[0]['terrain'],'mountain')
        self.assertEqual(rows[0]['covered_pixels'],4)

    def test_native_tables_and_conflicts(self):
        text='terrain={grass={type=grasslands color={0}}} categories={mountain={terrain_override={7}}}'
        self.assertEqual(terrain_tables(text),({0:'grasslands'},{7:'mountain'}))
        with self.assertRaises(ValueError):terrain_tables(text.replace('categories={','categories={forest={terrain_override={7}}'))


if __name__=='__main__':unittest.main()

"""Relief continuity, biome agreement and native-resolution tree constraints."""
import unittest

import numpy as np

from refine_masked_terrain import (smooth_weight, poisson_offset, matched_height,
                                   footprint_mask, graphical_province_types,
                                   trees_with_native_density)


class TerrainRefinementTests(unittest.TestCase):
    def test_feather_has_gentle_boundary_and_never_reaches_exterior(self):
        mask=np.zeros((120,120),bool);mask[5:115,5:115]=True
        weight=smooth_weight(mask)
        self.assertTrue(np.all(weight[~mask]==0))
        self.assertLess(weight[5,50],.0001)
        self.assertEqual(weight[60,60],1)
        self.assertTrue(np.all(np.diff(weight[5:54,60])>=0))

    def test_harmonic_correction_removes_constant_offset_and_preserves_exterior(self):
        mask=np.zeros((12,12),bool);mask[2:10,2:10]=True
        base=np.full(mask.shape,110.);source=np.full(mask.shape,170.)
        result=poisson_offset(source,base,mask)
        np.testing.assert_allclose(result[mask],110,atol=1e-10)
        np.testing.assert_array_equal(result[~mask],source[~mask])
        mask[0,0]=True
        with self.assertRaises(ValueError):poisson_offset(source,base,mask)

    def test_height_matches_native_range_and_preserves_coastal_rim(self):
        yy,xx=np.indices((160,160));source=110.+xx/8+yy/10
        original=95+.6*(source-95)
        mask=np.zeros(source.shape,bool);mask[50:110,50:110]=True
        land=np.ones(source.shape,bool);land[80:83,80:83]=False
        result,scale,domain=matched_height(original,source,mask,land)
        self.assertAlmostEqual(scale,.6,places=2)
        np.testing.assert_array_equal(result[~domain],original.astype(np.uint8)[~domain])
        self.assertFalse(domain[79:84,79:84].all())
        self.assertTrue(np.all(result[domain]>=96))
        self.assertLess(np.max(np.abs(result[domain].astype(float)-original[domain])),1)

    def test_noninteger_tree_footprints_require_every_native_pixel(self):
        mask=np.ones((7,9),bool);mask[2,3]=False
        actual=footprint_mask(mask,(3,4))
        expected=np.zeros_like(actual)
        for y in range(3):
            for x in range(4):
                expected[y,x]=mask[int(np.floor(y*7/3)):int(np.ceil((y+1)*7/3)),
                                   int(np.floor(x*9/4)):int(np.ceil((x+1)*9/4))].all()
        np.testing.assert_array_equal(actual,expected)
        self.assertFalse(actual.all())

    def test_partly_selected_provinces_use_full_visible_graphic_majority(self):
        ids=np.array([[1,1,1,2],[1,1,1,2],[3,3,3,2]])
        graphics=np.array([[1,2,2,1],[2,2,1,1],[1,2,2,1]])
        mask=np.zeros(ids.shape,bool);mask[0,0]=True;mask[2,0]=True;mask[0,3]=True
        definitions={1:['1','','','','land','','forest'],
                     2:['2','','','','sea','','ocean'],
                     3:['3','','','','land','','plains']}
        rows=graphical_province_types(ids,graphics,mask,definitions,{1:'forest',2:'mountain'})
        self.assertEqual([(r['province'],r['terrain']) for r in rows],[(1,'mountain'),(3,'mountain')])
        self.assertEqual(rows[0]['votes'],{'forest':2,'mountain':4})
        with self.assertRaises(ValueError):graphical_province_types(ids,graphics,mask,definitions,{1:'forest'})

    def test_trees_are_repeatable_native_models_only_on_woodland(self):
        graphics=np.full((100,100),1,np.uint8);graphics[:,35:65]=21;graphics[45:55]=2
        old=np.full((50,50),5,np.uint8);old[:,18:32]=28
        selected=np.zeros(graphics.shape,bool);selected[20:80,20:80]=True
        source=np.ones((10,10),np.uint8)
        result,allowed,stats=trees_with_native_density(old,source,graphics,selected)
        again,_,_=trees_with_native_density(old,source,graphics,selected)
        np.testing.assert_array_equal(result,again)
        np.testing.assert_array_equal(result[~allowed],old[~allowed])
        self.assertEqual(set(np.unique(result[allowed])),{0,5,28})
        self.assertTrue(np.all(result[23:27,10:40]==0))
        self.assertGreater(stats['forest']['after'],0)
        self.assertGreater(stats['jungle']['after'],0)


if __name__=='__main__':unittest.main()

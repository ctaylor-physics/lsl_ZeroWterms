# -*- coding: utf-8 -*-

"""
Unit test for the lsl.transform module.
"""

import os
import math
import ephem
import unittest

from lsl import transform
from lsl.astro import DJD_OFFSET
from lsl.common.stations import lwa1


__revision__ = "$Rev$"
__version__  = "0.1"
__author__    = "Jayce Dowell"


class transform_tests(unittest.TestCase):
    """A unittest.TestCase collection of unit tests for the lsl.transform
    module."""
    
    def test_time_init(self):
        """Test the transform.Time constructor."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        self.assertEqual(t0.utc_str, '2013-01-08 01:23:45.000')
        
    def test_planetaryposition_init(self):
        """Test the transform.PlanetaryPosition constructor."""
        
        p0 = transform.PlanetaryPosition('Jupiter')
        p1 = transform.PlanetaryPosition('Sun')
        
    def test_planetaryposition_saturn(self):
        """Test the location of Saturn."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        sat = ephem.Saturn()
        sat.compute(obs)
        
        p0 = transform.PlanetaryPosition('Saturn')
        
        self.assertAlmostEqual(p0.apparent_equ(t0)[0], sat.g_ra *180.0/math.pi, 4)
        self.assertAlmostEqual(p0.apparent_equ(t0)[1], sat.g_dec*180.0/math.pi, 4)
        
    def test_planetaryposition_jupiter(self):
        """Test the location of Jupiter."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        jove = ephem.Jupiter()
        jove.compute(obs)
        
        p0 = transform.PlanetaryPosition('Jupiter')
        
        self.assertAlmostEqual(p0.apparent_equ(t0)[0], jove.g_ra *180.0/math.pi, 4)
        self.assertAlmostEqual(p0.apparent_equ(t0)[1], jove.g_dec*180.0/math.pi, 4)
        
    def test_planetaryposition_mars(self):
        """Test the location of Mars."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        mars = ephem.Mars()
        mars.compute(obs)
        
        p0 = transform.PlanetaryPosition('Mars')
        
        self.assertAlmostEqual(p0.apparent_equ(t0)[0], mars.g_ra *180.0/math.pi, 4)
        self.assertAlmostEqual(p0.apparent_equ(t0)[1], mars.g_dec*180.0/math.pi, 4)
        
    def test_planetaryposition_venus(self):
        """Test the location of Venus."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        venu = ephem.Venus()
        venu.compute(obs)
        
        p0 = transform.PlanetaryPosition('Venus')
        
        self.assertAlmostEqual(p0.apparent_equ(t0)[0], venu.g_ra *180.0/math.pi, 4)
        self.assertAlmostEqual(p0.apparent_equ(t0)[1], venu.g_dec*180.0/math.pi, 4)
        
    def test_planetaryposition_sun(self):
        """Test the location of the Sun."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        sol = ephem.Sun()
        sol.compute(obs)
        
        p0 = transform.PlanetaryPosition('Sun')
        
        self.assertAlmostEqual(p0.apparent_equ(t0)[0], sol.g_ra *180.0/math.pi, 4)
        self.assertAlmostEqual(p0.apparent_equ(t0)[1], sol.g_dec*180.0/math.pi, 4)
        
    def test_geographicalposition_init(self):
        """Test the transform.GeographicalPosition constructor."""
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        
    def test_geographicalposition_ecef(self):
        """Test the tranform.GeographicalPosition EC-EF transform."""
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        self.assertAlmostEqual(g0.ecef[0], lwa1.getGeocentricLocation()[0], 6)
        self.assertAlmostEqual(g0.ecef[1], lwa1.getGeocentricLocation()[1], 6)
        self.assertAlmostEqual(g0.ecef[2], lwa1.getGeocentricLocation()[2], 6)
        
    def test_geographicalposition_lst(self):
        """Test the tranform.GeographicalPosition sidereal time."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        obs = lwa1.getObserver()
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        
        # The astro.get_apparent_sidereal_time() function doesn't care about
        # elevation
        obs.elev = 0.0
        
        obs.date = t0.utc_str
        self.assertAlmostEqual(g0.sidereal(t0), obs.sidereal_time()*12.0/math.pi, 4)
        
    def test_pointingdirection_init(self):
        """Test the transform.PointingDirection constructor."""
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        p0 = transform.PlanetaryPosition('Jupiter')
        
        d0 = transform.PointingDirection(p0, g0)
        
    def test_pointingdirection_azalt(self):
        """Test the transform.PointingDirection az/alt transform."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        jove = ephem.Jupiter()
        jove.compute(obs)
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        p0 = transform.PlanetaryPosition('Jupiter')
        d0 = transform.PointingDirection(p0, g0)
        
        self.assertAlmostEqual(d0.hrz(t0)[0], jove.az *180.0/math.pi, 1)
        self.assertAlmostEqual(d0.hrz(t0)[1], jove.alt*180.0/math.pi, 1)
        
    def test_pointingdirection_azalt(self):
        """Test the transform.PointingDirection az/alt transform."""
        
        t0 = transform.Time('2013-01-08 01:23:45.000', format='STR')
        
        lon = lwa1.long * 180.0/math.pi
        lat = lwa1.lat  * 180.0/math.pi
        elv = lwa1.elev
        obs = lwa1.getObserver()
        obs.date = t0.utc_str
        jove = ephem.Jupiter()
        jove.compute(obs)
        
        g0 = transform.GeographicalPosition([lon,lat,elv])
        p0 = transform.PlanetaryPosition('Jupiter')
        d0 = transform.PointingDirection(p0, g0)
        
        rst = d0.rst(t0)
        self.assertAlmostEqual(rst.rise, obs.next_rising(jove)*1.0+DJD_OFFSET, 2)
        self.assertAlmostEqual(rst.transit, obs.next_transit(jove)*1.0+DJD_OFFSET, 2)
        self.assertAlmostEqual(rst.set, obs.next_setting(jove)*1.0+DJD_OFFSET, 2)


class transform_test_suite(unittest.TestSuite):
    """A unittest.TestSuite class which contains all of the lsl.transform units 
    tests."""
    
    def __init__(self):
        unittest.TestSuite.__init__(self)
        
        loader = unittest.TestLoader()
        self.addTests(loader.loadTestsFromTestCase(transform_tests)) 


if __name__ == '__main__':
    unittest.main()

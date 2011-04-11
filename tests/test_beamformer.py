# -*- coding: utf-8 -*-

"""Unit test for the lsl.misc.beamformer module."""

import os
import unittest
import numpy

from lsl.misc import beamformer
from lsl.common import stations


__revision__ = "$Revision:1 $"
__version__  = "0.1"
__author__    = "Jayce Dowell"


class beamformer_tests(unittest.TestCase):
	"""A unittest.TestCase collection of unit tests for the lsl.sim.dp
	module."""

	def test_calcDelay(self):
		"""Check that the beamformer.calcDelay function actually runs"""

		station = stations.lwa1()
		antennas = station.getAntennas()

		out = beamformer.calcDelay(antennas[:3])
		self.assertEqual(len(out), 3)
		
		out = beamformer.calcDelay(antennas[:3], freq=49.0e6)
		self.assertEqual(len(out), 3)

		out = beamformer.calcDelay(antennas[:3], freq=49.0e6, azimuth=45, elevation=30)
		self.assertEqual(len(out), 3)

	def test_pointing_limits(self):
		"""Test that beamformer.calcDelay respects the pointing limits"""

		# Azimuth  checks
		self.assertRaises(beamformer.BeamformingError, beamformer.calcDelay, antennas[:3], 49.0e6, -5, 30)
		self.assertRaises(beamformer.BeamformingError, beamformer.calcDelay, antennas[:3], 49.0e6, 365, 30)

		# Elevation checks
		self.assertRaises(beamformer.BeamformingError, beamformer.calcDelay, antennas[:3], 49.0e6, 45, -5)
		self.assertRaises(beamformer.BeamformingError, beamformer.calcDelay, antennas[:3], 49.0e6, 45, 95)

	def test_intDelayAndSum(self):
		"""Check that the beamformer.intDelayAndSum function actually runs"""
		
		station = stations.lwa1()
		antennas = station.getAntennas()
		data = numpy.random.rand(3, 1000)
		
		beam = beamformer.intDelayAndSum(antennas[:3], data, azimuth=45.0, elevation=30.0)

	def test_intBeamShape(self):
		"""Check that the beamformer.intBeamShape function actually runs"""

		station = stations.lwa1()
		antennas = station.getAntennas()

		out = beamformer.intBeamShape(antennas[:3], azimuth=135.0, elevation=60.0)
		i = out.argmax()
		az = i / 90
		el = i % 90
		self.assertAlmostEqual(az, 135.0, 1)
		self.assertAlmostEqual(el, 60.0, 1)
		

class  beamformer_test_suite(unittest.TestSuite):
	"""A unittest.TestSuite class which contains all of the lsl.sim.vis units 
	tests."""
	
	def __init__(self):
		unittest.TestSuite.__init__(self)
		
		loader = unittest.TestLoader()
		self.addTests(loader.loadTestsFromTestCase(beamformer_tests)) 


if __name__ == '__main__':
	unittest.main()
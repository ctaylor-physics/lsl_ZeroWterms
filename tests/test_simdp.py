# -*- coding: utf-8 -*-

"""Unit test for the lsl.sim.dp module."""

import os
import unittest
import numpy
import tempfile

from lsl.sim import dp
from lsl.reader import tbw
from lsl.reader import tbn
from lsl.reader import drx
from lsl.common import dp as dp_common
from lsl.common import stations as lwa_common


__revision__ = "$ Revision: 2 $"
__version__  = "0.2"
__author__    = "Jayce Dowell"


class simdp_tests(unittest.TestCase):
	"""A unittest.TestCase collection of unit tests for the lsl.sim.dp
	module."""

	testPath = None

	def setUp(self):
		"""Turn off all numpy warnings and create the temporary file directory."""

		numpy.seterr(all='ignore')
		self.testPath = tempfile.mkdtemp(prefix='test-simdp-', suffix='.tmp')

	def test_basic_tbw(self):
		"""Test building a basic TBW signal"""

		testFile = os.path.join(self.testPath, 'tbw.dat')

		fh = open(testFile, 'wb')
		dp.basicSignal(fh, numpy.array([1,2,3,4]), 30000, mode='TBW', bits=12, tStart=1000)
		fh.close()

		# Check file size
		fileSize = os.path.getsize(testFile)
		nSamples = fileSize / tbw.FrameSize
		self.assertEqual(nSamples, 30000*4)

		# Check the time of the first frame
		fh = open(testFile, 'rb')
		frame = tbw.readFrame(fh)
		fh.close()
		self.assertEqual(frame.data.timeTag, 1000*dp_common.fS)

		# Check that the frames have the correct value of data bits
		self.assertEqual(frame.getDataBits(), 12)

	def test_basic_tbn(self):
		"""Test building a basic TBN signal"""

		testFile = os.path.join(self.testPath, 'tbn.dat')

		fh = open(testFile, 'wb')
		dp.basicSignal(fh, numpy.array([1,2,3,4]), 2000, mode='TBN', filter=7, tStart=1000)
		fh.close()

		# Check the file size
		fileSize = os.path.getsize(testFile)
		nSamples = fileSize / tbn.FrameSize
		self.assertEqual(nSamples, 2000*4*2)

		# Check the time of the first frame
		fh = open(testFile, 'rb')
		frame = tbn.readFrame(fh)
		fh.close()
		self.assertEqual(frame.data.timeTag, 1000*dp_common.fS)

	def test_basic_drx(self):
		"""Test building a basic DRX signal"""

		testFile = os.path.join(self.testPath, 'drx.dat')

		fh = open(testFile, 'wb')
		dp.basicSignal(fh, numpy.array([1,2,3,4]), 10, mode='DRX', filter=6, nTuning=2, tStart=1000)
		fh.close()

		# Check the file size
		fileSize = os.path.getsize(testFile)
		nSamples = fileSize / drx.FrameSize
		self.assertEqual(nSamples, 10*4*2*2)

		# Check the file size
		fh = open(testFile, 'rb')
		frame = drx.readFrame(fh)
		fh.close()
		self.assertEqual(frame.data.timeTag, 1000*dp_common.fS)

	def tearDown(self):
		"""Remove the test path directory and its contents"""

		tempFiles = os.listdir(self.testPath)
		for tempFile in tempFiles:
			os.unlink(os.path.join(self.testPath, tempFile))
		os.rmdir(self.testPath)
		self.testPath = None


class  simdp_test_suite(unittest.TestSuite):
	"""A unittest.TestSuite class which contains all of the lsl.sim.vis units 
	tests."""
	
	def __init__(self):
		unittest.TestSuite.__init__(self)
		
		loader = unittest.TestLoader()
		self.addTests(loader.loadTestsFromTestCase(simdp_tests)) 


if __name__ == '__main__':
	unittest.main()
# -*- coding: utf-8 -*-

"""
Module for querying the earth orientation parameters for a given date/list
of dates.
"""

import os
import gzip
import time
import ephem
import numpy
import socket
import urllib2
import logging
import tempfile

import lsl.astro as astro
import lsl.common.paths as paths

__version__ = '0.3'
__revision__ = '$Rev$'
__all__ = ['EOP', 'getEOP', 'getEOPRange', '__version__', '__revision__', '__all__']

# Logger for capturing problems with downloading EOP data
__logger = logging.getLogger('__main__')


# Create the cache directory
if not os.path.exists(os.path.join(os.path.expanduser('~'), '.lsl')):
	os.mkdir(os.path.join(os.path.expanduser('~'), '.lsl'))
_CacheDir = os.path.join(os.path.expanduser('~'), '.lsl', 'geodesy_cache')
if not os.path.exists(_CacheDir):
	os.mkdir(_CacheDir)


class EOP(object):
	"""
	Object for storing the geodetic parameters relevant for DiFX input 
	files:
	  * mjd - modified Julian Date of the measurement/prediction
	  * x - difference between the celestial ephemeric pole (CEP) and the 
	    international reference pole (IRP) in the direction of the IERS
	    meridian [arc seconds]
	  * y - difference between the CEP and IRP in the direction of 90 degrees 
	    west longitude [arc seconds]
	  * UT1-UTC - difference between rotation angle about the pole and UTC
	    [seconds]
	  * type - whether the values for the given MJD are observed (final/IERS) or
	    predicted.
	"""

	def __init__(self, mjd=0.0, x=0.0, y=0.0, dx=0.0, dy=0.0, utDiff=0.0, type='final'):
		self.mjd = mjd
		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.utDiff = utDiff
		self.type = type

		self.__setDate()

	def fromMAIA(self, line):
		"""
		Given a line from a MAIA standard rapid EOP data (IAU2000) file, fill
		in the object's values with the needed information.
		"""

		self.mjd = float(line[7:15])
		self.x = float(line[18:27])
		self.y = float(line[37:46])
		self.dx = float(line[97:106]) / 1000.0
		self.dy = float(line[116:125]) / 1000.0
		self.utDiff = float(line[58:68])
		if line[57] == 'I':
			self.type = 'final'
		else:
			self.type = 'prediction'

		self.__setDate()

	def __setDate(self):
		"""
		Use the ephem.Data object to get an easy-to-use date into the structure.
		"""

		# Catch statement for working is version of LSL older than 0.3
		try:
			self.date = ephem.Date(self.mjd + astro.MJD_OFFSET - astro.DJD_OFFSET)
		except AttributeError:
			self.date = ephem.Date(self.mjd + astro.MJD_OFFSET - 2415020.0)

	def __str__(self):
		"""
		Create a string representation of the EOP object that shows the MJD, x, 
		y, and UT1-UTC values.
		"""

		return "%.1f (%s): x=%.6f y=%.6f UT1-UTC=%.6f (%s)" % (self.mjd, str(self.date), self.x, self.y, self.utDiff, self.type)

	def __eq__(self, y):
		"""
		Determine if MJDs of two EOP objects are equal, or if the MJD of a EOP 
		object equal data of a numeric MJD.
		"""

		tX = self.mjd
		try:
			tY = y.mjd
		except:
			tY = float(y)

		if tX == tY:
			return True
		else:
			return False

	def __cmp__(self, y):
		"""
		Method for soring EOP objects based on their MJDs.
		"""

		tX = float(self.date)
		try:
			tY = float(y.date)
		except AttributeError:
			tY = float(y)
		if tY > tX:
			return -1
		elif tX > tY:
			return 1
		else:
			return 0


def __downloadFile(filename, baseURL='http://maia.usno.navy.mil/ser7/', timeout=120):
	try:
		eopFH = urllib2.urlopen('%s%s' % (baseURL, filename), timeout=timeout)
		lines = eopFH.readlines()
		eopFH.close()
	except IOError as e:
		__logger.error('Error downloading file \'%s\': %s', filename, str(e))
		lines = []
	except socket.timeout:
		__logger.error('Timeout after %i seconds downloading historic EOP data', timeout)
		lines = []
		
	if len(lines) == 0:
		return False
	else:
		fh = open(os.path.join(_CacheDir, filename), 'w')
		for line in lines:
			fh.write(line)
		fh.close()
		return True


def __loadHistoric1973(timeout=120):
	"""
	Load in historical values.  The file included with LSL contains values 
	from January 2, 1973 to November 18, 2010.
	"""
	
	if not os.path.exists(os.path.join(_CacheDir, 'finals2000A.all')):
		__downloadFile('finals2000A.all', timeout=timeout)
	else:
		age = time.time() - os.stat(os.path.join(_CacheDir, 'finals2000A.all')).st_mtime
		if age > (3600*24*7):
			__downloadFile('finals2000A.all', timeout=timeout)
			
	fh = open(os.path.join(_CacheDir, 'finals2000A.all'), 'r')
	lines = fh.readlines()
	fh.close()
	
	eops = []
	for line in lines:
		newEOP = EOP()
		try:
			newEOP.fromMAIA(line) 
			# Only include "final" values, not predictions
			if newEOP.type == 'final':
				eops.append(newEOP)
		except:
			pass
	if len(eops) == 0:
		eops.append(None)
	
	return eops


def __loadHistoric1992(timeout=120):
	"""
	Load in historical values from the web.  The downloaded file includes 
	values from January 1, 1992 until today (usually).
	"""
	
	if not os.path.exists(os.path.join(_CacheDir, 'finals2000A.data')):
		__downloadFile('finals2000A.data', timeout=timeout)
	else:
		age = time.time() - os.stat(os.path.join(_CacheDir, 'finals2000A.data')).st_mtime
		if age > (3600*24*7):
			__downloadFile('finals2000A.data', timeout=timeout)
			
	fh = open(os.path.join(_CacheDir, 'finals2000A.data'), 'r')
	lines = fh.readlines()
	fh.close()
	
	eops = []
	for line in lines:
		newEOP = EOP()
		try:
			newEOP.fromMAIA(line) 
			# Only include "final" values, not predictions
			if newEOP.type == 'final':
				eops.append(newEOP)
		except:
			pass
	if len(eops) == 0:
		eops.append(None)
	
	return eops


def __loadCurrent90(timeout=120):
	"""
	Load data for the current 90-day period from MAIA via the web.
	"""

	if not os.path.exists(os.path.join(_CacheDir, 'finals2000A.daily')):
		__downloadFile('finals2000A.daily', timeout=timeout)
	else:
		age = time.time() - os.stat(os.path.join(_CacheDir, 'finals2000A.daily')).st_mtime
		if age > (3600*24):
			__downloadFile('finals2000A.daily', timeout=timeout)
			
	fh = open(os.path.join(_CacheDir, 'finals2000A.daily'), 'r')
	lines = fh.readlines()
	fh.close()
	
	eops = []
	for line in lines:
		newEOP = EOP()
		try:
			newEOP.fromMAIA(line) 
			eops.append(newEOP)
		except:
			pass
	if len(eops) == 0:
		eops.append(None)
	
	return eops


def getEOP(mjd=None, timeout=120):
	"""
	Return a list of earth orientation parameter objects for the specified 
	MJDs.  A MJD of 'None' returns the values for today's date.
	
	.. versionchanged:: 0.5.2
		Added the `timeout' keyword to deal with failures download EOP data.
		The default value is 120 seconds.
		
	.. versionchanged:: 0.7.0
		Added caching of EOP values to speed up subsequent calls
	"""
	
	try:
		junk = len(mjd)
	except TypeError:
		if mjd is None:
			try:
				mjd = [int(float(ephem.now()) + astro.DJD_OFFSET - astro.MJD_OFFSET)]
			except AttributeError:
				mjd = [int(float(ephem.now()) + 2415020.0 - astro.MJD_OFFSET)]
		else:
			mjd = [int(mjd)]
	mjd = numpy.array(mjd).astype(numpy.int32)

	oldEOPs = []
	midEOPs = []
	newEOPs = __loadCurrent90()
	if mjd.min() < 48622:
		oldEOPs = __loadHistoric1973()
	if mjd.min() < newEOPs[0].mjd:
		midEOPs = __loadHistoric1992()
		
	outEOPs = []
	for day in mjd:
		if day in newEOPs:
			outEOPs.append(newEOPs[newEOPs.index(day)])
		elif day in midEOPs:
			outEOPs.append(midEOPs[midEOPs.index(day)])
		elif day in oldEOPs:
			outEOPs.append(oldEOPs[oldEOPs.index(day)])
		else:
			outEOPs.append(None)
	
	if len(mjd) == 1:
		outEOPs = outEOPs[0]
	return outEOPs
		

def getEOPRange(start=None, stop=None, timeout=120):
	"""
	Return a list of orientation parameter objects that span the start and 
	stop (inclusive) MJDs provided.  Values of 'None' indicate today's date.
	
	.. versionchanged:: 0.5.2
		Added the `timeout' keyword to deal with failures download EOP data.
		The default value is 120 seconds.
	"""

	if start is None:
		try:
			start = int(float(ephem.now()) + astro.DJD_OFFSET - astro.MJD_OFFSET)
		except AttributeError:
			start = int(float(ephem.now()) + 2415020.0 - astro.MJD_OFFSET)
	if stop is None:
		try:
			stop = int(float(ephem.now()) + astro.DJD_OFFSET - astro.MJD_OFFSET)
		except AttributeError:
			stop = int(float(ephem.now()) + 2415020.0 - astro.MJD_OFFSET)

	mjdList = numpy.arange(start, stop+1)
	return getEOP(mjdList, timeout=timeout)

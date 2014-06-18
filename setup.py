# -*- coding: utf-8 -*

import ez_setup
ez_setup.use_setuptools()

import os
import imp
import sys
import glob
import tempfile
import unittest
import commands
import platform

from setuptools import setup, Extension, Distribution, find_packages
try:
	import numpy
except ImportError:
	pass
try:
	import multiprocessing
except ImportError:
	pass
import logging


def get_version():
	"""Read the VERSION file and return the version number as a string."""

	return open('VERSION').read().strip()


def get_description(filename):
	"""Read in a README-type file and return the contents of the DESCRIPTION
	section."""

	desc = ''
	fh = open(filename, 'r')
	lines = fh.readlines()
	fh.close()

	inDescription = False
	for line in lines:
		line = line.replace('\n', '')
		line = line.replace('\t', '')
		if line.find('DESCRIPTION') == 0:
			inDescription = True
			continue
		if line.find('REQUIREMENTS') == 0:
			inDescription = False
			break
		if inDescription:
			desc = ' '.join([desc, line])

	return desc


def get_openmp():
	"""Try to compile/link an example program to check for OpenMP support.
	
	Based on:
	  1) http://stackoverflow.com/questions/16549893/programatically-testing-for-openmp-support-from-a-python-setup-script
	  2) https://github.com/lpsinger/healpy/blob/6c3aae58b5f3281e260ef7adce17b1ffc68016f0/setup.py
	"""
	
	import shutil
	from distutils import sysconfig
	from distutils import ccompiler
	compiler = ccompiler.new_compiler()
	sysconfig.get_config_vars()
	sysconfig.customize_compiler(compiler)
	cc = compiler.compiler
	
	tmpdir = tempfile.mkdtemp()
	curdir = os.getcwd()
	os.chdir(tmpdir)
	
	fh = open('test.c', 'w')
	fh.write(r"""#include <omp.h>
#include <stdio.h>
int main() {
#pragma omp parallel
printf("Hello from thread %d, nthreads %d\n", omp_get_thread_num(), omp_get_num_threads());
}
""")
	fh.close()
	
	status, output = commands.getstatusoutput('%s -fopenmp test.c -o test -lgomp' % ' '.join(cc))
	
	os.chdir(curdir)
	shutil.rmtree(tmpdir)
	
	if status == 0:
		outCFLAGS = ['-fopenmp',]
		outLIBS = ['-lgomp',]
	else:
		print "WARNING:  OpenMP does not appear to be supported by %s, disabling" % cc[0]
		outCFLAGS = []
		outLIBS = []
		
	return outCFLAGS, outLIBS


def get_fftw():
	"""Use pkg-config (if installed) to figure out the C flags and linker flags
	needed to compile a C program with FFTW3 (floating point version).  If FFTW3 
	cannot be found via pkg-config, some 'sane' values are returned."""

	status, output = commands.getstatusoutput('pkg-config fftw3f --exists')
	if status == 0:
		configCommand = 'pkg-config fftw3f'
		outVersion = os.popen('%s --modversion' % configCommand, 'r').readline().rstrip().split()
		outCFLAGS = os.popen('%s --cflags' % configCommand, 'r').readline().rstrip().split()
		outLIBS = os.popen('%s --libs' % configCommand, 'r').readline().rstrip().split()
		
		if len(outVersion) > 0:
			print "Found FFTW3, version %s" % outVersion[0]
			
	else:
		print "WARNING:  FFTW3 cannot be found, using defaults"
		if platform.system() != 'FreeBSD':
			outCFLAGS = []
			outLIBS = ['-lfftw3f', '-lm']
		else:
			outCFLAGS = ['-I/usr/local/include',]
			outLIBS = ['-L/usr/local/lib', '-lfftw3f', '-lm']
			
	return outCFLAGS, outLIBS


def get_atlas():
	"""Use NumPy's system_info module to find the location of ATLAS (and 
	cblas)."""
	
	from numpy.distutils.system_info import get_info
	
	atlas_info = get_info('atlas_blas', notfound_action=2)
	
	atlas_version = ([v[3:-3] for k,v in atlas_info.get('define_macros',[])
					if k == 'ATLAS_INFO']+[None])[0]
	if atlas_version:
		print "Found ATLAS, version %s" % atlas_version
		
	outCFLAGS = ['-I%s' % idir for idir in atlas_info['include_dirs']]
	outLIBS = ['-L%s' % ldir for ldir in atlas_info['library_dirs']]
	outLIBS.extend(['-l%s' % lib for lib in atlas_info['libraries']])
	
	return outCFLAGS, outLIBS


def write_version_info():
	"""Write the version info to a module in LSL."""
	
	lslVersion = get_version()
	shortVersion = '.'.join(lslVersion.split('.')[:2])
	
	contents = """# -*- coding: utf-8 -*-
# This file is automatically generated by setup.py

version = '%s'
full_version = '%s'
short_version = '%s'

""" % (lslVersion, lslVersion, shortVersion)


	
	fh = open('lsl/version.py', 'w')
	fh.write(contents)
	fh.close()
	
	return True


# Get the FFTW flags/libs and manipulate the flags and libraries for 
# correlator._core appropriately.  This will, hopefully, fix the build
# problems on Mac
cflags, libs = get_fftw()
atlasFlags, atlasLibs = get_atlas()
openmpFlags, openmpLibs = get_openmp()

coreExtraFlags = []
coreExtraFlags.extend(openmpFlags)
coreExtraFlags.extend(cflags)
coreExtraFlags.extend(atlasFlags)
coreExtraLibs = []
coreExtraLibs.extend(openmpLibs)
coreExtraLibs.extend(libs)
coreExtraLibs.extend(atlasLibs)

drsuExtraFlags = ['-D_GNU_SOURCE', '-O3', '-fmessage-length=0', '-MMD', '-MP']
drsuExtraLibs = ['-lrt', '-lgdbm']

# Create the list of extension modules.  We do this here so that we can turn 
# off the DRSU direct module for non-linux system
ExtensionModules = [Extension('reader._gofast', ['lsl/reader/gofast.c'], include_dirs=[numpy.get_include()], extra_compile_args=['-funroll-loops']),
			Extension('common._fir', ['lsl/common/fir.c'], include_dirs=[numpy.get_include()], 
libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs),
			Extension('correlator._spec', ['lsl/correlator/spec.c'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
			Extension('correlator._stokes', ['lsl/correlator/stokes.c'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs),
			Extension('correlator._core', ['lsl/correlator/core.c'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
			Extension('sim._simfast', ['lsl/sim/simfast.c', 'lsl/sim/const.c', 'lsl/sim/j1.c', 'lsl/sim/polevl.c', 'lsl/sim/mtherr.c', 'lsl/sim/sf_error.c'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
			Extension('misc._wisdom', ['lsl/misc/wisdom.c'],include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), ]

# Update the version information
write_version_info()

setup(
	name = "lsl", 
	version = get_version(), 
	description = "LWA Software Library", 
	author = "Jayce Dowell", 
	author_email = "jdowell@unm.edu", 
	url = "http://fornax.phys.unm.edu/lwa/trac/", 
	long_description = get_description('README'), 
	license = 'GPL',
	classifiers = ['Development Status :: 4 - Beta',
			'Intended Audience :: Science/Research',
			'License :: OSI Approved :: GNU General Public License (GPL)',
			'Topic :: Scientific/Engineering :: Astronomy'],
	packages = find_packages(), 
	scripts = glob.glob('scripts/*.py'), 
	setup_requires = ['numpy>=1.2'], 
	install_requires = ['pyfits>=3.1', 'numpy>=1.2', 'scipy>=0.7', 'pyephem>=3.7.5', 'aipy>=0.9.1', 'pytz>=2011k'], 
	dependency_links = ['http://www.stsci.edu/resources/software_hardware/pyfits/Download'], 
	include_package_data = True,  
	ext_package = 'lsl', 
	ext_modules = ExtensionModules,
	zip_safe = False,  
	test_suite = "tests.test_lsl.lsl_tests"
) 

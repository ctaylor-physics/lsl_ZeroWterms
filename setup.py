# -*- coding: utf-8 -*

# Python3 compatibility
from __future__ import print_function

import os
import imp
import sys
import glob
import tempfile
import unittest
import platform
import warnings
import subprocess
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

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
        if line.find('DESCRIPTION') == 0:
            inDescription = True
            continue
        if line.find('REQUIREMENTS') == 0:
            inDescription = False
            break
        if inDescription:
            if line[:3] == '---':
                continue
            desc = ''.join([desc, line])

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
int main(void) {
#pragma omp parallel
printf("Hello from thread %d, nthreads %d\n", omp_get_thread_num(), omp_get_num_threads());
return 0;
}
""")
    fh.close()
    
    ccmd = []
    ccmd.extend( cc )
    ccmd.extend( ['-fopenmp', 'test.c', '-o test', '-lgomp'] )
    try:
        output = subprocess.check_call(ccmd)
        outCFLAGS = ['-fopenmp',]
        outLIBS = ['-lgomp',]
        
    except subprocess.CalledProcessError:
        print("WARNING:  OpenMP does not appear to be supported by %s, disabling" % cc[0])
        outCFLAGS = []
        outLIBS = []
        
    finally:
        os.chdir(curdir)
        shutil.rmtree(tmpdir)
        
    return outCFLAGS, outLIBS


def get_fftw():
    """Use pkg-config (if installed) to figure out the C flags and linker flags
    needed to compile a C program with FFTW3 (floating point version).  If FFTW3 
    cannot be found via pkg-config, some 'sane' values are returned."""
    
    try:
        subprocess.check_call(['pkg-config', 'fftw3f', '--exists'])
        
        p = subprocess.Popen(['pkg-config', 'fftw3f', '--modversion'], stdout=subprocess.PIPE)
        outVersion = p.communicate()[0].rstrip().split()
        
        p = subprocess.Popen(['pkg-config', 'fftw3f', '--cflags'], stdout=subprocess.PIPE)
        outCFLAGS = p.communicate()[0].rstrip().split()
        try:
            outCFLAGS = [str(v, 'utf-8') for v in outCFLAGS]
        except TypeError:
            pass
        
        p = subprocess.Popen(['pkg-config', 'fftw3f', '--libs'], stdout=subprocess.PIPE)
        outLIBS = p.communicate()[0].rstrip().split()
        try:
            outLIBS = [str(v, 'utf-8') for v in outLIBS]
        except TypeError:
            pass
            
        if len(outVersion) > 0:
            print("Found FFTW3, version %s" % outVersion[0])
            
    except (OSError, subprocess.CalledProcessError):
        print("WARNING:  FFTW3 cannot be found, using defaults")
        outCFLAGS = []
        outLIBS = ['-lfftw3f', '-lm']
        
    return outCFLAGS, outLIBS


def get_atlas():
    """Use NumPy's system_info module to find the location of ATLAS (and 
    cblas)."""
    
    from numpy.distutils.system_info import get_info
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",category=DeprecationWarning)
        sys.stdout = StringIO()
        atlas_info = get_info('atlas_blas', notfound_action=2)
        sys.stdout = sys.__stdout__
        
    atlas_version = ([v[3:-3] for k,v in atlas_info.get('define_macros',[])
                    if k == 'ATLAS_INFO']+[None])[0]
    if atlas_version:
        print("Found ATLAS, version %s" % atlas_version)
        
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

import os
import glob
import hashlib

def _get_md5(filename, blockSize=262144):
    with open(filename, 'rb') as fh:
        m = hashlib.md5()
        while True:
            block = fh.read(blockSize)
            if len(block) == 0:
                break
            m.update(block)
            
    return m.hexdigest()

def get_fingerprint():
    \"\"\"
    Return a 'fingerprint' of the current LSL module state that is useful for
    tracking if the module has changed.
    \"\"\"
    
    filenames = []
    for ext in ('.py', '.so'):
        filenames.extend( glob.glob(os.path.join(os.path.dirname(__file__), '*%%s' %% ext)) )
        filenames.extend( glob.glob(os.path.join(os.path.dirname(__file__), '*', '*%%s' %% ext)) )
        
    m = hashlib.md5()
    for filename in filenames:
        m.update(_get_md5(filename))
    return m.hexdigest()

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

coreExtraFlags = ['-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION']
coreExtraFlags.extend(openmpFlags)
coreExtraFlags.extend(cflags)
coreExtraFlags.extend(atlasFlags)
coreExtraLibs = []
coreExtraLibs.extend(openmpLibs)
coreExtraLibs.extend(libs)
coreExtraLibs.extend(atlasLibs)

# Create the list of extension modules.  We do this here so that we can turn 
# off the DRSU direct module for non-linux system
ExtensionModules = [Extension('reader._gofast', ['lsl/reader/gofast.c', 'lsl/reader/tbw.c', 'lsl/reader/tbn.c', 'lsl/reader/drx.c', 'lsl/reader/drspec.c', 'lsl/reader/vdif.c', 'lsl/reader/tbf.c', 'lsl/reader/cor.c'], include_dirs=[numpy.get_include()], extra_compile_args=['-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION', '-funroll-loops']),
            Extension('common._fir', ['lsl/common/fir.cpp'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs),
            Extension('correlator._spec', ['lsl/correlator/spec.cpp'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
            Extension('correlator._stokes', ['lsl/correlator/stokes.cpp'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs),
            Extension('correlator._core', ['lsl/correlator/core.cpp'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
            Extension('imaging._gridder', ['lsl/imaging/gridder.cpp'], include_dirs=[numpy.get_include()], libraries=['m'], extra_compile_args=coreExtraFlags, extra_link_args=coreExtraLibs), 
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
    url = "https://fornax.phys.unm.edu/lwa/trac/", 
    long_description = get_description('README.md'), 
    license = 'GPL',
    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Topic :: Scientific/Engineering :: Astronomy',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX :: Linux'],
    packages = find_packages(), 
    scripts = glob.glob('scripts/*.py'), 
    python_requires='>=2.7, <3', 
    setup_requires = ['numpy>=1.7'], 
    install_requires = ['astropy<2.0', 'numpy>=1.2', 'scipy>=0.7', 'pyephem>=3.7.5', 'aipy>=1.0', 'pytz>=2011k'], 
    include_package_data = True,  
    ext_package = 'lsl', 
    ext_modules = ExtensionModules,
    zip_safe = False,  
    test_suite = "tests"
) 

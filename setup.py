from setuptools import setup, Extension, find_packages
import sys

# Try to import pysam, but don't fail if it's not available yet
# (it might be installed as a dependency)
try:
    import pysam
    PYSAM_AVAILABLE = True
    from distutils.version import LooseVersion
    required_pysam_version = '0.15'
    if LooseVersion(pysam.__version__) < LooseVersion(required_pysam_version):
        print(f'Warning: pysam version >= {required_pysam_version} is recommended; found {pysam.__version__}', 
              file=sys.stderr)
except ImportError:
    PYSAM_AVAILABLE = False
    pysam = None


def get_version():
    """Extract version number from source file."""
    from ast import literal_eval
    with open('pysamstats/__init__.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return literal_eval(line.partition('=')[2].lstrip())
    raise ValueError("__version__ not found")


import os

try:
    from Cython.Build import cythonize
    HAVE_CYTHON = True
except ImportError:
    HAVE_CYTHON = False

# Get pysam configuration if available
if PYSAM_AVAILABLE:
    pysam_include_dirs = pysam.get_include()
    pysam_defines = pysam.get_defines()
else:
    # Try to find pysam from installed packages or local build
    pysam_include_dirs = []
    pysam_defines = []
    
    # Check for local pysam build
    pysam_path = os.path.join(os.path.dirname(__file__), '..', 'pysam')
    if os.path.exists(pysam_path):
        pysam_include_dirs = [
            os.path.join(pysam_path, 'pysam'),
            os.path.join(pysam_path, 'htslib'),
        ]
    else:
        # Will be resolved at runtime after pysam is installed as dependency
        print('[pysamstats] Warning: pysam not found, using empty include dirs')

# Decide whether to use Cython or pre-compiled C
# Check if we have a pre-compiled C file
opt_c_file = 'pysamstats/opt.c'
has_precompiled_c = os.path.exists(opt_c_file)

# Prefer Cython if pysam is available, otherwise use pre-compiled C if available
if HAVE_CYTHON and PYSAM_AVAILABLE:
    print('[pysamstats] build with Cython (pysam available)')
    extensions = cythonize([
        Extension('pysamstats.opt',
                  sources=['pysamstats/opt.pyx'],
                  include_dirs=pysam_include_dirs,
                  define_macros=pysam_defines)]
    )
elif has_precompiled_c:
    print('[pysamstats] build from pre-compiled C (pysam not yet available or Cython missing)')
    # Use the pre-compiled .c file that doesn't require pysam at build time
    extensions = [Extension('pysamstats.opt',
                            sources=['pysamstats/opt.c'],
                            include_dirs=pysam_include_dirs,
                            define_macros=pysam_defines)]
else:
    raise Exception(
        '[pysamstats] ERROR: Cannot build extension. Either:\n'
        '  1. Install pysam first and have Cython available, or\n'
        '  2. Provide a pre-compiled pysamstats/opt.c file\n'
        f'  Current state: HAVE_CYTHON={HAVE_CYTHON}, PYSAM_AVAILABLE={PYSAM_AVAILABLE}, '
        f'has_precompiled_c={has_precompiled_c}'
    )


setup(
    name='pysamstats',
    version=get_version(),
    author='Alistair Miles',
    author_email='alimanfoo@googlemail.com',
    url='https://github.com/alimanfoo/pysamstats',
    license='MIT Licenses',
    description='A Python utility for calculating statistics against genome '
                'position based on sequence alignments from a SAM, '
                'BAM or CRAM file.',
    scripts=['scripts/pysamstats'],
    package_dir={'': '.'},
    install_requires=[
        "pysam>=0.15",
        "numpy",
    ],
    setup_requires=[
        "Cython>=0.29.12",
        "numpy",
    ],
    packages=find_packages(),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    ext_modules=extensions,
)

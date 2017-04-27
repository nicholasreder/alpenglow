from __future__ import absolute_import, division, print_function
from os.path import join as pjoin

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 2
_version_micro = ''  # use '' for first of series, number for 1 and above
_version_extra = 'dev'
# _version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Development Status :: 3 - Alpha",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: MIT License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

# Description should be a one-liner:
description = "alpenglow: stitching light-sheet images"
# Long description will go up on the pypi page
long_description = """
Alpenglow
========
Please go to the repository README_ for further details.
.. _README: https://github.com/nicholasreder/alpenglow/blob/master/README.md
"""

NAME = "alpenglow"
MAINTAINER = "Nicholas Reder"
MAINTAINER_EMAIL = "nreder@uw.edu"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://github.com/nicholasreder/alpenglow"
DOWNLOAD_URL = ""
LICENSE = "MIT"
AUTHOR = "Nicholas Reder"
AUTHOR_EMAIL = "nreder@uw.edu"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
REQUIRES = ["numpy", "skimage", "boto3", "PIL"]

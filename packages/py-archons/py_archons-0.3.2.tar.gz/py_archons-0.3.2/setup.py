"""Setup script for py-archons package."""

import os
import re
from setuptools import setup

def read_version():
    """Read version from py_archons/version.py"""
    version_file = os.path.join(os.path.dirname(__file__), 'py_archons', 'version.py')
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Extract version using regex
    version_match = re.search(r'__version__ = ["\']([^"\']*)["\']', content)
    if version_match:
        return version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in version.py")

setup(version=read_version())

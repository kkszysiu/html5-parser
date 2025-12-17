#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: Apache 2.0 Copyright: 2017, Kovid Goyal <kovid at kovidgoyal.net>

"""
Minimal setup.py for C extension configuration.
All metadata is in pyproject.toml.
"""

import os
import re
import shlex
import subprocess
import sys
from itertools import chain

from setuptools import Extension, setup

self_path = os.path.abspath(__file__)
base = os.path.dirname(self_path)

# Platform detection
iswindows = hasattr(sys, 'getwindowsversion')
PKGCONFIG = os.environ.get('PKGCONFIG_EXE', 'pkg-config')


def get_version():
    """Read version from pyproject.toml."""
    with open(os.path.join(base, 'pyproject.toml')) as f:
        match = re.search(r'^version = "(\d+)\.(\d+)\.(\d+)"', f.read(), flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find version in pyproject.toml")
    return tuple(map(int, match.groups()))


def pkg_config(pkg, *args):
    """Get compiler/linker flags from pkg-config."""
    try:
        val = subprocess.check_output([PKGCONFIG, pkg] + list(args)).decode('utf-8')
    except FileNotFoundError:
        raise SystemExit('pkg-config is required to build html5-parser')
    return list(filter(None, shlex.split(val)))


def env_var(which, default='', split=os.pathsep):
    """Get environment variable, optionally split by separator."""
    val = str(os.environ.get(which, default))
    if not split:
        return val
    return list(filter(None, val.split(split)))


def include_dirs():
    """Get include directories for libxml2."""
    if 'LIBXML_INCLUDE_DIRS' in os.environ:
        return env_var('LIBXML_INCLUDE_DIRS')
    return [x[2:] for x in pkg_config('libxml-2.0', '--cflags-only-I')]


def libraries():
    """Get libraries to link against."""
    if iswindows:
        return env_var('LIBXML_LIBS', 'libxml2')
    if 'LIBXML_LIBS' in os.environ:
        return env_var('LIBXML_LIBS')
    return [x[2:] for x in pkg_config('libxml-2.0', '--libs-only-l')]


def library_dirs():
    """Get library directories."""
    if 'LIBXML_LIB_DIRS' in os.environ:
        return env_var('LIBXML_LIB_DIRS')
    return [x[2:] for x in pkg_config('libxml-2.0', '--libs-only-L')]


def find_c_files(src_dir):
    """Find all C source files in a directory."""
    ans = []
    for x in sorted(os.listdir(os.path.join(base, src_dir))):
        if x.endswith('.c') and not x.endswith('-check.c'):
            ans.append(os.path.join(src_dir, x))
    return ans


# Source directories
SRC_DIRS = ['src', 'gumbo']

# Collect all C source files
src_files = list(chain(*[find_c_files(d) for d in SRC_DIRS]))

# Compiler flags
cargs = ['/O2'] if iswindows else ['-O3', '-std=c99', '-fvisibility=hidden']

# Get version for macros
version = get_version()

setup(
    ext_modules=[
        Extension(
            'html5_parser.html_parser',
            include_dirs=include_dirs(),
            libraries=libraries(),
            library_dirs=library_dirs(),
            extra_compile_args=cargs,
            define_macros=[
                ('MAJOR', str(version[0])),
                ('MINOR', str(version[1])),
                ('PATCH', str(version[2])),
            ],
            sources=src_files,
        )
    ]
)

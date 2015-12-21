from __future__ import print_function

from setuptools import setup
from setuptools.command.test import test as TestCommand

import os
import sys

import uberdict

here_dir = os.path.abspath(os.path.dirname(__file__))


def read(*filenames):
    buf = []
    for filename in filenames:
        filepath = os.path.join(here_dir, filename)
        try:
            with open(filepath, 'r') as f:
                buf.append(f.read())
        except IOError:
            # ignore tox IOError (no such file or directory)
            pass
    return '\n\n'.join(buf)

long_description = read('README.md', 'CHANGES.md')


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='uberdict',
    version=uberdict.__version__,
    url='http://github.com/eukaryote/uberdict/',
    author='Calvin Smith',
    author_email='sapientdust+uberdict@gmail.com',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    description=(
        'A Python dict that supports attribute-style access as '
        'well as hierarchical keys.'
    ),
    long_description=long_description,
    packages=['uberdict'],
    platforms='any',
    test_suite='tests',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 2 - Beta'
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    extras_require={
        'testing': ['pytest'],
        'develop': ['wheel'],
    }
)

#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup, find_packages

setup(name="boolmatch",
      version="1.0",
      description="Compare text to a boolean expression of terms.",
      author="Jack Diederich",
      author_email="jackdied@gmail.com",
      url="http://github.com/jackdied/boolmatch",
      packages = find_packages(),
      license = "MIT License",
      keywords="bool boolean",
      zip_safe = True,
      py_modules=['boolmatch'],
      classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
     )

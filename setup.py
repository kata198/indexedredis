#!/usr/bin/env python

import sys

from setuptools import setup

if __name__ == '__main__':

    summary = 'A super-fast ORM backed by Redis, supporting models and indexes with O(1) searches, and support for storing native/complex types and objects'
    try:
        with open('README.rst', 'rt') as f:
            long_description = f.read()
    except Exception as e:
        sys.stderr.write('Error reading description: %s\n' %(str(e),))
        long_description = summary

    setup(name='indexedredis',
        version='5.0.2',
        packages=['IndexedRedis', 'IndexedRedis.fields'],
        install_requires=['redis', 'QueryableList'],
        requires=['redis', 'QueryableList'],
        provides=['indexedredis'],
        keywords=['redis', 'IndexedRedis', 'SQL', 'nosql', 'orm', 'fast', 'python', 'filter', 'index', 'model'],
        url='https://github.com/kata198/indexedredis',
        long_description=long_description,
        author='Tim Savannah',
        author_email='kata198@gmail.com',
        maintainer='Tim Savannah',
        maintainer_email='kata198@gmail.com',
        license='LGPLv2',
        description=summary,
        classifiers=['Development Status :: 5 - Production/Stable',
            'Programming Language :: Python',
            'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Database :: Front-Ends',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ]
        
    )

#vim: set ts=4 sw=4 expandtab


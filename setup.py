#!/usr/bin/env python

from setuptools import setup

if __name__ == '__main__':

    with open('README.rst', 'r') as f:
        long_description = f.read()

    setup(name='indexedredis',
        version='2.8.0',
        packages=['IndexedRedis'],
        install_requires=['redis'],
        requires=['redis'],
        provides=['indexedredis'],
        keywords=['redis', 'IndexedRedis', 'SQL', 'nosql', 'orm', 'fast', 'python'],
	url='https://github.com/kata198/indexedredis',
        long_description=long_description,
        author='Tim Savannah',
        author_email='kata198@gmail.com',
        maintainer='Tim Savannah',
        maintainer_email='kata198@gmail.com',
        license='LGPLv2',
        description='redis-backed very very fast [O(1) efficency searches) ORM-style framework that supports indexes, and complete atomic replacement of datasets',
        classifiers=['Development Status :: 5 - Production/Stable',
            'Programming Language :: Python',
            'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Database :: Front-Ends',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ]
        
    )

#vim: set ts=4 sw=4 expandtab


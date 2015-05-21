from setuptools import setup

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(name='indexedredis',
    version='2.0.4',
    packages=['IndexedRedis'],
    install_requires=['redis'],
    requires=['redis'],
    provides=['indexedredis'],
    keywords=['redis', 'IndexedRedis', 'SQL', 'nosql', 'orm', 'fast', 'python'],
    long_description=long_description,
    author='Tim Savannah',
    author_email='kata198@gmail.com',
    maintainer='Tim Savannah',
    maintainer_email='kata198@gmail.com',
    license='LGPLv2',
    description='redis-backed very very fast ORM-style framework that supports indexes (similar to SQL), and complete atomic replacement of datasets',
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

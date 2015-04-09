from setuptools import setup

long_description = """
IndexedRedis
============
A redis-backed very very fast ORM-style framework that supports indexes (similar to SQL).

Requires a Redis server of at least version 2.6.0, and python-redis [ available at https://pypi.python.org/pypi/redis ]

It supports "equals" operator comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL (by refreshing SQL objects into Redis on a fixed timing interval).

It is compatible with python 2.7 and python 3. It has been extensivly tested with python 2.7, and somewhat tested with 3.4.

IndexedRedisModel
-----------------

   This is the model you should extend.

Required fields:

**FIELDS** is a list of strings, naming "fields" that will be stored

**INDEXED_FIELDS** is a list of strings containing the names of fields that should be indexed. Every field added here slows insert performance,
    because redis is fast, consider not indexing every possible field but rather indexing the ones for best performance and filtering thereafter.

NOTE: You may only query fields contained within the "INDEXED_FIELDS" array. It is certainly possible from within this lib to support non-indexed
    searching, but I'd rather that be done in the client to make obvious where the power of this library is.

**KEY_NAME** is a field which contains the "base" keyname, unique to this object. (Like "Users" or "Drinks")

**REDIS_CONNECTION_PARAMS** provides the arguments to pass into "redis.Redis", to construct a redis object.

An alternative to supplying REDIS_CONNECTION_PARAMS is to supply a class-level variable `_connection`, which contains the redis instance you would like to use. This variable can be created as a class-level override, or set on the model during __init__. 

Usage is like normal ORM:

Get Objects:
 |       SomeModel.objects.filter(param1=val).filter(param2=val).all()

Create Object:
 |      obj = SomeModel(...)
 |      obj.save()

There is also a powerful method called "reset" which will atomically and locked replace all elements belonging to a model. This is useful for cache-replacement, etc.


    x = [SomeModel(...), SomeModel(..)]

    SomeModel.reset(x)

You delete objects by:

    someObj.delete()

and save objects by:

    someObj.save()

Example:
--------

 |
 | from IndexedRedis import IndexedRedisModel
 |
 | class Song(IndexedRedisModel):
 |
 |    FIELDS = [  'artist',
 |                'title',
 |                'album',
 |                'track_number',
 |                'duration',
 |                'description',
 |                'copyright',
 |    ]
 |
 |    INDEXED_FIELDS = [  'artist',
 |                        'title'
 |    ]
 |
 |    KEY_NAME = 'Songs'
 |
 |    def __init__(self, \*args, \*\*kwargs):
 |        IndexedRedisModel.__init__(self)
 |
 |         for key, value in kwargs.items():
 |             setattr(self, key, value)
 |
 |
 |
 | Song.reset([]) # Clear any existing
 |
 | songObj = Song(artist='The Merry Men',
 |               title='Happy Go Lucky',
 |               album='The Merry Men LP',
 |               track_number=1,
 |               duration='1:58',
 |               description='A song about happy people',
 |               copyright='Copyright 2012 (c) Media Mogul Incorporated')
 | songObj.save()
 |
 | songObj = Song(artist='The Merry Men',
 |               title='Joy to Joy',
 |               album='The Merry Men LP',
 |               track_number=2,
 |               duration='2:54',
 |               description='A song about joy',
 |               copyright='Copyright 2012 (c) Media Mogul Incorporated')
 | songObj.save()
 |
 | songObj = Song(artist='The Unhappy Folk',
 |               title='Sadly she waits',
 |               album='Misery loses comfort',
 |               track_number=1,
 |               duration='15:44',
 |               description='A sad song',
 |               copyright='Copyright 2014 (c) Cheese Industries')
 | songObj.save()
 |
 |
 | merryMenSongs = Song.objects.filter(artist='The Merry Men').all()
 | from pprint import pprint
 |
 | for song in merryMenSongs:
 |     pprint(song.toDict)


Output:
-------
 | {'album': 'The Merry Men LP',
 | 'artist': 'The Merry Men',
 | 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
 | 'description': 'A song about joy',
 | 'duration': '2:54',
 | 'title': 'Joy to Joy',
 | 'track_number': '2'}

 | {'album': 'The Merry Men LP',
 |  'artist': 'The Merry Men',
 | 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
 | 'description': 'A song about happy people',
 | 'duration': '1:58',
 | 'title': 'Happy Go Lucky',
 | 'track_number': '1'}

"""


setup(name='indexedredis',
    version='1.1.2',
    py_modules=['IndexedRedis'],
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

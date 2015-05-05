indexedredis
============

A redis-backed very very fast ORM-style framework that supports indexes (similar to SQL).

Requires a Redis server of at least version 2.6.0, and python-redis [ available at https://pypi.python.org/pypi/redis ]

IndexedRedis supports both "equals" and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.

If you have ever used Flask or Django you will recognize strong similarities in the filtering interface. 

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs. For actually redesigning the system to prefetch and .reset (as mentioned above), response time went from ~3.5s per page load to ~20ms [ 17500% faster ].

It is compatible with python 2.7 and python 3. It has been tested with python 2.7 and 3.4.


IndexedRedisModel
-----------------

	This is the model you should extend.

	Required fields:

	**FIELDS** is a list of strings, which name the fields that can be used for storage.

	**INDEXED_FIELDS** is a list of strings containing the names of fields that should be indexed. Every field listed here adds insert performance. To filter on a field, it must be in the INDEXED_FIELDS list.
	
	**KEY_NAME** is the name that represents this model. Think of it like a table name.

	**REDIS_CONNECTION_PARAMS** provides the arguments to pass into "redis.Redis", to construct a redis object.

        | An alternative to supplying REDIS_CONNECTION_PARAMS is to supply a class-level variable `_connection`, which contains the redis instance you would like to use. This variable can be created as a class-level override, or set on the model during __init__. 

		Usage is like normal ORM

		SomeModel.objects.filter(param1=val).filter(param2=val).all()

		obj = SomeModel(...)
		obj.save()

		There is also a powerful method called "reset" which will atomically and locked replace all elements belonging to a model. This is useful for cache-replacement, etc.


		x = [SomeModel(...), SomeModel(..)]

		SomeModel.reset(x)

	You delete objects by

		someObj.delete()

	and save objects by

		someObj.save()
		
Example
-------

 |	import sys
 |	from IndexedRedis import IndexedRedisModel
 |
 |
 |	# Define the model
 |	class Song(IndexedRedisModel):
 |		
 |		FIELDS = [ \\
 |				'artist',
 |				'title',
 |				'album',
 | 				'track_number',
 |				'duration',
 |				'description',
 |				'copyright',
 |		]
 |
 |		INDEXED_FIELDS = [ \\
 |					'artist',
 |					'title',
 |					'track_number',
 |		]
 |
 |		KEY_NAME = 'Songs'
 |
 |		def __init__(self, \*args, \*\*kwargs):
 |			IndexedRedisModel.__init__(self, \*args, \*\*kwargs)
 |
 |
 |	if '--keep-data' not in sys.argv:
 |		newSongs = []
 |
 |		# Add data
 |		songObj = Song(artist='The Merry Men',
 |				title='Happy Go Lucky',
 |				album='The Merry Men LP',
 |				track_number=1,
 |				duration='1:58',
 |				description='A song about happy people',
 |				copyright='Copyright 2012 (c) Media Mogul Incorporated')
 |		newSongs.append(songObj)
 |
 |		songObj = Song(artist='The Merry Men',
 |				title='Joy to Joy',
 |				album='The Merry Men LP',
 |				track_number=2,
 |				duration='2:54',
 |				description='A song about joy',
 |				copyright='Copyright 2012 (c) Media Mogul Incorporated')
 |
 |		newSongs.append(songObj)
 |
 |		songObj = Song(artist='The Unhappy Folk',
 |				title='Sadly she waits',
 |				album='Misery loses comfort',
 |				track_number=1,
 |				duration='15:44',
 |				description='A sad song',
 |				copyright='Copyright 2014 (c) Cheese Industries')
 |		newSongs.append(songObj)
 |
 |		# Atomically reset the Song dataset to just the songs in "newSongs" list
 |		Song.reset(newSongs)
 |
 |		# Add some additional songs one-at-a-time
 |		songObj = Song(artist='Mega Men',
 |				title='Nintendo 1',
 |				album='Super Tracks',
 |				track_number=1,
 |				duration='1:15',
 |				description='Super Nintendo',
 |				copyright='Copyright 2014 (c) Cheese Industries')
 |		songObj.save()
 |
 |		songObj = Song(artist='Mega Men',
 |				title='Nintendo 2',
 |				album='Super Tracks',
 |				track_number=2,
 |				duration='1:55',
 |				description='Super Nintendo',
 |				copyright='Copyright 2014 (c) Cheese Industries')
 |		songObj.save()
 |
 |
 |	# Query some songs by artist
 |	merryMenSongs = Song.objects.filter(artist='The Merry Men').all()
 |	from pprint import pprint
 |
 |	sys.stdout.write("Merry Men Songs:\\n")
 |	for song in merryMenSongs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 |
 |	# Query some songs not by artist
 |	sys.stdout.write('\\n\\nNot Mega Men Songs:\\n')
 |	notMegaMenSongs = Song.objects.filterInline(artist__ne='Mega Men').all()
 |	for song in notMegaMenSongs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 |
 |
 |	sys.stdout.write('\\n\\n')
 |	# Show passing filter objects around functions, and not actually fetching until .all is called.
 |	def getTracks(filterSet, trackNo):
 |		return filterSet.filter(track_number=trackNo).all()
 |
 |	sys.stdout.write('\\nAll track one songs:\\n')
 |
 |	allTrackOneSongs = getTracks(Song.objects, 1)
 |	for song in allTrackOneSongs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 |
 |	sys.stdout.write('\\nMega Men track ones:')
 |	megaMenTracks = Song.objects.filter(artist='Mega Men')
 |
 |
 |	objs = getTracks(megaMenTracks, 1)
 |	for song in objs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 |
 |	sys.stdout.write('\\nMega Men track twos:\\n')
 |
 |	objs = getTracks(megaMenTracks, 2)
 |	for song in objs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 |
 |
 |	sys.stdout.write('\\nAfter Delete, Mega Men Track twos (should be blank):\\n')
 |	song.delete()
 |	objs = getTracks(megaMenTracks, 2)
 |	for song in objs:
 |		pprint(song.asDict())
 |		sys.stdout.write('\\n')
 
 

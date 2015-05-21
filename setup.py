#!/usr/bin/env python

from setuptools import setup

if __name__ == '__main__':

    with open('README.rst', 'r') as f:
        long_description = f.read()

    setup(name='indexedredis',
        version='2.0.4.1',
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

#vim: set ts=4 sw=4 expandtab

example_program = '''
import sys
from IndexedRedis import IndexedRedisModel


# Define the model
class Song(IndexedRedisModel):
	
	FIELDS = [ \
			'artist',
			'title',
			'album',
			'track_number',
			'duration',
			'description',
			'copyright',
	]

	INDEXED_FIELDS = [ \
				'artist',
				'title',
				'track_number',
	]

	KEY_NAME = 'Songs'

	def __init__(self, *args, **kwargs):
		IndexedRedisModel.__init__(self, *args, **kwargs)


if '--keep-data' not in sys.argv:
	newSongs = []

	# Add data
	songObj = Song(artist='The Merry Men',
			title='Happy Go Lucky',
			album='The Merry Men LP',
			track_number=1,
			duration='1:58',
			description='A song about happy people',
			copyright='Copyright 2012 (c) Media Mogul Incorporated')
	newSongs.append(songObj)

	songObj = Song(artist='The Merry Men',
			title='Joy to Joy',
			album='The Merry Men LP',
			track_number=2,
			duration='2:54',
			description='A song about joy',
			copyright='Copyright 2012 (c) Media Mogul Incorporated')

	newSongs.append(songObj)

	songObj = Song(artist='The Unhappy Folk',
			title='Sadly she waits',
			album='Misery loses comfort',
			track_number=1,
			duration='15:44',
			description='A sad song',
			copyright='Copyright 2014 (c) Cheese Industries')
	newSongs.append(songObj)

	# Atomically reset the Song dataset to just the songs in "newSongs" list
	Song.reset(newSongs)

	# Add some additional songs one-at-a-time
	songObj = Song(artist='Mega Men',
			title='Nintendo 1',
			album='Super Tracks',
			track_number=1,
			duration='1:15',
			description='Super Nintendo',
			copyright='Copyright 2014 (c) Cheese Industries')
	songObj.save()

	songObj = Song(artist='Mega Men',
			title='Nintendo 2',
			album='Super Tracks',
			track_number=2,
			duration='1:55',
			description='Super Nintendo',
			copyright='Copyright 2014 (c) Cheese Industries')
	songObj.save()


# Query some songs by artist
merryMenSongs = Song.objects.filter(artist='The Merry Men').all()
from pprint import pprint

sys.stdout.write("Merry Men Songs:\n")
for song in merryMenSongs:
	pprint(song.asDict())
	sys.stdout.write('\n')

# Query some songs not by artist
sys.stdout.write('\n\nNot Mega Men Songs:\n')
notMegaMenSongs = Song.objects.filterInline(artist__ne='Mega Men').all()
for song in notMegaMenSongs:
	pprint(song.asDict())
	sys.stdout.write('\n')


sys.stdout.write('\n\n')
# Show passing filter objects around functions, and not actually fetching until .all is called.
def getTracks(filterSet, trackNo):
	return filterSet.filter(track_number=trackNo).all()

sys.stdout.write('\nAll track one songs:\n')

allTrackOneSongs = getTracks(Song.objects, 1)
for song in allTrackOneSongs:
	pprint(song.asDict())
	sys.stdout.write('\n')

sys.stdout.write('\nMega Men track ones:')
megaMenTracks = Song.objects.filter(artist='Mega Men')


objs = getTracks(megaMenTracks, 1)
for song in objs:
	pprint(song.asDict())
	sys.stdout.write('\n')

sys.stdout.write('\nMega Men track twos:\n')

objs = getTracks(megaMenTracks, 2)
for song in objs:
	pprint(song.asDict())
	sys.stdout.write('\n')


sys.stdout.write('\nAfter Delete, Mega Men Track twos (should be blank):\n')
song.delete()
objs = getTracks(megaMenTracks, 2)
for song in objs:
	pprint(song.asDict())
	sys.stdout.write('\n')
'''

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

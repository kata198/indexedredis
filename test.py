from IndexedRedis import IndexedRedisModel

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
				'title'
	]

	KEY_NAME = 'Songs'

	def __init__(self, *args, **kwargs):
		IndexedRedisModel.__init__(self)

		for key, value in kwargs.iteritems():
			setattr(self, key, value)



Song.reset([]) # Clear any existing

songObj = Song(artist='The Merry Men',
		title='Happy Go Lucky',
		album='The Merry Men LP',
		track_number=1,
		duration='1:58',
		description='A song about happy people',
		copyright='Copyright 2012 (c) Media Mogul Incorporated')
songObj.save()

songObj = Song(artist='The Merry Men',
		title='Joy to Joy',
		album='The Merry Men LP',
		track_number=2,
		duration='2:54',
		description='A song about joy',
		copyright='Copyright 2012 (c) Media Mogul Incorporated')
songObj.save()

songObj = Song(artist='The Unhappy Folk',
		title='Sadly she waits',
		album='Misery loses comfort',
		track_number=1,
		duration='15:44',
		description='A sad song',
		copyright='Copyright 2014 (c) Cheese Industries')
songObj.save()


merryMenSongs = Song.objects.filter(artist='The Merry Men').all()
from pprint import pprint

for song in merryMenSongs:
	pprint(song.__dict__)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

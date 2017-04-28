#!/usr/bin/env python
# vim: set ts=4 sw=4 st=4 expandtab :

import time

startTime = time.time()

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField, setDefaultRedisConnectionParams
from IndexedRedis.fields import IRCompressedField, IRFieldChain, IRRawField, IRBytesField, IRUnicodeField

# vim: set ts=8 sw=8 st=8 expandtab :

#  Change this to match your Redis server info
REDIS_CONNECTION_PARAMS = { 'host' : '127.0.0.1', 'port' : 6379, 'db' : 0 }

# Define the model
class Song(IndexedRedisModel):
    
    FIELDS = [ \
            IRField('artist'),
            IRField('title'),
            IRField('album'),
            IRField('track_number', valueType=int), # Convert automatically to/from int
            IRField('duration'),
            IRField('releaseDate', valueType=datetime.datetime),
            IRField('description'),
            IRField('copyright'),
            IRRawField('mp3_data'), # Do not perform any conversion on the data.
            IRFieldChain('thumbnail', [IRBytesField(), IRCompressedField(compressMode='gzip')]),      # Compress this field in storage using "bz2" compression
            IRField('tags', valueType=list),
            IRFieldChain('lyrics', [ IRUnicodeField(encoding='utf-8'), IRCompressedField() ], defaultValue='No lyrics found'),
    ]

    INDEXED_FIELDS = [ \
                'artist',
                'title',
                'track_number',
    ]

    KEY_NAME = 'Songs'

if __name__ == '__main__':

    setDefaultRedisConnectionParams(REDIS_CONNECTION_PARAMS)

    fakeMp3 = b"\x99\x12\x14"

    fakeThumbnail = b"\x15\x1A\x1A\x1A\x1A\x1A\x1A\x1B\x1A\x1A\x1A\x1B" + (b"\x1A" * 30) # Compressable data

    sys.stdout.write('Testing IndexedRedis version %s\n' %(IndexedRedis.__version__,))

    if '--keep-data' not in sys.argv:
            newSongs = []
            # Add data
            songObj = Song(artist='The Merry Men',
                            title='Happy Go Lucky',
                            album='The Merry Men LP',
                            track_number=1,
                            duration='1:58',
                            description='A song about happy people',
                            mp3_data=fakeMp3,
                            thumbnail=fakeThumbnail,
                            tags=['happy', 'guitar', 'smooth'],
                            copyright='Copyright 2012 (c) Media Mogul Incorporated')

            songObj.lyrics = '''To love, to lie,
to feel something rather than die
A line, a fall
I guess we can't be loved by them all..
'''

            newSongs.append(songObj)

            songObj = Song(artist='The Merry Men',
                            title='Joy to Joy',
                            album='The Merry Men LP',
                            track_number=2,
                            duration='2:54',
                            description='A song about joy',
                            mp3_data=fakeMp3,
                            thumbnail=fakeThumbnail,
                            tags=['joyful', 'piano', 'Key C'],
                            copyright='Copyright 2012 (c) Media Mogul Incorporated')

            newSongs.append(songObj)

            songObj = Song(artist='The Unhappy Folk',
                            title='Sadly she waits',
                            album='Misery loses comfort',
                            track_number=1,
                            duration='15:44',
                            description='A sad song',
                            mp3_data=fakeMp3,
                            thumbnail=fakeThumbnail,
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
                            mp3_data=fakeMp3,
                            thumbnail=fakeThumbnail,
                            copyright='Copyright 2014 (c) Cheese Industries')
            songObj.save()

            songObj = Song(artist='Mega Men',
                            title='Nintendo 2',
                            album='Super Tracks',
                            track_number=2,
                            duration='1:55',
                            description='Super Nintendo',
                            mp3_data=fakeMp3,
                            thumbnail=fakeThumbnail,
                            copyright='Copyright 2014 (c) Cheese Industries')
            songObj.save()


    # Query some songs by artist
    merryMenSongs = Song.objects.filter(artist='The Merry Men').all()

    sys.stdout.write("Merry Men Songs:\n")
    merryMenSongs.pprint()

    # Query some songs not by artist
    sys.stdout.write('\n\nNot Mega Men Songs:\n')
    notMegaMenSongs = Song.objects.filterInline(artist__ne='Mega Men').all()
    notMegaMenSongs.pprint()


    sys.stdout.write('\n\n')
    # Show passing filter objects around functions, and not actually fetching until .all is called.
    def getTracks(filterSet, trackNo):
            return filterSet.filter(track_number=trackNo).all()

    sys.stdout.write('\nAll track one songs:\n')

    allTrackOneSongs = getTracks(Song.objects, 1)
    for song in allTrackOneSongs:
            song.pprint()
            sys.stdout.write('\n')

    sys.stdout.write('\nMega Men track ones:')
    megaMenTracks = Song.objects.filter(artist='Mega Men')


    objs = getTracks(megaMenTracks, 1)
    for song in objs:
            song.pprint()
            sys.stdout.write('\n')

    sys.stdout.write('\nMega Men track twos (should be just one entry):\n')

    objs = getTracks(megaMenTracks, 2)
    for song in objs:
            song.pprint()
            sys.stdout.write('\n')

    pk = song.getPk()
    sys.stdout.write('\nPrimary key of previous song: %s\n' %(pk,))

    sys.stdout.write('\nSong pk=%s exists? (should be True) %s\n' %(pk, str(Song.objects.exists(pk)) ) )

    sys.stdout.write('\nAfter Delete, Mega Men Track twos (should be blank):\n')
    song.delete()
    objs = getTracks(megaMenTracks, 2)
    for song in objs:
            song.pprint()
            sys.stdout.write('\n')

    sys.stdout.write('\nSong pk=%s exists? (should now be False) %s\n' %(pk, str(Song.objects.exists(pk)) ) )
    
    # delete remaining Mega Men songs
    numDeleted = Song.objects.filter(artist='Mega Men').delete()
    sys.stdout.write('\nDeleting remaining Mega Men Tracks: %d deleted.\n' %(numDeleted,))

    sys.stdout.write('\nRemaining Mega Men tracks (should be blank):\n')
    songs = Song.objects.filter(artist='Mega Men').all()
    sys.stdout.write(str(songs) + '\n')

    endTime = time.time()

    sys.stderr.write("TIME: %.6f\n" %(endTime - startTime, ))
        

# vim: set ts=4 sw=4 st=4 expandtab :



###############################
##         OUTPUT:            #
###############################

#Testing IndexedRedis version 4.1.4
#Merry Men Songs:
#{'album': 'The Merry Men LP',
# 'artist': 'The Merry Men',
# 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
# 'description': 'A song about joy',
# 'duration': '2:54',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': ['joyful', 'piano', 'Key C'],
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Joy to Joy',
# 'track_number': 2}
#
#{'album': 'The Merry Men LP',
# 'artist': 'The Merry Men',
# 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
# 'description': 'A song about happy people',
# 'duration': '1:58',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': ['happy', 'guitar', 'smooth'],
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Happy Go Lucky',
# 'track_number': 1}
#
#
#
#Not Mega Men Songs:
#{'album': 'The Merry Men LP',
# 'artist': 'The Merry Men',
# 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
# 'description': 'A song about joy',
# 'duration': '2:54',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': ['joyful', 'piano', 'Key C'],
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Joy to Joy',
# 'track_number': 2}
#
#{'album': 'Misery loses comfort',
# 'artist': 'The Unhappy Folk',
# 'copyright': 'Copyright 2014 (c) Cheese Industries',
# 'description': 'A sad song',
# 'duration': '15:44',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': IRNullType(),
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Sadly she waits',
# 'track_number': 1}
#
#{'album': 'The Merry Men LP',
# 'artist': 'The Merry Men',
# 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
# 'description': 'A song about happy people',
# 'duration': '1:58',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': ['happy', 'guitar', 'smooth'],
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Happy Go Lucky',
# 'track_number': 1}
#
#
#
#
#All track one songs:
#{'album': 'Super Tracks',
# 'artist': 'Mega Men',
# 'copyright': 'Copyright 2014 (c) Cheese Industries',
# 'description': 'Super Nintendo',
# 'duration': '1:15',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': IRNullType(),
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Nintendo 1',
# 'track_number': 1}
#
#{'album': 'Misery loses comfort',
# 'artist': 'The Unhappy Folk',
# 'copyright': 'Copyright 2014 (c) Cheese Industries',
# 'description': 'A sad song',
# 'duration': '15:44',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': IRNullType(),
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Sadly she waits',
# 'track_number': 1}
#
#{'album': 'The Merry Men LP',
# 'artist': 'The Merry Men',
# 'copyright': 'Copyright 2012 (c) Media Mogul Incorporated',
# 'description': 'A song about happy people',
# 'duration': '1:58',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': ['happy', 'guitar', 'smooth'],
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Happy Go Lucky',
# 'track_number': 1}
#
#
#Mega Men track ones:{'album': 'Super Tracks',
# 'artist': 'Mega Men',
# 'copyright': 'Copyright 2014 (c) Cheese Industries',
# 'description': 'Super Nintendo',
# 'duration': '1:15',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': IRNullType(),
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Nintendo 1',
# 'track_number': 1}
#
#
#Mega Men track twos (should be just one entry):
#{'album': 'Super Tracks',
# 'artist': 'Mega Men',
# 'copyright': 'Copyright 2014 (c) Cheese Industries',
# 'description': 'Super Nintendo',
# 'duration': '1:55',
# 'mp3_data': b'\x99\x12\x14',
# 'releaseDate': IRNullType(),
# 'tags': IRNullType(),
# 'thumbnail': b'\x15\x1a\x1a\x1a\x1a\x1a\x1a\x1b\x1a\x1a\x1a\x1b'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a\x1a'
#              b'\x1a\x1a\x1a\x1a\x1a\x1a',
# 'title': 'Nintendo 2',
# 'track_number': 2}
#
#
#Primary key of previous song: 6
#
#Song pk=6 exists? (should be True) True
#
#After Delete, Mega Men Track twos (should be blank):
#
#Song pk=6 exists? (should now be False) False
#
#Deleting remaining Mega Men Tracks: 1 deleted.
#
#Remaining Mega Men tracks (should be blank):
#IRQueryableList([])


# vim: set ts=4 sw=4 st=4 expandtab :

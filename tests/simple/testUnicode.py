#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField, setDefaultIREncoding
from IndexedRedis.fields import IRCompressedField, IRUnicodeField


# Make sure native type will fail
setDefaultIREncoding('ascii')

# on python2 you'll probably get some unicode escape sequences, but you'll get pretty pictures on python3
prettyPictures = b' \xe2\x9c\x8f \xe2\x9c\x90 \xe2\x9c\x91 \xe2\x9c\x92 \xe2\x9c\x93 \xe2\x9c\x94 \xe2\x9c\x95 \xe2\x9c\x96 \xe2\x9c\x97 \xe2\x9c\x98 \xe2\x9c\x99 \xe2\x9c\x9a \xe2\x9c\x9b \xe2\x9c\x9c \xe2\x9c\x9d \xe2\x9c\x9e \xe2\x9c\x9f \xe2\x9c\xa0 \xe2\x9c\xa1 \xe2\x9c\xa2 \xe2\x9c\xa3 \xe2\x9c\xa4 \xe2\x9c\xa5 \xe2\x9c\xa6 \xe2\x9c\xa7 \xe2\x9c\xa9 \xe2\x9c\xaa \xe2\x9c\xab '

# vim: ts=4 sw=4 expandtab

class MyUnicodeModel(IndexedRedisModel):

    FIELDS = [ \
        IRField('name'),
        IRUnicodeField('unicodeField', encoding='utf-8'),
    ]

    INDEXED_FIELDS = [ \
        'name',
#        'data',
    ]

    KEY_NAME = 'MyUnicodeModel'


if __name__ == '__main__':

    MyUnicodeModel.objects.delete()
    newObj = MyUnicodeModel(name='hello', unicodeField=prettyPictures)

    print ( "My unicodeField: <%s>%s\n\n" %(str(type(newObj.unicodeField)), repr(newObj.unicodeField)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True)),))

    newObj.save()

    fetch1 = MyUnicodeModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 unicodeField: <%s>%s\n\n" %(str(type(fetch1.unicodeField)), repr(fetch1.unicodeField)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True)),))
        
#    fetch2 = MyUnicodeModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 data: <%s>%s\n\n" %(str(type(fetch2.data)), repr(fetch2.data)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))

#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField
from IndexedRedis.fields.FieldValueTypes import IRDatetimeValue

# vim: ts=4 sw=4 expandtab

class MyDatetimeModel(IndexedRedisModel):

    FIELDS = [ \
        'name',
        IRField('timestamp', valueType=IRDatetimeValue),
    ]

    INDEXED_FIELDS = [ \
        'name',
        'timestamp',
    ]

    KEY_NAME = 'MyDatetimeModel'


if __name__ == '__main__':

    MyDatetimeModel.objects.delete()
    
    newObj = MyDatetimeModel(name='hello', timestamp=datetime.datetime(1989, 6, 28, 12, 12, 0))

    print ( "My timestamp: <%s>%s\n\n" %(str(type(newObj.timestamp)), repr(newObj.timestamp)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False, strKeys=True)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True, strKeys=True)),))

    newObj.save()

    fetch1 = MyDatetimeModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 timestamp: <%s>%s\n\n" %(str(type(fetch1.timestamp)), repr(fetch1.timestamp)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False, strKeys=True)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True, strKeys=True)),))
        
    fetch2 = MyDatetimeModel.objects.filter(timestamp=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
    if not fetch2:
        print ( "No result for fetch2\n\n" )
    else:
        print ( "fetch2 timestamp: <%s>%s\n\n" %(str(type(fetch2.timestamp)), repr(fetch2.timestamp)))
        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False, strKeys=True)),))
        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True, strKeys=True)),))

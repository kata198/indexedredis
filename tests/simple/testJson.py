#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField
from IndexedRedis.fields.FieldValueTypes import IRJsonValue

# vim: ts=4 sw=4 expandtab

class MyJsonModel(IndexedRedisModel):

    FIELDS = [ \
        'name',
        IRField('data', valueType=IRJsonValue),
    ]

    INDEXED_FIELDS = [ \
        'name',
    ]

    KEY_NAME = 'MyJsonModel'


if __name__ == '__main__':

    MyJsonModel.objects.delete()

    vanillaDict = { 'hello' : 'world', 'deep' : { 'getting' : 'deeper' } }
    
    newObj = MyJsonModel(name='hello', data=vanillaDict)

    print ( "My data: <%s>%s\n\n" %(str(type(newObj.data)), repr(newObj.data)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True)),))

    newObj.save()

    fetch1 = MyJsonModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 data: <%s>%s\n\n" %(str(type(fetch1.data)), repr(fetch1.data)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True)),))
        
#    fetch2 = MyJsonModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 timestamp: <%s>%s\n\n" %(str(type(fetch2.timestamp)), repr(fetch2.timestamp)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))

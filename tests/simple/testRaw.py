#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField
from IndexedRedis.fields import IRRawField

# vim: ts=4 sw=4 expandtab

class MyRawModel(IndexedRedisModel):

    FIELDS = [ \
        IRField('name'),
        IRRawField('data'),
    ]

    INDEXED_FIELDS = [ \
        'name',
#        'data',
    ]

    KEY_NAME = 'MyRawModel'


if __name__ == '__main__':

    MyRawModel.objects.delete()
    
    newObj = MyRawModel(name='hello', data=b'hello world')

    print ( "My data: <%s>%s\n\n" %(str(type(newObj.data)), repr(newObj.data)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False, strKeys=True)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True, strKeys=True)),))

    newObj.save()

    fetch1 = MyRawModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 data: <%s>%s\n\n" %(str(type(fetch1.data)), repr(fetch1.data)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False, strKeys=True)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True, strKeys=True)),))
        
#    fetch2 = MyRawModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 data: <%s>%s\n\n" %(str(type(fetch2.data)), repr(fetch2.data)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False, strKeys=True)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True, strKeys=True)),))

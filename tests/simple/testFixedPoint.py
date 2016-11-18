#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField
from IndexedRedis.fields import IRFixedPointField

# vim: ts=4 sw=4 expandtab

class MyFixedPointModel(IndexedRedisModel):

    FIELDS = [ \
        'name',
        IRFixedPointField('value', decimalPlaces=22),
    ]

    INDEXED_FIELDS = [ \
        'name',
        'value',
    ]

    KEY_NAME = 'MyFixedPointModel'


if __name__ == '__main__':

    MyFixedPointModel.objects.delete()

    pi = 21.991192 / 7.0
    
    newObj = MyFixedPointModel(name='hello', value=pi)

    print ( "My value: <%s>%s\n\n" %(str(type(newObj.value)), repr(newObj.value)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True)),))

    newObj.save()

    fetch1 = MyFixedPointModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 value: <%s>%s\n\n" %(str(type(fetch1.value)), repr(fetch1.value)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True)),))
        
    fetch2 = MyFixedPointModel.objects.filter(value=pi).first()
    if not fetch2:
        print ( "No result for fetch2\n\n" )
    else:
        print ( "fetch2 value: <%s>%s\n\n" %(str(type(fetch2.value)), repr(fetch2.value)))
        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))

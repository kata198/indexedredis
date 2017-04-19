#!/usr/bin/env python

import datetime
import sys
import IndexedRedis
from IndexedRedis import IndexedRedisModel, IRField
from IndexedRedis.fields import IRFieldChain, IRCompressedField, IRBase64Field
from IndexedRedis.fields.FieldValueTypes import IRJsonValue

# vim: ts=4 sw=4 expandtab

class MyChainedModel(IndexedRedisModel):

    FIELDS = [ \
        IRField('name'),
        IRFieldChain('data', [IRField(valueType=IRJsonValue), IRCompressedField(), IRBase64Field()]) ,
    ]

    INDEXED_FIELDS = [ \
        'name',
    ]

    KEY_NAME = 'MyChainedModel'


if __name__ == '__main__':

    MyChainedModel.objects.delete()

    vanillaDict = { 'hello' : 'world', 'deep' : { 'getting' : 'deeper' } }
    
    newObj = MyChainedModel(name='hello', data=vanillaDict)

    print ( "My data: <%s>%s\n\n" %(str(type(newObj.data)), repr(newObj.data)))
    print ( "My dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False, strKeys=True)),))
    print ( "My dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True, strKeys=True)),))

    newObj.save()

    fetch1 = MyChainedModel.objects.filter(name='hello').first()

    if not fetch1:
        print ( "No result for fetch1\n\n" )
    else:
        print ( "fetch1 data: <%s>%s\n\n" %(str(type(fetch1.data)), repr(fetch1.data)))
        print ( "fetch1 dict (not for storage): %s\n\n" %(str(fetch1.asDict(forStorage=False, strKeys=True)),))
        print ( "fetch1 dict (for storage): %s\n\n" %(str(fetch1.asDict(forStorage=True, strKeys=True)),))
        
#    fetch2 = MyChainedModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 timestamp: <%s>%s\n\n" %(str(type(fetch2.timestamp)), repr(fetch2.timestamp)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))

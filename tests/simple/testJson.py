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

    print ( "JsonDict data: <%s>%s\n\n" %(str(type(newObj.data)), repr(newObj.data)))
    print ( "JsonDict dict (not for storage): %s\n\n" %(str(newObj.asDict(forStorage=False)),))
    print ( "JsonDict dict (for storage): %s\n\n" %(str(newObj.asDict(forStorage=True)),))

    newObj.save()

    fetchDict = MyJsonModel.objects.filter(name='hello').first()

    if not fetchDict:
        print ( "No result for fetchDict\n\n" )
    else:
        print ( "fetchDict data: <%s>%s\n\n" %(str(type(fetchDict.data)), repr(fetchDict.data)))
        print ( "fetchDict dict (not for storage): %s\n\n" %(str(fetchDict.asDict(forStorage=False)),))
        print ( "fetchDict dict (for storage): %s\n\n" %(str(fetchDict.asDict(forStorage=True)),))

    myList = [1, 2]

    obj2 = MyJsonModel(name='listy', data=myList)
    print ( "JsonArray data: <%s>%s\n\n" %(str(type(obj2.data)), repr(obj2.data)))
    print ( "JsonArray dict (not for storage): %s\n\n" %(str(obj2.asDict(forStorage=False)),))
    print ( "JsonArray dict (for storage): %s\n\n" %(str(obj2.asDict(forStorage=True)),))

    obj2.save()

    fetchArray = MyJsonModel.objects.filter(name='listy').first()
    
    if not fetchArray:
        print ( "No result for fetchArray\n\n" )
    else:
        print ( "fetchArray data: <%s>%s\n\n" %(str(type(fetchArray.data)), repr(fetchArray.data)))
        print ( "fetchArray dict (not for storage): %s\n\n" %(str(fetchArray.asDict(forStorage=False)),))
        print ( "fetchArray dict (for storage): %s\n\n" %(str(fetchArray.asDict(forStorage=True)),))

    myStr = '"Free like the mountain stream"'

    obj3 = MyJsonModel(name='stringy', data=myStr)
    
    print ( "JsonString data: <%s>%s\n\n" %(str(type(obj3.data)), repr(obj3.data)))
    print ( "JsonString dict (not for storage): %s\n\n" %(str(obj3.asDict(forStorage=False)),))
    print ( "JsonString dict (for storage): %s\n\n" %(str(obj3.asDict(forStorage=True)),))

    obj3.save()

    fetchString = MyJsonModel.objects.filter(name='stringy').first()
    
    if not fetchString:
        print ( "No result for fetchString\n\n" )
    else:
        print ( "fetchString data: <%s>%s\n\n" %(str(type(fetchString.data)), repr(fetchString.data)))
        print ( "fetchString dict (not for storage): %s\n\n" %(str(fetchString.asDict(forStorage=False)),))
        print ( "fetchString dict (for storage): %s\n\n" %(str(fetchString.asDict(forStorage=True)),))

    obj4 = MyJsonModel(name='inty', data=14)
    
    print ( "JsonInt data: <%s>%s\n\n" %(str(type(obj4.data)), repr(obj4.data)))
    print ( "JsonInt dict (not for storage): %s\n\n" %(str(obj4.asDict(forStorage=False)),))
    print ( "JsonInt dict (for storage): %s\n\n" %(str(obj4.asDict(forStorage=True)),))

    obj4.save()

    fetchInt = MyJsonModel.objects.filter(name='inty').first()
    
    if not fetchInt:
        print ( "No result for fetchInt\n\n" )
    else:
        print ( "fetchInt data: <%s>%s\n\n" %(str(type(fetchInt.data)), repr(fetchInt.data)))
        print ( "fetchInt dict (not for storage): %s\n\n" %(str(fetchInt.asDict(forStorage=False)),))
        print ( "fetchInt dict (for storage): %s\n\n" %(str(fetchInt.asDict(forStorage=True)),))

    obj5 = MyJsonModel(name='booly', data=False)
    
    print ( "JsonBool data: <%s>%s\n\n" %(str(type(obj5.data)), repr(obj5.data)))
    print ( "JsonBool dict (not for storage): %s\n\n" %(str(obj5.asDict(forStorage=False)),))
    print ( "JsonBool dict (for storage): %s\n\n" %(str(obj5.asDict(forStorage=True)),))

    obj5.save()

    fetchBool = MyJsonModel.objects.filter(name='booly').first()
    
    if not fetchBool:
        print ( "No result for fetchBool\n\n" )
    else:
        print ( "fetchBool data: <%s>%s\n\n" %(str(type(fetchBool.data)), repr(fetchBool.data)))
        print ( "fetchBool dict (not for storage): %s\n\n" %(str(fetchBool.asDict(forStorage=False)),))
        print ( "fetchBool dict (for storage): %s\n\n" %(str(fetchBool.asDict(forStorage=True)),))


    obj6 = MyJsonModel(name='novaluey')
    print ( "JsonNoValue data: <%s>%s\n\n" %(str(type(obj6.data)), repr(obj6.data)))
    print ( "JsonNoValue dict (not for storage): %s\n\n" %(str(obj6.asDict(forStorage=False)),))
    print ( "JsonNoValue dict (for storage): %s\n\n" %(str(obj6.asDict(forStorage=True)),))

    obj6.save()

    fetchNoValue = MyJsonModel.objects.filter(name='novaluey').first()
    
    if not fetchNoValue:
        print ( "No result for fetchNoValue\n\n" )
    else:
        print ( "fetchNoValue data: <%s>%s\n\n" %(str(type(fetchNoValue.data)), repr(fetchNoValue.data)))
        print ( "fetchNoValue dict (not for storage): %s\n\n" %(str(fetchNoValue.asDict(forStorage=False)),))
        print ( "fetchNoValue dict (for storage): %s\n\n" %(str(fetchNoValue.asDict(forStorage=True)),))

    obj7 = MyJsonModel(name='nully', data=None)
    print ( "JsonNull data: <%s>%s\n\n" %(str(type(obj7.data)), repr(obj7.data)))
    print ( "JsonNull dict (not for storage): %s\n\n" %(str(obj7.asDict(forStorage=False)),))
    print ( "JsonNull dict (for storage): %s\n\n" %(str(obj7.asDict(forStorage=True)),))

    obj7.save()

    fetchNull = MyJsonModel.objects.filter(name='nully').first()
    
    if not fetchNull:
        print ( "No result for fetchNull\n\n" )
    else:
        print ( "fetchNull data: <%s>%s\n\n" %(str(type(fetchNull.data)), repr(fetchNull.data)))
        print ( "fetchNull dict (not for storage): %s\n\n" %(str(fetchNull.asDict(forStorage=False)),))
        print ( "fetchNull dict (for storage): %s\n\n" %(str(fetchNull.asDict(forStorage=True)),))
        
        
#    fetch2 = MyJsonModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 timestamp: <%s>%s\n\n" %(str(type(fetch2.timestamp)), repr(fetch2.timestamp)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))
        
#    fetch2 = MyJsonModel.objects.filter(data=datetime.datetime(1989, 6, 28, 12, 12, 0)).first()
#    if not fetch2:
#        print ( "No result for fetch2\n\n" )
#    else:
#        print ( "fetch2 timestamp: <%s>%s\n\n" %(str(type(fetch2.timestamp)), repr(fetch2.timestamp)))
#        print ( "fetch2 dict (not for storage): %s\n\n" %(str(fetch2.asDict(forStorage=False)),))
#        print ( "fetch2 dict (for storage): %s\n\n" %(str(fetch2.asDict(forStorage=True)),))

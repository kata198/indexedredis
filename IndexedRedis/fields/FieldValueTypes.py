# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# FieldValueTypes - Types that can be passed to "valueType" of an IRField for special implicit conversions
#

import json

from . import irNull, IRNullType

from datetime import datetime
from ..compat_str import to_unicode

__all__ = ('IRDatetimeValue', 'IRJsonValue')

try:
    unicode
except NameError:
    unicode = str

class IRDatetimeValue(datetime):
    '''
        IRDatetimeValue - A field type that is a datetime. Pass this as "valueType" to an IRField to use a datetime
    '''

    CAN_INDEX = True

    def __new__(self, *args, **kwargs):
        # No need to actually create this object, we just need to override instantiation to create a datetime from several forms.
        if len(args) == 1:
            if type(args[0]) == bytes:
                theArg = to_unicode(args[0])
            else:
                theArg = args[0]

            if type(theArg) in (str, unicode) and (theArg.isdigit() or len([1 for x in theArg.split('.') if x.isdigit()]) == 2):
                tmp = datetime.fromtimestamp(float(theArg))
            elif type(theArg) in (int, float):
                tmp = datetime.fromtimestamp(float(theArg))
            elif issubclass(theArg.__class__, datetime):
                tmp = theArg
            else:
                # If microsecond is present, drop it. Not available on all platforms.
                if '.' in theArg:
                    theArg = theArg[:theArg.index('.')]
                tmp = datetime.strptime(theArg, '%Y-%m-%d %H:%M:%S')
                
            return datetime(tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute, tmp.second)
        else:
            # If microsecond is present, drop it. Not available on all platforms.
            if 'microsecond' in kwargs:
                kwargs.pop('microsecond')
            elif len(args) == 7:
                args = args[:-1]

            return datetime(*args, **kwargs)

#    def __repr__(self):
#        '''
#            __repr__ - Be invisible.
#        '''
#        return datetime.__repr__(self).replace('IRDatetimeValue', 'datetime')

def __ir_json__str__(self):
#    if bool(self) is False:
#        return irNull

    return json.dumps(self)
        

class _IRJsonDict(dict):
    __str__ = __ir_json__str__
    def __new__(self, *args, **kwargs):
        return dict.__new__(self, *args, **kwargs)
_IRJsonObject = _IRJsonDict

class _IRJsonString(str):
    __str__ = __ir_json__str__
    def __new__(self, *args, **kwargs):
        return str.__new__(self, *args, **kwargs)

# Cannot subclass bool..... how stupid.
#class _IRJsonBool(bool):
#    __str__ = __ir_json__str__
#    def __new__(self, *args, **kwargs):
#        return bool.__new__(self, *args, **kwargs)
    

class _IRJsonArray(list):
    __str__ = __ir_json__str__
    def __new__(self, *args, **kwargs):
        return list.__new__(self, *args, **kwargs)

class _IRJsonNumber(float):
    __str__ = __ir_json__str__
    def __new__(self, *args, **kwargs):
        return float.__new__(self, *args, **kwargs)

# Cannot subclass NoneType, so use IRNullType to represent null.
class _IRJsonNull(IRNullType):
    def __str__(self):
        return 'null'
    

class IRJsonValue(type):
    '''
        IRJsonValue - A value which is interpreted as json. 
            Supports object (dicts), strings, array, number. 

        "null" is supported using IRNullType, because cannot subclass "NoneType".
        "bool" is supported using a number 0.0 or 1.0 - because cannot subclass "bool"
    '''

    # TODO: This probably shouldn't be indexable... although maybe when I implement hashed indexes.
    CAN_INDEX = False

    def __init__(self, *args, **kwargs):
        pass


    def __str__(self):
        if bool(self) is False:
            return irNull

        return json.dumps(self)
            

    def __new__(self, *args, **kwargs):
        if len(args) == 1:


            if issubclass(args[0].__class__, dict):
                myRet = _IRJsonDict()
                myRet.update(args[0])
                return myRet

            elif issubclass(args[0].__class__, (list, tuple)):
                myRet = _IRJsonArray(args[0])
                return myRet
            elif issubclass(args[0].__class__, (int, float)):
                myRet = _IRJsonNumber(args[0])
                return myRet
            elif isinstance(args[0], bool):
                if args[0] is False:
                    val = 0
                else:
                    val = 1
                myRet = _IRJsonNumber(val)
                return myRet
            elif args[0] is None or issubclass(args[0].__class__, IRNullType):
                myRet = _IRJsonNull()
                return myRet
                
            if type(args[0]) == bytes:
                theArg = to_unicode(args[0])
            else:
                theArg = args[0]

            if len(theArg) == 0:
                return irNull

            try:
                jsonObj = json.loads(theArg)
            except Exception as e:
                raise ValueError('Cannot decode json [%s]: %s%s' %(str(e), str(type(theArg)), repr(theArg)))

            if isinstance(jsonObj, dict):
                myRet = _IRJsonDict()
                myRet.update(jsonObj)
                return myRet
            elif issubclass(jsonObj.__class__, (list, tuple, set)):
                myRet = _IRJsonArray(jsonObj)
                return myRet
            elif isinstance(jsonObj, (int, float)):
                myRet = _IRJsonNumber(jsonObj)
                return myRet
            elif isinstance(jsonObj, bool):
                if jsonObj is False:
                    val = 0
                else:
                    val = 1
                myRet = _IRJsonNumber(val)
                return myRet
            elif jsonObj is None:
                return _IRJsonNull()
            else:
                myRet = _IRJsonString(jsonObj)
                return myRet

        return irNull

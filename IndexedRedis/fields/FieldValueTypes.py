# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# FieldValueTypes - Types that can be passed to "valueType" of an IRField for special implicit conversions
#

import json

from . import irNull

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

    def __new__(self, *args, **kwargs):
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
                tmp = datetime.strptime(theArg, '%Y-%m-%d %H:%M:%S')
                
            return datetime.__new__(self, tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute, tmp.second)
        else:
            return datetime.__new__(self, *args, **kwargs)

    def __repr__(self):
        '''
            __repr__ - Be invisible.
        '''
        return datetime.__repr__(self).replace('IRDatetimeValue', 'datetime')


# TODO: This probably shouldn't be indexable... although maybe when I implement hashed indexes.
class IRJsonValue(dict):
    '''
        IRJsonValue - A value which is interpreted as json.
    '''

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
                myRet = dict.__new__(self)
                myRet.update(args[0])
                return myRet


            if type(args[0]) == bytes:
                theArg = to_unicode(args[0])
            else:
                theArg = args[0]

            if len(theArg) == 0:
                return irNull

            jsonDict = json.loads(theArg)

            myRet = dict.__new__(self)
            myRet.update(jsonDict)
            return myRet

        return irNull

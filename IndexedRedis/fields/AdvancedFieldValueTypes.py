# Copyright (c) 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# AdvancedFieldValueTypes - Types that can be passed to "valueType" of an IRField for special implicit conversions
#

from datetime import datetime

__all__ = ('IRDatetimeFieldType',)

class IRDatetimeFieldType(datetime):
    '''
        IRDatetimeFieldType - A field type that is a datetime. Pass this as "valueType" to an IRField to use a datetime
    '''

    def __new__(self, *args, **kwargs):
        if len(args) == 1:
            if type(args[0]) == str and (args[0].isdigit() or len([1 for x in args[0].split('.') if x.isdigit()]) == 2):
                tmp = datetime.fromtimestamp(float(args[0]))
            elif type(args[0]) in (int, float):
                tmp = datetime.fromtimestamp(float(args[0]))
            elif issubclass(args[0].__class__, datetime):
                tmp = args[0]
            else:
                tmp = datetime.strptime(args[0], '%Y-%m-%d %H:%M:%S')
                
            return datetime.__new__(self, tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute, tmp.second)
        else:
            return datetime.__new__(self, *args, **kwargs)

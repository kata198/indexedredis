# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields - Some types and objects related to advanced fields
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

__all__ = ('IRField', 'IRNullType', 'irNull', 'IRPickleField', 
	'IRCompressedField', 'IRUnicodeField', 'IRRawField', 'IRBase64Field', 
	'IRFixedPointField', 'IRDatetimeValue', 'IRJsonValue', 
	'IRBytesField',
	'IR_NULL_STR', 'IR_NULL_BYTES', 'IR_NULL_UNICODE', 'IR_NULL_STRINGS' )

import sys
from datetime import datetime

from ..compat_str import to_unicode, tobytes

from hashlib import md5

try:
	unicode
except NameError:
	unicode = str

IR_NULL_STR = 'IRNullType()'
IR_NULL_BYTES = b'IRNullType()'
IR_NULL_UNICODE = u'IRNullType()'

if sys.version_info.major >= 3:
	IR_NULL_STRINGS = (IR_NULL_STR, IR_NULL_BYTES)
else:
	# This generates a unicode warning, but we SHOULDN'T have such a condition.. I don't think
#	IR_NULL_STRINGS = (IR_NULL_STR, IR_NULL_UNICODE)
	IR_NULL_STRINGS = (IR_NULL_STR, )


class IRField(str):
	'''
		IRField - An advanced field

		@param name <str> - The field name
		@param valueType <None/type> - The type to use for the value of this field. Default is str (str/unicode will both be unicode). If on python3 and bytes are passed, will be decoded to bytes using default encoding.
		  Using None, the raw data will be used (bytes) on retrieval and for storage.
		  Can be a basic type (like int). Use BINARY_FIELDS array on the model to have value be "bytes"

		If a type is defined other than default/str/bytes/None , an empty value (empty string in Redis) will be assigned to the IRNullType instance provided in this module, irNull.
		irNull does not equal anything except irNull (or another IRNullType). Use this to check if a value has been assigned for other types.

		BE VERY CAREFUL ABOUT USING "float" as a type! It is an inprecise field and can vary from system to system. Instead of using a float,
		consider using fields.IRFixedPointField, which is indexable.
		
	'''

	# CAN_INDEX - Set this to True if this type can be indexed. Otherwise, set it to False to disallow indexing on this field.
        #    The object itself is checked, so if a field is generally indexable except under certain conditions, the class can have
        #      True while the specific object that should be disallowed can be False.
        #
        # If IRField base class is used, the following types are CAN_INDEX=True: str, unicode, int, bool.  Otherwise, if CAN_INDEX is defined
        #   on the type, that value will be used.
	CAN_INDEX = False


	# Start as a class variable, so "toIndex" works even if IRField constructor is not called (which really shouldn't be called on extending classes)
	hashIndex = False

	def __init__(self, name='', valueType=str, hashIndex=False):
		'''
			__init__ - Create an IRField. Use this directly in the FIELDS array for advanced functionality on a field.

			@param name <str> - The name of this field
			@param valueType <type> - The type that will be used for this field. Default str/unicode (and bytes on python2)
				act the same as non-IRField FIELDS entries (just plain string), i.e. they are encoded to unicode to and from Redis.

				If you pass in None, then no decoding will take place (so whatever you provide goes in, and bytes come out of Redis).
				This is similar to IRFieldRaw

				On python3, if you pass bytes, than the field will be left as bytes.
				To be both python2 and python3 compatible, however, you can use IRBytesField

				If bool is used, then "1" and "true" are True, "0" and "false" are False, any other value is an exception.

				You can also pass an advanced type (see IndexedRedis.fields.FieldValueTypes) like datetime and json.

				All types other than string/unicode/bytes/None will be assigned 'irNull' if they were not provided a value.
				@see irNull - Equals only irNull (or other IRNullType instances). You can use this to check if an integer is defined versus 0, for example.

				While this class is create for primitive types (like int's and datetimes), more complex types extend IRField (such as pickle, compressed, or unicode with a specific encoding).

			@param hashIndex - If true, the md5 hash of the value will be used for indexing and filtering. This may be useful for very long fields.


			NOTE: If you are extending IRField, you should probably not call this __init__ function. So long as you implement your own "convert", any fields used are set on a class-level.
		'''
		if valueType in (str, unicode):
			valueType = str
			self.convert = self._convertStr
			self.toStorage = self._convertStr
		elif bytes != str and valueType == bytes:
			valueType = bytes
			self.convert = self._convertBytes
			self.toStorage = self._convertBytes
			self.CAN_INDEX = False
		elif valueType in (None, type(None)):
			self.convert = self._noConvert
			self.toStorage = self._noConvert
			self.CAN_INDEX = False
		# I don't like these next two conditions, but it will train folks to use the correct types (whereas they may just try to shove dict in, and give up that it doesn't work)
		elif valueType in (dict, list, tuple):
			valueType = IRJsonValue
			#sys.stderr.write('WARNING: Implicitly converting IRField(%s, valueType=%s) to IRField(%s, valueType=IndexedRedis.fields.FieldValueTypes.IRJsonValue)\n' %(repr(name), valueType.__name__, repr(name)))
			self.CAN_INDEX = False
		elif valueType == datetime:
			valueType = IRDatetimeValue
			#sys.stderr.write('WARNING: Implicitly converting IRField(%s, valueType=datetime.datetime) to IRField(%s, valueType=IndexedRedis.fields.FieldValueTypes.IRDatetimeValue)\n' %(repr(name), repr(name)))
			self.CAN_INDEX = True
		else:
			if not isinstance(valueType, type):
				raise TypeError('valueType %s is not a type. Use int, str, etc' %(repr(valueType,)))
			if valueType == bool:
				self.convert = self._convertBool
			elif isinstance(valueType, (set, frozenset, )):
				raise TypeError('set types are not supported types. Use IRPickleField to store pickles of any type (which allow storing objects, etc), or use IRField(.. valueType=IRJsonValue) to store basic data (strings, integers) in lists.')
		self.valueType = valueType

		if valueType in (str, unicode, int, bool):
			self.CAN_INDEX = True
		elif hasattr(valueType, 'CAN_INDEX'):
			self.CAN_INDEX = valueType.CAN_INDEX
		# XXX: Commented because default CAN_INDEX is False.
#		elif valueType == float:
#			# Floats are not filterable/indexable across platforms, as they may have different rounding issues, or different number
#			#  of points of accuracy, etc.
#			# Use fields.IRFixedPointField if you need to index/filter on a floating point value.
#			self.CAN_INDEX = False
#		elif issubclass(valueType.__class__, object):
#			# Don't allow objects to index by default unless they define CAN_INDEX to be True
#			self.CAN_INDEX = False

		self.hashIndex = hashIndex

	def toStorage(self, value):
		'''
			toStorage - Convert the value to a string representation for storage.

			  The default implementation will work here for basic types.

			@param value - The value of the item to convert
			@return A string value suitable for storing.
		'''
		return to_unicode(value)

	def convert(self, value):
		'''
			convert - Convert the value from storage (string) to the value type.

			@return - The converted value, or "irNull" if no value was defined (and field type is not default/string)
		'''
		if self._isNullValue(value):
			return irNull
		return self.valueType(value)

	def toIndex(self, value):
		'''
			toIndex - An optional method which will return the value prepped for index.

			By default, "toStorage" will be called. If you provide "hashIndex=True" on the constructor,
			the field will be md5summed for indexing purposes. This is useful for large strings, etc.
		'''
		ret = self.toStorage(value)
		if self.isIndexHashed is False:
			return ret

		return md5(tobytes(ret)).hexdigest()

	@property
	def isIndexHashed(self):
		'''
			isIndexHashed - Returns if the index value should be hashed

			@return <bool> - True if this field should be hashed before indexing / filtering
		'''
		return bool(self.hashIndex)

	def _convertStr(self, value):
		return to_unicode(value)

	def _convertBytes(self, value):
		return tobytes(value)
	

	def _noConvert(self, value):
		return value

	def _convertBool(self, value):
		if self._isNullValue(value):
			return irNull
		xvalue = value.lower()
		if xvalue in ('true', '1'):
			return True
		elif xvalue in ('false', '0'):
			return False

		# I'm not sure what to do here... Should we raise an exception because the data is invalid? Should just return True?
		raise ValueError('Unexpected value for bool type: %s' %(value,))


	@staticmethod
	def _isNullValue(value):
		'''
			_isNullValue - Tests value if it should be represented by irNull.

			convert and toStorage should test if value is null and return null (for most types)
		'''
		return bool(value in (b'', '', irNull) or value in IR_NULL_STRINGS )

	def __new__(self, name='', valueType=None, hashIndex=False):
		return str.__new__(self, name)


# There is an odd "feature" of python 2.7 where the __eq__ method is not called when
#  u'' == irNull
#  however it is in all other forms (including: irNull == u'')
#  
#  when IRNullType extends str. But when it extends unicode, it works as expected.
#
if unicode == str:
	IrNullBaseType = str
else:
	IrNullBaseType = unicode

class IRNullType(IrNullBaseType):
	'''
		The type to represent NULL for anything except string which has no NULL.

		Values of this type only equal other values of this type (i.e. '' does not equal IRNullType())
		Even False does not equal IRNull.

		You probably shouldn't ever need to use this directly, instead use the static instance, "irNull", defined in this module.
	'''

	def __new__(self, val=''):
		'''
			Don't let this be assigned a value.
		'''
		return IrNullBaseType.__new__(self, '')

	def __eq__(self, otherVal):
		return bool(issubclass(otherVal.__class__, IRNullType))
	
	def __ne__(self, otherVal):
		return not bool(issubclass(otherVal.__class__, IRNullType))

	def __str__(self):
		return ''

	def __bool__(self):
		return False
	
	def __nonzero__(self):
		return False
	
	def __repr__(self):
		return IR_NULL_STR


# For all fields which have a type, if they have a null value this will be returned. IRNullType('') != str('') so you can
#  filter out nulls on result like:
#  myObjs = MyModel.objects.all()
#  notNullMyFieldObjs = results.filter(myField__ne=IR_NULL)
global irNull
irNull = IRNullType()

from .compressed import IRCompressedField
from .pickle import IRPickleField
from .unicode import IRUnicodeField
from .raw import IRRawField
from .chain import IRFieldChain
from .b64 import IRBase64Field
from .fixedpoint import IRFixedPointField
from .bytes import IRBytesField

from .FieldValueTypes import IRDatetimeValue, IRJsonValue

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

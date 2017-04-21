# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields - Some types and objects related to advanced fields
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

__all__ = ('IRField', 'IRNullType', 'irNull', 'IRPickleField', 
	'IRCompressedField', 'IRUnicodeField', 'IRRawField', 'IRBase64Field', 
	'IRFixedPointField', 'IRDatetimeValue', 'IRJsonValue', 
	'IRBytesField', 'IRClassicField',
	'IR_NULL_STR', 'IR_NULL_BYTES', 'IR_NULL_UNICODE', 'IR_NULL_STRINGS' )

import sys
from datetime import datetime

from ..compat_str import to_unicode, tobytes
from ..deprecated import deprecatedMessage

from .null import irNull, IR_NULL_STRINGS, IR_NULL_STR, IR_NULL_BYTES, IR_NULL_UNICODE, IRNullType

from hashlib import md5


try:
	unicode
except NameError:
	unicode = str


class IRField(str):
	'''
		IRField - An advanced field

		@param name <str> - The field name

		@param valueType <None/type> - The type to use for the value of this field. Default is str (str/unicode will both be unicode). If on python3 and bytes are passed, will be decoded to bytes using default encoding.
		  Using None, the raw data will be used (bytes) on retrieval and for storage.
		  Can be a basic type (like int). Use BINARY_FIELDS array on the model to have value be "bytes"

		@param hashIndex <bool> (default False) - If True, the value will be hashed for use in the index. This is useful on fields where the value may be very large. For smaller fields, can keep this as False.

		@param defaultValue <any> (default irNull) - The value assigned to this field as a "default", i.e. when no value has yet been set. Generally, it makes sense to keep this as irNull, but you may want a different default.

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


	# TODO: Investigate changing valueType to encoded_str_type
	def __init__(self, name='', valueType=str, defaultValue=irNull, hashIndex=False):
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

			@param defaultValue <any> (default irNull) - The value assigned to this field as a "default", i.e. when no value has yet been set. Generally, it makes sense to keep this as irNull, but you may want a different default.

			@param hashIndex <bool> (default False) - If true, the md5 hash of the value will be used for indexing and filtering. This may be useful for very long fields.


			NOTE: If you are extending IRField, you should probably not call this __init__ function. So long as you implement your own "convert", any fields used are set on a class-level.
		'''
		self.defaultValue = defaultValue
		self.hashIndex = hashIndex

		if valueType in (str, unicode):
			valueType = str
			self.convert = self._convertStr
			self.convertFromInput = self._convertStr
			self.toStorage = self._convertStr
		elif bytes != str and valueType == bytes:
			valueType = bytes
			self.convert = self._convertBytes
			self.convertFromInput = self._convertBytes
			self.toStorage = self._convertBytes

			# Cannot index here, but CAN index if using IRBytesField. This is because python2 and python3 could handle it differently in certain cases.
			self.CAN_INDEX = False
		elif valueType in (None, type(None)):
			self.convert = self._noConvert
			self.convertFromInput = self._noConvert
			self.toStorage = self._noConvert
			self.CAN_INDEX = False
		# I don't like these next two conditions, but it will train folks to use the correct types (whereas they may just try to shove dict in, and give up that it doesn't work)
		elif valueType in (dict, list, tuple):
#			deprecatedMessage('WARNING: Implicitly converting IRField(%s, valueType=%s) to IRField(%s, valueType=IndexedRedis.fields.FieldValueTypes.IRJsonValue)\n' %(repr(name), valueType.__name__, repr(name)), printStack=True)
			valueType = IRJsonValue
			self.CAN_INDEX = IRJsonValue.CAN_INDEX
		elif valueType == datetime:
#			deprecatedMessage('WARNING: Implicitly converting IRField(%s, valueType=datetime.datetime) to IRField(%s, valueType=IndexedRedis.fields.FieldValueTypes.IRDatetimeValue)\n' %(repr(name), repr(name)), printStack=True)
			valueType = IRDatetimeValue
			self.CAN_INDEX = IRDatetimeValue.CAN_INDEX
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

	def convertFromInput(self, value):
		'''
			convertFromInput - Convert the value from input (constructor) to the value type.

			  This is intended to be used when the data is guarenteed to NOT be from storage.

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
		if self._isIrNull(ret):
			ret = repr(irNull)

		if self.isIndexHashed is False:
			return ret

		return md5(tobytes(ret)).hexdigest()

	def getDefaultValue(self):
		if not hasattr(self, 'defaultValue'):
			return irNull

		return self.defaultValue

	@property
	def isIndexHashed(self):
		'''
			isIndexHashed - Returns if the index value should be hashed

			@return <bool> - True if this field should be hashed before indexing / filtering
		'''
		return bool(self.hashIndex)

	def _convertStr(self, value):
		if self._isIrNull(value):
			return irNull
		return to_unicode(value)

	def _convertBytes(self, value):
		if self._isIrNull(value):
			return irNull
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
		return bool(value in (b'', '', irNull, None) or value in IR_NULL_STRINGS )
	
	@staticmethod
	def _isIrNull(value):
		return bool( value == irNull or value in IR_NULL_STRINGS )

	def _getReprProperties(self):
		'''
			_getReprProperties - Get the properties of this field to display in repr().

				These should be in the form of $propertyName=$propertyRepr

				The default IRField implementation handles just the "hashIndex" property.

				defaultValue is part of "__repr__" impl. You should just extend this method
				with your object's properties instead of rewriting repr.

		'''
		ret = []
		if getattr(self, 'valueType', None) is not None:
			ret.append('valueType=%s' %(self.valueType.__name__, ))
		if hasattr(self, 'hashIndex'):
			ret.append('hashIndex=%s' %(self.hashIndex, ))

		return ret


	def __repr__(self):
		'''
			__repr__ - Return an object-representation string of this field instance.

			You should NOT need to extend this on your IRField, instead just implement _getReprProperties

			  to return your type's specific properties associated with this instance.

			  @see _getReprProperties
		'''
		ret = [ self.__class__.__name__, '( ', '"%s"' %(str(self), ) ]

		reprProperties = self._getReprProperties()

		defaultValue = self.getDefaultValue()
		if defaultValue == irNull:
			reprProperties.append('defaultValue=irNull')
		else:
			reprProperties.append('defaultValue=%s' %(repr(defaultValue), ))

		ret.append(', ')
		ret.append(', '.join(reprProperties))

		ret.append(' )')
		
		return ''.join(ret)

	def __new__(self, name='', valueType=None, defaultValue=irNull, hashIndex=False):
		return str.__new__(self, name)


from .compressed import IRCompressedField
from .pickle import IRPickleField
from .unicode import IRUnicodeField
from .raw import IRRawField
from .chain import IRFieldChain
from .b64 import IRBase64Field
from .fixedpoint import IRFixedPointField
from .bytes import IRBytesField
# Prevent these modules from conflicting with builtin / importable types...
try:
	del unicode
	del bytes
	del pickle
except:
	pass

try:
	unicode
except NameError:
	unicode = str

from .classic import IRClassicField

from .FieldValueTypes import IRDatetimeValue, IRJsonValue

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

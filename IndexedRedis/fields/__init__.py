# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields - Some types and objects related to advanced fields
#


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

__all__ = ('IRField', 'IRNullType', 'irNull', 'IRPickleField', 'IRCompressedField', 'IRUnicodeField')

from ..compat_str import to_unicode

try:
	unicode
except NameError:
	unicode = str

# TODO: Implement a "Fixed-Point" type

class IRField(str):
	'''
		IRField - An advanced field

		@param name <str> - The field name
		@param valueType <None/type> - The type to use for the value of this field. Default is str (None/bytes/str/unicode will all be "str")
		  Can be a basic type (like int). Use BINARY_FIELDS array on the model to have value be "bytes"

		If a type is defined other than default/str , an empty value (empty string in Redis) will be assigned to the IRNullType instance provided in this module, irNull.
		irNull does not equal anything except irNull (or another IRNullType). Use this to check if a value has been assigned for other types.

		Keep in mind that all storage happens as Strings, so your value should be able to flow to/from "str" without changing.

		BE VERY CAREFUL ABOUT USING "float" as a type! It is an inprecise field and can vary from system to system. Instead of using a float,
		consider using a fixed-point float string, like:
		
		 myFixedPoint = "%2.5f" %(myFloatingPoint,)

		 Which wll support up to 2 numerals and 5 decimal places.
	'''

	def __init__(self, name, valueType=None):
		if not name:
			raise ValueError('IRField defined without a name!')

		if valueType in (str, bytes, unicode):
			valueType = None
		if valueType != None:
			if not isinstance(valueType, type):
				raise ValueError('valueType %s is not a type. Use int, str, etc' %(repr(valueType,)))
			if valueType == bool:
				self.convert = self._convertBool
		else:
			self.convert = self._noConvert
		self.valueType = valueType

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
		if value in ('', irNull):
			return irNull
		return self.valueType(value)

	# TODO: Test if including this function and then deleting it later will put it in pydoc.
#	def toBytes(self, value):
#		'''
#			toBytes - Implement this function to return a "bytes" version of your object, to support base64 encoding
#			  if default encoding won't work.
#		'''
#		raise NotImplementedError('toBytes is not really here.')
#	del toBytes
		

	def _noConvert(self, value):
		return value

	def _convertBool(self, value):
		if value == '':
			return irNull
		xvalue = value.lower()
		if xvalue in ('true', '1'):
			return True
		elif xvalue in ('false', '0'):
			return False

		# I'm not sure what to do here... Should we raise an exception because the data is invalid? Should just return True?
		raise ValueError('Unexpected value for bool type: %s' %(value,))

	@classmethod
	def canIndex(cls):
		return True

	def __new__(self, name, valueType=None):
		if not name:
			raise ValueError('IRField defined without a name!')

		return str.__new__(self, name)


class IRNullType(str):
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
		return str.__new__(self, '')

	def __eq__(self, otherVal):
		return bool(isinstance(otherVal, IRNullType))
	
	def __ne__(self, otherVal):
		return not bool(isinstance(otherVal, IRNullType))

	def __str__(self):
		return ''
	
	def __repr__(self):
		return 'IRNullType()'


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

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

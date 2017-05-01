# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


from . import IRField
from .null import irNull

from ..compat_str import getDefaultIREncoding, tobytes, to_unicode

# Note for this class, if encoding=None we fetch getDefaultIREncoding on every convert,
#   because some usage scenario somewhere may need to use a global and have it change depending on operation
class IRUnicodeField(IRField):
	'''
		IRUnicodeField - A field which supports storing/retrieving data in an arbitrary unicode encoding (may be different than global getDefaultIREncoding/setDefaultIREncoding)

		If "encoding" is None (default) - each time the value is converted getEncoding() will be called to get the encoding. This makes it roughly the same as
		a regular IRField.

		In practice, you may have fields with different encodings (different languages maybe, different platforms, etc), and through this you can support those cases.

		This field type is indeaxble, and the index is forced to be hashed.
	'''

	CAN_INDEX = True

	# We gotta hash this to ensure it works
	hashIndex = True

	def __init__(self, name='', encoding=None, defaultValue=irNull):
		'''
			__init__ - Create an IRUnicodeField

			@param name <str> - The field name
			
			@param encoding <None/str> - A specific encoding to use. If None, defaultIREncoding will be used.

			@param defaultValue - The default value for this field

			This field type is indeaxble, and the index is forced to be hashed.
		'''
		self.valueType = None
		self.encoding = encoding
		self.defaultValue = defaultValue


	def getEncoding(self):
		'''
			getEncoding - Get the encoding codec associated with this field.

				If you provided None, this will return the defaultIREncoding

			@return <str> - Encoding
		'''
		if not self.encoding:
			return getDefaultIREncoding()
		return self.encoding

	def _fromStorage(self, value):
		return to_unicode(value, encoding=self.getEncoding())

	def _toStorage(self, value):
		return tobytes(value, encoding=self.getEncoding())

	def _fromInput(self, value):
		return to_unicode(value, encoding=self.getEncoding())


	def toBytes(self, value):
		'''
			toBytes - Convert a value to bytes using the encoding specified on this field

			@param value <str> - The field to convert to bytes

			@return <bytes> - The object encoded using the codec specified on this field.

			NOTE: This method may go away.
		'''
		if type(value) == bytes:
			return value
		return value.encode(self.getEncoding())

	def _getReprProperties(self):
		return ['encoding=%s' %(repr(self.encoding), )]

	def copy(self):
		return self.__class__(name=self.name, encoding=self.encoding, defaultValue=self.defaultValue)

	def __new__(self, name='', encoding=None, defaultValue=irNull):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

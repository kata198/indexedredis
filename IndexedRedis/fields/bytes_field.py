# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.bytes - Ensures field is stored as "bytes"
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull

from ..compat_str import tobytes

class IRBytesField(IRField):
	'''
		IRBytesField - Ensure the data is always "bytes" type.
		
		Similar to IRRawField, except IRRawField does not touch encoding, this forces to bytes.

		This is replacement for BINARY_FIELDS

		An IRBytesField is indexable, and the index is forced to be hashed.
	'''

	CAN_INDEX = True
	hashIndex = True

	def __init__(self, name='', defaultValue=irNull, encoding=None):
		'''
			__init__ - Create an IRBytesField object

			@param name <str> - Field name

			@param defaultValue <any> default irNull - Default value for this field

			@param encoding <None/str> - If None, defaultIREncoding will be used when converting to bytes,
			  otherwise you can provide an explicit encoding

			An IRBytesField is indexable, and the index is forced to be hashed.
		'''
		self.valueType = None
		self.defaultValue = defaultValue
		self.encoding = encoding

	def _convertBytes(self, value):
		return tobytes(value, self.encoding)

	_fromStorage = _convertBytes

	_fromInput = _convertBytes

	_toStorage = _convertBytes

	def copy(self):
		return self.__class__(name=self.name, defaultValue=self.defaultValue, encoding=self.encoding)


	def __new__(self, name='', defaultValue=irNull, encoding=None):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

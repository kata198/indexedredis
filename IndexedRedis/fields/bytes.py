# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.bytes - Ensures field is stored as "bytes"
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, IR_NULL_STRINGS, irNull

from ..compat_str import tobytes

class IRBytesField(IRField):
	'''
		IRBytesField - Ensure the data is always "bytes" type.
		
		Similar to IRRawField, except IRRawField does not touch encoding, this forces to bytes.

		This is replacement for BINARY_FIELDS
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
		'''
		self.valueType = None
		self.defaultValue = defaultValue
		self.encoding = encoding

	def _convertBytes(self, value):
		return tobytes(value, self.encoding)

	_fromStorage = _convertBytes

	_fromInput = _convertBytes

	_toStorage = _convertBytes


	def __new__(self, name='', defaultValue=irNull, encoding=None):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

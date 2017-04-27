# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.b64 - Field type for base64 encoded/decoded fields
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull

from ..compat_str import tobytes, isStringy, isEmptyString

from base64 import b64decode, b64encode

try:
	unicode
except NameError:
	unicode = str

class IRBase64Field(IRField):
	'''
		IRBase64Field - Encode/Decode data automatically into base64 for storage and from for retrieval. 

		Data will be found on the object in bytes format (right after assignment, after fetching, etc). To convert to another format,
		  use an IRFieldChain.

		  Like, use it with an IRUnicodeField as the far left to have it be a utf-16 value, or use IRField(valueType=str) for a string, or IRField(valueType=int) for int, etc.
	'''

	CAN_INDEX = False

	def __init__(self, name='', defaultValue=irNull, encoding=None):
		'''
			__init__ - Create an IRBase64Field object.

			@param name <str> - Field name

			@param defaultValue <any> (Default irNull) - Default value of field

			@param encoding <None/str> (default None) - An explicit encoding to use when converting to bytes. If None, the global defaultIREncoding will be used.

		'''
		self.valueType = None
		self.encoding = encoding
		self.defaultValue = defaultValue

	def _fromStorage(self, value):
		if isEmptyString(value):
			return ''

		return b64decode(tobytes(value, self.encoding))

	def _fromInput(self, value):
		return tobytes(value, self.encoding)

	def _toStorage(self, value):
		if isEmptyString(value):
			return ''
		return b64encode(tobytes(value, self.encoding))

	def _getReprProperties(self):
		return ['encoding=%s' %(repr(self.encoding), )]

	def copy(self):
		return self.__class__(name=self.name, defaultValue=self.defaultValue, encoding=self.encoding)

	def __new__(self, name='', defaultValue=irNull, encoding=None):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

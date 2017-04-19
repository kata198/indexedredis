# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.b64 - Field type for base64 encoded/decoded fields
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull

from ..compat_str import tobytes, isStringy

from base64 import b64decode, b64encode

try:
	unicode
except NameError:
	unicode = str

class IRBase64Field(IRField):
	'''
		IRBase64Field - Encode/Decode data automatically into base64 for storage and from for retrieval. 
	'''

	CAN_INDEX = False

	def __init__(self, name='', defaultValue=irNull):
		# XXX: Maybe need to give this an "encoding" field incase it needs to decode a string? Or maybe a field type that does decoding itself?
		self.valueType = None
		self.defaultValue = irNull

	def convert(self, value=b''):
		if not isStringy(value) or not value:
			return value

		return b64decode(tobytes(value))

	def convertFromInput(self, value=''):
		return value

	def toStorage(self, value=b''):
		if not value:
			return ''
		return b64encode(tobytes(value))

	def _getReprProperties(self):
		return []

	def __new__(self, name='', defaultValue=irNull):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

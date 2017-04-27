# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


from . import IRField
from .null import irNull

from ..compat_str import getDefaultIREncoding, tobytes, to_unicode

import sys

# Don't actually need this, but it silences pyflakes
try:
	unicode
except NameError:
	unicode = str

# Note for this class, if encoding=None we fetch getDefaultIREncoding on every convert,
#   because some usage scenario somewhere may need to use a global and have it change depending on operation
class IRUnicodeField(IRField):
	'''
		IRUnicodeField - A field which supports storing/retrieving data in an arbitrary unicode encoding (may be different than global getDefaultIREncoding/setDefaultIREncoding)

		If "encoding" is None (default) - each time the value is converted getEncoding() will be called to get the encoding. This makes it roughly the same as
		a regular IRField.

		In practice, you may have fields with different encodings (different languages maybe, different platforms, etc), and through this you can support those cases.
	'''

	CAN_INDEX = True

	# We gotta hash this to ensure it works
	hashIndex = True

	def __init__(self, name='', encoding=None, defaultValue=irNull):
		self.valueType = None
		self.encoding = encoding
		self.defaultValue = defaultValue


	def getEncoding(self):
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

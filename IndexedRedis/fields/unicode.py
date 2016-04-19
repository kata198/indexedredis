# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


from . import IRField
from ..compat_str import getEncoding

import sys

# Don't actually need this, but it silences pyflakes
try:
	unicode
except NameError:
	unicode = str

# Note for this class, if encoding=None we fetch getEncoding on every convert,
#   because some usage scenario somewhere may need to use a global and have it change depending on operation
class IRUnicodeField(IRField):
	'''
		IRUnicodeField - A field which supports storing/retrieving data in an arbitrary unicode encoding (may be different than global getEncoding/setEncoding)

		If "encoding" is None (default) - each time the value is converted getEncoding() will be called to get the encoding. This makes it roughly the same as
		a regular IRField.

		In practice, you may have fields with different encodings (different languages maybe, different platforms, etc), and through this you can support those cases.
	'''

	def __init__(self, name, encoding=None):
		self.valueType = None
		self.encoding = encoding


	def getEncoding(self):
		if not self.encoding:
			return getEncoding()
		return self.encoding

	if sys.version_info.major == 2:
		def convert(self, value=u''):
			encoding = self.getEncoding()
			
			if not issubclass(value.__class__, unicode):
				if issubclass(value.__class__, str):
					return value.decode(encoding)
				else:
					return str(value).decode(encoding)
				
			return value
	else:
		def convert(self, value=u''):
			encoding = self.getEncoding()

			if not issubclass(value.__class__, str):
				if issubclass(value.__class__, bytes):
					return value.decode(encoding)
				else:
					return str(value)

			return value

	def toBytes(self, value):
		if type(value) == bytes:
			return value
		return value.encode(self.getEncoding())


	def __new__(self, name, encoding=None):
		return IRField.__new__(self, name)

# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

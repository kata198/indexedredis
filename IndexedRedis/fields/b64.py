# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.b64 - Field type for base64 encoded/decoded fields
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField

from ..compat_str import tobytes

from base64 import b64decode, b64encode

class IRBase64Field(IRField):
	'''
		IRBase64Field - Encode/Decode data automatically into base64 for storage and from for retrieval. 
	'''

	def __init__(self, name=''):
		# XXX: Maybe need to give this an "encoding" field incase it needs to decode a string? Or maybe a field type that does decoding itself?
		self.valueType = None

	def convert(self, value=b''):
		if not value:
			return value

		# TODO: do this better maybe?
		if not issubclass(value.__class__, (str, bytes)):
			return value

		try:
			return b64decode(tobytes(value))
		except Exception as e:
			# XXX: remove this print before release
			print ("Exception %s\n" %(str(e),))

		return value

	def toStorage(self, value=b''):
		if not value:
			return ''
		return b64encode(tobytes(value))

	def __new__(self, name=''):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

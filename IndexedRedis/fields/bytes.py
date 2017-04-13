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

	CAN_INDEX = False

	def __init__(self, name=''):
		self.valueType = None

	convert = IRField._convertBytes

	toStorage = IRField._convertBytes

	def __new__(self, name=''):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

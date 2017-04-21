# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.raw - Raw field, no encoding or decoding will occur.
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField
from .null import irNull, IR_NULL_STR, IR_NULL_STRINGS

class IRRawField(IRField):
	'''
		IRRawField - Return the raw data from Redis, without any extra encoding, decoding, or translation
	'''

	CAN_INDEX = False

	def __init__(self, name='', defaultValue=irNull):
		self.valueType = None
		self.defaultValue = defaultValue

	def _fromStorage(self, value):
		return value

	def _fromInput(self, value):
		return value

	def _toStorage(self, value):
		return value

	def _getReprProperties(self):
		return []

	def __new__(self, name='', defaultValue=irNull):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

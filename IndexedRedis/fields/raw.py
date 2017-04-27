# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.raw - Raw field, no encoding or decoding will occur.
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull

class IRRawField(IRField):
	'''
		IRRawField - Return the raw data from Redis, without any extra encoding, decoding, or translation.

		NOTE: This type does NOT support irNull, nor default values (because no encoding/decoding).

		After fetch, the value will always be bytes (Again, no translation).
	'''

	CAN_INDEX = False

	def __init__(self, name=''):
		'''
			__init__ - Create an IRRawField. Only takes a name
		'''
		self.valueType = None
		self.defaultValue = ''

	def _fromStorage(self, value):
		return value

	fromStorage = _fromStorage

	def _fromInput(self, value):
		return value
	
	fromInput = _fromInput

	def _toStorage(self, value):
		return value
	
	toStorage = _toStorage

	def _getReprProperties(self):
		return []

	def copy(self):
		return self.__class__(name=self.name)

	def __new__(self, name=''):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

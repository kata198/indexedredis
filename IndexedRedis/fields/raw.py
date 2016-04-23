# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField

class IRRawField(IRField):
	'''
		IRRawField - Return the raw data from Redis, without any extra encoding, decoding, or translation
	'''

	CAN_INDEX = False

	def __init__(self, name=''):
		self.valueType = None

	def convert(self, value=b''):
		return value

	def toStorage(self, value=b''):
		return value

	def __new__(self, name=''):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

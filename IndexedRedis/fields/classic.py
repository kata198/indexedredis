# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.classic - The IRField type which behaves like the "classic" IndexedRedis string-named fields.
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField

from ..compat_str import tobytes, encoded_str_type

class IRClassicField(IRField):
	'''
		IRClassicField - The IRField type which behaves like the "classic" IndexedRedis string-named fields.
		

		This will store and retrieve data encoding into the default encoding (@see IndexedRedis.compat_str.setDefaultIREncoding)

		and have a default value of empty string.
	'''

	CAN_INDEX = True

	def __init__(self, name='', hashIndex=False):
		IRField.__init__(self, name=name, valueType=encoded_str_type, hashIndex=hashIndex, defaultValue='')

	def __new__(self, name='', hashIndex=False):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

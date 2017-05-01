# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.classic - The IRField type which behaves like the "classic" IndexedRedis string-named fields.
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField

class IRClassicField(IRField):
	'''
		IRClassicField - The IRField type which behaves like the "classic" IndexedRedis string-named fields.
		

		This will store and retrieve data encoding into the default encoding (@see IndexedRedis.compat_str.setDefaultIREncoding)

		and have a default value of empty string.

		An IRClassicField is indexable, but there is no option to hash the index.
	'''

	CAN_INDEX = True

	def __init__(self, name=''):
		'''
			__init__ - Create an IRClassicField.
			  This field behaves as a plain string entry in FIELDS did prior to 5.0.0.

			  The default value is empty string, and it stores strings using defaultIREncoding.

			  Consider changing to an IRField or one of the other many types.

			  @param name <str> - Field name
		'''
		IRField.__init__(self, name=name, valueType=str, defaultValue='')

	def __new__(self, name=''):
		return IRField.__new__(self, name)

	def copy(self):
		return self.__class__(name=self.name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

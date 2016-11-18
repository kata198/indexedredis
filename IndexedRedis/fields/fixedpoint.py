# Copyright (c) 2014, 2015, 2016 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.fixedpoint - Fixed-point float to allow float values to be safely used cross-platform and for indexes and filtering.
#    Trying to use a native float will yield different results on different architectures, python versions, etc.
#

# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :

from . import IRField, irNull

__all__ = ('IRFixedPointField',)

class IRFixedPointField(IRField):
	'''
		IRFixedPointField - A field which represents a real number (a whole part and a fractional part), such as 3.7 or 3.14159).

	        Use this instead of an IRField(...valueType=float) to get accurate results across platforms, systems, and python versions, and to use for indexing.



	'''

	CAN_INDEX = True

	def __init__(self, name='', decimalPlaces=5):
		'''
			__init__ - Create this object.

			@param name <str> - Field name (or blank if used in an IRFieldChain)
			@param decimalPlaces <int> - The number of decimal places to use (precision). Values will be rounded to this many places, and always have
			  this many digits after the decimal point.
		'''
		self.decimalPlaces = decimalPlaces

	def convert(self, value):
		if self._isNullValue(value):
			return irNull

		return float(value)

	def toStorage(self, value):
		if self._isNullValue(value):
			return irNull

		if type(value) != float:
			value = float(value)

		return self._getFormatStr() % (value,)

	def _getFormatStr(self):
		return '%.' + str(self.decimalPlaces) + 'f'

	def __new__(self, name='', decimalPlaces=5):
		return IRField.__new__(self, name)


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
